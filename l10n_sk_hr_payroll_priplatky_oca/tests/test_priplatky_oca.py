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

from odoo.addons.l10n_sk_hr_payroll_priplatky.models.surcharge_calc import (
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
        self, contract, employee, hours_by_code=None, worked=None, absence=None
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
                            "name": "Holiday",
                            "code": "DOVOLENKA",
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
        phz = p.l10n_sk_average_hourly_earnings()
        line = p.get_salary_line_total
        # § 121: the wage for the hour PLUS at least 25 % of average earnings.
        self.assertAlmostEqual(
            line("NADCAS_MZDA"), surcharge_amount(10, phz, 100.0), places=2
        )
        self.assertAlmostEqual(
            line("PRIPLATOK_NADCAS"), surcharge_amount(10, phz, 25.0), places=2
        )
        # The uplift really is a quarter of the pay for the same hours.
        self.assertAlmostEqual(
            line("PRIPLATOK_NADCAS") / line("NADCAS_MZDA"), 0.25, places=3
        )

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
