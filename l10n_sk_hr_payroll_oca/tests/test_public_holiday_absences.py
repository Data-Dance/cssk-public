# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A public holiday of the working calendar inside an absence.

Monday to Friday, eight hours, monthly salary 2 000. April 2026 schedules 22
days (176 hours) with Good Friday on the 3rd and Easter Monday on the 6th;
May 2026 schedules 21 days (168 hours) with 1 May on a Friday. The holidays
are public holidays of the calendar, as Time Off enters them.
"""

from datetime import date, datetime

import pytz

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkPublicHolidayAbsences(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Holiday Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "SK 40h/week",
                "company_id": cls.company.id,
                "tz": "Europe/Bratislava",
            }
        )
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        for day in (date(2026, 4, 3), date(2026, 4, 6), date(2026, 5, 1)):
            cls._public_holiday(day)

    @classmethod
    def _public_holiday(cls, day):
        tz = pytz.timezone("Europe/Bratislava")

        def utc(hour, minute, second):
            local = tz.localize(datetime(day.year, day.month, day.day, hour, minute, second))
            return local.astimezone(pytz.utc).replace(tzinfo=None)

        return cls.env["resource.calendar.leaves"].create(
            {
                "name": "Public holiday %s" % day,
                "company_id": cls.company.id,
                "calendar_id": cls.calendar.id,
                "date_from": utc(0, 0, 0),
                "date_to": utc(23, 59, 59),
            }
        )

    def _employee(self, name, wage=2000.0, **vals):
        employee = self.env["hr.employee"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
            }
        )
        values = {
            "contract_date_start": date(2024, 1, 1),
            "date_version": date(2024, 1, 1),
            "wage": wage,
            "resource_calendar_id": self.calendar.id,
            "struct_id": self.structure.id,
        }
        values.update(vals)
        employee.version_id.write(values)
        return employee

    def _leave(self, employee, xmlid, d_from, d_to):
        leave_type = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
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

    def _slip(self, employee, month, last_day, inputs=()):
        contract = employee.version_id
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Slip %s" % month,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, month, 1),
                    "date_to": date(2026, month, last_day),
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

    @staticmethod
    def _worked(slip):
        return {
            line.code: (abs(line.number_of_days), abs(line.number_of_hours))
            for line in slip.worked_days_line_ids
        }

    # ------------------------------------------------------------------
    # no absence
    # ------------------------------------------------------------------
    def test_public_holiday_alone_is_inside_the_salary(self):
        slip = self._slip(self._employee("Holiday only"), 5, 31)
        self.assertEqual(
            self._worked(slip), {"WORK100": (21.0, 168.0), "GLOBAL": (1.0, 8.0)}
        )
        self.assertEqual(slip.get_salary_line_total("BASIC"), 2000.0)

    # ------------------------------------------------------------------
    # absences that take the holiday
    # ------------------------------------------------------------------
    def test_sickness_from_a_public_holiday_is_sickness(self):
        # Sick 1 to 15 May: 11 scheduled days, the holiday among them. The
        # employee is absent for the incapacity, so no wage is due for the
        # holiday: 2 000 x 80 / 168 = 952.3810. Sick pay runs by calendar
        # day, 14 days on a daily base of 40: 3 x 10 + 11 x 22.
        employee = self._employee("Sick from the holiday")
        self._leave(employee, "l10n_sk_leave_type_pn", date(2026, 5, 1), date(2026, 5, 15))
        slip = self._slip(employee, 5, 31, inputs=[("PN_DVZ", 40.0)])
        self.assertEqual(
            self._worked(slip), {"WORK100": (21.0, 168.0), "PN": (11.0, 88.0)}
        )
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 952.39)
        self.assertEqual(line("SICK_COMP"), 272.0)
        self.assertEqual(line("GROSS"), 952.39)

    def test_sickness_across_a_public_holiday_is_sickness(self):
        employee = self._employee("Sick across the holiday")
        self._leave(employee, "l10n_sk_leave_type_pn", date(2026, 4, 27), date(2026, 5, 5))
        slip = self._slip(employee, 5, 31, inputs=[("PN_DVZ", 40.0)])
        # 1, 4 and 5 May
        self.assertEqual(
            self._worked(slip), {"WORK100": (21.0, 168.0), "PN": (3.0, 24.0)}
        )
        # 2 000 x 144 / 168 = 1 714.2857
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1714.29)

    def test_family_and_unpaid_leave_from_a_public_holiday_pay_no_wage(self):
        for xmlid, code in (
            ("l10n_sk_leave_type_materska", "MATERSKA"),
            ("l10n_sk_leave_type_rodicovska", "RODICOVSKA"),
            ("l10n_sk_leave_type_otcovska", "OTCOVSKA"),
            ("l10n_sk_leave_type_neplatene", "NEPLATENE"),
            ("l10n_sk_leave_type_ocr", "OCR"),
        ):
            with self.subTest(code=code):
                employee = self._employee("Whole May %s" % code)
                self._leave(employee, xmlid, date(2026, 5, 1), date(2026, 5, 31))
                slip = self._slip(employee, 5, 31)
                self.assertEqual(
                    self._worked(slip), {"WORK100": (21.0, 168.0), code: (21.0, 168.0)}
                )
                self.assertEqual(slip.get_salary_line_total("BASIC"), 0.0)
                self.assertEqual(slip.get_salary_line_total("GROSS"), 0.0)

    # ------------------------------------------------------------------
    # paid leave: the holiday is not a day of leave
    # ------------------------------------------------------------------
    def test_leave_from_a_public_holiday_starts_after_it(self):
        # Leave 3 to 10 April: Good Friday and Easter Monday are holidays,
        # the leave is 7 to 10 April. 2 000 x 144 / 176 = 1 636.3636; leave
        # pay 32 h x 11.3636 (2 000 / 176) = 363.6352.
        employee = self._employee("Leave from Good Friday")
        leave = self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 4, 3), date(2026, 4, 10)
        )
        self.assertEqual(leave.number_of_days, 4.0)
        slip = self._slip(employee, 4, 30)
        self.assertEqual(
            self._worked(slip),
            {"WORK100": (22.0, 176.0), "GLOBAL": (2.0, 16.0), "DOVOLENKA": (4.0, 32.0)},
        )
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 1636.37)
        self.assertEqual(line("DOVOLENKA_NAHRADA"), 363.64)
        self.assertEqual(line("GROSS"), 2000.01)

    def test_public_holiday_inside_leave_is_not_a_day_of_leave(self):
        # Leave 27 April to 5 May: six days of leave, 1 May is not one of
        # them. May: 2 000 x 152 / 168 = 1 809.5238; leave pay 16 h x
        # 11.9048 (2 000 / 168) = 190.4768.
        employee = self._employee("Leave across the holiday")
        leave = self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 4, 27), date(2026, 5, 5)
        )
        self.assertEqual(leave.number_of_days, 6.0)
        may = self._slip(employee, 5, 31)
        self.assertEqual(
            self._worked(may),
            {"WORK100": (21.0, 168.0), "GLOBAL": (1.0, 8.0), "DOVOLENKA": (2.0, 16.0)},
        )
        line = may.get_salary_line_total
        self.assertEqual(line("BASIC"), 1809.53)
        self.assertEqual(line("DOVOLENKA_NAHRADA"), 190.48)
        self.assertEqual(line("GROSS"), 2000.01)
        april = self._slip(employee, 4, 30)
        self.assertEqual(self._worked(april)["DOVOLENKA"], (4.0, 32.0))

    def test_two_public_holidays_inside_leave(self):
        # Leave 2 to 10 April: 2, 7, 8, 9 and 10 April. 2 000 x 136 / 176 =
        # 1 545.4545; leave pay 40 h x 11.3636 = 454.544.
        employee = self._employee("Leave over Easter")
        leave = self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 4, 2), date(2026, 4, 10)
        )
        self.assertEqual(leave.number_of_days, 5.0)
        slip = self._slip(employee, 4, 30)
        self.assertEqual(
            self._worked(slip),
            {"WORK100": (22.0, 176.0), "GLOBAL": (2.0, 16.0), "DOVOLENKA": (5.0, 40.0)},
        )
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 1545.46)
        self.assertEqual(line("DOVOLENKA_NAHRADA"), 454.55)

    def test_obstacle_on_a_public_holiday_is_the_holiday(self):
        # A doctor's visit booked over 30 April and 1 May is one day.
        employee = self._employee("Obstacle on the holiday")
        self._leave(employee, "l10n_sk_leave_type_obstacle", date(2026, 4, 30), date(2026, 5, 1))
        slip = self._slip(employee, 5, 31)
        self.assertEqual(
            self._worked(slip), {"WORK100": (21.0, 168.0), "GLOBAL": (1.0, 8.0)}
        )
        self.assertEqual(slip.get_salary_line_total("BASIC"), 2000.0)

    def test_absence_for_part_of_a_public_holiday_keeps_only_its_hours(self):
        # Two hours of unpaid leave booked on 1 May: the other six scheduled
        # hours of the day are the holiday. 2 000 x 166 / 168 = 1 976.1905.
        employee = self._employee("Two hours on the holiday")
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Unpaid hours",
                "request_unit": "hour",
                "requires_allocation": False,
                "company_id": self.company.id,
                "l10n_sk_payroll_code": "NEPLATENE",
            }
        )
        tz = pytz.timezone("Europe/Bratislava")

        def utc(hour):
            local = tz.localize(datetime(2026, 5, 1, hour, 0, 0))
            return local.astimezone(pytz.utc).replace(tzinfo=None)

        # Time Off itself takes no request on a public holiday, so the
        # absence is written the way an approved request is kept.
        request = (
            self.env["hr.leave"]
            .with_company(self.company)
            .create(
                {
                    "name": leave_type.name,
                    "employee_id": employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": date(2026, 5, 4),
                    "request_date_to": date(2026, 5, 4),
                }
            )
        )
        request.action_approve()
        self.env["resource.calendar.leaves"].search(
            [("holiday_id", "=", request.id)]
        ).write({"date_from": utc(8), "date_to": utc(10)})
        slip = self._slip(employee, 5, 31)
        self.assertEqual(
            self._worked(slip),
            {"WORK100": (21.0, 168.0), "GLOBAL": (0.75, 6.0), "NEPLATENE": (0.25, 2.0)},
        )
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1976.2)

    def test_meal_days_exclude_the_holiday_and_the_absence_once(self):
        employee = self._employee(
            "Meals", l10n_sk_meal_allowance_type="financial"
        )
        self._leave(employee, "l10n_sk_leave_type_pn", date(2026, 5, 1), date(2026, 5, 5))
        slip = self._slip(employee, 5, 31)
        meal = slip.line_ids.filtered(lambda row: row.code == "MEALEMPLOYER")
        # 21 scheduled days less 1, 4 and 5 May
        self.assertEqual(meal.quantity, 18.0)
