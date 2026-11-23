# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The holidays kept by ``l10n_cssk_public_holidays`` on a Slovak payslip."""

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkGeneratedPublicHolidays(TransactionCase):
    def test_generated_holidays_reach_the_payslip(self):
        if "calendar.public.holiday" not in self.env or not hasattr(
            self.env["calendar.public.holiday"], "cssk_generate"
        ):
            self.skipTest("l10n_cssk_public_holidays is not installed")
        company = self.env["res.company"].create(
            {"name": "SK Generated Co", "country_id": self.env.ref("base.sk").id}
        )
        self.env.user.company_ids |= company
        calendar = self.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": company.id, "tz": "Europe/Bratislava"}
        )
        structure = self.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        Holiday = self.env["calendar.public.holiday"]
        Holiday.search([("year", "=", 2031)]).unlink()
        Holiday.cssk_generate(years=(2031,), country_codes=("SK",))
        Holiday.cssk_sync_calendar_leaves()

        def slip(name, sick=False):
            employee = self.env["hr.employee"].create(
                {"name": name, "company_id": company.id, "resource_calendar_id": calendar.id}
            )
            employee.version_id.write(
                {
                    "contract_date_start": date(2024, 1, 1),
                    "date_version": date(2024, 1, 1),
                    "wage": 2000.0,
                    "resource_calendar_id": calendar.id,
                    "struct_id": structure.id,
                }
            )
            if sick:
                leave_type = self.env.ref("l10n_sk_hr_payroll_oca.l10n_sk_leave_type_pn")
                self.env["hr.leave"].with_company(company).create(
                    {
                        "name": leave_type.name,
                        "employee_id": employee.id,
                        "holiday_status_id": leave_type.id,
                        "request_date_from": date(2031, 5, 1),
                        "request_date_to": date(2031, 5, 9),
                    }
                ).action_approve()
            payslip = (
                self.env["hr.payslip"]
                .with_company(company)
                .create(
                    {
                        "name": name,
                        "employee_id": employee.id,
                        "contract_id": employee.version_id.id,
                        "struct_id": structure.id,
                        "company_id": company.id,
                        "date_from": date(2031, 5, 1),
                        "date_to": date(2031, 5, 31),
                    }
                )
            )
            payslip.onchange_dates()
            payslip.compute_sheet()
            return payslip

        # May 2031: 22 scheduled days, 1 and 8 May on Thursdays.
        worked = slip("Worked")
        self.assertEqual(
            {
                line.code: (abs(line.number_of_days), abs(line.number_of_hours))
                for line in worked.worked_days_line_ids
            },
            {"WORK100": (22.0, 176.0), "GLOBAL": (2.0, 16.0)},
        )
        self.assertEqual(worked.get_salary_line_total("BASIC"), 2000.0)
        # Sick 1 to 9 May: seven scheduled days, both holidays among them.
        # 2 000 x 120 / 176 = 1 363.6364.
        sick = slip("Sick", sick=True)
        self.assertEqual(
            {
                line.code: (abs(line.number_of_days), abs(line.number_of_hours))
                for line in sick.worked_days_line_ids
            },
            {"WORK100": (22.0, 176.0), "PN": (7.0, 56.0)},
        )
        self.assertEqual(sick.get_salary_line_total("BASIC"), 1363.64)

    def test_a_holiday_of_the_oca_time_off_module_stays_inside_the_salary(self):
        # ``hr_holidays_public`` takes the holidays of the OCA calendar out of
        # the schedule whenever the engine asks for worked days.
        if "exclude_public_holidays" not in self.env["hr.leave.type"]._fields:
            self.skipTest("hr_holidays_public is not installed")
        company = self.env["res.company"].create(
            {"name": "SK OCA holidays Co", "country_id": self.env.ref("base.sk").id}
        )
        self.env.user.company_ids |= company
        calendar = self.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": company.id, "tz": "Europe/Bratislava"}
        )
        structure = self.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        Holiday = self.env["calendar.public.holiday"]
        Holiday.search([("year", "=", 2031)]).unlink()
        holiday = Holiday.create({"year": 2031, "country_id": self.env.ref("base.sk").id})
        self.env["calendar.public.holiday.line"].create(
            {"public_holiday_id": holiday.id, "date": date(2031, 5, 1), "name": "Sviatok práce"}
        )
        employee = self.env["hr.employee"].create(
            {"name": "Whole May", "company_id": company.id, "resource_calendar_id": calendar.id}
        )
        employee.version_id.write(
            {
                "contract_date_start": date(2024, 1, 1),
                "date_version": date(2024, 1, 1),
                "wage": 2000.0,
                "resource_calendar_id": calendar.id,
                "struct_id": structure.id,
            }
        )
        leave_type = self.env.ref("l10n_sk_hr_payroll_oca.l10n_sk_leave_type_pn")
        self.env["hr.leave"].with_company(company).create(
            {
                "name": leave_type.name,
                "employee_id": employee.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": date(2031, 5, 26),
                "request_date_to": date(2031, 5, 26),
            }
        ).action_approve()
        payslip = (
            self.env["hr.payslip"]
            .with_company(company)
            .create(
                {
                    "name": "Whole May",
                    "employee_id": employee.id,
                    "contract_id": employee.version_id.id,
                    "struct_id": structure.id,
                    "company_id": company.id,
                    "date_from": date(2031, 5, 1),
                    "date_to": date(2031, 5, 31),
                }
            )
        )
        payslip.onchange_dates()
        payslip.compute_sheet()
        worked = payslip.worked_days_line_ids.filtered(lambda line: line.code == "WORK100")
        # 22 scheduled days in May 2031, the holiday among them; one day sick.
        self.assertEqual((worked.number_of_days, worked.number_of_hours), (22.0, 176.0))
        # 2 000 x 168 / 176 = 1 909.0909
        self.assertEqual(payslip.get_salary_line_total("BASIC"), 1909.1)
