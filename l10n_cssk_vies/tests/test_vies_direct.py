from datetime import date
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestViesDirect(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "ACME EU s.r.o.", "vat": "SK2023456787"}
        )
        # A checksum-valid SK IČ DPH: base_vat rejects the number this fixture used
        # to carry (SK2022334455), so setUpClass died before a single test ran.
        cls.env.company.vat = "SK2022749619"

    # A valid approximate VIES response (requester + traderName supplied):
    # the registered name/address come back in name/address, while the
    # traderName echo field carries the "---" placeholder.
    VALID_RESP = {
        "countryCode": "SK",
        "vatNumber": "2023456787",
        "requestDate": "2026-06-11T17:36:15.872Z",
        "valid": True,
        "requestIdentifier": "WAPIAAAAX3lU8bHe",
        "name": "ACME EU s. r. o.",
        "address": "Nová 1184/38\n90024 Veľký Biel\nSlovensko",
        "traderName": "---",
        "traderNameMatch": "VALID",
    }

    # ---- result mapping / proof storage (offline) -----------------------

    def test_valid_stores_consultation_proof(self):
        status = self.partner._apply_vies_direct_result(self.VALID_RESP, store=True)
        self.assertEqual(status, "valid")
        self.assertEqual(
            self.partner.vies_consultation_number, "WAPIAAAAX3lU8bHe"
        )
        # Registered name comes from "name", not the "---" traderName echo.
        self.assertEqual(self.partner.vies_trader_name, "ACME EU s. r. o.")
        self.assertEqual(
            self.partner.vies_address, "Nová 1184/38\n90024 Veľký Biel\nSlovensko"
        )
        self.assertEqual(self.partner.vies_name_match, "VALID")
        self.assertEqual(self.partner.vies_request_date, date(2026, 6, 11))
        self.assertTrue(self.partner.vies_check_date)

    def test_invalid_clears_stale_proof(self):
        self.partner._apply_vies_direct_result(self.VALID_RESP, store=True)
        status = self.partner._apply_vies_direct_result(
            {"valid": False, "requestDate": "2026-06-11T00:00:00.000Z"}, store=True
        )
        self.assertEqual(status, "invalid")
        self.assertFalse(self.partner.vies_consultation_number)
        # The check still timestamps when it ran.
        self.assertTrue(self.partner.vies_check_date)
        # ...and the earlier proof is still in the log.
        self.assertIn(
            "WAPIAAAAX3lU8bHe",
            self.partner.vies_check_ids.mapped("consultation_number"))

    def test_transient_fault_preserves_proof(self):
        self.partner._apply_vies_direct_result(self.VALID_RESP, store=True)
        status = self.partner._apply_vies_direct_result(
            {"valid": False, "userError": "MS_UNAVAILABLE"}, store=True
        )
        self.assertEqual(status, "fault")
        # The fault is logged but does not replace the last answer.
        self.assertEqual(self.partner.vies_consultation_number, "WAPIAAAAX3lU8bHe")
        self.assertTrue(self.partner.vies_fault_date)
        self.assertEqual(
            self.partner.vies_check_ids[:1].fault_reason, "MS_UNAVAILABLE")

    def test_store_false_writes_nothing(self):
        status = self.partner._apply_vies_direct_result(self.VALID_RESP, store=False)
        self.assertEqual(status, "valid")
        self.assertFalse(self.partner.vies_consultation_number)
        self.assertFalse(self.partner.vies_check_date)

    # ---- network wiring (mocked) ----------------------------------------

    def test_check_direct_posts_requester_and_stores(self):
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.json.return_value = self.VALID_RESP
        with patch(
            "odoo.addons.l10n_cssk_vies.models.res_partner.requests.post",
            return_value=fake,
        ) as mock_post:
            status = self.partner._check_vies_direct(store=True)
        self.assertEqual(status, "valid")
        # The qualified call carried the company as requester and sent the
        # partner name for the approximate match.
        _args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["countryCode"], "SK")
        self.assertEqual(kwargs["json"]["vatNumber"], "2023456787")
        self.assertEqual(kwargs["json"]["requesterMemberStateCode"], "SK")
        self.assertEqual(kwargs["json"]["traderName"], "ACME EU s.r.o.")
        self.assertEqual(self.partner.vies_consultation_number, "WAPIAAAAX3lU8bHe")

    def test_check_direct_network_error_is_fault(self):
        import requests as _requests

        with patch(
            "odoo.addons.l10n_cssk_vies.models.res_partner.requests.post",
            side_effect=_requests.exceptions.ConnectionError("boom"),
        ):
            status = self.partner._check_vies_direct(store=True)
        self.assertEqual(status, "fault")


@tagged("post_install", "-at_install")
class TestViesPerCompany(TransactionCase):
    """Two companies sharing a partner keep their own proof."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Shared EU s.r.o.", "vat": "SK2023456787"})
        cls.company_a = cls.env.company
        cls.company_a.vat = "SK2022749619"
        cls.company_b = cls.env["res.company"].create({
            "name": "Second Co", "country_id": cls.env.ref("base.cz").id,
        })

    def _answer(self, company, number):
        partner = self.partner.with_company(company)
        partner._apply_vies_direct_result(
            dict(TestViesDirect.VALID_RESP, requestIdentifier=number), store=True)
        return partner

    def test_each_company_sees_its_own_consultation_number(self):
        self._answer(self.company_a, "AAA")
        self.assertFalse(
            self.partner.with_company(self.company_b).vies_consultation_number)
        self._answer(self.company_b, "BBB")
        self.assertEqual(
            self.partner.with_company(self.company_a).vies_consultation_number,
            "AAA")
        self.assertEqual(
            self.partner.with_company(self.company_b).vies_consultation_number,
            "BBB")
        checks = self.partner.sudo().vies_check_ids
        self.assertEqual(set(checks.mapped("company_id").ids),
                         {self.company_a.id, self.company_b.id})

    def test_the_log_records_the_requester(self):
        self._answer(self.company_a, "AAA")
        check = self.partner.sudo().vies_check_ids[:1]
        self.assertEqual(check.requester_vat, "SK2022749619")
        self.assertEqual(check.vat, "SK2023456787")
        self.assertEqual(check.user_id, self.env.user)

    def test_a_legacy_check_serves_until_the_company_checks(self):
        self.env["cssk.vies.check"].create({
            "partner_id": self.partner.id, "result": "valid",
            "consultation_number": "LEGACY",
        })
        self.assertEqual(
            self.partner.with_company(self.company_b).vies_consultation_number,
            "LEGACY")
        self._answer(self.company_b, "BBB")
        self.assertEqual(
            self.partner.with_company(self.company_b).vies_consultation_number,
            "BBB")

    def test_users_cannot_write_the_log(self):
        from odoo.exceptions import AccessError

        user = self.env["res.users"].create({
            "name": "Clerk", "login": "vies_clerk",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        self._answer(self.company_a, "AAA")
        check = self.partner.sudo().vies_check_ids[:1]
        with self.assertRaises(AccessError):
            check.with_user(user).write({"consultation_number": "FORGED"})
