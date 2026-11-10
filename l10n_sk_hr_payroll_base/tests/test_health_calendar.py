# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import BaseCase, tagged

from ..health_calendar import month_context


def interval(kind, start, end=None):
    return {"kind": kind, "start": start, "end": end}


@tagged("post_install", "-at_install")
class TestHealthCalendar(BaseCase):
    def context(self, *rows, month="2026-06-01"):
        return month_context(rows, month)

    def test_whole_month_employment_and_partial_contract_boundaries(self):
        full = self.context(interval("2", "2026-01-01"))
        self.assertEqual(
            (full["employment_days"], full["insured_days"], full["minimum_days"]),
            (30, 30, 30),
        )
        partial = self.context(interval("2", "2026-06-16", "2026-06-25"))
        self.assertEqual(
            (partial["op_employment_days"], partial["minimum_days"]), (10, 10)
        )

    def test_agreement_uses_reviewed_work_days_without_inventing_weekends(self):
        facts = self.context(
            interval("2D", "2026-06-02", "2026-06-02"),
            interval("2D", "2026-06-12", "2026-06-12"),
        )
        self.assertEqual(facts["insured_days"], 2)
        self.assertEqual(facts["minimum_days"], 2)
        self.assertEqual(facts["op_employment_days"], 0)

    def test_reviewed_five_work_days_plus_two_rest_days_are_a_seven_day_span(self):
        facts = self.context(interval("2D", "2026-06-01", "2026-06-07"))
        self.assertEqual(facts["insured_days"], 7)

    def test_concurrent_employment_and_agreement_are_not_counted_twice(self):
        facts = self.context(
            interval("2", "2026-06-01"), interval("2D", "2026-06-01", "2026-06-15")
        )
        self.assertEqual(facts["insured_days"], 30)

    def test_duplicate_and_overlapping_periods_are_unioned(self):
        facts = self.context(
            interval("2D", "2026-06-01", "2026-06-07"),
            interval("2D", "2026-06-05", "2026-06-10"),
        )
        self.assertEqual(facts["insured_days"], 10)

    def test_one_day_2y_does_not_become_the_old_contract_duration(self):
        facts = self.context(interval("2Y", "2026-06-30", "2026-06-30"))
        self.assertEqual(
            (facts["insured_days"], facts["minimum_days"], facts["op_employment_days"]),
            (1, 1, 0),
        )

    def test_benefit_days_reduce_insured_days_but_not_op_employment(self):
        facts = self.context(
            interval("2", "2026-06-01"), interval("benefit", "2026-06-04", "2026-06-13")
        )
        self.assertEqual(
            (facts["insured_days"], facts["minimum_days"], facts["op_employment_days"]),
            (20, 20, 30),
        )

    def test_2n_no_income_days_are_not_employment_for_op(self):
        facts = self.context(
            interval("2", "2026-06-01"), interval("2N", "2026-06-16", "2026-06-30")
        )
        self.assertEqual(
            (facts["insured_days"], facts["minimum_days"], facts["op_employment_days"]),
            (15, 15, 15),
        )

    def test_one_disability_day_changes_the_rate_and_exempts_the_whole_minimum(self):
        facts = self.context(
            interval("2", "2026-06-01"),
            interval("disabled", "2026-06-30", "2026-06-30"),
        )
        self.assertTrue(facts["disability_in_month"])
        self.assertEqual(facts["minimum_days"], 0)
        self.assertEqual(facts["insured_days"], 30)

    def test_all_minimum_exceptions_union_without_double_subtraction(self):
        facts = self.context(
            interval("2", "2026-06-01"),
            interval("state", "2026-06-01", "2026-06-10"),
            interval("state", "2026-06-05", "2026-06-15"),
            interval("self_employed", "2026-06-15", "2026-06-20"),
            interval("missing", "2026-06-20", "2026-06-25"),
        )
        self.assertEqual(facts["minimum_days"], 5)
        self.assertEqual(facts["insured_days"], 30)

    def test_concurrency_requires_actual_date_overlap(self):
        sequential = self.context(
            interval("2", "2026-06-01", "2026-06-10"),
            interval("self_employed", "2026-06-11"),
            interval("other_employment", "2026-06-11"),
        )
        self.assertFalse(sequential["concurrent_self_employment"])
        self.assertFalse(sequential["concurrent_other_employment"])
        overlap = self.context(
            interval("2", "2026-06-01"),
            interval("self_employed", "2026-06-10"),
            interval("other_employment", "2026-06-30", "2026-06-30"),
        )
        self.assertTrue(overlap["concurrent_self_employment"])
        self.assertTrue(overlap["concurrent_other_employment"])

    def test_leap_year_and_year_boundary_use_real_calendar_dates(self):
        february = self.context(interval("2", "2024-01-01"), month="2024-02-01")
        self.assertEqual(february["insured_days"], 29)
        january = self.context(
            interval("2", "2025-12-20", "2026-01-10"), month="2026-01-01"
        )
        self.assertEqual(january["insured_days"], 10)

    def test_invalid_sources_are_rejected_without_silent_clamping(self):
        for row in [
            interval("unknown", "2026-06-01"),
            interval("2", "2026-06-10", "2026-06-01"),
            interval("2Y", "2026-06-01"),
            interval("2Y", "2026-06-01", "2026-06-02"),
        ]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.context(row)
