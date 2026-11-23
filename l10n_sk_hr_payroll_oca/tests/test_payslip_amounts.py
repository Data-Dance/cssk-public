# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Whole-cent wage amounts, the part month at both ends, inputs and meal days.

Monday to Friday, eight hours: March and June 2026 schedule 22 working days
(176 hours), May 2026 schedules 21 (168 hours).
"""

from datetime import date, datetime
from functools import wraps
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


def expected_failure(reason):
    """Pass while the test fails; the Odoo runner has no expected failures."""

    def decorator(test):
        @wraps(test)
        def wrapper(self):
            try:
                test(self)
            except self.failureException:
                return
            self.fail("Passes now, drop the marker: %s" % reason)

        return wrapper

    return decorator


@tagged("post_install", "-at_install")
class TestSkPayslipAmounts(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Amounts Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )

    def setUp(self):
        super().setUp()
        # Some wages here are below the minimum wage claim; the top-up of
        # l10n_sk_hr_payroll_surcharges has its own tests.
        Payslip = type(self.env["hr.payslip"])
        if hasattr(Payslip, "_l10n_sk_min_wage_claim_applies"):
            patcher = patch.object(
                Payslip, "_l10n_sk_min_wage_claim_applies", return_value=False
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def _contract(self, wage, start=date(2024, 1, 1), end=None, **vals):
        employee = self.env["hr.employee"].create(
            {
                "name": "Employee %s" % wage,
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
            }
        )
        values = {
            "contract_date_start": start,
            "date_version": start,
            "wage": wage,
            "resource_calendar_id": self.calendar.id,
            "struct_id": self.structure.id,
        }
        if end:
            values["contract_date_end"] = end
        values.update(vals)
        employee.version_id.write(values)
        return employee.version_id, employee

    def _slip(self, contract, employee, year, month, last_day, inputs=()):
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Slip %s/%s" % (month, year),
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(year, month, 1),
                    "date_to": date(year, month, last_day),
                    "input_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": name,
                                "code": code,
                                "amount": amount,
                                "contract_id": contract.id,
                            },
                        )
                        for code, name, amount in inputs
                    ],
                }
            )
        )
        # What the form does: fill the worked-day lines.
        slip.onchange_dates()
        slip.compute_sheet()
        return slip

    def _leave(self, employee, xmlid, d_from, d_to, half=None, hours=None):
        """Book an approved absence; ``half`` ("am"/"pm") or ``hours``
        ((from, to)) make it a part of the day, on a copy of the type that
        takes half days or hours."""
        leave_type = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
        values = {
            "name": leave_type.name,
            "employee_id": employee.id,
            "holiday_status_id": leave_type.id,
            "request_date_from": d_from,
            "request_date_to": d_to,
        }
        unit = "half_day" if half else "hour" if hours else None
        if unit:
            # A type of its own: changing the unit of the starter type would
            # recompute the absences already approved on it.
            copies = self.__dict__.setdefault("_part_day_types", {})
            if (leave_type.id, unit) not in copies:
                copies[leave_type.id, unit] = leave_type.copy({"request_unit": unit})
            leave_type = copies[leave_type.id, unit]
            values["holiday_status_id"] = leave_type.id
        if half:
            values.update(request_date_from_period=half, request_date_to_period=half)
        elif hours:
            values.update(request_hour_from=hours[0], request_hour_to=hours[1])
        leave = self.env["hr.leave"].with_company(self.company).create(values)
        leave.action_approve()
        return leave

    @staticmethod
    def _worked(slip, code="WORK100"):
        lines = slip.worked_days_line_ids.filtered(lambda line: line.code == code)
        return sum(lines.mapped("number_of_days")), sum(lines.mapped("number_of_hours"))

    # ------------------------------------------------------------------
    # part month
    # ------------------------------------------------------------------
    def test_salary_is_prorated_in_the_month_the_contract_ends(self):
        # 1 to 15 June 2026 holds 11 of the 22 working days.
        contract, employee = self._contract(2000.0, end=date(2026, 6, 15))
        slip = self._slip(contract, employee, 2026, 6, 30)
        self.assertEqual(self._worked(slip), (11.0, 88.0))
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1000.0)
        self.assertEqual(slip.get_salary_line_total("GROSS"), 1000.0)

    def test_salary_is_prorated_in_the_month_the_contract_starts(self):
        contract, employee = self._contract(2000.0, start=date(2026, 6, 16))
        slip = self._slip(contract, employee, 2026, 6, 30)
        self.assertEqual(self._worked(slip), (11.0, 88.0))
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1000.0)

    def test_contract_within_one_month_pays_its_own_days(self):
        # 8 to 19 June 2026: 10 of the 22 working days.
        contract, employee = self._contract(
            2200.0, start=date(2026, 6, 8), end=date(2026, 6, 19)
        )
        slip = self._slip(contract, employee, 2026, 6, 30)
        self.assertEqual(self._worked(slip), (10.0, 80.0))
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1000.0)

    def test_contract_ending_on_the_last_day_is_a_full_month(self):
        contract, employee = self._contract(2000.0, end=date(2026, 6, 30))
        slip = self._slip(contract, employee, 2026, 6, 30)
        self.assertEqual(self._worked(slip), (22.0, 176.0))
        self.assertEqual(slip.get_salary_line_total("BASIC"), 2000.0)

    def test_contract_ended_before_the_period_has_no_worked_days(self):
        contract, _employee = self._contract(2000.0, end=date(2026, 6, 15))
        lines = self.env["hr.payslip"].get_worked_day_lines(
            contract, date(2026, 7, 1), date(2026, 7, 31)
        )
        self.assertEqual(
            [(row["code"], row["number_of_days"], row["number_of_hours"]) for row in lines],
            [("WORK100", 0.0, 0.0)],
        )

    def test_leave_after_the_contract_end_is_not_on_the_payslip(self):
        contract, employee = self._contract(2000.0)
        self._leave(
            employee, "l10n_sk_leave_type_neplatene", date(2026, 6, 15), date(2026, 6, 16)
        )
        contract.contract_date_end = date(2026, 6, 15)
        slip = self._slip(contract, employee, 2026, 6, 30)
        self.assertEqual(self._worked(slip), (11.0, 88.0))
        self.assertEqual(self._worked(slip, "NEPLATENE"), (-1.0, -8.0))
        # 2 000 x 80 / 176 = 909.0909, rounded up
        self.assertEqual(slip.get_salary_line_total("BASIC"), 909.1)

    @expected_failure(
        "a wage change dated inside a month is paid as a hire on that date"
    )
    def test_wage_change_inside_a_month_pays_both_parts(self):
        contract, employee = self._contract(1500.0)
        employee.create_version({"date_version": date(2026, 6, 16), "wage": 1800.0})
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Wage change",
                    "employee_id": employee.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                }
            )
        )
        slip.onchange_employee()
        slip.compute_sheet()
        # 1 500 x 88 / 176 + 1 800 x 88 / 176
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1650.0)

    # ------------------------------------------------------------------
    # whole cents
    # ------------------------------------------------------------------
    def test_prorated_salary_is_a_whole_cent_amount_for_every_reader(self):
        # Hired 10 March 2026: 16 of 22 working days, 1 000 x 128 / 176 =
        # 727.2727, a wage component, so 727.28. Levies on 727.28: 10.18 +
        # 29.09 + 21.81 + 7.27 + 36.36 = 104.71; tax 19 % of 622.57 = 118.2883.
        contract, employee = self._contract(1000.0, start=date(2026, 3, 10))
        slip = self._slip(contract, employee, 2026, 3, 31)
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 727.28)
        self.assertEqual(line("SICK"), -10.18)
        self.assertEqual(line("PENSION"), -29.09)
        self.assertEqual(line("DISABILITY"), -21.81)
        self.assertEqual(line("UNEMPLOYMENT"), -7.27)
        self.assertEqual(line("HEALTH"), -36.36)
        self.assertEqual(line("SOCIALEMPLOYEETOTAL"), -104.71)
        self.assertEqual(line("TAXBASE"), 622.57)
        self.assertEqual(line("INCOMETAX"), -118.29)
        self.assertEqual(line("NET"), 504.28)

    def test_levies_are_computed_on_the_whole_cent_gross(self):
        # May 2026, one unpaid day: 900 x 160 / 168 = 857.142857, a wage
        # component, so 857.15. Sickness insurance 1.4 % of 857.15 is
        # 12.0001, so 12.00; health 5 % is 42.8575, so 42.85.
        contract, employee = self._contract(900.0)
        self._leave(
            employee, "l10n_sk_leave_type_neplatene", date(2026, 5, 12), date(2026, 5, 12)
        )
        slip = self._slip(contract, employee, 2026, 5, 31)
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 857.15)
        self.assertEqual(line("GROSS"), 857.15)
        self.assertEqual(line("SICK"), -12.0)
        self.assertEqual(line("HEALTH"), -42.85)
        # 857.15 - 12.00 - 34.28 - 25.71 - 8.57 - 42.85
        self.assertEqual(line("TAXBASE"), 733.74)
        # The GROSS line the sick-pay daily base reads is the base the
        # sickness rule charged on.
        charged = [
            float(row["base"])
            for row in slip._l10n_sk_read_recorded_fund_bases()
            if row["fund"] == "sickness" and row["side"] == "employee"
        ]
        self.assertEqual(charged, [857.15])
        self.assertEqual(slip._l10n_sk_dvz_sickness_base(), 857.15)

    def test_full_month_is_exactly_the_salary(self):
        for wage in (2000.0, 1234.57, 915.01, 3333.33):
            for month, last_day in ((2, 28), (3, 31), (5, 31), (6, 30)):
                with self.subTest(wage=wage, month=month):
                    slip = self._slip(*self._contract(wage), 2026, month, last_day)
                    self.assertEqual(slip.get_salary_line_total("BASIC"), wage)
                    self.assertEqual(slip.get_salary_line_total("GROSS"), wage)

    def _public_holiday(self, day):
        return self.env["resource.calendar.leaves"].create(
            {
                "name": "Public holiday %s" % day,
                "calendar_id": self.calendar.id,
                "company_id": self.company.id,
                "date_from": datetime(day.year, day.month, day.day, 0, 0, 0),
                "date_to": datetime(day.year, day.month, day.day, 21, 0, 0),
            }
        )

    def test_base_pay_and_leave_pay_are_each_rounded_up(self):
        # May 2026 with the public holiday of 1 May in the calendar:
        # 20 working days and one holiday, 168 hours. One day of leave:
        # 2 000 x 160 / 168 = 1 904.7619. No payslips in the first quarter,
        # so the leave is paid at 2 000 / 168 = 11.9048: 95.2384.
        self._public_holiday(date(2026, 5, 1))
        contract, employee = self._contract(2000.0)
        self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 5, 12), date(2026, 5, 12)
        )
        slip = self._slip(contract, employee, 2026, 5, 31)
        self.assertEqual(self._worked(slip), (21.0, 168.0))
        self.assertEqual(self._worked(slip, "GLOBAL"), (-1.0, -8.0))
        line = slip.get_salary_line_total
        self.assertEqual(line("BASIC"), 1904.77)
        self.assertEqual(line("DOVOLENKA_NAHRADA"), 95.24)
        self.assertEqual(line("GROSS"), 2000.01)

    def test_leave_pay_is_hours_at_the_average_rounded_up_once(self):
        # Second quarter of 2026 at 2 000 a month: 6 000 / 520 = 11.5385.
        contract, employee = self._contract(2000.0)
        for month, last_day in ((4, 30), (5, 31), (6, 30)):
            self._slip(contract, employee, 2026, month, last_day).action_payslip_done()
        self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 7, 6), date(2026, 7, 6)
        )
        one_day = self._slip(contract, employee, 2026, 7, 31)
        self.assertEqual(one_day.l10n_sk_average_hourly_earnings(), 11.5385)
        # 8 h x 11.5385 = 92.308
        self.assertEqual(one_day.get_salary_line_total("DOVOLENKA_NAHRADA"), 92.31)
        self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 7, 7), date(2026, 7, 8)
        )
        three_days = self._slip(contract, employee, 2026, 7, 31)
        # 24 h x 11.5385 = 276.924; July has 184 hours, 2 000 x 160 / 184 =
        # 1 739.1304.
        self.assertEqual(three_days.get_salary_line_total("DOVOLENKA_NAHRADA"), 276.93)
        self.assertEqual(three_days.get_salary_line_total("BASIC"), 1739.14)
        self.assertEqual(three_days.get_salary_line_total("GROSS"), 2016.07)

    def test_obstacle_pay_is_rounded_up(self):
        # June 2026, no payslips before: 2 000 / 176 = 11.3636. One day at
        # the doctor: 8 h x 11.3636 = 90.9088; 2 000 x 168 / 176 = 1 909.0909.
        contract, employee = self._contract(2000.0)
        self._leave(
            employee, "l10n_sk_leave_type_obstacle", date(2026, 6, 9), date(2026, 6, 9)
        )
        slip = self._slip(contract, employee, 2026, 6, 30)
        line = slip.get_salary_line_total
        self.assertEqual(line("OBSTACLE_NAHRADA"), 90.91)
        self.assertEqual(line("BASIC"), 1909.1)

    def test_employer_obstacle_parts_are_summed_before_rounding(self):
        # 8 h of weather at 50 % and 8 h of serious operational reasons at
        # 60 % of 11.3636: 45.4544 + 54.54528 = 99.99968, so 100.00. Rounded
        # one by one they would be 45.46 + 54.55 = 100.01.
        contract, employee = self._contract(2000.0)
        self._leave(
            employee, "l10n_sk_leave_type_employer_pocasie", date(2026, 6, 9), date(2026, 6, 9)
        )
        self._leave(
            employee, "l10n_sk_leave_type_employer_vazne", date(2026, 6, 10), date(2026, 6, 10)
        )
        slip = self._slip(contract, employee, 2026, 6, 30)
        self.assertEqual(slip.get_salary_line_total("PREKAZKA_NAHRADA"), 100.0)

    def test_hourly_pay_is_rounded_up_once(self):
        # 7.25 h x 5.33 = 38.6425
        contract, employee = self._contract(2000.0, l10n_sk_hourly_wage=5.33)
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Hourly",
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                    "worked_days_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Attendance",
                                "code": "WORK100",
                                "number_of_days": 1.0,
                                "number_of_hours": 7.25,
                                "contract_id": contract.id,
                            },
                        )
                    ],
                }
            )
        )
        slip.compute_sheet()
        self.assertEqual(slip.get_salary_line_total("BASIC"), 38.65)
        # 160 h x 5.25 is a whole-cent amount and stays it.
        slip.worked_days_line_ids.number_of_hours = 160.0
        contract.l10n_sk_hourly_wage = 5.25
        slip.compute_sheet()
        self.assertEqual(slip.get_salary_line_total("BASIC"), 840.0)

    def test_net_is_income_less_the_rounded_tax(self):
        # 1 238 with the declaration, March 2026: levies 178.27, taxable wage
        # 1 059.73 - 497.23 = 562.50, tax 106.875.
        contract, employee = self._contract(
            1238.0, l10n_sk_tax_declaration_signed=True
        )
        slip = self._slip(contract, employee, 2026, 3, 31)
        line = slip.get_salary_line_total
        self.assertEqual(line("SOCIALEMPLOYEETOTAL"), -178.27)
        self.assertEqual(line("INCOMETAX"), -106.88)
        self.assertEqual(line("NET"), 952.85)

    def test_net_is_income_less_the_rounded_tax_plus_the_rounded_bonus(self):
        # 587 with two children under 15, March 2026: levies 84.52, tax
        # 0.9975, bonus capped at 36 % of 502.48 = 180.8928.
        contract, employee = self._contract(
            587.0,
            l10n_sk_tax_declaration_signed=True,
            l10n_sk_children_under_15=2,
        )
        slip = self._slip(contract, employee, 2026, 3, 31)
        line = slip.get_salary_line_total
        self.assertEqual(line("SOCIALEMPLOYEETOTAL"), -84.52)
        self.assertEqual(line("INCOMETAX"), -1.0)
        self.assertEqual(line("CHILD_BONUS"), 180.89)
        self.assertEqual(line("NET"), 682.37)

    def test_payslip_lines_add_up_to_net(self):
        # With two children the bonus is capped at 36 % of the tax base in
        # this range, so the tax and the bonus both carry a fraction of a cent.
        for wage in range(560, 640):
            with self.subTest(wage=wage):
                contract, employee = self._contract(
                    float(wage),
                    l10n_sk_tax_declaration_signed=True,
                    l10n_sk_children_under_15=2,
                )
                slip = self._slip(contract, employee, 2026, 3, 31)
                line = slip.get_salary_line_total
                self.assertAlmostEqual(
                    line("NET"),
                    line("GROSS")
                    + line("SOCIALEMPLOYEETOTAL")
                    + line("INCOMETAX")
                    + line("CHILD_BONUS"),
                    places=6,
                )

    # ------------------------------------------------------------------
    # inputs
    # ------------------------------------------------------------------
    def test_two_inputs_of_one_code_are_both_deducted(self):
        contract, employee = self._contract(1000.0)
        slip = self._slip(
            contract,
            employee,
            2026,
            6,
            30,
            inputs=[("DEDUCTION", "Advance", 50.0), ("DEDUCTION", "Union dues", 30.0)],
        )
        self.assertEqual(slip.get_salary_line_total("DEDUCTION"), -80.0)
        # 1 000 - 144.00 levies - 162.64 tax - 80.00
        self.assertEqual(slip.get_salary_line_total("NET"), 613.36)
        deduction = slip.line_ids.filtered(lambda row: row.code == "DEDUCTION")
        self.assertEqual(deduction.name, "Advance, Union dues")

    def test_one_input_keeps_its_name(self):
        contract, employee = self._contract(1000.0)
        slip = self._slip(
            contract, employee, 2026, 6, 30, inputs=[("DEDUCTION", "Advance", 50.0)]
        )
        deduction = slip.line_ids.filtered(lambda row: row.code == "DEDUCTION")
        self.assertEqual(deduction.name, "Advance")
        self.assertEqual(deduction.total, -50.0)

    def test_every_amount_input_is_summed(self):
        signs = {
            "ATTACH_SALARY": -1,
            "ASSIG_SALARY": -1,
            "CHILD_SUPPORT": -1,
            "DEDUCTION": -1,
            "REIMBURSEMENT": 1,
            "ANNUAL_TAX_SETTLEMENT": 1,
        }
        for code, sign in signs.items():
            with self.subTest(code=code):
                contract, employee = self._contract(1000.0)
                slip = self._slip(
                    contract,
                    employee,
                    2026,
                    6,
                    30,
                    inputs=[(code, "First", 12.5), (code, "Second", 20.0)],
                )
                self.assertEqual(slip.get_salary_line_total(code), sign * 32.5)

    def test_two_garnishment_inputs_are_one_debt(self):
        # Net 693.36 less 397.78 leaves 295.58; a third of 295.56 is 98.52.
        contract, employee = self._contract(1000.0)
        slip = self._slip(
            contract,
            employee,
            2026,
            6,
            30,
            inputs=[("GARNISHMENT", "First", 50.0), ("GARNISHMENT", "Second", 30.0)],
        )
        self.assertEqual(slip.get_salary_line_total("GARNISHMENT"), -80.0)
        slip = self._slip(
            *self._contract(1000.0),
            2026,
            6,
            30,
            inputs=[("GARNISHMENT", "First", 70.0), ("GARNISHMENT", "Second", 60.0)],
        )
        self.assertEqual(slip.get_salary_line_total("GARNISHMENT"), -98.52)

    def test_two_sick_day_inputs_are_one_count(self):
        contract, employee = self._contract(1500.0)
        slip = self._slip(
            contract,
            employee,
            2026,
            6,
            30,
            inputs=[
                ("PN_DAYS", "First", 2.0),
                ("PN_DAYS", "Second", 2.0),
                ("PN_DVZ", "Daily base", 20.0),
            ],
        )
        # Three days at 25 % and one at 55 % of 20.
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 26.0)

    # ------------------------------------------------------------------
    # meal days
    # ------------------------------------------------------------------
    def test_meal_days_are_the_days_worked(self):
        # May 2026: 21 scheduled days, five on leave, the holiday of 1 May.
        self._public_holiday(date(2026, 5, 1))
        contract, employee = self._contract(
            2000.0, l10n_sk_meal_allowance_type="financial"
        )
        self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 5, 11), date(2026, 5, 15)
        )
        slip = self._slip(contract, employee, 2026, 5, 31)
        self.assertEqual(self._worked(slip), (21.0, 168.0))
        meal = slip.line_ids.filtered(lambda row: row.code == "MEALEMPLOYER")
        self.assertEqual(meal.quantity, 15.0)
        # 55 % of 9.30 is 5.115, 5.12 a day: 15 x 5.12.
        self.assertEqual(meal.total, 76.80)

    def test_meal_days_of_the_voucher_share_are_the_days_worked(self):
        contract, employee = self._contract(
            2000.0, l10n_sk_meal_allowance_type="voucher"
        )
        self._leave(
            employee, "l10n_sk_leave_type_pn", date(2026, 6, 8), date(2026, 6, 12)
        )
        slip = self._slip(contract, employee, 2026, 6, 30)
        for code in ("MEALEMPLOYER", "MEALEMPLOYEE"):
            meal = slip.line_ids.filtered(lambda row, code=code: row.code == code)
            self.assertEqual(meal.quantity, 17.0, code)

    def test_meal_days_on_the_contract_win(self):
        contract, employee = self._contract(
            2000.0, l10n_sk_meal_allowance_type="financial", l10n_sk_meal_days=20
        )
        self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 6, 8), date(2026, 6, 12)
        )
        slip = self._slip(contract, employee, 2026, 6, 30)
        meal = slip.line_ids.filtered(lambda row: row.code == "MEALEMPLOYER")
        self.assertEqual(meal.quantity, 20.0)

    # § 152 ods. 2 Zákonníka práce: a meal day is a day with more than four
    # hours worked. June 2026 schedules 22 days of eight hours; the
    # contribution is 5.12 a day.
    def _june_meal(self, employee):
        slip = self._slip(employee.version_id, employee, 2026, 6, 30)
        meal = slip.line_ids.filtered(lambda row: row.code == "MEALEMPLOYER")
        return slip, meal.quantity, meal.total

    def _meal_employee(self, **vals):
        _contract, employee = self._contract(
            2000.0, l10n_sk_meal_allowance_type="financial", **vals
        )
        return employee

    def test_full_month_earns_a_meal_every_day(self):
        _slip, days, total = self._june_meal(self._meal_employee())
        self.assertEqual(days, 22.0)
        self.assertEqual(total, 112.64)

    def test_afternoon_closed_in_the_calendar_earns_no_meal(self):
        # The employer closes on the afternoon of 29 June: four hours worked
        # that day, which is not more than four. 21 x 5.12.
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Afternoon closed",
                "calendar_id": self.calendar.id,
                "company_id": self.company.id,
                "date_from": datetime(2026, 6, 29, 12, 0, 0),
                "date_to": datetime(2026, 6, 29, 21, 0, 0),
            }
        )
        slip, days, total = self._june_meal(self._meal_employee())
        self.assertEqual(self._worked(slip, "GLOBAL"), (-0.5, -4.0))
        self.assertEqual(days, 21.0)
        self.assertEqual(total, 107.52)

    def test_half_day_of_leave_earns_no_meal(self):
        employee = self._meal_employee()
        self._leave(
            employee,
            "l10n_sk_leave_type_dovolenka",
            date(2026, 6, 8),
            date(2026, 6, 8),
            half="am",
        )
        slip, days, total = self._june_meal(employee)
        self.assertEqual(self._worked(slip, "DOVOLENKA"), (-0.5, -4.0))
        self.assertEqual(days, 21.0)
        self.assertEqual(total, 107.52)

    def test_two_half_days_do_not_add_up_to_a_meal_day(self):
        employee = self._meal_employee()
        for day, half in ((8, "am"), (9, "pm")):
            self._leave(
                employee,
                "l10n_sk_leave_type_dovolenka",
                date(2026, 6, day),
                date(2026, 6, day),
                half=half,
            )
        slip, days, total = self._june_meal(employee)
        self.assertEqual(self._worked(slip, "DOVOLENKA"), (-1.0, -8.0))
        # 2 000 x 168 / 176 = 1 909.0909.
        self.assertEqual(slip.get_salary_line_total("BASIC"), 1909.10)
        # 21 days worked in all, on 20 of them more than four hours.
        self.assertEqual(days, 20.0)
        self.assertEqual(total, 102.40)

    def test_two_hours_at_the_doctor_keep_the_meal(self):
        employee = self._meal_employee()
        self._leave(
            employee,
            "l10n_sk_leave_type_obstacle",
            date(2026, 6, 8),
            date(2026, 6, 8),
            hours=(8.0, 10.0),
        )
        slip, days, total = self._june_meal(employee)
        self.assertEqual(self._worked(slip, "OBSTACLE"), (-0.25, -2.0))
        # Six hours worked on 8 June.
        self.assertEqual(days, 22.0)
        self.assertEqual(total, 112.64)

    def test_schedule_of_four_hours_a_day_earns_no_meal(self):
        self.calendar = self.env["resource.calendar"].create(
            {
                "name": "SK 20h/week",
                "company_id": self.company.id,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "d%s" % day,
                            "dayofweek": str(day),
                            "hour_from": 8.0,
                            "hour_to": 12.0,
                            "day_period": "morning",
                        },
                    )
                    for day in range(5)
                ],
            }
        )
        slip, days, total = self._june_meal(self._meal_employee())
        self.assertEqual(self._worked(slip)[1], 88.0)
        self.assertEqual(days, 0.0)
        self.assertEqual(total, 0.0)

    # § 152 ods. 9: an employer may provide the meal on a shorter shift too.
    def _four_hour_calendar(self):
        return self.env["resource.calendar"].create(
            {
                "name": "SK 20h/week",
                "company_id": self.company.id,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "d%s" % day,
                            "dayofweek": str(day),
                            "hour_from": 8.0,
                            "hour_to": 12.0,
                            "day_period": "morning",
                        },
                    )
                    for day in range(5)
                ],
            }
        )

    def test_short_shift_option_gives_a_four_hour_schedule_its_meals(self):
        self.calendar = self._four_hour_calendar()
        employee = self._meal_employee(l10n_sk_meal_short_shift=True)
        _slip, days, total = self._june_meal(employee)
        self.assertEqual(days, 22.0)
        self.assertEqual(total, 112.64)

    def test_short_shift_option_keeps_the_meal_of_a_half_day_of_leave(self):
        employee = self._meal_employee(l10n_sk_meal_short_shift=True)
        self._leave(
            employee,
            "l10n_sk_leave_type_dovolenka",
            date(2026, 6, 8),
            date(2026, 6, 8),
            half="am",
        )
        _slip, days, total = self._june_meal(employee)
        self.assertEqual(days, 22.0)
        self.assertEqual(total, 112.64)

    def test_short_shift_option_gives_no_meal_for_a_day_without_work(self):
        # 8 June on leave, the afternoon of 29 June closed: 21 days with work.
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Afternoon closed",
                "calendar_id": self.calendar.id,
                "company_id": self.company.id,
                "date_from": datetime(2026, 6, 29, 12, 0, 0),
                "date_to": datetime(2026, 6, 29, 21, 0, 0),
            }
        )
        employee = self._meal_employee(l10n_sk_meal_short_shift=True)
        self._leave(
            employee, "l10n_sk_leave_type_dovolenka", date(2026, 6, 8), date(2026, 6, 8)
        )
        _slip, days, total = self._june_meal(employee)
        self.assertEqual(days, 21.0)
        self.assertEqual(total, 107.52)

    def test_short_shift_option_leaves_the_number_on_the_contract(self):
        employee = self._meal_employee(
            l10n_sk_meal_short_shift=True, l10n_sk_meal_days=20
        )
        _slip, days, total = self._june_meal(employee)
        self.assertEqual(days, 20.0)
        self.assertEqual(total, 102.40)

    def test_worked_day_lines_typed_by_hand_count_their_whole_days(self):
        # No absence is booked; the officer types two and a half days of
        # leave into the worked-day lines. The lines do not say which days:
        # 19.5 days worked hold 19 whole days.
        employee = self._meal_employee()
        slip = self._slip(employee.version_id, employee, 2026, 6, 30)
        slip.worked_days_line_ids = [
            (
                0,
                0,
                {
                    "name": "Leave",
                    "code": "DOVOLENKA",
                    "number_of_days": -2.5,
                    "number_of_hours": -20.0,
                    "contract_id": employee.version_id.id,
                },
            )
        ]
        slip.compute_sheet()
        meal = slip.line_ids.filtered(lambda row: row.code == "MEALEMPLOYER")
        self.assertEqual(meal.quantity, 19.0)
        self.assertEqual(meal.total, 97.28)

    # ------------------------------------------------------------------
    # annual settlement and dated data
    # ------------------------------------------------------------------
    def test_annual_tax_rounds_an_exact_half_cent_up(self):
        # 2025: 15 753.29 - 5 753.79 = 9 999.50; 19 % is 1 899.905.
        contract, employee = self._contract(2000.0)
        settlement = self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": employee.id,
                "company_id": self.company.id,
                "year": 2025,
                "gather_from_payslips": False,
                "annual_tax_base": 15753.29,
                "annual_advance_tax": 1899.91,
            }
        )
        self.assertEqual(settlement.taxable_base, 9999.5)
        self.assertEqual(settlement.annual_tax, 1899.91)
        self.assertEqual(settlement.result_amount, 0.0)

    def test_meal_allowance_values_of_2024(self):
        value = self.env["hr.rule.parameter"]._get_parameter_value
        code = "l10n_sk_stravne_5_12h"
        self.assertEqual(value(code, date(2024, 1, 1)), 7.8)
        self.assertEqual(value(code, date(2024, 8, 31)), 7.8)
        self.assertEqual(value(code, date(2024, 9, 1)), 8.3)
        self.assertEqual(value(code, date(2024, 12, 31)), 8.3)
        self.assertEqual(value(code, date(2025, 3, 31)), 8.3)
        self.assertEqual(value(code, date(2025, 4, 1)), 8.8)

    # ------------------------------------------------------------------
    # employer sick pay
    # ------------------------------------------------------------------
    @expected_failure(
        "the rule needs a PN worked-day line, and a sick day off work makes none"
    )
    def test_sick_days_on_days_off_are_paid(self):
        # Sick from Friday 30 January to Sunday 1 February 2026: February
        # holds the third calendar day, 25 % of 40.
        contract, employee = self._contract(1500.0)
        self._leave(
            employee, "l10n_sk_leave_type_pn", date(2026, 1, 30), date(2026, 2, 1)
        )
        slip = self._slip(
            contract, employee, 2026, 2, 28, inputs=[("PN_DVZ", "Daily base", 40.0)]
        )
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 10.0)

    @expected_failure("adjoining sick leaves are counted as one incapacity")
    def test_adjoining_sick_leaves_are_two_incapacities(self):
        contract, employee = self._contract(1500.0)
        self._leave(
            employee, "l10n_sk_leave_type_pn", date(2026, 11, 2), date(2026, 11, 6)
        )
        self._leave(
            employee, "l10n_sk_leave_type_pn", date(2026, 11, 7), date(2026, 11, 11)
        )
        slip = self._slip(
            contract, employee, 2026, 11, 30, inputs=[("PN_DVZ", "Daily base", 20.0)]
        )
        # Each: three days at 25 % and two at 55 % of 20 = 37.
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 74.0)
