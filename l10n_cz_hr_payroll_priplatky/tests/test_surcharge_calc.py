# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Unit tests for the Odoo-free Czech surcharge kernel.

Hand-derived figures throughout. A test that recomputes the implementation
proves only that the code is self-consistent, which is worthless for a
statutory minimum.
"""

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_cz_hr_payroll_priplatky.models import surcharge_calc as sc


@tagged("post_install", "-at_install")
class TestCzSurchargeCalc(TransactionCase):
    """No database is touched; TransactionCase is only the runner."""

    RATES = {
        "prescas_pct": 25.0,
        "svatek_pct": 100.0,
        "nocni_pct": 10.0,
        "nocni_agreed_pct": 15.0,
        "vikend_pct": 10.0,
        "vikend_agreed_pct": 0.0,
        "ztizene_pct": 10.0,
    }

    # -- which base each surcharge takes ------------------------------------
    def test_only_the_difficult_environment_uses_the_minimum_wage(self):
        """The single most important difference from the Slovak kernel.

        In Slovakia most surcharges are a percentage of the minimum wage; in
        Czechia only § 117 is, and the rest follow average earnings. Getting
        this backwards produces plausible money that is wrong for everyone
        whose average earnings differ from the minimum wage.
        """
        self.assertEqual(
            sc.SURCHARGE_BASE[sc.CODE_DIFFICULT], sc.BASE_MIN_WAGE
        )
        for code in (
            sc.CODE_OVERTIME,
            sc.CODE_HOLIDAY,
            sc.CODE_NIGHT,
            sc.CODE_WEEKEND,
        ):
            self.assertEqual(
                sc.SURCHARGE_BASE[code],
                sc.BASE_AVG_EARNINGS,
                "%s must be a percentage of average earnings" % code,
            )

    # -- percentages --------------------------------------------------------
    def test_statutory_percentages(self):
        self.assertEqual(sc.surcharge_pct(self.RATES, sc.CODE_OVERTIME), 25.0)
        self.assertEqual(sc.surcharge_pct(self.RATES, sc.CODE_HOLIDAY), 100.0)
        self.assertEqual(sc.surcharge_pct(self.RATES, sc.CODE_NIGHT), 10.0)
        self.assertEqual(sc.surcharge_pct(self.RATES, sc.CODE_WEEKEND), 10.0)
        self.assertEqual(sc.surcharge_pct(self.RATES, sc.CODE_DIFFICULT), 10.0)

    def test_agreed_rate_applies_only_where_the_statute_allows_it(self):
        """§ 116 and § 118 permit an agreed minimum; § 114/115/117 do not."""
        self.assertEqual(
            sc.surcharge_pct(self.RATES, sc.CODE_NIGHT, agreed=True), 15.0
        )
        # No agreed figure configured -> falls back to the statutory one.
        self.assertEqual(
            sc.surcharge_pct(self.RATES, sc.CODE_WEEKEND, agreed=True), 10.0
        )
        # Overtime has no agreed variant at all, so the flag is inert.
        self.assertEqual(
            sc.surcharge_pct(self.RATES, sc.CODE_OVERTIME, agreed=True), 25.0
        )

    def test_missing_percentage_raises_rather_than_paying_nothing(self):
        """A statutory floor must never silently become 0 %."""
        with self.assertRaises(KeyError):
            sc.surcharge_pct({"prescas_pct": 25.0}, sc.CODE_NIGHT)

    def test_unknown_code_raises(self):
        with self.assertRaises(KeyError):
            sc.surcharge_pct(self.RATES, "NOT_A_CODE")

    # -- money --------------------------------------------------------------
    def test_overtime_amount(self):
        """8 h overtime at 25 % of a 200.00 Kč average hourly wage = 400.00."""
        self.assertAlmostEqual(
            sc.surcharge_amount(8.0, 200.0, 25.0), 400.0, places=2
        )

    def test_holiday_amount_is_a_whole_extra_hour(self):
        """§ 115 at 100 %: the supplement equals the hourly earnings."""
        self.assertAlmostEqual(
            sc.surcharge_amount(6.0, 187.50, 100.0), 1125.0, places=2
        )

    def test_difficult_environment_pays_per_factor(self):
        """§ 117 is owed for EACH aggravating influence.

        Two influences on a 134.40 Kč minimum hourly wage: 8 h x 134.40 x
        10 % x 2 = 215.04.
        """
        self.assertAlmostEqual(
            sc.surcharge_amount(8.0, 134.40, 10.0, factors=2), 215.04, places=2
        )

    def test_no_factors_means_no_difficult_environment_pay(self):
        self.assertEqual(
            sc.surcharge_amount(8.0, 134.40, 10.0, factors=0), 0.0
        )

    def test_amounts_round_up_because_the_figure_is_a_floor(self):
        """1 h at 10 % of 100.055 = 10.0055 -> 10.01, never 10.00."""
        self.assertAlmostEqual(
            sc.surcharge_amount(1.0, 100.055, 10.0), 10.01, places=2
        )

    def test_zero_inputs_pay_nothing(self):
        self.assertEqual(sc.surcharge_amount(0.0, 200.0, 25.0), 0.0)
        self.assertEqual(sc.surcharge_amount(8.0, 0.0, 25.0), 0.0)
        self.assertEqual(sc.surcharge_amount(8.0, 200.0, 0.0), 0.0)

    # -- minimum wage for a shorter week -----------------------------------
    def test_shorter_established_week_raises_the_hourly_claim(self):
        """37.5 h week: 134.40 x 40 / 37.5 = 143.36."""
        self.assertAlmostEqual(
            sc.min_wage_hourly(134.40, 37.5), 143.36, places=2
        )

    def test_a_longer_week_never_lowers_the_claim(self):
        self.assertAlmostEqual(sc.min_wage_hourly(134.40, 42.5), 134.40, places=2)

    def test_full_week_leaves_the_claim_alone(self):
        self.assertAlmostEqual(sc.min_wage_hourly(134.40, 40.0), 134.40, places=2)

    # -- doplatek do minimální mzdy ----------------------------------------
    def test_hourly_topup(self):
        """160 h paid 20 000 Kč = 125.00/h against a 134.40 claim.

        Shortfall 9.40/h x 160 h = 1504.00.
        """
        self.assertAlmostEqual(
            sc.min_wage_topup_hourly(20000.0, 160.0, 134.40), 1504.0, places=2
        )

    def test_no_hourly_topup_when_already_above(self):
        self.assertEqual(
            sc.min_wage_topup_hourly(30000.0, 160.0, 134.40), 0.0
        )

    def test_monthly_topup_is_prorated_by_hours_actually_worked(self):
        """Half a month worked owes half the monthly claim.

        80 of 160 full-time hours, paid 10 000 against a 22 400 claim:
        claim = 11 200, top-up = 1 200.
        """
        self.assertAlmostEqual(
            sc.min_wage_topup_monthly(10000.0, 80.0, 160.0, 22400.0),
            1200.0,
            places=2,
        )

    def test_monthly_topup_ratio_is_clamped_at_one(self):
        """Extra hours do not raise the monthly minimum."""
        self.assertEqual(
            sc.min_wage_topup_monthly(22400.0, 200.0, 160.0, 22400.0), 0.0
        )

    def test_monthly_topup_needs_a_full_time_reference(self):
        """Without it the proration is undefined, so nothing is claimed."""
        self.assertEqual(
            sc.min_wage_topup_monthly(10000.0, 80.0, 0.0, 22400.0), 0.0
        )
