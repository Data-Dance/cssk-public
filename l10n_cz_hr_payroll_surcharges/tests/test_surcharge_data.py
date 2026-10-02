# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The shipped statutory data, asserted against the published figures.

These are the numbers an employer is audited against, so they are written out
here rather than read back off the records under test.
"""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

MOD = "l10n_cz_hr_payroll_surcharges"


@tagged("post_install", "-at_install")
class TestCzSurchargeData(TransactionCase):
    # -- minimum wage -------------------------------------------------------
    def test_minimum_wage_2026(self):
        wage = self.env.ref(MOD + ".minimum_wage_2026")
        self.assertEqual(wage.amount_monthly, 22400.0)
        self.assertEqual(wage.amount_hourly, 134.40)

    def test_minimum_wage_2025(self):
        wage = self.env.ref(MOD + ".minimum_wage_2025")
        self.assertEqual(wage.amount_monthly, 20800.0)
        self.assertEqual(wage.amount_hourly, 124.40)

    def test_lookup_picks_the_vintage_in_force(self):
        Wage = self.env["l10n.cz.minimum.wage"]
        self.assertEqual(
            Wage._get_for_date(date(2026, 6, 30)).amount_monthly, 22400.0
        )
        self.assertEqual(
            Wage._get_for_date(date(2025, 12, 31)).amount_monthly, 20800.0
        )

    def test_lookup_before_any_record_raises(self):
        """Silently returning nothing would become a zero top-up."""
        with self.assertRaises(UserError):
            self.env["l10n.cz.minimum.wage"]._get_for_date(date(2000, 1, 1))

    # -- surcharge percentages ---------------------------------------------
    def test_statutory_percentages_shipped(self):
        rate = self.env.ref(MOD + ".wage_surcharge_rate_2024")
        self.assertEqual(rate.prescas_pct, 25.0)   # § 114
        self.assertEqual(rate.svatek_pct, 100.0)   # § 115
        self.assertEqual(rate.nocni_pct, 10.0)     # § 116
        self.assertEqual(rate.ztizene_pct, 10.0)   # § 117
        self.assertEqual(rate.vikend_pct, 10.0)    # § 118

    def test_agreed_percentages_ship_empty(self):
        """A default here would apply someone else's collective agreement."""
        rate = self.env.ref(MOD + ".wage_surcharge_rate_2024")
        self.assertFalse(rate.nocni_agreed_pct)
        self.assertFalse(rate.vikend_agreed_pct)

    def test_percentage_for_reads_through_to_the_kernel(self):
        rate = self.env.ref(MOD + ".wage_surcharge_rate_2024")
        self.assertEqual(rate.percentage_for("PRESCAS"), 25.0)
        self.assertEqual(rate.percentage_for("NOCNI"), 10.0)
        # No agreed figure configured, so the statutory one stands.
        self.assertEqual(rate.percentage_for("NOCNI", agreed=True), 10.0)

    def test_a_zero_statutory_percentage_is_refused(self):
        rate = self.env.ref(MOD + ".wage_surcharge_rate_2024")
        with self.assertRaises(UserError):
            rate.write({"nocni_pct": 0.0})

    # -- the contract fields ------------------------------------------------
    def test_contract_carries_the_two_surcharge_inputs(self):
        fields_ = self.env["hr.version"]._fields
        self.assertIn("l10n_cz_difficult_factors", fields_)
        self.assertIn("l10n_cz_surcharge_agreed", fields_)

    def test_no_czech_wage_level_field_exists(self):
        """Zaručená mzda was abolished for the private sector in 2025.

        The Slovak module carries a six-level stupeň náročnosti on the
        contract and the job. Porting that to Czechia would invent a
        classification the commercial sector no longer has — zákon č. 230/2024
        Sb. left one minimum wage for every private employer. Asserted so the
        omission reads as a decision rather than an oversight.
        """
        self.assertNotIn("l10n_cz_wage_level", self.env["hr.version"]._fields)
