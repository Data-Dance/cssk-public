# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo.tests import TransactionCase, tagged

from ..sick_pay import split_sick_days


@tagged("post_install", "-at_install")
class TestSickPaySplit(TransactionCase):
    def split(self, spans):
        return split_sick_days(spans, date(2026, 11, 1), date(2026, 11, 30), 3, 14)

    def test_fourteen_calendar_days(self):
        """A 14-day sickness is 3 + 11 days, whatever falls on a weekend."""
        self.assertEqual(self.split([(date(2026, 11, 2), date(2026, 11, 15))]), (3, 11, 14))

    def test_sickness_from_the_previous_month_keeps_counting(self):
        """Sick from 30 Oct: 1 Nov is already the third day."""
        self.assertEqual(self.split([(date(2026, 10, 30), date(2026, 11, 3))]), (1, 2, 3))

    def test_days_after_the_employer_limit_are_still_counted(self):
        self.assertEqual(self.split([(date(2026, 11, 1), date(2026, 11, 20))]), (3, 11, 20))

    def test_adjoining_leaves_are_one_sickness(self):
        spans = [(date(2026, 11, 2), date(2026, 11, 3)), (date(2026, 11, 4), date(2026, 11, 8))]
        self.assertEqual(self.split(spans), (3, 4, 7))

    def test_a_gap_starts_a_new_sickness(self):
        spans = [(date(2026, 11, 2), date(2026, 11, 3)), (date(2026, 11, 10), date(2026, 11, 11))]
        self.assertEqual(self.split(spans), (4, 0, 4))
