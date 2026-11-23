# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The daily base of the employer's sick pay for a new hire, on either engine.

The cases are the same for both payroll engines; each engine's suite mixes
this class into a ``TransactionCase`` and supplies the five helpers. Monthly
salary 2 000 on a Monday to Friday calendar of eight hours with no public
holiday: March, April and June 2026 schedule 22 days (176 hours) each.

§ 8 zákona 462/2003 Z. z. in force from 1 January 2026:

* ods. 4, under 90 insured days: the decisive period runs from the start of
  the insurance to the day before the incapacity;
* ods. 5: the bases reached in it over its days;
* ods. 6: no base in it, the base premium would be paid on in the month the
  incapacity began;
* ods. 8: four places, downward. Sick pay: 25 % for days 1 to 3, 55 % for
  days 4 to 14, rounded up to the cent (§ 10 ods. 2).
"""

from calendar import monthrange
from datetime import date

from odoo.exceptions import UserError
from odoo.tools import format_date


class NewHireSickBaseCases:
    # -- supplied by the engine's suite ---------------------------------
    def _hire(self, name, start, wage=2000.0):
        raise NotImplementedError

    def _absence(self, employee, kind, d_from, d_to):
        """Book and approve ``kind``: ``"pn"`` or ``"neplatene"``."""
        raise NotImplementedError

    def _payslip(self, employee, year, month, dvz=None):
        """A computed payslip of the month, with the PN_DVZ input if given."""
        raise NotImplementedError

    def _confirm(self, slip):
        raise NotImplementedError

    def _line(self, slip, code):
        raise NotImplementedError

    # -- shared ---------------------------------------------------------
    @staticmethod
    def _month(year, month):
        return date(year, month, 1), date(year, month, monthrange(year, month)[1])

    def _assert_says_base_is_missing(self, slip, employee, onset):
        self.assertFalse(slip.l10n_sk_pn_determined_daily_base(onset))
        self.assertEqual(self._line(slip, "SICK_COMP"), 0.0)
        message = slip._l10n_sk_pn_missing_base_message()
        self.assertTrue(message)
        self.assertIn(employee.name, message)
        self.assertIn(format_date(slip.env, onset), message)
        self.assertIn("PN_DVZ", message)
        with self.assertRaises(UserError) as refused:
            self._confirm(slip)
        self.assertIn("PN_DVZ", str(refused.exception))

    # -- under 90 days ----------------------------------------------------
    def test_under_90_days_the_period_ends_the_day_before_the_incapacity(self):
        # Hired 1 March, sick 20 to 30 April: 1 March to 19 April, 50 days.
        # March 2 000.00; April before the incapacity 13 of 22 days,
        # 2 000 x 104 / 176 = 1 181.8182, so 1 181.82. 3 181.82 / 50 =
        # 63.6364. Eleven days: (3 x 25 % + 8 x 55 %) x 63.6364 = 327.72746.
        employee = self._hire("Sick in the second month", date(2026, 3, 1))
        self._confirm(self._payslip(employee, 2026, 3))
        self._absence(employee, "pn", date(2026, 4, 20), date(2026, 4, 30))
        april = self._payslip(employee, 2026, 4)
        self.assertEqual(self._line(april, "GROSS"), 1181.82)
        self.assertEqual(
            april.l10n_sk_pn_determined_daily_base(date(2026, 4, 20)), 63.6364
        )
        self.assertEqual(self._line(april, "SICK_COMP"), 327.73)
        self.assertFalse(april._l10n_sk_pn_missing_base_message())
        self._confirm(april)

    def test_the_base_stays_when_the_incapacity_runs_into_the_next_month(self):
        # The same employee sick from 20 April to 8 May. May holds days 12 to
        # 14: 3 x 55 % x 63.6364 = 105.00006, so 105.01.
        employee = self._hire("Sick into May", date(2026, 3, 1))
        self._confirm(self._payslip(employee, 2026, 3))
        self._absence(employee, "pn", date(2026, 4, 20), date(2026, 5, 8))
        april = self._payslip(employee, 2026, 4)
        self.assertEqual(self._line(april, "SICK_COMP"), 327.73)
        self._confirm(april)
        may = self._payslip(employee, 2026, 5)
        self.assertEqual(
            may.l10n_sk_pn_determined_daily_base(date(2026, 4, 20)), 63.6364
        )
        self.assertEqual(self._line(may, "SICK_COMP"), 105.01)

    def test_under_90_days_the_period_lies_inside_the_first_month(self):
        # Hired 10 March, sick 25 to 31 March: 10 to 24 March, 15 days, 11
        # of them worked. 2 000 x 88 / 176 = 1 000.00; 1 000 / 15 = 66.6666.
        # Seven days: (3 x 25 % + 4 x 55 %) x 66.6666 = 196.66647.
        employee = self._hire("Sick in the first month", date(2026, 3, 10))
        self._absence(employee, "pn", date(2026, 3, 25), date(2026, 3, 31))
        march = self._payslip(employee, 2026, 3)
        self.assertEqual(self._line(march, "GROSS"), 1000.0)
        self.assertEqual(
            march.l10n_sk_pn_determined_daily_base(date(2026, 3, 25)), 66.6666
        )
        self.assertEqual(self._line(march, "SICK_COMP"), 196.67)
        self.assertFalse(march._l10n_sk_pn_missing_base_message())

    def test_work_after_the_incapacity_in_its_month_leaves_the_base_to_be_typed(self):
        # Hired 10 March, sick 25 to 27 March, back on the 30th: the base of
        # March then holds the wage of the 30th and 31st as well, and what
        # was reached by the 24th is on no payslip.
        employee = self._hire("Back within the month", date(2026, 3, 10))
        self._absence(employee, "pn", date(2026, 3, 25), date(2026, 3, 27))
        march = self._payslip(employee, 2026, 3)
        self._assert_says_base_is_missing(march, employee, date(2026, 3, 25))

    # -- the first day and no base ------------------------------------------
    def test_sick_on_the_first_day_gets_the_base_of_that_month(self):
        # Hired 1 June, sick 1 to 5 June: no base before the incapacity, so
        # the base premium would be paid on in June, 2 000, over its 30
        # days: 66.6666. Five days: (3 x 25 % + 2 x 55 %) x 66.6666 =
        # 123.33321. The wage: 2 000 x 136 / 176 = 1 545.4545.
        employee = self._hire("Sick on the first day", date(2026, 6, 1))
        self._absence(employee, "pn", date(2026, 6, 1), date(2026, 6, 5))
        june = self._payslip(employee, 2026, 6)
        self.assertEqual(self._line(june, "GROSS"), 1545.46)
        self.assertEqual(
            june.l10n_sk_pn_determined_daily_base(date(2026, 6, 1)), 66.6666
        )
        self.assertEqual(self._line(june, "SICK_COMP"), 123.34)
        self.assertFalse(june._l10n_sk_pn_missing_base_message())
        self._confirm(june)

    def test_no_base_in_the_period_gets_the_base_of_the_month_of_the_incapacity(self):
        # Hired 1 May, unpaid leave for the whole of May, sick from 1 June:
        # the period is May, with no base and no day left.
        employee = self._hire("Nothing earned before", date(2026, 5, 1))
        self._absence(employee, "neplatene", date(2026, 5, 1), date(2026, 5, 31))
        may = self._payslip(employee, 2026, 5)
        self.assertEqual(self._line(may, "GROSS"), 0.0)
        self._confirm(may)
        self._absence(employee, "pn", date(2026, 6, 1), date(2026, 6, 5))
        june = self._payslip(employee, 2026, 6)
        self.assertEqual(
            june.l10n_sk_pn_determined_daily_base(date(2026, 6, 1)), 66.6666
        )
        self.assertEqual(self._line(june, "SICK_COMP"), 123.34)

    def test_sick_on_the_first_day_of_a_part_month_leaves_the_base_to_be_typed(self):
        # Hired 10 June and sick the same day: June is insured in part, and
        # the Act names no divisor for it.
        employee = self._hire("First day mid-month", date(2026, 6, 10))
        self._absence(employee, "pn", date(2026, 6, 10), date(2026, 6, 12))
        june = self._payslip(employee, 2026, 6)
        self._assert_says_base_is_missing(june, employee, date(2026, 6, 10))

    # -- the typed base ----------------------------------------------------
    def test_the_typed_base_wins_in_every_case(self):
        cases = (
            # hired, sick from, to, paid days as (25 %, 55 %), sick pay at 40
            (date(2026, 3, 1), date(2026, 4, 20), date(2026, 4, 30), 206.0),
            (date(2026, 3, 10), date(2026, 3, 25), date(2026, 3, 31), 118.0),
            (date(2026, 6, 1), date(2026, 6, 1), date(2026, 6, 5), 74.0),
            (date(2026, 3, 10), date(2026, 3, 25), date(2026, 3, 27), 30.0),
        )
        for hired, sick_from, sick_to, expected in cases:
            with self.subTest(hired=hired, sick_from=sick_from):
                employee = self._hire("Typed %s" % sick_from, hired)
                if hired.month != sick_from.month:
                    self._confirm(self._payslip(employee, 2026, hired.month))
                self._absence(employee, "pn", sick_from, sick_to)
                slip = self._payslip(employee, 2026, sick_from.month, dvz=40.0)
                self.assertEqual(self._line(slip, "SICK_COMP"), expected)
                self.assertFalse(slip._l10n_sk_pn_missing_base_message())
                self._confirm(slip)

    # -- a long employment without its payslips -----------------------------
    def test_a_missing_history_is_said_too(self):
        # Employed since 2024 with no payslip on file for 2025.
        employee = self._hire("No history", date(2024, 1, 1))
        self._absence(employee, "pn", date(2026, 6, 8), date(2026, 6, 10))
        june = self._payslip(employee, 2026, 6)
        self._assert_says_base_is_missing(june, employee, date(2026, 6, 8))

    def test_nothing_is_said_when_the_employer_pays_no_day(self):
        # Sick since 4 May: June holds only days after the fourteenth.
        employee = self._hire("Past the employer's days", date(2024, 1, 1))
        self._absence(employee, "pn", date(2026, 5, 4), date(2026, 6, 12))
        june = self._payslip(employee, 2026, 6)
        self.assertEqual(self._line(june, "SICK_COMP"), 0.0)
        self.assertFalse(june._l10n_sk_pn_missing_base_message())
        self._confirm(june)
