# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The meal allowance in money and its exempt limit.

§ 6 odst. 9 písm. b) zák. 586/1992 Sb. exempts "příjem zaměstnance ve formě
příspěvku na stravování poskytnutého zaměstnavatelem za jednu směnu ... v
úhrnu do výše 70 % horní hranice stravného, které lze poskytnout zaměstnancům
odměňovaným platem při pracovní cestě trvající 5 až 12 hodin": 129.50 Kč in
2026. What is paid above it is taxable income, and the assessment bases of
both insurances are the income that is "předmětem daně z příjmů fyzických
osob ... a nejsou od této daně osvobozeny" (§ 5 odst. 1 zák. 589/1992 Sb.,
§ 3 odst. 1 zák. 592/1992 Sb.).

May 2026 has 21 working days and February 20 on a calendar without public
holidays. Every expected figure is computed by hand in the test's docstring.
"""

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCzMealAllowance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
        cls.company = cls.env["res.company"].create({
            "name": "CZ Meal Co",
            "country_id": cls.env.ref("base.cz").id,
            "currency_id": cls.env.ref("base.CZK").id,
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h/week", "company_id": cls.company.id})
        cls.structure = cls.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")

    def _employee(self, name, wage, calendar=None, **version_vals):
        calendar = calendar or self.calendar
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": name,
            "company_id": self.company.id,
            "resource_calendar_id": calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": wage,
            "struct_id": self.structure.id,
        })
        employee.version_id.write(dict(
            version_vals, resource_calendar_id=calendar.id,
            struct_id=self.structure.id))
        return employee

    def _payslip(self, employee, month=5, confirm=False):
        """A real payslip: the allowance is paid per shift worked, so the
        worked-day lines must exist."""
        d_from = date(2026, month, 1)
        d_to = d_from + relativedelta(day=31)
        version = employee.version_id
        payslip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip %s %s" % (employee.name, month),
            "employee_id": employee.id,
            "contract_id": version.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": d_from,
            "date_to": d_to,
        })
        # The engine fills the worked-day lines from an onchange, which does
        # not fire on create().
        payslip.worked_days_line_ids = [
            (0, 0, line)
            for line in payslip.get_worked_day_lines(version, d_from, d_to)
        ]
        payslip.compute_sheet()
        if confirm:
            payslip.write({"state": "done"})
        return payslip

    def _line(self, payslip, code):
        return payslip.line_ids.filtered(lambda line: line.code == code)

    def _t(self, payslip, code):
        return round(sum(self._line(payslip, code).mapped("total")), 2)

    def test_allowance_within_the_limit_is_all_exempt(self):
        """129 Kč a shift, 21 shifts: 2 709 exempt, nothing above the limit.
        The bases are the wage alone; NET 39 270 + 2 709."""
        p = self._payslip(self._employee(
            "Meal Within", 50000.0, l10n_cz_tax_declaration=True,
            l10n_cz_meal_allowance=129.0))
        self.assertEqual(self._t(p, "MEAL"), 2709.0)
        self.assertFalse(self._line(p, "MEALTAXABLE"))
        self.assertEqual(self._t(p, "TAXBASE"), 50000.0)
        self.assertEqual(self._line(p, "SOCIALER").amount, 50000.0)
        self.assertEqual(self._t(p, "HEALTHEE"), -2250.0)
        self.assertEqual(self._t(p, "NET"), 41979.0)

    def test_excess_is_paid_taxed_and_insured(self):
        """150 Kč a shift, 21 shifts = 3 150 paid: 21 x 129.50 = 2 719.50
        exempt, 21 x 20.50 = 430.50 above the limit. GROSS stays 50 000.
        Social base 50 430.50 -> 50 431 (§ 5d): 3 580.601 -> 3 581. Health
        13.5 % of 50 430.50 = 6 808.12 -> 6 809, a third 2 270. Tax base
        50 430.50 -> 50 500 x 15 % = 7 575 - 2 570. NET 50 000 + 3 150 -
        3 581 - 2 270 - 5 005 = 42 294."""
        p = self._payslip(self._employee(
            "Meal Above", 50000.0, l10n_cz_tax_declaration=True,
            l10n_cz_meal_allowance=150.0))
        meal, excess = self._line(p, "MEAL"), self._line(p, "MEALTAXABLE")
        self.assertEqual((meal.quantity, meal.amount), (21.0, 129.5))
        self.assertEqual((excess.quantity, excess.amount), (21.0, 20.5))
        self.assertEqual(meal.total, 2719.5)
        self.assertEqual(excess.total, 430.5)
        self.assertEqual(self._t(p, "GROSS"), 50000.0)
        self.assertEqual(self._t(p, "TAXBASE"), 50430.5)
        self.assertEqual(self._line(p, "SOCIALER").amount, 50431.0)
        self.assertEqual(self._t(p, "SOCIALEE"), -3581.0)
        self.assertEqual(self._t(p, "HEALTHEE"), -2270.0)
        self.assertEqual(self._t(p, "HEALTHER"), 4539.0)
        self.assertEqual(self._t(p, "INCOMETAX"), -7575.0)
        self.assertEqual(self._t(p, "NET"), 42294.0)

    def test_excess_counts_towards_the_annual_maximum_base(self):
        """January: 2 000 000 + 22 x 20.50 = 2 000 451 insured. February
        (20 shifts, 410 above the limit) is insured on what is left of the
        maximum base (§ 15a zák. 589/1992 Sb.) after 2 000 451, not after
        2 000 000."""
        employee = self._employee(
            "Meal Maximum", 2000000.0, l10n_cz_tax_declaration=True,
            l10n_cz_meal_allowance=150.0)
        january = self._payslip(employee, month=1, confirm=True)
        self.assertEqual(self._line(january, "SOCIALER").amount, 2000451.0)
        february = self._payslip(employee, month=2)
        maximum = february.rule_parameter("l10n_cz_social_max_base")
        self.assertEqual(
            self._line(february, "SOCIALER").amount, maximum - 2000451.0)

    def test_excess_counts_for_the_insurance_limit_of_an_agreement(self):
        """A DPP of 11 900 Kč on four Monday shifts of four hours in May,
        with 160 Kč a shift: 4 x 30.50 = 122 above the limit, so the income
        counted for the insurance is 12 022, over the 12 000 of § 7a odst. 1
        zák. 187/2006 Sb. Insured: 12 022 x 7.1 % = 853.562 -> 854."""
        mondays = self.env["resource.calendar"].create({
            "name": "CZ Mondays", "company_id": self.company.id,
            "attendance_ids": [(0, 0, {
                "name": "Monday", "dayofweek": "0",
                "hour_from": 8.0, "hour_to": 12.0, "day_period": "morning",
            })],
        })
        p = self._payslip(self._employee(
            "Meal DPP", 11900.0, calendar=mondays,
            l10n_cz_agreement_type="dpp", l10n_cz_meal_allowance=160.0))
        self.assertEqual(self._t(p, "GROSS"), 11900.0)
        self.assertEqual(self._t(p, "MEALTAXABLE"), 122.0)
        self.assertEqual(self._line(p, "SOCIALER").amount, 12022.0)
        self.assertEqual(self._t(p, "SOCIALEE"), -854.0)
