# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Several leave types of one Slovak payroll code in one payslip.

Monday to Friday, eight hours, monthly salary 2 000. June 2026 schedules 22
days (176 hours) and has no public holiday. The starter leave types share
payroll codes: unpaid leave and unpaid leave for education are both
NEPLATENE, sickness and quarantine are both PN, and the paid obstacles of
§ 136 to § 141 Zákonníka práce are all OBSTACLE. Each leave type has a
worked-day line of its own; the pay of a code is the pay of all of them.
"""

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkSharedPayrollCodes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Shared Code Co", "country_id": cls.env.ref("base.sk").id}
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

    def _employee(self, name, **vals):
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
            "wage": 2000.0,
            "resource_calendar_id": self.calendar.id,
            "struct_id": self.structure.id,
        }
        values.update(vals)
        employee.version_id.write(values)
        return employee

    def _leave(self, employee, xmlid, first, last=None):
        leave_type = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
        leave = (
            self.env["hr.leave"]
            .with_company(self.company)
            .create(
                {
                    "name": leave_type.name,
                    "employee_id": employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": date(2026, 6, first),
                    "request_date_to": date(2026, 6, last or first),
                }
            )
        )
        leave.action_approve()
        return leave

    def _draft_slip(self, employee, inputs=()):
        contract = employee.version_id
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "June 2026",
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
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
        return slip

    def _slip(self, employee, inputs=()):
        slip = self._draft_slip(employee, inputs=inputs)
        slip.compute_sheet()
        return slip

    @staticmethod
    def _lines(slip, code):
        """The hours of each worked-day line of ``code``, smallest first."""
        return sorted(
            abs(line.number_of_hours)
            for line in slip.worked_days_line_ids
            if line.code == code
        )

    # ------------------------------------------------------------------
    # NEPLATENE: unpaid leave and unpaid leave for education
    # ------------------------------------------------------------------
    def test_two_unpaid_leave_types_are_both_unpaid(self):
        employee = self._employee("Two unpaid types")
        self._leave(employee, "l10n_sk_leave_type_neplatene", 2)
        self._leave(employee, "l10n_sk_leave_type_vzdelavanie_unpaid", 4)
        slip = self._slip(employee)
        self.assertEqual(self._lines(slip, "NEPLATENE"), [8.0, 8.0])
        # 2 000 x 160 / 176 = 1 818.1818
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1818.19)
        self.assertEqual(slip.get_salary_line_total("GROSS"), 1818.19)

    def test_the_rules_read_the_lines_of_a_code_as_one(self):
        employee = self._employee("Two unpaid types, read")
        self._leave(employee, "l10n_sk_leave_type_neplatene", 2)
        self._leave(employee, "l10n_sk_leave_type_vzdelavanie_unpaid", 4)
        slip = self._slip(employee)
        worked_days = slip._get_baselocaldict(employee.version_id)["worked_days"]
        unpaid = worked_days.NEPLATENE
        self.assertEqual(
            (unpaid.code, unpaid.number_of_days, unpaid["number_of_hours"]),
            ("NEPLATENE", -2.0, -16.0),
        )
        self.assertEqual(unpaid.contract_id, employee.version_id)
        self.assertEqual(worked_days.WORK100.number_of_hours, 176.0)

    def test_two_unpaid_leave_types_leave_the_worked_time(self):
        employee = self._employee(
            "Two unpaid types, meals", l10n_sk_meal_allowance_type="financial"
        )
        self._leave(employee, "l10n_sk_leave_type_neplatene", 2)
        self._leave(employee, "l10n_sk_leave_type_vzdelavanie_unpaid", 4)
        slip = self._slip(employee)
        meal = slip.line_ids.filtered(lambda row: row.code == "MEALEMPLOYER")
        self.assertEqual(meal.quantity, 20.0)
        self.assertEqual(slip._l10n_sk_average_worked_time(), (20.0, 160.0))

    # ------------------------------------------------------------------
    # PN: sickness and quarantine
    # ------------------------------------------------------------------
    def test_sickness_and_quarantine_both_reduce_the_salary(self):
        # Sick on 8 and 9 June, in quarantine from 15 to 17 June: five
        # scheduled days. 2 000 x 136 / 176 = 1 545.4545. Two incapacities,
        # each counted from its own first day (§ 8 zákona 462/2003): on a
        # daily base of 40 at 25 %, 2 x 10 + 3 x 10.
        employee = self._employee("Sick and in quarantine")
        self._leave(employee, "l10n_sk_leave_type_pn", 8, 9)
        self._leave(employee, "l10n_sk_leave_type_karantena", 15, 17)
        slip = self._slip(employee, inputs=[("PN_DVZ", 40.0)])
        self.assertEqual(self._lines(slip, "PN"), [16.0, 24.0])
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 1545.46)
        self.assertEqual(line("SICK_COMP"), 50.0)
        self.assertEqual(line("GROSS"), 1545.46)

    # ------------------------------------------------------------------
    # OBSTACLE: the paid obstacles
    # ------------------------------------------------------------------
    def test_three_paid_obstacle_types_are_all_compensated(self):
        # Three days, each of another obstacle: 24 hours at the probable
        # average of 2 000 / 176 = 11.3636, 272.7264; the salary for the
        # remaining 152 hours is 2 000 x 152 / 176 = 1 727.2727.
        employee = self._employee("Three obstacles")
        self._leave(employee, "l10n_sk_leave_type_obstacle", 22)
        self._leave(employee, "l10n_sk_leave_type_darovanie_krvi", 23)
        self._leave(employee, "l10n_sk_leave_type_vzdelavanie", 24)
        slip = self._slip(employee)
        self.assertEqual(self._lines(slip, "OBSTACLE"), [8.0, 8.0, 8.0])
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 1727.28)
        self.assertEqual(line("OBSTACLE_NAHRADA"), 272.73)
        self.assertEqual(line("GROSS"), 2000.01)

    # ------------------------------------------------------------------
    # lines that the calendar did not build
    # ------------------------------------------------------------------
    def test_a_second_line_typed_by_hand_counts(self):
        employee = self._employee("Typed line")
        self._leave(employee, "l10n_sk_leave_type_neplatene", 2)
        slip = self._draft_slip(employee)
        generated = slip.worked_days_line_ids.filtered(
            lambda row: row.code == "NEPLATENE"
        )
        generated.copy({"payslip_id": slip.id, "name": "Typed by hand"})
        slip.compute_sheet()
        self.assertEqual(self._lines(slip, "NEPLATENE"), [8.0, 8.0])
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1818.19)

    def test_one_line_of_a_code_is_the_line_itself(self):
        employee = self._employee("One type")
        self._leave(employee, "l10n_sk_leave_type_neplatene", 2)
        slip = self._slip(employee)
        worked_days = slip._get_baselocaldict(employee.version_id)["worked_days"]
        unpaid = slip.worked_days_line_ids.filtered(lambda row: row.code == "NEPLATENE")
        self.assertEqual(worked_days.dict["NEPLATENE"], unpaid)
        # 2 000 x 168 / 176 = 1 909.0909
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1909.1)
