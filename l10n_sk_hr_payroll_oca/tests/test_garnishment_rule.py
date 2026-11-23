# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The GARNISHMENT rule's input path against the decree and the register.

Nariadenie vlády 268/2006 Z. z. § 4 rounds the protected sums of § 1 to § 2b
and the limit of § 3 ods. 1 down to the cent; § 71 ods. 1 Exekučného poriadku
rounds what is left of the net wage down to a sum divisible by three.
"""
import unittest
from datetime import date
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkGarnishmentRule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "SK Garnishment Co", "country_id": cls.env.ref("base.sk").id})
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create({
            "name": "SK 40h/week", "company_id": cls.company.id})
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary")

    def setUp(self):
        super().setUp()
        # The minimum wage top-up belongs to another module; keep it out of
        # the wages used here.
        Payslip = type(self.env["hr.payslip"])
        if hasattr(Payslip, "_l10n_sk_min_wage_claim_applies"):
            self.startPatcher(patch.object(
                Payslip, "_l10n_sk_min_wage_claim_applies", return_value=False))

    def _worker(self, wage, calendar=None, **vals):
        calendar = calendar or self.calendar
        employee = self.env["hr.employee"].create({
            "name": "Povinny %s" % wage, "company_id": self.company.id,
            "resource_calendar_id": calendar.id})
        employee.version_id.write(dict(
            vals, contract_date_start=date(2024, 1, 1),
            date_version=date(2024, 1, 1), wage=wage,
            resource_calendar_id=calendar.id,
            struct_id=self.structure.id))
        return employee

    def _short_calendar(self):
        """Five hours a week: 200.00 is above the minimum wage on it."""
        return self.env["resource.calendar"].create({
            "name": "SK 5h", "company_id": self.company.id,
            "full_time_required_hours": 40.0, "hours_per_day": 1.0,
            "attendance_ids": [(5, 0, 0)] + [(0, 0, {
                "name": "d%d" % day, "dayofweek": str(day), "hour_from": 8.0,
                "hour_to": 9.0, "day_period": "morning"}) for day in range(5)],
        })

    def _payslip(self, employee, first):
        return self.env["hr.payslip"].with_company(self.company).create({
            "name": "Slip %s" % first, "employee_id": employee.id,
            "contract_id": employee.version_id.id,
            "struct_id": self.structure.id, "company_id": self.company.id,
            "date_from": first,
            "date_to": first + relativedelta(months=1, days=-1)})

    def _inputs(self, slip, amounts):
        """Other inputs of the payslip; they stay when the claim changes."""
        for code, amount in amounts.items():
            self.env["hr.payslip.input"].create({
                "payslip_id": slip.id, "contract_id": slip.contract_id.id,
                "name": code, "code": code, "amount": amount, "sequence": 10})

    def _claims(self, slip):
        return slip.input_line_ids.filtered(
            lambda line: line.code in ("GARNISHMENT", "GARNISHMENT_PRIORITY"))

    @staticmethod
    def _line(slip, code):
        return round(sum(
            slip.line_ids.filtered(lambda x: x.code == code).mapped("total")), 2)

    @staticmethod
    def _category(slip, code):
        return round(sum(slip.line_ids.filtered(
            lambda x: x.category_id.code == code).mapped("total")), 2)

    def _by_input(self, slip, code, debt):
        self._claims(slip).unlink()
        self._inputs(slip, {code: debt})
        slip.compute_sheet()
        return slip.get_salary_line_total("GARNISHMENT")

    def _by_register(self, slip, claim_class, debt):
        self._claims(slip).unlink()
        order = self.env["hr.wage.garnishment"].create({
            "case_number": "1 EX 1/2024", "employee_id": slip.employee_id.id,
            "company_id": self.company.id, "claim_class": claim_class,
            "date_delivered": date(2024, 1, 2), "total_amount": debt,
            "state": "running"})
        slip.compute_sheet()
        amount = slip.get_salary_line_total("GARNISHMENT")
        order.unlink()
        return amount

    def test_protected_sums_are_rounded_down(self):
        """July 2026, living minimum 295.22: 140 % is 413.308, protected
        413.30; a dependant adds 25 %, 103.327, protected 103.32. With two
        dependants 619.94 of the net wage 1 134.51 is protected, 514.57 is
        left, 514.56 is divisible by three and one third is 171.52."""
        employee = self._worker(
            1500.0, l10n_sk_tax_declaration_signed=True,
            l10n_sk_garnishment_dependents=2)
        slip = self._payslip(employee, date(2026, 7, 1))
        self.assertEqual(self._by_input(slip, "GARNISHMENT", 5000.0), -171.52)
        self.assertEqual(slip.get_salary_line_total("NET"), 962.99)

    def test_2024_sums_are_rounded_down(self):
        """August 2024, living minimum 273.99: 140 % is 383.586, protected
        383.58, and three times that, 1 150.74, is the limit of § 3."""
        employee = self._worker(4000.0)
        slip = self._payslip(employee, date(2024, 8, 1))
        # A claim of nothing deducts nothing: NET is the net wage.
        self.assertEqual(self._by_input(slip, "GARNISHMENT", 0.0), 0.0)
        net = slip.get_salary_line_total("NET")
        # Everything above 383.58 + 1 150.74 is deducted without limit.
        over = round(net - 383.58 - 1150.74, 2)
        self.assertGreater(over, 0.0)
        self.assertEqual(
            self._by_input(slip, "GARNISHMENT", 100000.0),
            -round(383.58 + over, 2))

    def test_input_and_register_deduct_the_same(self):
        """One claim typed as a payslip input and the same claim kept in the
        garnishment register give the same deduction."""
        if "hr.wage.garnishment" not in self.env:
            raise unittest.SkipTest("the garnishment register is not installed")
        classes = (("GARNISHMENT", "ordinary"),
                   ("GARNISHMENT_PRIORITY", "priority"))
        for first in (date(2024, 3, 1), date(2024, 8, 1), date(2025, 8, 1),
                      date(2026, 3, 1), date(2026, 8, 1)):
            for wage in (800.0, 1500.0, 3200.0, 6000.0):
                employee = self._worker(wage)
                slip = self._payslip(employee, first)
                for dependents in (0, 1, 3):
                    employee.version_id.l10n_sk_garnishment_dependents = (
                        dependents)
                    for code, claim_class in classes:
                        with self.subTest(month=first, wage=wage,
                                          dependents=dependents, code=code):
                            self.assertEqual(
                                self._by_input(slip, code, 100000.0),
                                self._by_register(slip, claim_class, 100000.0))

    # ------------------------------------------------------------------
    # The net wage the deduction is computed from (§ 69 and § 89 ods. 1
    # Exekučného poriadku, § 118 ods. 2 Zákonníka práce)
    # ------------------------------------------------------------------
    def _register_net_wage(self, slip):
        """The net wage the rule handed to the garnishment register."""
        if "l10n_cssk_garnishment_net" not in slip._fields:
            raise unittest.SkipTest("the garnishment register is not installed")
        self._by_register(slip, "ordinary", 100000.0)
        return slip.l10n_cssk_garnishment_net

    def test_child_bonus_is_not_part_of_the_net_wage(self):
        """The daňový bonus is not wage (§ 118 ods. 2 Zákonníka práce), and
        the advance deducted from the wage is the one before the bonus.
        July 2026, two children, two dependants: 1 500.00 less premiums of
        216.00 and an advance of 149.49 is a net wage of 1 134.51; 619.94 is
        protected, 514.56 of the rest is divisible by three and one third is
        171.52. The bonus of 200.00 is paid on top of it in full."""
        employee = self._worker(
            1500.0, l10n_sk_tax_declaration_signed=True,
            l10n_sk_children_under_15=2, l10n_sk_garnishment_dependents=2)
        slip = self._payslip(employee, date(2026, 7, 1))
        self.assertEqual(self._by_input(slip, "GARNISHMENT", 5000.0), -171.52)
        self.assertEqual(self._line(slip, "GROSS"), 1500.0)
        self.assertEqual(self._category(slip, "SOCIALEMPLOYEE"), -216.0)
        self.assertEqual(self._category(slip, "INCOMETAX"), -149.49)
        self.assertEqual(self._line(slip, "CHILD_BONUS"), 200.0)
        # 1 134.51 + 200.00 - 171.52
        self.assertEqual(self._line(slip, "NET"), 1162.99)
        if "hr.wage.garnishment" in self.env:
            self.assertEqual(
                self._by_register(slip, "ordinary", 5000.0), -171.52)
            self.assertEqual(self._line(slip, "NET"), 1162.99)
        if "l10n_cssk_garnishment_net" in slip._fields:
            self.assertEqual(slip.l10n_cssk_garnishment_net, 1134.51)

    def test_net_wage_deducts_every_tax_line_and_premium(self):
        """The whole advance, in both bands, and every premium of the
        employee are deducted from the wage (§ 69 ods. 1)."""
        employee = self._worker(6000.0, l10n_sk_tax_declaration_signed=True)
        slip = self._payslip(employee, date(2026, 7, 1))
        net = self._register_net_wage(slip)
        tax = self._category(slip, "INCOMETAX")
        # 19 % of 3 665.28 and 25 % of the base above it.
        self.assertLess(tax, -0.19 * 3665.28 - 100.0)
        self.assertEqual(net, round(
            self._line(slip, "GROSS") + self._category(slip, "SOCIALEMPLOYEE")
            + tax, 2))
        self.assertEqual(net, round(
            6000.0 + self._category(slip, "SOCIALEMPLOYEE") + tax, 2))

    def test_net_wage_has_sick_pay_and_no_other_addition(self):
        """The employer's sick pay replaces the wage and is deducted from
        like it (§ 89 ods. 1). The child bonus, the meal contribution, a
        reimbursement (§ 69 ods. 2) and the result of the annual tax
        settlement are no part of the net wage."""
        employee = self._worker(
            1500.0, l10n_sk_tax_declaration_signed=True,
            l10n_sk_children_under_15=1,
            l10n_sk_meal_allowance_type="financial", l10n_sk_meal_days=20)
        slip = self._payslip(employee, date(2026, 7, 1))
        # Five sick days on a daily base of 40: 3 x 25 % and 2 x 55 %.
        self._inputs(slip, {"PN_DAYS": 5.0, "PN_DVZ": 40.0,
                            "REIMBURSEMENT": 50.0,
                            "ANNUAL_TAX_SETTLEMENT": 30.0})
        net = self._register_net_wage(slip)
        self.assertEqual(self._line(slip, "SICK_COMP"), 74.0)
        self.assertEqual(self._line(slip, "CHILD_BONUS"), 100.0)
        self.assertEqual(self._line(slip, "REIMBURSEMENT"), 50.0)
        self.assertEqual(self._line(slip, "ANNUAL_TAX_SETTLEMENT"), 30.0)
        self.assertGreater(abs(self._line(slip, "MEALEMPLOYER")), 0.0)
        self.assertEqual(net, round(
            1500.0 + self._category(slip, "SOCIALEMPLOYEE")
            + self._category(slip, "INCOMETAX") + 74.0, 2))

    def test_net_wage_deducts_the_health_minimum_top_up(self):
        """The top-up to the minimum advance is health insurance the employee
        pays (§ 16a ods. 4 zákona 580/2004 Z. z.). March 2026, 200.00 on five
        hours a week: premiums 18.80 + 10.00 + 13.45, advance 29.97, net wage
        127.78."""
        employee = self._worker(200.0, calendar=self._short_calendar())
        slip = self._payslip(employee, date(2026, 3, 1))
        net = self._register_net_wage(slip)
        self.assertEqual(
            self._line(slip, "HEALTHDOPLATOK")
            + self._line(slip, "HEALTH_DOPLATOK"), -13.45)
        self.assertEqual(self._category(slip, "SOCIALEMPLOYEE"), -42.25)
        self.assertEqual(self._category(slip, "INCOMETAX"), -29.97)
        self.assertEqual(net, 127.78)

    def test_living_minimum_is_the_same_in_both_sources(self):
        """The rule parameter and the register's rate records hold the same
        living minimum and coefficients on every date either of them starts
        a new value."""
        if "hr.wage.garnishment.rate" not in self.env:
            raise unittest.SkipTest("the garnishment register is not installed")
        Parameter = self.env["hr.rule.parameter"]
        pairs = {
            "l10n_sk_zivotne_minimum": "sk_zivotne_minimum",
            "l10n_sk_garnishment_basic_coeff": "sk_basic_coeff",
            "l10n_sk_garnishment_priority_coeff": "sk_priority_coeff",
            "l10n_sk_garnishment_dependent_coeff": "sk_dependent_coeff",
            "l10n_sk_garnishment_unlimited_mult": "sk_unlimited_mult",
        }
        minimum = Parameter.search([("code", "=", "l10n_sk_zivotne_minimum")])
        rates = self.env["hr.wage.garnishment.rate"].search(
            [("country_id.code", "=", "SK")])
        payroll_from = min(minimum.parameter_value_ids.mapped("date_from"))
        days = set(minimum.parameter_value_ids.mapped("date_from"))
        days |= {day for day in rates.mapped("date_from") if day >= payroll_from}
        self.assertGreaterEqual(len(days), 4)
        for day in sorted(days):
            rate = self.env["hr.wage.garnishment.rate"]._get_rate("SK", day)
            for code, field in pairs.items():
                with self.subTest(day=day, code=code):
                    self.assertAlmostEqual(
                        Parameter._get_parameter_value(code, day),
                        rate[field], places=4)
