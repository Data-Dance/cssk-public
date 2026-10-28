# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""OCA payroll restricts hr.payslip to the user's companies but not the lines,
inputs and worked days of a payslip. A payroll manager of one company must not
read another company's payslip lines (wages, deductions) from a list, a report
or an export."""

from datetime import date

from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestPayslipCompanyRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.structure = cls.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")
        country = cls.env.ref("base.cz")
        cls.company_a = cls.env["res.company"].create(
            {"name": "CZ Payroll A", "country_id": country.id})
        cls.company_b = cls.env["res.company"].create(
            {"name": "CZ Payroll B", "country_id": country.id})
        cls.slip_a = cls._computed_payslip(cls.company_a, "Worker A")
        cls.slip_b = cls._computed_payslip(cls.company_b, "Worker B")
        cls.user_b = new_test_user(
            cls.env, login="payroll_b_cz",
            groups="base.group_user,payroll.group_payroll_manager",
            company_id=cls.company_b.id,
            company_ids=[(6, 0, cls.company_b.ids)])

    @classmethod
    def _computed_payslip(cls, company, name):
        env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=company.ids))
        calendar = env["resource.calendar"].create(
            {"name": "40h %s" % name, "company_id": company.id})
        employee = env["hr.employee"].create({
            "name": name,
            "company_id": company.id,
            "resource_calendar_id": calendar.id,
        })
        version = employee.version_id
        version.write({
            "contract_date_start": date(2026, 1, 1),
            "date_version": date(2026, 1, 1),
            "wage": 3000.0,
            "resource_calendar_id": calendar.id,
            "struct_id": cls.structure.id,
        })
        slip = env["hr.payslip"].create({
            "name": "Payslip %s" % name,
            "employee_id": employee.id,
            "contract_id": version.id,
            "struct_id": cls.structure.id,
            "company_id": company.id,
            "date_from": date(2026, 3, 1),
            "date_to": date(2026, 3, 31),
        })
        slip.compute_sheet()
        env["hr.payslip.input"].create({
            "name": "Bonus", "code": "BONUS", "amount": 100.0,
            "payslip_id": slip.id, "contract_id": version.id,
        })
        env["hr.payslip.worked_days"].create({
            "name": "Worked", "code": "WORK100", "number_of_days": 22.0,
            "payslip_id": slip.id, "contract_id": version.id,
        })
        return slip

    def test_children_of_payslip_scoped_to_company(self):
        self.assertTrue(self.slip_a.line_ids, "fixture: payslip A has lines")
        env_b = self.env(user=self.user_b, context=dict(
            self.env.context, allowed_company_ids=self.company_b.ids))
        for model, field in (("hr.payslip.line", "slip_id"),
                             ("hr.payslip.input", "payslip_id"),
                             ("hr.payslip.worked_days", "payslip_id")):
            seen = env_b[model].search([])
            self.assertFalse(
                seen.filtered(lambda r, f=field: r.sudo()[f] == self.slip_a),
                "%s of another company is visible" % model)
            self.assertTrue(
                seen.filtered(lambda r, f=field: r.sudo()[f] == self.slip_b),
                "%s of the user's own company is hidden" % model)
