# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The shared new-hire sick-pay base cases on the OCA payroll engine."""

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_sk_hr_payroll_base.tests.sick_base_cases import (
    NewHireSickBaseCases,
)


@tagged("post_install", "-at_install")
class TestSkNewHireSickBase(NewHireSickBaseCases, TransactionCase):
    # The cases are methods of the shared class.
    allow_inherited_tests_method = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Sick Base Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )

    def _hire(self, name, start, wage=2000.0):
        employee = self.env["hr.employee"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
            }
        )
        employee.version_id.write(
            {
                "contract_date_start": start,
                "date_version": start,
                "wage": wage,
                "resource_calendar_id": self.calendar.id,
                "struct_id": self.structure.id,
            }
        )
        return employee

    def _absence(self, employee, kind, d_from, d_to):
        leave_type = self.env.ref("l10n_sk_hr_payroll_oca.l10n_sk_leave_type_%s" % kind)
        leave = (
            self.env["hr.leave"]
            .with_company(self.company)
            .create(
                {
                    "name": leave_type.name,
                    "employee_id": employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": d_from,
                    "request_date_to": d_to,
                }
            )
        )
        leave.action_approve()
        return leave

    def _payslip(self, employee, year, month, dvz=None):
        date_from, date_to = self._month(year, month)
        contract = employee.version_id
        inputs = [("PN_DVZ", dvz)] if dvz else []
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "%s %s/%s" % (employee.name, month, year),
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date_from,
                    "date_to": date_to,
                    "input_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": code,
                                "code": code,
                                "amount": amount,
                                "contract_id": contract.id,
                            },
                        )
                        for code, amount in inputs
                    ],
                }
            )
        )
        slip.onchange_dates()
        slip.compute_sheet()
        return slip

    def _confirm(self, slip):
        slip.action_payslip_done()

    def _line(self, slip, code):
        return slip.get_salary_line_total(code)
