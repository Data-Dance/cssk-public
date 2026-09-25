# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

MODULE = "odoo.addons.l10n_cssk_vies.models.res_partner"


@tagged("post_install", "-at_install")
class TestViesCron(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.vies_use_direct = True
        # A checksum-valid SK IČ DPH: base_vat rejects the number this fixture used
        # to carry (SK2022334455), so setUpClass died before a single test ran.
        cls.env.company.vat = "SK2022749619"
        Partner = cls.env["res.partner"].with_context(no_vat_validation=True)
        cls.eu_sk = Partner.create({"name": "EU SK", "vat": "SK2023456787"})
        cls.eu_el = Partner.create({"name": "EU Greek", "vat": "EL123456783"})
        cls.non_eu = Partner.create(
            {"name": "Swiss", "vat": "CHE-116.281.710"}
        )

    def _run_cron(self, status="valid", **kw):
        """Run the cron with the network layer fully mocked; return the list
        of partner VATs that were actually checked."""
        checked = []

        def fake_check(partner, store=True):
            checked.append(partner.vat)
            return status

        PartnerCls = type(self.env["res.partner"])
        CronCls = type(self.env["ir.cron"])
        with patch.object(
            PartnerCls, "_check_vies_direct", autospec=True,
            side_effect=fake_check,
        ), patch.object(
            CronCls, "_commit_progress", return_value=float("inf"),
        ), patch(f"{MODULE}.time.sleep") as mock_sleep:
            self.env["res.partner"]._cron_check_vies_direct(**kw)
        return checked, mock_sleep

    def test_eu_prefixes_derived_from_country_group(self):
        prefixes = self.env["res.partner"]._vies_eu_vat_prefixes()
        self.assertIn("SK", prefixes)
        self.assertIn("CZ", prefixes)
        self.assertIn("EL", prefixes)  # Greece: EL, not GR
        self.assertNotIn("GR", prefixes)
        self.assertIn("XI", prefixes)  # Northern Ireland
        self.assertNotIn("CH", prefixes)
        self.assertNotIn("GB", prefixes)

    def test_cron_skips_non_eu_vats(self):
        """Non-EU-format VATs must not occupy the batch window."""
        checked, _sleep = self._run_cron()
        self.assertIn(self.eu_sk.vat, checked)
        self.assertIn(self.eu_el.vat, checked)
        self.assertNotIn(self.non_eu.vat, checked)

    def test_faulting_partner_rotates_out_of_window(self):
        """A faulting partner is stamped and leaves the window, instead of
        being retried forever and starving everyone behind it."""
        checked1, _s = self._run_cron(status="fault")
        self.assertIn(self.eu_sk.vat, checked1)
        self.assertTrue(self.eu_sk.vies_fault_date)
        self.assertFalse(self.eu_sk.vies_check_date)
        # Second run within the stale window: the faulting partner is gone.
        checked2, _s = self._run_cron(status="fault")
        self.assertNotIn(self.eu_sk.vat, checked2)

    def test_cron_throttles_between_calls(self):
        checked, mock_sleep = self._run_cron()
        self.assertTrue(checked)
        self.assertEqual(mock_sleep.call_count, len(checked))
        mock_sleep.assert_called_with(0.5)
