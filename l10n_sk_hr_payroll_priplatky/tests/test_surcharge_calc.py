# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Worked examples for the surcharge arithmetic.

These derive from ``TransactionCase`` rather than ``unittest.TestCase`` even
though the code under test needs no database: Odoo's test loader collects only
classes carrying its test tags, so a plain ``unittest.TestCase`` here would be
silently skipped by ``--test-enable`` and the suite would report success
without running a line of it.
"""

from odoo.tests import TransactionCase

from ..models.surcharge_calc import (
    CODE_NIGHT,
    CODE_OVERTIME,
    CODE_SATURDAY,
    CODE_SUNDAY,
    min_wage_hourly,
    min_wage_topup_hourly,
    min_wage_topup_monthly,
    surcharge_amount,
    surcharge_pct,
)

# The 1 June 2023 percentages, as shipped in data.
RATES = {
    "noc_pct": 40.0,
    "noc_risk_pct": 50.0,
    "noc_reduced_pct": 35.0,
    "sobota_pct": 50.0,
    "sobota_reduced_pct": 45.0,
    "nedela_pct": 100.0,
    "nedela_reduced_pct": 90.0,
    "stazeny_pct": 20.0,
    "pohotovost_pct": 20.0,
    "sviatok_pct": 100.0,
    "nadcas_pct": 25.0,
    "nadcas_risk_pct": 35.0,
}

MIN_HOURLY_2026 = 5.259
MIN_HOURLY_2025 = 4.690


class TestSurchargePct(TransactionCase):
    def test_standard_rates(self):
        self.assertEqual(surcharge_pct(RATES, CODE_NIGHT), 40.0)
        self.assertEqual(surcharge_pct(RATES, CODE_SATURDAY), 50.0)
        self.assertEqual(surcharge_pct(RATES, CODE_SUNDAY), 100.0)
        self.assertEqual(surcharge_pct(RATES, CODE_OVERTIME), 25.0)

    def test_risk_rate_applies_where_supported(self):
        self.assertEqual(surcharge_pct(RATES, CODE_NIGHT, risk=True), 50.0)
        self.assertEqual(surcharge_pct(RATES, CODE_OVERTIME, risk=True), 35.0)

    def test_risk_flag_ignored_where_no_risk_rate_exists(self):
        # There is no risky-work variant of the Saturday surcharge.
        self.assertEqual(surcharge_pct(RATES, CODE_SATURDAY, risk=True), 50.0)

    def test_reduced_rate_by_collective_agreement(self):
        self.assertEqual(surcharge_pct(RATES, CODE_NIGHT, reduced=True), 35.0)
        self.assertEqual(surcharge_pct(RATES, CODE_SATURDAY, reduced=True), 45.0)
        self.assertEqual(surcharge_pct(RATES, CODE_SUNDAY, reduced=True), 90.0)

    def test_risk_beats_reduced(self):
        """§ 122a ods. 3 bars the reduced night rate for risky work."""
        self.assertEqual(
            surcharge_pct(RATES, CODE_NIGHT, risk=True, reduced=True), 50.0
        )

    def test_a_missing_base_percentage_raises_rather_than_paying_zero(self):
        """Silently paying 0 % of a statutory minimum is an underpayment."""
        with self.assertRaises(KeyError):
            surcharge_pct({}, CODE_NIGHT)

    def test_an_unknown_code_raises(self):
        with self.assertRaises(KeyError):
            surcharge_pct(RATES, "NEEXISTUJE")

    def test_a_missing_optional_variant_falls_back_to_the_base(self):
        """Only the base rate is mandatory; the variants may be absent."""
        self.assertEqual(surcharge_pct({"noc_pct": 40.0}, CODE_NIGHT, risk=True), 40.0)


class TestSurchargeAmount(TransactionCase):
    def test_night_shift_2026(self):
        # 8 night hours at 40 % of €5.259 = €16.8288 -> €16.83
        self.assertEqual(surcharge_amount(8, MIN_HOURLY_2026, 40.0), 16.83)

    def test_sunday_is_the_whole_minimum_hourly_wage(self):
        # 12 Sunday hours at 100 % of €5.259 = €63.108 -> €63.11
        self.assertEqual(surcharge_amount(12, MIN_HOURLY_2026, 100.0), 63.11)

    def test_saturday_2025_reduced(self):
        # 6 Saturday hours at 45 % of €4.690 = €12.663 -> €12.67
        self.assertEqual(surcharge_amount(6, MIN_HOURLY_2025, 45.0), 12.67)

    def test_overtime_uplift_on_average_earnings(self):
        # 10 overtime hours at 25 % of €9.4321 average = €23.58025 -> €23.59
        self.assertEqual(surcharge_amount(10, 9.4321, 25.0), 23.59)

    def test_rounds_up_never_down(self):
        """Every rate is a statutory floor, so a cent may only be added."""
        # 1 hour at 40 % of €5.259 = €2.1036; half-up would give €2.10.
        self.assertEqual(surcharge_amount(1, MIN_HOURLY_2026, 40.0), 2.11)

    def test_exact_cent_is_not_bumped(self):
        # 100 hours at 50 % of €4.690 = €234.50 exactly.
        self.assertEqual(surcharge_amount(100, MIN_HOURLY_2025, 50.0), 234.50)

    def test_zero_inputs(self):
        self.assertEqual(surcharge_amount(0, MIN_HOURLY_2026, 40.0), 0.0)
        self.assertEqual(surcharge_amount(8, 0.0, 40.0), 0.0)
        self.assertEqual(surcharge_amount(8, MIN_HOURLY_2026, 0.0), 0.0)


class TestMinimumWageClaim(TransactionCase):
    def test_forty_hour_week_is_unchanged(self):
        self.assertEqual(min_wage_hourly(5.259, 40.0), 5.259)

    def test_shorter_week_raises_the_hourly_claim(self):
        # 38.75 h week: 5.259 x 40 / 38.75
        self.assertAlmostEqual(min_wage_hourly(5.259, 38.75), 5.4286, places=4)
        # 37.5 h week: 5.259 x 40 / 37.5
        self.assertAlmostEqual(min_wage_hourly(5.259, 37.5), 5.6096, places=4)

    def test_longer_week_does_not_lower_it(self):
        """§ 120 ods. 5 only ever raises the figure."""
        self.assertEqual(min_wage_hourly(5.259, 42.5), 5.259)

    def test_missing_calendar_falls_back_to_the_quoted_figure(self):
        self.assertEqual(min_wage_hourly(5.259, 0.0), 5.259)


class TestMinimumWageTopupHourly(TransactionCase):
    """The hourly comparison, which applies to hourly-paid contracts."""

    def test_no_topup_when_the_wage_already_clears_the_claim(self):
        # €1200 over 174 h = €6.90/h, well above the level-1 €5.259.
        self.assertEqual(min_wage_topup_hourly(1200.0, 174.0, 5.259), 0.0)

    def test_topup_to_level_1(self):
        # €800 over 174 h = €4.5977/h; claim €5.259 -> shortfall €0.6613/h
        # over 174 h = €115.066 -> €115.07.
        self.assertEqual(min_wage_topup_hourly(800.0, 174.0, 5.259), 115.07)

    def test_topup_to_a_higher_difficulty_level(self):
        # €6.592 x 174 h = €1147.008 owed against €915 paid.
        self.assertEqual(min_wage_topup_hourly(915.0, 174.0, 6.592), 232.01)

    def test_part_month_needs_no_proration(self):
        """The per-hour comparison prorates itself."""
        full = min_wage_topup_hourly(800.0, 174.0, 5.259)
        half = min_wage_topup_hourly(400.0, 87.0, 5.259)
        self.assertAlmostEqual(half, full / 2, places=1)

    def test_no_hours_means_no_claim(self):
        self.assertEqual(min_wage_topup_hourly(0.0, 0.0, 5.259), 0.0)

    def test_exactly_at_the_claim(self):
        self.assertEqual(min_wage_topup_hourly(5.259 * 174.0, 174.0, 5.259), 0.0)


class TestMinimumWageTopupMonthly(TransactionCase):
    """The monthly comparison, which applies to salaried contracts."""

    def test_the_monthly_minimum_is_lawful_in_a_176_hour_month(self):
        """The regression an hourly comparison would have caused.

        June 2026 schedules 176 hours, but the €5.259 hourly figure is €915
        over the statutory 174. An employee paid exactly €915 clears the
        monthly minimum and owes nothing, even though €915/176 = €5.199 sits
        under the hourly figure.
        """
        self.assertEqual(min_wage_topup_monthly(915.0, 176.0, 176.0, 915.0), 0.0)
        # ...whereas the hourly comparison would have invented a top-up.
        self.assertGreater(min_wage_topup_hourly(915.0, 176.0, 5.259), 0.0)

    def test_topup_to_level_1(self):
        self.assertEqual(min_wage_topup_monthly(800.0, 176.0, 176.0, 915.0), 115.0)

    def test_topup_to_a_higher_difficulty_level(self):
        # Level 3 in 2026 is €1147/month.
        self.assertEqual(min_wage_topup_monthly(915.0, 176.0, 176.0, 1147.0), 232.0)

    def test_part_month_prorates_the_claim(self):
        """§ 120 ods. 4 — half a month worked, half the claim."""
        # Claim 915 x 88/176 = 457.50 against €400 paid.
        self.assertEqual(min_wage_topup_monthly(400.0, 88.0, 176.0, 915.0), 57.50)

    def test_a_part_timer_on_a_proportionate_wage_owes_nothing(self):
        self.assertEqual(min_wage_topup_monthly(457.50, 88.0, 176.0, 915.0), 0.0)

    def test_the_denominator_is_full_time_not_the_part_timers_own_schedule(self):
        """A half-timer owes half the claim, not all of it.

        June 2025 schedules 168 full-time hours; a half-time contract works
        84 of them. €500 clears the halved €408 claim. Had the denominator
        been the employee's own 84 scheduled hours the ratio would have been
        1 and the full €816 claimed.
        """
        self.assertEqual(min_wage_topup_monthly(500.0, 84.0, 168.0, 816.0), 0.0)
        self.assertEqual(min_wage_topup_monthly(500.0, 84.0, 84.0, 816.0), 316.0)

    def test_extra_hours_do_not_raise_the_claim(self):
        """The ratio is clamped at 1."""
        self.assertEqual(min_wage_topup_monthly(915.0, 200.0, 176.0, 915.0), 0.0)

    def test_no_scheduled_hours_means_no_claim(self):
        self.assertEqual(min_wage_topup_monthly(0.0, 0.0, 0.0, 915.0), 0.0)

    def test_nothing_worked_means_no_claim(self):
        self.assertEqual(min_wage_topup_monthly(0.0, 0.0, 176.0, 915.0), 0.0)
