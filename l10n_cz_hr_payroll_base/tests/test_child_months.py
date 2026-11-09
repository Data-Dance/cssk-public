# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Which months a child counts in for the child tax benefit (§ 35c ZDP)."""

from datetime import date

from odoo.tests import TransactionCase, tagged

from ..models.hr_employee_child import birth_number_date


@tagged("post_install", "-at_install")
class TestChildMonths(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Rodič"})

    def _child(self, **vals):
        return self.env["l10n.cz.employee.child"].create(dict({
            "employee_id": self.employee.id,
            "first_name": "Dítě",
            "surname": "Rodičovo",
        }, **vals))

    def _months(self, child, year=2026):
        return [m for m in range(1, 13) if child._l10n_cz_claimed_in(year, m)]

    def test_born_during_the_year_counts_from_the_month_of_birth(self):
        child = self._child(birthday=date(2026, 9, 15))
        self.assertEqual(self._months(child), [9, 10, 11, 12])

    def test_born_on_the_first_counts_that_month(self):
        child = self._child(birthday=date(2026, 9, 1))
        self.assertEqual(self._months(child), [9, 10, 11, 12])

    def test_claimed_from_counts_its_own_month(self):
        """§ 35c odst. 10: adopted on 10 March, March already counts. A child
        coming to the household otherwise is entered from 1 April."""
        child = self._child(birthday=date(2020, 5, 5),
                            date_from=date(2026, 3, 10))
        self.assertEqual(self._months(child), list(range(3, 13)))
        child.date_from = date(2026, 4, 1)
        self.assertEqual(self._months(child), list(range(4, 13)))

    def test_the_last_month_of_the_claim_still_counts(self):
        child = self._child(birthday=date(2000, 1, 1),
                            date_to=date(2026, 6, 15))
        self.assertEqual(self._months(child), [1, 2, 3, 4, 5, 6])

    def test_not_claimed_is_never_counted(self):
        child = self._child(birthday=date(2020, 1, 1), order="N")
        self.assertEqual(self._months(child), [])
        self.assertTrue(child._l10n_cz_maintained_in(2026, 5))

    def test_birth_number_gives_the_date_of_birth(self):
        self.assertEqual(birth_number_date("2659151234"), date(2026, 9, 15))
        self.assertEqual(birth_number_date("267915/1234"), date(2026, 9, 15))
        self.assertEqual(birth_number_date("530101123"), date(1953, 1, 1))
        child = self._child(birth_number="2609150005")
        self.assertEqual(self._months(child), [9, 10, 11, 12])

    def test_counts_from_records_put_ztpp_on_the_childs_own_order(self):
        self._child(birthday=date(2015, 1, 1), order="1")
        self._child(birthday=date(2018, 1, 1), order="2", ztpp=True)
        self._child(birthday=date(2026, 9, 15), order="3")
        version = self.employee.version_id
        version.write({"l10n_cz_children_t1": 5})  # ignored: records exist
        self.assertEqual(version._l10n_cz_child_counts(date(2026, 8, 1)),
                         {"1": [1, 0], "2": [1, 1], "3": [0, 0]})
        self.assertEqual(version._l10n_cz_child_counts(date(2026, 9, 1)),
                         {"1": [1, 0], "2": [1, 1], "3": [1, 0]})
        amounts = {"l10n_cz_child_1": 100.0, "l10n_cz_child_2": 200.0,
                   "l10n_cz_child_3": 300.0}
        # 100 + 2 x 200 (ZTP/P doubles the second child's own amount) + 300
        self.assertEqual(version._l10n_cz_child_benefit(
            date(2026, 9, 1), amounts.__getitem__), 800.0)

    def test_counts_without_records_come_from_the_version(self):
        version = self.employee.version_id
        version.write({"l10n_cz_children_t1": 1, "l10n_cz_children_t2": 1,
                       "l10n_cz_children_ztpp": 1})
        self.assertEqual(version._l10n_cz_child_counts(date(2026, 1, 1)),
                         {"1": [1, 1], "2": [1, 0], "3": [0, 0]})
        version.write({"l10n_cz_children_t1": 0, "l10n_cz_children_t2": 0})
        # "of which ZTP/P" without any child claims nothing.
        self.assertEqual(version._l10n_cz_child_benefit(
            date(2026, 1, 1), lambda code: 100.0), 0.0)

    def test_claim_period_must_not_end_before_it_starts(self):
        with self.assertRaises(Exception):
            self._child(date_from=date(2026, 5, 1), date_to=date(2026, 4, 1))

    def test_two_first_children_in_the_same_months_are_refused(self):
        self._child(birthday=date(2015, 1, 1), order="1",
                    date_to=date(2026, 5, 31))
        # Successive claims are fine: the next one starts after the first ends.
        self._child(birthday=date(2018, 1, 1), order="1",
                    date_from=date(2026, 6, 1))
        with self.assertRaises(Exception):
            self._child(birthday=date(2020, 1, 1), order="1")
        # The third order holds every further child.
        self._child(birthday=date(2021, 1, 1), order="3")
        self._child(birthday=date(2022, 1, 1), order="3")
