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
        self.partner.vies_consultation_number = "OLD123"
        status = self.partner._apply_vies_direct_result(
            {"valid": False, "requestDate": "2026-06-11T00:00:00.000Z"}, store=True
        )
        self.assertEqual(status, "invalid")
        self.assertFalse(self.partner.vies_consultation_number)
        # The check still timestamps when it ran.
        self.assertTrue(self.partner.vies_check_date)

    def test_transient_fault_preserves_proof(self):
        self.partner.vies_consultation_number = "KEEP99"
        self.partner.vies_check_date = "2026-06-01 08:00:00"
        status = self.partner._apply_vies_direct_result(
            {"valid": False, "userError": "MS_UNAVAILABLE"}, store=True
        )
        self.assertEqual(status, "fault")
        # Nothing overwritten on a service fault.
        self.assertEqual(self.partner.vies_consultation_number, "KEEP99")

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
