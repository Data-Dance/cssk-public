# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""End-to-end surcharge rules on the OCA payroll engine.

The percentage-of-minimum-wage surcharges are asserted against hand-computed
figures, since the 2026 minimum hourly wage (€5.259) is fixed data. The
holiday and overtime surcharges are percentages of average earnings, which
depend on the resource calendar's hours in the period, so those expectations
are derived from the same helper the rules use — the point of the assertion is
the percentage and the base, not a re-derivation of § 134.
"""

from datetime import date

from odoo.addons.l10n_sk_hr_payroll_surcharges.models.surcharge_calc import (
    surcharge_amount,
)
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPriplatkyOca(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Priplatky Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )

    @classmethod
    def _make_contract(cls, name, wage, **l10n):
        employee = cls.env["hr.employee"].create(
            {
                "name": name,
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
            }
        )
        version = employee.version_id
        # The structure declares the employment form, and a contract may not
        # disagree with it, so a dohoda fixture sits on the matching one.
        by_form = {
            "dovp": "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dovp",
            "dopc": "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dopc",
            "dobps": "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dobps",
        }
        xmlid = by_form.get(l10n.get("l10n_sk_agreement_type"))
        struct = cls.env.ref(xmlid) if xmlid else cls.structure
        vals = {
            "contract_date_start": date(2024, 1, 1),
            "date_version": date(2024, 1, 1),
            "wage": wage,
            "resource_calendar_id": cls.calendar.id,
            "struct_id": struct.id,
        }
        vals.update(l10n)
        version.write(vals)
        return version, employee

    def _make_payslip(
        self,
        contract,
        employee,
        hours_by_code=None,
        worked=None,
        absence=None,
        absence_code="DOVOLENKA",
    ):
        vals = {
            "name": "Payslip",
            "employee_id": employee.id,
            "contract_id": contract.id,
            "struct_id": (contract.struct_id or self.structure).id,
            "company_id": self.company.id,
            "date_from": date(2026, 6, 1),
            "date_to": date(2026, 6, 30),
        }
        if hours_by_code:
            vals["input_line_ids"] = [
                (
                    0,
                    0,
                    {
                        "name": code,
                        "code": code,
                        "amount": hours,
                        "contract_id": contract.id,
                    },
                )
                for code, hours in hours_by_code.items()
            ]
        if worked:
            lines = [
                (
                    0,
                    0,
                    {
                        "name": "Attendance",
                        "code": "WORK100",
                        "number_of_days": worked[0],
                        "number_of_hours": worked[1],
                        "contract_id": contract.id,
                    },
                )
            ]
            if absence:
                # The OCA engine records absences as NEGATIVE worked-day lines
                # alongside a WORK100 line that still holds the full month.
                lines.append(
                    (
                        0,
                        0,
                        {
                            "name": "Absence",
                            "code": absence_code,
                            "number_of_days": -absence[0],
                            "number_of_hours": -absence[1],
                            "contract_id": contract.id,
                        },
                    )
                )
            vals["worked_days_line_ids"] = lines
        payslip = self.env["hr.payslip"].with_company(self.company).create(vals)
        payslip.compute_sheet()
        return payslip

    # ------------------------------------------------------------------
    # percentage of the minimum hourly wage
    # ------------------------------------------------------------------
    def test_night_saturday_sunday_standard_rates(self):
        contract, employee = self._make_contract("Nocny Robotnik", 2000.0)
        p = self._make_payslip(
            contract, employee, {"NOC": 10.0, "SOBOTA": 8.0, "NEDELA": 4.0}
        )
        line = p.get_salary_line_total
        # 10 h x 40 % x 5.259 = 21.036 -> 21.04
        self.assertAlmostEqual(line("PRIPLATOK_NOC"), 21.04, places=2)
        # 8 h x 50 % x 5.259 = 21.036 -> 21.04
        self.assertAlmostEqual(line("PRIPLATOK_SOBOTA"), 21.04, places=2)
        # 4 h x 100 % x 5.259 = 21.036 -> 21.04
        self.assertAlmostEqual(line("PRIPLATOK_NEDELA"), 21.04, places=2)

    def test_2027_surcharges_use_the_new_dated_base(self):
        contract, employee = self._make_contract('Dated 2027 wage surcharge', 2000.0)
        slip = self._make_payslip(contract, employee, {'NOC': 10.0, 'SOBOTA': 8.0, 'NEDELA': 4.0})
        self.assertAlmostEqual(slip.get_salary_line_total('PRIPLATOK_NOC'), 21.04, places=2)
        slip.write({'date_from': date(2027, 1, 1), 'date_to': date(2027, 1, 31)})
        slip.compute_sheet()
        # Each statutory floor is 22.344 EUR, paid as 22.35 EUR.
        for code in ('PRIPLATOK_NOC', 'PRIPLATOK_SOBOTA', 'PRIPLATOK_NEDELA'):
            self.assertAlmostEqual(slip.get_salary_line_total(code), 22.35, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total('GROSS'), 2067.05, places=2)

    def test_2027_level_two_topup_uses_the_published_monthly_claim(self):
        contract, employee = self._make_contract('Dated 2027 minimum claim', 500.0, l10n_sk_wage_level='2')
        slip = self._make_payslip(contract, employee)
        slip.write({'date_from': date(2027, 1, 1), 'date_to': date(2027, 1, 31)})
        slip.compute_sheet()
        self.assertAlmostEqual(slip.get_salary_line_total('MIN_WAGE_TOPUP'), 588.0, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total('GROSS'), 1088.0, places=2)

    def test_surcharges_roll_into_gross(self):
        """A mzdové zvýhodnenie is insurable and taxable income."""
        contract, employee = self._make_contract("Vikendovy Robotnik", 2000.0)
        p = self._make_payslip(contract, employee, {"NEDELA": 4.0})
        self.assertAlmostEqual(
            p.get_salary_line_total("GROSS"), 2000.0 + 21.04, places=2
        )

    def test_risky_work_raises_the_night_rate(self):
        contract, employee = self._make_contract(
            "Rizikovy Robotnik", 2000.0, l10n_sk_risk_work=True
        )
        p = self._make_payslip(contract, employee, {"NOC": 10.0})
        # 10 h x 50 % x 5.259 = 26.295 -> 26.30
        self.assertAlmostEqual(p.get_salary_line_total("PRIPLATOK_NOC"), 26.30, places=2)

    def test_collective_agreement_lowers_the_night_rate(self):
        contract, employee = self._make_contract(
            "Nocna Prevadzka", 2000.0, l10n_sk_night_reduced=True
        )
        p = self._make_payslip(contract, employee, {"NOC": 10.0})
        # 10 h x 35 % x 5.259 = 18.4065 -> 18.41
        self.assertAlmostEqual(p.get_salary_line_total("PRIPLATOK_NOC"), 18.41, places=2)

    def test_risky_work_beats_the_reduced_night_rate(self):
        """§ 122a ods. 3 bars the reduced rate for risky work."""
        contract, employee = self._make_contract(
            "Rizikova Nocna",
            2000.0,
            l10n_sk_risk_work=True,
            l10n_sk_night_reduced=True,
        )
        p = self._make_payslip(contract, employee, {"NOC": 10.0})
        self.assertAlmostEqual(p.get_salary_line_total("PRIPLATOK_NOC"), 26.30, places=2)

    def test_reduced_weekend_rates(self):
        contract, employee = self._make_contract(
            "Vikendova Prevadzka",
            2000.0,
            l10n_sk_saturday_reduced=True,
            l10n_sk_sunday_reduced=True,
        )
        p = self._make_payslip(contract, employee, {"SOBOTA": 8.0, "NEDELA": 4.0})
        line = p.get_salary_line_total
        # 8 h x 45 % x 5.259 = 18.9324 -> 18.94
        self.assertAlmostEqual(line("PRIPLATOK_SOBOTA"), 18.94, places=2)
        # 4 h x 90 % x 5.259 = 18.9324 -> 18.94
        self.assertAlmostEqual(line("PRIPLATOK_NEDELA"), 18.94, places=2)

    def test_difficult_conditions_and_standby(self):
        contract, employee = self._make_contract("Stazeny Vykon", 2000.0)
        p = self._make_payslip(
            contract, employee, {"STAZENY": 5.0, "POHOTOVOST": 6.0}
        )
        line = p.get_salary_line_total
        # 5 h x 20 % x 5.259 = 5.259 -> 5.26
        self.assertAlmostEqual(line("PRIPLATOK_STAZENY"), 5.26, places=2)
        # 6 h x 20 % x 5.259 = 6.3108 -> 6.32
        self.assertAlmostEqual(line("PRIPLATOK_POHOTOVOST"), 6.32, places=2)

    def test_no_hours_means_no_line(self):
        contract, employee = self._make_contract("Denny Robotnik", 2000.0)
        p = self._make_payslip(contract, employee)
        for code in (
            "PRIPLATOK_NOC",
            "PRIPLATOK_SOBOTA",
            "PRIPLATOK_NEDELA",
            "PRIPLATOK_SVIATOK",
            "PRIPLATOK_NADCAS",
            "NADCAS_MZDA",
            "PRIPLATOK_STAZENY",
            "PRIPLATOK_POHOTOVOST",
        ):
            self.assertAlmostEqual(p.get_salary_line_total(code), 0.0, places=2)

    # ------------------------------------------------------------------
    # percentage of average earnings
    # ------------------------------------------------------------------
    def test_overtime_pays_the_hour_and_the_uplift(self):
        contract, employee = self._make_contract("Nadcasnik", 2000.0)
        p = self._make_payslip(contract, employee, {"NADCAS": 10.0})
        line = p.get_salary_line_total
        # § 121 ods. 1: the wage achieved for the hours, the salary over the
        # 176 hours of June 2026: 2 000 x 10 / 176 = 113.6364.
        self.assertEqual(line("NADCAS_MZDA"), 113.64)
        # And at least 25 % of average earnings on top. No payslips in the
        # quarter before: the probable average 11.3636, 28.409.
        self.assertEqual(line("PRIPLATOK_NADCAS"), 28.41)

    def _confirmed_first_quarter(self, contract, employee):
        """January to March 2026 without overtime: 176 + 160 + 176 hours."""
        for month, last_day in ((1, 31), (2, 28), (3, 31)):
            self._make_dated_payslip(
                contract,
                employee,
                date(2026, month, 1),
                date(2026, month, last_day),
                overtime=0.0,
            ).action_payslip_done()

    def test_overtime_after_a_raise_is_paid_at_the_new_salary(self):
        """The hours at the wage achieved, the premium on average earnings.

        1 600 a month in the first quarter of 2026, an average of
        4 800 / 512 = 9.375. From April 2 100, and eight overtime hours in
        April (176 hours): 2 100 x 8 / 176 = 95.4545 for the hours, and
        8 x 9.375 x 25 % = 18.75 on top.
        """
        contract, employee = self._make_contract("Nadcas Po Zvyseni", 1600.0)
        self._confirmed_first_quarter(contract, employee)
        contract.wage = 2100.0
        april = self._make_dated_payslip(
            contract, employee, date(2026, 4, 1), date(2026, 4, 30), overtime=8.0
        )
        self.assertEqual(april.l10n_sk_average_hourly_earnings(), 9.375)
        line = april.get_salary_line_total
        self.assertEqual(line("NADCAS_MZDA"), 95.46)
        self.assertEqual(line("PRIPLATOK_NADCAS"), 18.75)
        self.assertEqual(line("GROSS"), 2214.21)

    def test_overtime_of_an_hourly_wage_is_paid_at_the_exact_rate(self):
        """6.125 an hour in the first quarter of 2026, 7.333 from April.

        Eight overtime hours in April: 8 x 7.333 = 58.664 for the hours, and
        8 x 6.125 x 25 % = 12.25 on the average of the quarter. The 176
        hours of April are 1 290.608.
        """
        contract, employee = self._make_contract(
            "Nadcas Hodinovy", 0.0, l10n_sk_hourly_wage=6.125
        )
        self._confirmed_first_quarter(contract, employee)
        contract.l10n_sk_hourly_wage = 7.333
        april = self._make_dated_payslip(
            contract, employee, date(2026, 4, 1), date(2026, 4, 30), overtime=8.0
        )
        self.assertEqual(april.l10n_sk_average_hourly_earnings(), 6.125)
        line = april.get_salary_line_total
        self.assertEqual(line("BASIC"), 1290.61)
        self.assertEqual(line("NADCAS_MZDA"), 58.67)
        self.assertEqual(line("PRIPLATOK_NADCAS"), 12.25)
        self.assertEqual(line("GROSS"), 1361.53)

    def test_overtime_in_a_month_with_an_unpaid_day_keeps_the_months_divisor(self):
        """The salary is divided by the month's hours, not by the hours worked.

        June 2026, 176 hours, 2 000 and one unpaid day: the salary is
        2 000 x 168 / 176 = 1 909.0909, and eight overtime hours are
        2 000 x 8 / 176 = 90.9091 (over 168 hours they would be 95.24).
        """
        contract, employee = self._make_contract("Nadcas Neplatene", 2000.0)
        p = self._make_payslip(
            contract,
            employee,
            {"NADCAS": 8.0},
            worked=(22.0, 176.0),
            absence=(1.0, 8.0),
            absence_code="NEPLATENE",
        )
        line = p.get_salary_line_total
        self.assertEqual(line("BASIC"), 1909.1)
        self.assertEqual(line("NADCAS_MZDA"), 90.91)
        # 8 x 11.3636 x 25 % = 22.7272
        self.assertEqual(line("PRIPLATOK_NADCAS"), 22.73)
        self.assertEqual(line("GROSS"), 2022.74)

    def test_overtime_on_a_payslip_of_a_part_of_the_month(self):
        """The divisor is the whole month, whatever days the payslip covers.

        A payslip of 10 to 30 June 2026 on 2 000: eight overtime hours are
        2 000 x 8 / 176 = 90.9091, not the salary over the 120 hours of
        those days.
        """
        contract, employee = self._make_contract("Nadcas Cast Mesiaca", 2000.0)
        p = self._make_dated_payslip(
            contract, employee, date(2026, 6, 10), date(2026, 6, 30), overtime=8.0
        )
        self.assertEqual(p._l10n_sk_overtime_fund_hours(), 176.0)
        self.assertEqual(p.get_salary_line_total("NADCAS_MZDA"), 90.91)

    def test_public_holiday_is_the_uplift_only(self):
        contract, employee = self._make_contract("Sviatocny Robotnik", 2000.0)
        p = self._make_payslip(contract, employee, {"SVIATOK": 8.0})
        phz = p.l10n_sk_average_hourly_earnings()
        self.assertAlmostEqual(
            p.get_salary_line_total("PRIPLATOK_SVIATOK"),
            surcharge_amount(8, phz, 100.0),
            places=2,
        )

    # ------------------------------------------------------------------
    # minimum wage claim
    # ------------------------------------------------------------------
    def test_no_topup_for_a_wage_above_the_claim(self):
        contract, employee = self._make_contract("Dobre Plateny", 2000.0)
        p = self._make_payslip(contract, employee, worked=(22.0, 176.0))
        self.assertAlmostEqual(p.get_salary_line_total("MIN_WAGE_TOPUP"), 0.0, places=2)

    def test_topup_to_the_level_1_minimum(self):
        contract, employee = self._make_contract("Podpriemerny", 800.0)
        p = self._make_payslip(contract, employee, worked=(22.0, 176.0))
        # A full month worked, so the whole €915 level-1 claim is due.
        self.assertAlmostEqual(p._l10n_sk_full_time_hours(), 176.0, places=2)
        self.assertAlmostEqual(
            p.get_salary_line_total("MIN_WAGE_TOPUP"), 115.0, places=2
        )

    def test_the_monthly_minimum_wage_is_not_topped_up(self):
        """June 2026 schedules 176 h, but the claim is monthly, not hourly.

        €915/176 = €5.199 is under the €5.259 hourly figure, yet €915 is
        exactly the monthly minimum wage and nothing is owed.
        """
        contract, employee = self._make_contract("Minimalna Mzda", 915.0)
        p = self._make_payslip(contract, employee, worked=(22.0, 176.0))
        self.assertAlmostEqual(p.get_salary_line_total("MIN_WAGE_TOPUP"), 0.0, places=2)

    def test_higher_difficulty_level_raises_the_claim(self):
        """A level-3 job on the plain minimum wage is still underpaid."""
        contract, employee = self._make_contract(
            "Odborny Pracovnik", 915.0, l10n_sk_wage_level="3"
        )
        p = self._make_payslip(contract, employee, worked=(22.0, 176.0))
        # The 2026 level-3 monthly claim is €1147 against €915 paid.
        self.assertAlmostEqual(
            p.get_salary_line_total("MIN_WAGE_TOPUP"), 232.0, places=2
        )

    def test_surcharges_do_not_count_towards_the_minimum_wage(self):
        """§ 120 ods. 3 — a night surcharge cannot mask a sub-minimum wage."""
        contract, employee = self._make_contract("Podpriemerny Nocny", 800.0)
        without = self._make_payslip(contract, employee, worked=(22.0, 176.0))
        with_night = self._make_payslip(
            contract, employee, {"NOC": 40.0}, worked=(22.0, 176.0)
        )
        self.assertAlmostEqual(
            with_night.get_salary_line_total("MIN_WAGE_TOPUP"),
            without.get_salary_line_total("MIN_WAGE_TOPUP"),
            places=2,
        )
        # ...and the surcharge is still paid on top.
        self.assertGreater(with_night.get_salary_line_total("PRIPLATOK_NOC"), 0.0)

    def test_a_full_month_of_absence_owes_no_topup(self):
        """The regression that motivated netting absences off WORK100.

        The OCA engine's WORK100 line holds the FULL scheduled month even when
        the employee was absent throughout — it documents that it "don't
        substract leaves by default". BASIC meanwhile prorates to zero. Pairing
        that zero wage with a full month of hours used to claim the entire
        monthly minimum wage as a top-up for someone who did not work.
        """
        contract, employee = self._make_contract("Cely Mesiac Dovolenka", 800.0)
        p = self._make_payslip(
            contract, employee, worked=(22.0, 176.0), absence=(22.0, 176.0)
        )
        self.assertAlmostEqual(p._l10n_sk_ordinary_hours(), 0.0, places=2)
        self.assertAlmostEqual(p.get_salary_line_total("MIN_WAGE_TOPUP"), 0.0, places=2)

    def test_half_a_month_of_absence_halves_the_claim(self):
        contract, employee = self._make_contract("Polovica Dovolenka", 800.0)
        p = self._make_payslip(
            contract, employee, worked=(22.0, 176.0), absence=(11.0, 88.0)
        )
        self.assertAlmostEqual(p._l10n_sk_ordinary_hours(), 88.0, places=2)
        # Claim 915 x 88/176 = 457.50; BASIC prorated to 400.00 -> 57.50 due.
        self.assertAlmostEqual(p.get_salary_line_total("BASIC"), 400.0, places=2)
        self.assertAlmostEqual(p.get_salary_line_total("MIN_WAGE_TOPUP"), 57.50, places=2)

    def test_every_absence_that_cuts_the_wage_cuts_the_claim(self):
        """§ 120 ods. 6: the monthly claim follows the time worked.

        A month of parental leave, or of any other absence BASIC is cut for,
        leaves no wage and no hours, so no top-up.
        """
        codes = self.env["hr.payslip"].l10n_sk_absence_codes()
        self.assertEqual(len(codes), 12)
        for code in codes:
            with self.subTest(code=code):
                contract, employee = self._make_contract("Absent %s" % code, 800.0)
                p = self._make_payslip(
                    contract,
                    employee,
                    worked=(22.0, 176.0),
                    absence=(22.0, 176.0),
                    absence_code=code,
                )
                self.assertEqual(p._l10n_sk_ordinary_hours(), 0.0)
                self.assertEqual(p.get_salary_line_total("BASIC"), 0.0)
                self.assertEqual(p.get_salary_line_total("MIN_WAGE_TOPUP"), 0.0)

    def test_half_a_month_of_parental_leave_halves_the_claim(self):
        contract, employee = self._make_contract("Polovica Rodicovska", 800.0)
        p = self._make_payslip(
            contract,
            employee,
            worked=(22.0, 176.0),
            absence=(11.0, 88.0),
            absence_code="RODICOVSKA",
        )
        self.assertEqual(p._l10n_sk_ordinary_hours(), 88.0)
        # Claim 915 x 88/176 = 457.50; BASIC 400.00.
        self.assertEqual(p.get_salary_line_total("BASIC"), 400.0)
        self.assertEqual(p.get_salary_line_total("MIN_WAGE_TOPUP"), 57.5)

    # ------------------------------------------------------------------
    # average earnings
    # ------------------------------------------------------------------
    def test_overtime_hours_are_time_worked_for_the_average(self):
        """§ 134 ods. 1: the wage of the quarter over the time worked in it.

        Second quarter of 2026, 520 scheduled hours, 2 000 a month and ten
        overtime hours each month. The overtime pay is in the wage, so the
        thirty hours belong to the divisor: 550, not 520.
        """
        contract, employee = self._make_contract("Nadcas Priemer", 2000.0)
        gross = 0.0
        for month, last_day in ((4, 30), (5, 31), (6, 30)):
            slip = self._make_dated_payslip(
                contract, employee, date(2026, month, 1), date(2026, month, last_day)
            )
            self.assertGreater(slip.get_salary_line_total("NADCAS_MZDA"), 0.0)
            gross += slip.get_salary_line_total("GROSS")
            slip.action_payslip_done()
        # 113.64 + 28.41, 119.05 + 29.77, 113.64 + 28.41 on top of 6 000.
        self.assertAlmostEqual(gross, 6432.92, places=2)
        july = self._make_dated_payslip(
            contract, employee, date(2026, 7, 1), date(2026, 7, 31), overtime=0.0
        )
        self.assertEqual(july.l10n_sk_average_hourly_earnings(), 11.6962)

    def _make_dated_payslip(self, contract, employee, date_from, date_to, overtime=10.0):
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip %s" % date_from,
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
                                "name": "NADCAS",
                                "code": "NADCAS",
                                "amount": overtime,
                                "contract_id": contract.id,
                            },
                        )
                    ]
                    if overtime
                    else [],
                }
            )
        )
        slip.onchange_dates()
        slip.compute_sheet()
        return slip

    def test_a_dohodar_gets_no_minimum_wage_topup(self):
        """§ 120 sets claims for a pracovný pomer, not for agreements.

        A dohodár is entitled to the minimum HOURLY wage under zák. 663/2007
        and has no stupeň náročnosti. Topping their monthly remuneration up to
        a full-time monthly claim invents an entitlement they do not have —
        which is what this module did until the applicability was made
        explicit.
        """
        contract, employee = self._make_contract(
            "Dohodar Peter", 400.0, l10n_sk_agreement_type="dovp"
        )
        p = self._make_payslip(contract, employee, worked=(22.0, 176.0))
        self.assertAlmostEqual(p.get_salary_line_total("MIN_WAGE_TOPUP"), 0.0, places=2)

    def test_an_employee_on_the_same_wage_is_still_topped_up(self):
        """The guard must be about the employment form, not the amount."""
        contract, employee = self._make_contract("Zamestnanec", 400.0)
        p = self._make_payslip(contract, employee, worked=(22.0, 176.0))
        self.assertGreater(p.get_salary_line_total("MIN_WAGE_TOPUP"), 0.0)
