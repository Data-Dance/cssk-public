# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date
from decimal import Decimal

from odoo.tests import TransactionCase, tagged

from ..sick_pay import (
    daily_assessment_base,
    decisive_period,
    probable_daily_base,
    round_sick_pay,
    sick_pay_amount,
    split_sick_days,
)


@tagged("post_install", "-at_install")
class TestSickPaySplit(TransactionCase):
    def test_compensation_rounds_up_without_binary_float_extra_cent(self):
        self.assertEqual(round_sick_pay(sick_pay_amount(20, 3, 11, 0.25, 0.55)), 136)
        self.assertEqual(
            round_sick_pay(sick_pay_amount(20.00019, 1, 0, 0.25, 0.55)), 5.01
        )
        self.assertEqual(
            round_sick_pay(sick_pay_amount(94.0274, 1, 7, 0.25, 0.55)), 385.52
        )

    def split(self, spans):
        return split_sick_days(spans, date(2026, 11, 1), date(2026, 11, 30), 3, 14)

    def test_fourteen_calendar_days(self):
        """A 14-day sickness is 3 + 11 days, whatever falls on a weekend."""
        self.assertEqual(
            self.split([(date(2026, 11, 2), date(2026, 11, 15))]), (3, 11, 14)
        )

    def test_sickness_from_the_previous_month_keeps_counting(self):
        """Sick from 30 Oct: 1 Nov is already the third day."""
        self.assertEqual(
            self.split([(date(2026, 10, 30), date(2026, 11, 3))]), (1, 2, 3)
        )

    def test_days_after_the_employer_limit_are_still_counted(self):
        self.assertEqual(
            self.split([(date(2026, 11, 1), date(2026, 11, 20))]), (3, 11, 20)
        )

    def test_adjoining_leaves_are_one_sickness(self):
        spans = [
            (date(2026, 11, 2), date(2026, 11, 3)),
            (date(2026, 11, 4), date(2026, 11, 8)),
        ]
        self.assertEqual(self.split(spans), (3, 4, 7))

    def test_a_gap_starts_a_new_sickness(self):
        spans = [
            (date(2026, 11, 2), date(2026, 11, 3)),
            (date(2026, 11, 10), date(2026, 11, 11)),
        ]
        self.assertEqual(self.split(spans), (4, 0, 4))


@tagged("post_install", "-at_install")
class TestDailyAssessmentBase(TransactionCase):
    """§ 8 ods. 4, 5 and 8 zákona 462/2003, § 54 zákona 461/2003."""

    def test_long_employment_takes_the_previous_calendar_year(self):
        self.assertEqual(
            decisive_period(date(2019, 5, 1), date(2026, 6, 8)),
            (date(2025, 1, 1), date(2025, 12, 31)))
        # insured exactly since 1 January of the previous year
        self.assertEqual(
            decisive_period(date(2025, 1, 1), date(2026, 1, 2)),
            (date(2025, 1, 1), date(2025, 12, 31)))

    def test_ninety_days_runs_to_the_end_of_the_previous_month(self):
        self.assertEqual(
            decisive_period(date(2025, 9, 15), date(2026, 6, 8)),
            (date(2025, 9, 15), date(2026, 5, 31)))
        # day 90 exactly: 1 January + 90 days = 1 April
        self.assertEqual(
            decisive_period(date(2026, 1, 1), date(2026, 4, 1)),
            (date(2026, 1, 1), date(2026, 3, 31)))

    def test_under_ninety_days_runs_to_the_day_before(self):
        self.assertEqual(
            decisive_period(date(2026, 1, 1), date(2026, 3, 31)),
            (date(2026, 1, 1), date(2026, 3, 30)))

    def test_incapacity_on_the_first_day_has_no_period(self):
        self.assertIsNone(decisive_period(date(2026, 6, 8), date(2026, 6, 8)))

    def test_base_is_cut_to_four_places_downward(self):
        period = (date(2026, 1, 1), date(2026, 5, 31))  # 151 days
        self.assertEqual(daily_assessment_base(7500, period, []), 49.6688)
        # 7500 / 146 = 51.36986...: five excluded days, counted once
        excluded = [(date(2026, 2, 2), date(2026, 2, 6)),
                    (date(2026, 2, 4), date(2026, 2, 5))]
        self.assertEqual(daily_assessment_base(7500, period, excluded), 51.3698)

    def test_excluded_days_outside_the_period_do_not_count(self):
        period = (date(2026, 1, 1), date(2026, 5, 31))
        excluded = [(date(2025, 12, 20), date(2026, 1, 2))]  # two days inside
        self.assertEqual(daily_assessment_base(7450, period, excluded), 50.0)

    def test_no_base_or_no_day_is_not_a_base(self):
        period = (date(2026, 1, 1), date(2026, 1, 31))
        self.assertIsNone(daily_assessment_base(0, period, []))
        self.assertIsNone(daily_assessment_base(
            1000, period, [(date(2026, 1, 1), date(2026, 1, 31))]))

    def test_part_month_period_of_a_new_hire(self):
        # Hired 1 March, sick on 20 April: 50 days, 2 000.00 + 1 181.82.
        period = decisive_period(date(2026, 3, 1), date(2026, 4, 20))
        self.assertEqual(period, (date(2026, 3, 1), date(2026, 4, 19)))
        self.assertEqual(
            daily_assessment_base(Decimal("3181.82"), period, []), 63.6364)
        # Hired 10 March, sick on 25 March: 15 days.
        period = decisive_period(date(2026, 3, 10), date(2026, 3, 25))
        self.assertEqual(period, (date(2026, 3, 10), date(2026, 3, 24)))
        self.assertEqual(daily_assessment_base(1000, period, []), 66.6666)

    def test_probable_base_is_the_month_over_its_days(self):
        """§ 8 ods. 6: the base premium would be paid on in the month the
        incapacity began, over the days of that month, cut to four places."""
        self.assertEqual(probable_daily_base(2000, 2026, 6), 66.6666)
        self.assertEqual(probable_daily_base(2000, 2026, 5), 64.5161)
        self.assertEqual(probable_daily_base(2000, 2026, 2), 71.4285)
        self.assertEqual(probable_daily_base(1234.56, 2026, 4), 41.152)
        self.assertIsNone(probable_daily_base(0, 2026, 6))
