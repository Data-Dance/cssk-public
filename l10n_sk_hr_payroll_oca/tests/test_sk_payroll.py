# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# These tests assert the CORRECTED Slovak payroll behaviour (v18.0.2.0.0):
#   * TAXBASE = gross − employee social − employee health
#   * NČZD applied (and gated on the signed declaration)
#   * income tax matches a hand-computed monthly advance
#   * CHILD_BONUS credited for an employee with children
#   * dated parameters exercised by one 2025-dated and one 2026-dated payslip
#     (health rate 4% -> 5%, NČZD 479.48 -> 497.23).

from datetime import date, datetime

from odoo.tests import TransactionCase, tagged
from odoo.tools.convert import convert_file


@tagged("post_install", "-at_install")
class TestSkPayroll(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "SK Test Co",
                "country_id": cls.env.ref("base.sk").id,
            }
        )
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "SK 40h/week",
                "company_id": cls.company.id,
            }
        )
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Jozko Mrkvicka",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
            }
        )
        # Declaration signed, 2 children < 15, standard (non-ZŤP), no meal.
        cls.contract = cls.env["hr.contract"].create(
            {
                "name": "Jozko Contract",
                "employee_id": cls.employee.id,
                "company_id": cls.company.id,
                "wage": 2000.0,
                "state": "open",
                "date_start": date(2024, 1, 1),
                "resource_calendar_id": cls.calendar.id,
                "struct_id": cls.structure.id,
                "l10n_sk_tax_declaration_signed": True,
                "l10n_sk_children_under_15": 2,
            }
        )
        # Employee without a signed declaration (to prove NČZD gating).
        cls.employee_nodecl = cls.env["hr.employee"].create(
            {
                "name": "Anna Bezvyhlasenia",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
            }
        )
        cls.contract_nodecl = cls.env["hr.contract"].create(
            {
                "name": "Anna Contract",
                "employee_id": cls.employee_nodecl.id,
                "company_id": cls.company.id,
                "wage": 2000.0,
                "state": "open",
                "date_start": date(2024, 1, 1),
                "resource_calendar_id": cls.calendar.id,
                "struct_id": cls.structure.id,
                "l10n_sk_tax_declaration_signed": False,
            }
        )

    def _make_payslip(self, contract, employee, date_from, date_to):
        payslip = (
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
                }
            )
        )
        payslip.compute_sheet()
        return payslip

    def test_2026_payslip(self):
        """2026: health ee 5%, NČZD 497.23, bonus for 2 children."""
        p = self._make_payslip(
            self.contract, self.employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total

        # gross = full monthly wage (meal excluded)
        self.assertAlmostEqual(line("GROSS"), 2000.0, places=2)
        # SOCIALEMPLOYEE category holds BOTH social funds (9.4% = 188) and the
        # employee health premium (5% = 100), so the total is -288.00.
        self.assertAlmostEqual(line("SOCIALEMPLOYEETOTAL"), -288.0, places=2)
        # health ee 5% (2026) -> -100.00
        self.assertAlmostEqual(line("HEALTH"), -100.0, places=2)
        # TAXBASE = 2000 - 188 - 100 = 1712.00
        self.assertAlmostEqual(line("TAXBASE"), 1712.0, places=2)
        # tax = 19% × (1712 − 497.23 NČZD) = 19% × 1214.77 = -230.81
        self.assertAlmostEqual(line("INCOMETAX"), -230.81, places=2)
        # child bonus: 2 × €100 = 200 (< 36% of 1712 cap; no taper) -> +200.00
        self.assertAlmostEqual(line("CHILD_BONUS"), 200.0, places=2)
        # net = 2000 − 288 − 230.81 + 200 = 1681.19
        self.assertAlmostEqual(line("NET"), 1681.19, places=2)
        # employer health 11% -> +220.00
        self.assertAlmostEqual(line("HEALTHEMPLOYER"), 220.0, places=2)

    def test_2025_payslip(self):
        """2025: health ee 4%, NČZD 479.48 (dated params differ from 2026)."""
        p = self._make_payslip(
            self.contract, self.employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        line = p.get_salary_line_total

        self.assertAlmostEqual(line("GROSS"), 2000.0, places=2)
        # health ee 4% (2025) -> -80.00 (proves the dated health rate)
        self.assertAlmostEqual(line("HEALTH"), -80.0, places=2)
        # TAXBASE = 2000 - 188 - 80 = 1732.00
        self.assertAlmostEqual(line("TAXBASE"), 1732.0, places=2)
        # tax = 19% × (1732 − 479.48 NČZD) = 19% × 1252.52 = -237.98
        self.assertAlmostEqual(line("INCOMETAX"), -237.98, places=2)
        self.assertAlmostEqual(line("CHILD_BONUS"), 200.0, places=2)
        # net = 2000 − 268 − 237.98 + 200 = 1694.02
        self.assertAlmostEqual(line("NET"), 1694.02, places=2)

    def test_nczd_gating_and_bonus_gating(self):
        """No signed declaration -> no NČZD, no child bonus -> higher tax."""
        p = self._make_payslip(
            self.contract_nodecl,
            self.employee_nodecl,
            date(2026, 6, 1),
            date(2026, 6, 30),
        )
        line = p.get_salary_line_total

        self.assertAlmostEqual(line("TAXBASE"), 1712.0, places=2)
        # No NČZD: tax = 19% × 1712 = -325.28
        self.assertAlmostEqual(line("INCOMETAX"), -325.28, places=2)
        # No declaration => no child bonus even if children were set
        self.assertAlmostEqual(line("CHILD_BONUS"), 0.0, places=2)
        # net = 2000 − 288 − 325.28 = 1386.72
        self.assertAlmostEqual(line("NET"), 1386.72, places=2)

    def test_ztp_halved_health(self):
        """ZŤP employee: health ee halved to 2.5% (2026)."""
        self.contract.l10n_sk_ztp = True
        p = self._make_payslip(
            self.contract, self.employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.contract.l10n_sk_ztp = False
        # 2.5% of 2000 -> -50.00
        self.assertAlmostEqual(p.get_salary_line_total("HEALTH"), -50.0, places=2)

    # ---- Feature: Health OOP (odvodová odpočítateľná položka) --------------
    def _make_low_earner(self, **vals):
        """A €500 earner, on a HALF-TIME calendar.

        €500 a month is below the Slovak minimum wage for a full-time job, so
        a full-time fixture would be an unlawful contract — and
        ``l10n_sk_hr_payroll_surcharges``, where installed, correctly tops it
        up and shifts every figure below. Half time makes the same €500 gross
        a lawful wage without touching any of the OOP arithmetic, which is
        computed on the monthly gross and not on hours.
        """
        calendar = self.env["resource.calendar"].create(
            {
                "name": "SK 20h/week",
                "company_id": self.company.id,
                "hours_per_day": 4.0,
                "attendance_ids": [
                    (0, 0, {
                        "name": day_name,
                        "dayofweek": str(day),
                        "hour_from": 8.0,
                        "hour_to": 12.0,
                        "day_period": "morning",
                    })
                    for day, day_name in enumerate(
                        ["Mon", "Tue", "Wed", "Thu", "Fri"]
                    )
                ],
            }
        )
        employee = self.env["hr.employee"].create(
            {
                "name": "Maly Zarobok",
                "company_id": self.company.id,
                "resource_calendar_id": calendar.id,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Maly Contract",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "wage": 500.0,
                "state": "open",
                "date_start": date(2024, 1, 1),
                "resource_calendar_id": calendar.id,
                "struct_id": self.structure.id,
                **vals,
            }
        )
        return contract, employee

    def test_health_oop_low_earner(self):
        """Health OOP for a €500 earner (2025): base reduced, employer intact."""
        contract, employee = self._make_low_earner(l10n_sk_health_oop_claim=True)
        p = self._make_payslip(
            contract, employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        line = p.get_salary_line_total
        # OOP = 380 - 2*(500-380) = 140 -> health base = 500 - 140 = 360.
        # employee health 4% (2025) of 360 -> -14.40 (vs -20.00 without OOP)
        self.assertAlmostEqual(line("HEALTH"), -14.40, places=2)
        # employer health is charged on the FULL 500 -> +55.00 (not reduced)
        self.assertAlmostEqual(line("HEALTHEMPLOYER"), 55.0, places=2)
        # tax base subtracts the ACTUAL (reduced) health: 500 - 47 social - 14.40
        self.assertAlmostEqual(line("TAXBASE"), 438.60, places=2)

    def test_health_oop_off_matches_full_base(self):
        """Without the claim the €500 earner pays health on the full base."""
        contract, employee = self._make_low_earner(l10n_sk_health_oop_claim=False)
        p = self._make_payslip(
            contract, employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        # 4% of the full 500 -> -20.00
        self.assertAlmostEqual(p.get_salary_line_total("HEALTH"), -20.0, places=2)

    # ---- Feature: Agreements (dohody) DoVP / DoPČ -------------------------
    def _make_dohodar(self, **vals):
        employee = self.env["hr.employee"].create(
            {
                "name": "Dohodar Peter",
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Dohoda Contract",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "wage": 1000.0,
                "state": "open",
                "date_start": date(2024, 1, 1),
                "resource_calendar_id": self.calendar.id,
                "struct_id": self.structure.id,
                **vals,
            }
        )
        return contract, employee

    def test_dovp_reduced_contributions(self):
        """DoVP (irregular income): no sickness/unemployment; only 7% social."""
        contract, employee = self._make_dohodar(l10n_sk_agreement_type="dovp")
        p = self._make_payslip(
            contract, employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        line = p.get_salary_line_total
        # Skipped funds -> no line -> 0.0
        self.assertAlmostEqual(line("SICK"), 0.0, places=2)
        self.assertAlmostEqual(line("UNEMPLOYMENT"), 0.0, places=2)
        self.assertAlmostEqual(line("SHORTTIMEEMPLOYER"), 0.0, places=2)
        # Employee pays only pension 4% + disability 3% = 7% of 1000
        self.assertAlmostEqual(line("PENSION"), -40.0, places=2)
        self.assertAlmostEqual(line("DISABILITY"), -30.0, places=2)
        # Health still applies (regular dohodár), 4% (2025) -> -40.00
        self.assertAlmostEqual(line("HEALTH"), -40.0, places=2)
        # Employer pension 14%, reserve 4.75%, guarantee 0.25%, accident 0.8%
        self.assertAlmostEqual(line("PENSIONEMPLOYER"), 140.0, places=2)
        self.assertAlmostEqual(line("RESERVEFUNDEMPLOYER"), 47.5, places=2)

    def test_dovp_pension_oop(self):
        """DoVP with pension OOP: pension/disability base reduced by €200."""
        contract, employee = self._make_dohodar(
            l10n_sk_agreement_type="dovp", l10n_sk_agreement_oop=True
        )
        p = self._make_payslip(
            contract, employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        line = p.get_salary_line_total
        # base = 1000 - 200 = 800 -> pension 4% -> -32.00, disability 3% -> -24.00
        self.assertAlmostEqual(line("PENSION"), -32.0, places=2)
        self.assertAlmostEqual(line("DISABILITY"), -24.0, places=2)
        # employer reserve fund on the reduced base 800 -> 4.75% -> +38.00
        self.assertAlmostEqual(line("RESERVEFUNDEMPLOYER"), 38.0, places=2)
        # informational OOP line shows the €200 applied
        self.assertAlmostEqual(line("OOP_PENSION"), 200.0, places=2)

    def test_oop_2027_uses_300_and_preserves_2026(self):
        """z.461/2003 §138a: OOP 300 from 2027; a 2026 payslip keeps 200."""
        contract, employee = self._make_dohodar(
            l10n_sk_agreement_type="dovp", l10n_sk_agreement_oop=True
        )
        future = self._make_payslip(
            contract, employee, date(2027, 1, 1), date(2027, 1, 31))
        self.assertEqual(future.rule_parameter("l10n_sk_dohoda_oop"), 300)
        # base = 1000 - 300 = 700 -> pension 4%, disability 3%, reserve 4.75%
        for code, expected in (("PENSION", -28.0), ("DISABILITY", -21.0),
                               ("RESERVEFUNDEMPLOYER", 33.25),
                               ("OOP_PENSION", 300.0)):
            self.assertAlmostEqual(
                future.get_salary_line_total(code), expected, places=2,
                msg=code)

        historical = self._make_payslip(
            contract, employee, date(2026, 12, 1), date(2026, 12, 31))
        self.assertEqual(historical.rule_parameter("l10n_sk_dohoda_oop"), 200)
        for code, expected in (("PENSION", -32.0), ("DISABILITY", -24.0),
                               ("RESERVEFUNDEMPLOYER", 38.0)):
            self.assertAlmostEqual(
                historical.get_salary_line_total(code), expected, places=2,
                msg=code)

    def test_meal_allowance_december_2026(self):
        """Oznámenie č. 255/2026 Z. z.: 9.80 from 1 December 2026, not January.

        Explicit meal days isolate the rate from the calendar.
        """
        for year, month, last, rate, employer, employee_share in (
            (2027, 1, 31, 9.80, 107.80, -39.20),
            (2026, 12, 31, 9.80, 107.80, -39.20),
            (2026, 11, 30, 9.30, 102.40, -37.20),
        ):
            for kind in ("financial", "voucher"):
                with self.subTest(year=year, month=month, kind=kind):
                    employee = self.env["hr.employee"].create(
                        {"name": "Meal %s" % kind, "company_id": self.company.id}
                    )
                    contract = self.env["hr.contract"].create(
                        {
                            "name": "Dated statutory meal allowance",
                            "employee_id": employee.id,
                            "company_id": self.company.id,
                            "wage": 2000.0,
                            "state": "open",
                            "date_start": date(2026, 1, 1),
                            "resource_calendar_id": self.calendar.id,
                            "struct_id": self.structure.id,
                            "l10n_sk_meal_allowance_type": kind,
                            "l10n_sk_meal_days": 20,
                        }
                    )
                    slip = self._make_payslip(
                        contract, employee, date(year, month, 1), date(year, month, last)
                    )
                    self.assertEqual(slip.rule_parameter("l10n_sk_stravne_5_12h"), rate)
                    self.assertAlmostEqual(
                        slip.get_salary_line_total("MEALEMPLOYER"), employer, places=2
                    )
                    self.assertAlmostEqual(
                        slip.get_salary_line_total("MEALEMPLOYEE"),
                        employee_share if kind == "voucher" else 0,
                        places=2,
                    )

    def test_dopc_matches_standard_social(self):
        """DoPČ (regular income): full social set, unchanged from employment."""
        contract, employee = self._make_dohodar(l10n_sk_agreement_type="dopc")
        p = self._make_payslip(
            contract, employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        line = p.get_salary_line_total
        # sickness + unemployment still charged (9.4% social of 1000)
        self.assertAlmostEqual(line("SICK"), -14.0, places=2)
        self.assertAlmostEqual(line("UNEMPLOYMENT"), -10.0, places=2)
        self.assertAlmostEqual(line("SOCIALEMPLOYEETOTAL"), -134.0, places=2)

    # ---- Feature: partial-month proration of the basic wage ----------------
    def _make_mon_fri_calendar(self):
        Att = self.env["resource.calendar.attendance"]
        calendar = self.env["resource.calendar"].create(
            {
                "name": "SK Mon-Fri 40h",
                "company_id": self.company.id,
                "hours_per_day": 8.0,
            }
        )
        atts = []
        for dow in range(5):  # Monday..Friday
            atts.append(
                Att.create(
                    {
                        "name": "Morning",
                        "dayofweek": str(dow),
                        "hour_from": 8.0,
                        "hour_to": 12.0,
                        "day_period": "morning",
                        "calendar_id": calendar.id,
                    }
                ).id
            )
            atts.append(
                Att.create(
                    {
                        "name": "Afternoon",
                        "dayofweek": str(dow),
                        "hour_from": 13.0,
                        "hour_to": 17.0,
                        "day_period": "afternoon",
                        "calendar_id": calendar.id,
                    }
                ).id
            )
        return calendar

    def test_basic_proration_half_month(self):
        """Mid-month hire prorates BASIC by worked / scheduled working days."""
        calendar = self._make_mon_fri_calendar()
        employee = self.env["hr.employee"].create(
            {
                "name": "Novy Zamestnanec",
                "company_id": self.company.id,
                "resource_calendar_id": calendar.id,
            }
        )
        # Hired mid-month (16 June 2026), so ~half the working days are worked.
        contract = self.env["hr.contract"].create(
            {
                "name": "Novy Contract",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "wage": 2000.0,
                "state": "open",
                "date_start": date(2026, 6, 16),
                "resource_calendar_id": calendar.id,
                "struct_id": self.structure.id,
            }
        )
        p = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Proration slip",
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                }
            )
        )
        # Populate worked-day lines (WORK100), clamped by the engine to the
        # 16 June contract start.
        wd = p.get_worked_day_lines(contract, date(2026, 6, 1), date(2026, 6, 30))
        p.worked_days_line_ids = [(0, 0, line) for line in wd]
        p.compute_sheet()

        worked = sum(
            line.number_of_days
            for line in p.worked_days_line_ids
            if line.code == "WORK100"
        )
        scheduled = p.l10n_sk_scheduled_days()
        self.assertGreater(worked, 0.0)
        self.assertGreater(scheduled, worked)  # partial month
        # BASIC prorated exactly; ~half the month (11 of 22 working days).
        self.assertAlmostEqual(
            p.get_salary_line_total("BASIC"), 2000.0 * worked / scheduled, places=2
        )
        self.assertAlmostEqual(p.get_salary_line_total("BASIC"), 1000.0, places=2)

    # ---- Feature: wage garnishment (exekučné zrážky) ----------------------
    def _make_plain_worker(self, wage, **vals):
        employee = self.env["hr.employee"].create(
            {
                "name": "Dlznik Pavol",
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Dlznik Contract",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "wage": wage,
                "state": "open",
                "date_start": date(2024, 1, 1),
                "resource_calendar_id": self.calendar.id,
                "struct_id": self.structure.id,
                **vals,
            }
        )
        return contract, employee

    def _payslip_with_inputs(self, contract, employee, date_from, date_to, inputs):
        p = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Slip %s" % date_from,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date_from,
                    "date_to": date_to,
                }
            )
        )
        for code, amount in inputs:
            self.env["hr.payslip.input"].create(
                {
                    "payslip_id": p.id,
                    "contract_id": contract.id,
                    "name": code,
                    "code": code,
                    "amount": amount,
                    "sequence": 10,
                }
            )
        p.compute_sheet()
        return p

    def test_garnishment_ordinary(self):
        """Neprednostná exekúcia: 1/3 of the rounded net-wage remainder.

        Net wage (€1000 gross, no declaration, 2026) = 1000 − 144 − 162.64
        = 693.36. Non-seizable (140% ŽM, 0 dependants) = 397.78. Remainder
        295.58 → rounded down to divisible by three = 295.56 → 1/3 = 98.52.
        """
        contract, employee = self._make_plain_worker(1000.0)
        p = self._payslip_with_inputs(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            [("GARNISHMENT", 500.0)],
        )
        line = p.get_salary_line_total
        self.assertAlmostEqual(line("GARNISHMENT"), -98.52, places=2)
        # NET = net wage − garnishment = 693.36 − 98.52 = 594.84
        self.assertAlmostEqual(line("NET"), 594.84, places=2)

    def test_garnishment_priority_two_thirds(self):
        """Prednostná exekúcia (výživné/dane): 2/3 of the remainder."""
        contract, employee = self._make_plain_worker(1000.0)
        p = self._payslip_with_inputs(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            [("GARNISHMENT_PRIORITY", 500.0)],
        )
        # 2 × 98.52 = 197.04
        self.assertAlmostEqual(p.get_salary_line_total("GARNISHMENT"), -197.04, places=2)

    def test_garnishment_capped_by_debt(self):
        """The deduction never exceeds the outstanding debt."""
        contract, employee = self._make_plain_worker(1000.0)
        p = self._payslip_with_inputs(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            [("GARNISHMENT", 40.0)],
        )
        self.assertAlmostEqual(p.get_salary_line_total("GARNISHMENT"), -40.0, places=2)

    def test_garnishment_inactive_without_input(self):
        """No garnishment input -> no deduction line."""
        contract, employee = self._make_plain_worker(1000.0)
        p = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertAlmostEqual(p.get_salary_line_total("GARNISHMENT"), 0.0, places=2)

    def test_garnishment_dependents_raise_non_seizable(self):
        """Each dependant raises the non-seizable amount (25% of the basic)."""
        contract, employee = self._make_plain_worker(
            1000.0, l10n_sk_garnishment_dependents=1
        )
        p = self._payslip_with_inputs(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            [("GARNISHMENT", 500.0)],
        )
        # Non-seizable = 397.78 + ~99.44/99.45 = ~497.22/497.23. Remainder
        # ~196.13 → 1/3 ~= 65.37/65.38. The dependant raises protection, so
        # strictly less is seized than the 0-dependant case (−98.52).
        seized = p.get_salary_line_total("GARNISHMENT")
        self.assertGreater(seized, -98.52)  # less seized (more protected)
        self.assertLess(seized, -65.0)
        self.assertGreater(seized, -66.0)

    # ---- Feature: sickness compensation (náhrada príjmu pri PN) ------------
    def test_sickness_compensation_2026(self):
        """14 employer-paid days (2026): 3 × 25% + 11 × 55% of the DVZ."""
        contract, employee = self._make_plain_worker(1500.0)
        p = self._payslip_with_inputs(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            [("PN_DAYS", 14.0), ("PN_DVZ", 20.0)],
        )
        # 20 × (3 × 0.25 + 11 × 0.55) = 20 × 6.80 = 136.00
        self.assertAlmostEqual(p.get_salary_line_total("SICK_COMP"), 136.0, places=2)

    def test_sickness_compensation_day_cap(self):
        """Only the first 14 days (2026) are employer-paid, extra days ignored."""
        contract, employee = self._make_plain_worker(1500.0)
        p = self._payslip_with_inputs(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            [("PN_DAYS", 30.0), ("PN_DVZ", 20.0)],
        )
        # capped at 14 days -> same 136.00 (SP pays from day 15)
        self.assertAlmostEqual(p.get_salary_line_total("SICK_COMP"), 136.0, places=2)

    # ---- Feature: absence -> payroll + priemerný zárobok (average earnings) -
    # Mon-Fri 8h calendar; June 2026 & March 2026 both have 22 working days,
    # June 1 2026 is a Monday so June 8-12 is a full working week (5 days).
    def _abs_setup(self, wage=2000.0):
        calendar = self._make_mon_fri_calendar()
        employee = self.env["hr.employee"].create(
            {
                "name": "Absenter Adam",
                "company_id": self.company.id,
                "resource_calendar_id": calendar.id,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Absenter Contract",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "wage": wage,
                "state": "open",
                "date_start": date(2024, 1, 1),
                "resource_calendar_id": calendar.id,
                "struct_id": self.structure.id,
            }
        )
        return contract, employee, calendar

    def _worked_payslip(self, contract, employee, date_from, date_to, inputs=None):
        p = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Slip %s" % date_from,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date_from,
                    "date_to": date_to,
                }
            )
        )
        wd = p.get_worked_day_lines(contract, date_from, date_to)
        p.worked_days_line_ids = [(0, 0, line) for line in wd]
        for code, amount in inputs or []:
            self.env["hr.payslip.input"].create(
                {
                    "payslip_id": p.id,
                    "contract_id": contract.id,
                    "name": code,
                    "code": code,
                    "amount": amount,
                    "sequence": 10,
                }
            )
        p.compute_sheet()
        return p

    def _make_leave(self, employee, xmlid, d_from, d_to):
        ltype = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
        leave = (
            self.env["hr.leave"]
            .with_company(self.company)
            .create(
                {
                    "name": ltype.name,
                    "employee_id": employee.id,
                    "holiday_status_id": ltype.id,
                    "request_date_from": d_from,
                    "request_date_to": d_to,
                }
            )
        )
        leave.action_validate()
        return leave

    def _seed_prior_quarter(self, contract, employee, bonus=0.0):
        """A full worked March 2026 (Q1): GROSS 2000 over 176 worked hours.

        priemerný hodinový zárobok = 2000 / 176 = 11.3636 — which is also what
        the pravdepodobný-zárobok fallback produces for this contract, so a
        test that needs to prove the SEEDED quarter was used must pass a
        ``bonus`` to move the two apart.
        """
        original = contract.wage
        if bonus:
            contract.wage = original + bonus
        p = self._worked_payslip(
            contract, employee, date(2026, 3, 1), date(2026, 3, 31)
        )
        self.assertAlmostEqual(
            p.get_salary_line_total("GROSS"), original + bonus, places=2)
        # CONFIRM it: compute_sheet leaves the payslip in "verify" (Waiting),
        # computed but not confirmed, and §134 counts the wage *zúčtovaná*.
        # Before restoring the wage, because action_payslip_done recomputes.
        p.action_payslip_done()
        contract.wage = original
        hours = sum(
            l.number_of_hours
            for l in p.worked_days_line_ids
            if l.code == "WORK100"
        )
        self.assertAlmostEqual(hours, 176.0, places=2)
        return p

    def test_average_hourly_earnings_from_prior_quarter(self):
        """PHZ comes from the SEEDED quarter, not the fallback.

        The seed is paid at 2400 rather than 2000, so the counted gross is
        2400 over 176 hours = 13.6364 — deliberately DIFFERENT from the
        pravdepodobný-zárobok fallback of 2000/176 = 11.3636. Without that the
        two branches produce the same number and the test cannot tell them
        apart: it passed with the payslip-state filter set to "cancel", which
        selects nothing at all.
        """
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee, bonus=400.0)
        june = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "June",
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                }
            )
        )
        self.assertAlmostEqual(
            june.l10n_sk_average_hourly_earnings(), 13.6364, places=4
        )


    def test_unconfirmed_payslips_do_not_feed_the_average(self):
        """§134 counts the wage *zúčtovaná* in the determining period.

        compute_sheet leaves a payslip in "verify" (Waiting) — computed but
        not confirmed. The search used to count it, so a half-finished month
        moved every náhrada in the next quarter.
        """
        contract, employee, _cal = self._abs_setup()
        original = contract.wage
        contract.wage = original + 400.0
        self._worked_payslip(
            contract, employee, date(2026, 3, 1), date(2026, 3, 31)
        )  # deliberately NOT confirmed
        contract.wage = original
        june = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertAlmostEqual(
            june.l10n_sk_average_hourly_earnings(), 11.3636, places=4
        )

    def test_average_earnings_min_wage_floor(self):
        """No prior quarter + tiny wage -> probable earnings floored to min wage."""
        contract, employee, _cal = self._abs_setup(wage=100.0)
        june = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "June",
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                }
            )
        )
        # 100/176 = 0.568 < 5.259 (2026 min hourly) -> raised to 5.259
        self.assertAlmostEqual(
            june.l10n_sk_average_hourly_earnings(), 5.259, places=3
        )

    def test_holiday_nahrada_no_proration_cut(self):
        """5 dovolenka days: BASIC cut, náhrada at PHZ, GROSS made whole."""
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee)
        self._make_leave(
            employee,
            "l10n_sk_leave_type_dovolenka",
            date(2026, 6, 8),
            date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total
        dov_days = sum(
            abs(l.number_of_days)
            for l in p.worked_days_line_ids
            if l.code == "DOVOLENKA"
        )
        self.assertAlmostEqual(dov_days, 5.0, places=2)
        # BASIC prorated: 2000 * 17/22 = 1545.45
        self.assertAlmostEqual(line("BASIC"), 2000.0 * 17 / 22, places=2)
        # náhrada = 40h * PHZ(11.3636, rounded to 4 dp per §134) = 454.54
        self.assertAlmostEqual(line("DOVOLENKA_NAHRADA"), 454.54, places=2)
        # GROSS made whole (no cut) up to the 4-dp PHZ rounding: ~2000.00
        self.assertAlmostEqual(line("GROSS"), 2000.0, places=1)

    def test_unpaid_leave_prorates_basic(self):
        """5 unpaid-leave days: BASIC prorated, no náhrada, GROSS follows."""
        contract, employee, _cal = self._abs_setup()
        self._make_leave(
            employee,
            "l10n_sk_leave_type_neplatene",
            date(2026, 6, 8),
            date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total
        self.assertAlmostEqual(line("BASIC"), 2000.0 * 17 / 22, places=2)
        self.assertAlmostEqual(line("DOVOLENKA_NAHRADA"), 0.0, places=2)
        # GROSS = prorated BASIC only (no náhrada)
        self.assertAlmostEqual(line("GROSS"), 2000.0 * 17 / 22, places=2)

    def test_pn_leave_drives_sick_comp(self):
        """3 PN working days from the leave drive SICK_COMP (3 x 25% of DVZ)."""
        contract, employee, _cal = self._abs_setup(wage=1500.0)
        self._make_leave(
            employee,
            "l10n_sk_leave_type_pn",
            date(2026, 6, 8),
            date(2026, 6, 10),
        )
        p = self._worked_payslip(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            inputs=[("PN_DVZ", 20.0)],
        )
        pn_days = sum(
            abs(l.number_of_days) for l in p.worked_days_line_ids if l.code == "PN"
        )
        self.assertAlmostEqual(pn_days, 3.0, places=2)
        # days 1-3 at 25%: 20 * 3 * 0.25 = 15.00
        self.assertAlmostEqual(p.get_salary_line_total("SICK_COMP"), 15.0, places=2)
        # BASIC prorated for the 3 absent days: 1500 * 19/22
        self.assertAlmostEqual(
            p.get_salary_line_total("BASIC"), 1500.0 * 19 / 22, places=2
        )

    def test_full_worked_month_unchanged_with_calendar(self):
        """Full Mon-Fri month, no leave: BASIC and GROSS stay the full wage."""
        contract, employee, _cal = self._abs_setup()
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertAlmostEqual(p.get_salary_line_total("BASIC"), 2000.0, places=2)
        self.assertAlmostEqual(p.get_salary_line_total("GROSS"), 2000.0, places=2)

    # ---- Feature: annual tax reconciliation (ročné zúčtovanie dane) --------
    def test_rz_taper_nedoplatok_manual(self):
        """Hand-computed NČZD taper true-up -> nedoplatok (2025 figures).

        Annual base 30000 > 25 426,27 taper threshold, so NČZD na daňovníka
        = 12 110,36 − ¼×30000 = 4 610,36 (vs 5 753,79 full). Taxable
        25 389,64; tax 19% (< 48 441,43) = 4 824,03. With only 4000 withheld
        the settlement is 4000 − 4824,03 = −824,03 (nedoplatok).
        """
        rz = self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": self.employee_nodecl.id,
                "company_id": self.company.id,
                "year": 2025,
                "gather_from_payslips": False,
                "annual_tax_base": 30000.0,
                "annual_advance_tax": 4000.0,
            }
        )
        self.assertAlmostEqual(rz.nczd_taxpayer, 4610.36, places=2)
        self.assertAlmostEqual(rz.taxable_base, 25389.64, places=2)
        self.assertAlmostEqual(rz.annual_tax, 4824.03, places=2)
        self.assertAlmostEqual(rz.result_amount, -824.03, places=2)
        self.assertEqual(rz.result_type, "nedoplatok")

    def test_rz_full_nczd_preplatok_manual(self):
        """Below the taper threshold: full NČZD 5 753,79, preplatok (2025)."""
        rz = self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": self.employee_nodecl.id,
                "company_id": self.company.id,
                "year": 2025,
                "gather_from_payslips": False,
                "annual_tax_base": 20000.0,
                "annual_advance_tax": 3000.0,
            }
        )
        # NČZD 5 753,79 -> taxable 14 246,21 -> tax 19% = 2 706,78.
        self.assertAlmostEqual(rz.nczd_taxpayer, 5753.79, places=2)
        self.assertAlmostEqual(rz.annual_tax, 2706.78, places=2)
        # 3000 − 2706,78 = 293,22 preplatok
        self.assertAlmostEqual(rz.result_amount, 293.22, places=2)
        self.assertEqual(rz.result_type, "preplatok")

    def test_rz_dds_cap_and_spouse(self):
        """DDS is capped at 180; spouse NČZD adds to the total (2025)."""
        rz = self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": self.employee_nodecl.id,
                "company_id": self.company.id,
                "year": 2025,
                "gather_from_payslips": False,
                "annual_tax_base": 20000.0,
                "annual_advance_tax": 3000.0,
                "dds_contributions": 500.0,  # capped to 180
                "nczd_spouse": 1000.0,
            }
        )
        # NČZD total = 5 753,79 + 1000 spouse + 180 DDS = 6 933,79
        self.assertAlmostEqual(rz.nczd_total, 6933.79, places=2)

    def test_rz_from_payslips_and_posting(self):
        """Seed 12 monthly payslips, gather, and post the settlement (2026)."""
        for month in range(1, 13):
            last = 28 if month == 2 else 30
            self._make_payslip(
                self.contract,
                self.employee,
                date(2026, month, 1),
                date(2026, month, last),
            )
        rz = self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": self.employee.id,
                "company_id": self.company.id,
                "year": 2026,
            }
        )
        rz.action_compute()
        # Σ TAXBASE = 12 × 1712 = 20544 ; Σ child bonus = 12 × 200 = 2400.
        self.assertAlmostEqual(rz.annual_tax_base, 20544.0, places=2)
        self.assertAlmostEqual(rz.annual_child_bonus_paid, 2400.0, places=2)
        # Constant income -> annual computation trues up to ~0 (only rounding).
        self.assertLess(abs(rz.result_amount), 1.0)
        self.assertEqual(rz.state, "computed")

        # Post the settlement onto a February-2027 reconciliation payslip.
        settlement_slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "RZ settlement",
                    "employee_id": self.employee.id,
                    "contract_id": self.contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2027, 2, 1),
                    "date_to": date(2027, 2, 28),
                }
            )
        )
        # Force a non-trivial result to prove the line posts with the sign.
        rz.gather_from_payslips = False
        rz.annual_advance_tax = rz.annual_advance_tax + 50.0
        rz.settlement_payslip_id = settlement_slip.id
        rz.action_post_settlement()
        self.assertTrue(rz.settlement_line_posted)
        self.assertEqual(rz.state, "posted")
        self.assertAlmostEqual(
            settlement_slip.get_salary_line_total("ANNUAL_TAX_SETTLEMENT"),
            rz.result_amount,
            places=2,
        )

    def test_rz_no_settlement_on_plain_payslip(self):
        """A standard monthly payslip has no settlement line (input-driven)."""
        p = self._make_payslip(
            self.contract, self.employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertAlmostEqual(
            p.get_salary_line_total("ANNUAL_TAX_SETTLEMENT"), 0.0, places=2
        )
# -- Multi-company country scoping (config visible only per country) ---

    def test_country_scoping_config(self):
        """SK salary structure and leave types are country-scoped: a payroll
        user working in an SK company sees only SK (and country-global) config,
        never another country's, mirroring the accounting localization."""
        sk = self.env.ref("base.sk")
        cz = self.env.ref("base.cz")
        # Our shipped config carries SK and is company-global.
        self.assertEqual(self.structure.country_id, sk)
        self.assertFalse(self.structure.company_id)
        leave_sk = self.env.ref(
            "l10n_sk_hr_payroll_oca.l10n_sk_leave_type_dovolenka"
        )
        self.assertEqual(leave_sk.country_id, sk)
        self.assertFalse(leave_sk.company_id)
        # Foreign (CZ) config created inline to prove isolation.
        cz_struct = self.env["hr.payroll.structure"].create(
            {"name": "CZ Struct", "code": "CZX",
             "country_id": cz.id, "company_id": False}
        )
        cz_leave = self.env["hr.leave.type"].create(
            {"name": "CZ Leave", "country_id": cz.id, "company_id": False}
        )
        # A payroll user who works in the SK company only.
        gfield = "group_ids" if "group_ids" in self.env.user._fields else "groups_id"
        user = self.env["res.users"].create(
            {
                "name": "SK Scope User",
                "login": "sk_scope_user",
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                gfield: [
                    (4, self.env.ref("payroll.group_payroll_user").id),
                    (4, self.env.ref("hr_holidays.group_hr_holidays_user").id),
                ],
            }
        )
        structs = self.env["hr.payroll.structure"].with_user(user).search([])
        self.assertIn(self.structure, structs)
        self.assertNotIn(cz_struct, structs)
        leaves = self.env["hr.leave.type"].with_user(user).search([])
        self.assertIn(leave_sk, leaves)
        self.assertNotIn(cz_leave, leaves)
        # An explicit country-filtered search returns only SK config too.
        sk_only = self.env["hr.payroll.structure"].search(
            ["|", ("country_id", "=", False), ("country_id", "=", sk.id)]
        )
        self.assertIn(self.structure, sk_only)
        self.assertNotIn(cz_struct, sk_only)

    # ------------------------------------------------------------------
    # § 142 — prekážky na strane ZAMESTNÁVATEĽA (ported from 19.0)
    # ------------------------------------------------------------------
    def test_employer_obstacle_weather_is_paid_at_half(self):
        """§ 142 ods. 2: adverse weather is náhrada at 50 % of priemerný
        zárobok. Booked against the generic § 141 obstacle it would be paid in
        full — which is what used to happen, overpaying by half."""
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee)
        self._make_leave(
            employee, "l10n_sk_leave_type_employer_pocasie",
            date(2026, 6, 8), date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total
        phz = p.l10n_sk_average_hourly_earnings()
        self.assertAlmostEqual(line("PREKAZKA_NAHRADA"),
                               round(40 * phz * 0.5, 2), places=2)
        self.assertLess(line("PREKAZKA_NAHRADA"), round(40 * phz, 2))

    def test_employer_obstacle_each_reason_has_its_own_rate(self):
        """All four § 142 reasons in one month, each at its own percentage."""
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee)
        for xmlid, day in (
            ("l10n_sk_leave_type_employer_prestoj", 2),
            ("l10n_sk_leave_type_employer_pocasie", 9),
            ("l10n_sk_leave_type_employer_ine", 16),
            ("l10n_sk_leave_type_employer_vazne", 23),
        ):
            self._make_leave(employee, xmlid, date(2026, 6, day), date(2026, 6, day))
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        phz = p.l10n_sk_average_hourly_earnings()
        expected = round(8 * phz * (1.0 + 0.5 + 1.0 + 0.6), 2)
        self.assertAlmostEqual(
            p.get_salary_line_total("PREKAZKA_NAHRADA"), expected, places=2)

    def test_family_leave_is_unpaid_by_the_employer(self):
        """Materské / rodičovský príspevok / otcovské are dávky of the
        Sociálna poisťovňa: the employer prorates the wage and pays nothing."""
        for xmlid, code in (
            ("l10n_sk_leave_type_materska", "MATERSKA"),
            ("l10n_sk_leave_type_rodicovska", "RODICOVSKA"),
            ("l10n_sk_leave_type_otcovska", "OTCOVSKA"),
        ):
            with self.subTest(code=code):
                contract, employee, _cal = self._abs_setup()
                self._make_leave(employee, xmlid,
                                 date(2026, 6, 8), date(2026, 6, 12))
                p = self._worked_payslip(
                    contract, employee, date(2026, 6, 1), date(2026, 6, 30))
                line = p.get_salary_line_total
                self.assertAlmostEqual(line("BASIC"), 2000.0 * 136 / 176, places=2)
                self.assertAlmostEqual(line("PREKAZKA_NAHRADA"), 0.0, places=2)
                self.assertAlmostEqual(line("GROSS"), line("BASIC"), places=2)

    def test_further_absences_use_the_right_bucket(self):
        for xmlid, code in (
            ("l10n_sk_leave_type_darovanie_krvi", "OBSTACLE"),
            ("l10n_sk_leave_type_verejna_funkcia", "OBSTACLE"),
            ("l10n_sk_leave_type_obcianska_povinnost", "OBSTACLE"),
            ("l10n_sk_leave_type_vzdelavanie", "OBSTACLE"),
            ("l10n_sk_leave_type_vzdelavanie_unpaid", "NEPLATENE"),
            ("l10n_sk_leave_type_karantena", "PN"),
        ):
            with self.subTest(xmlid=xmlid):
                ltype = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
                self.assertEqual(ltype.l10n_sk_payroll_code, code)
                self.assertEqual(ltype.requires_allocation, "no")

    def _part_month_contract(self, wage, **vals):
        employee = self.env["hr.employee"].create(
            {"name": "Part Month", "company_id": self.company.id}
        )
        values = {
            "name": "Part-month contract",
            "employee_id": employee.id,
            "company_id": self.company.id,
            "wage": wage,
            "state": "open",
            "date_start": date(2026, 11, 16),
            "resource_calendar_id": self.calendar.id,
            "struct_id": self.structure.id,
        }
        values.update(vals)
        return self.env["hr.contract"].create(values), employee

    def test_employee_cap_prorated_for_part_month(self):
        contract, _employee = self._part_month_contract(20000.0)
        self.assertEqual(
            contract.l10n_sk_employee_social_cap(16764.0, date(2026, 11, 1)), 8382.0
        )
        self.assertEqual(
            contract.l10n_sk_employee_social_cap(16764.0, date(2026, 12, 1)), 16764.0
        )

    def test_part_month_cap_reaches_the_employee_premium(self):
        contract, employee = self._part_month_contract(20000.0)
        p = self._make_payslip(contract, employee, date(2026, 11, 1), date(2026, 11, 30))
        # Halved cap at 1.4 %, floored to the cent.
        self.assertAlmostEqual(p.get_salary_line_total("SICK"), -117.34, places=2)

    def test_daily_cap_rounding_reaches_the_actual_disability_premium(self):
        contract, employee = self._part_month_contract(
            50000.0, date_start=date(2026, 1, 16)
        )
        slip = self._make_payslip(contract, employee, date(2026, 1, 1), date(2026, 1, 31))
        self.assertGreater(slip.get_salary_line_total("GROSS"), 16764)
        # § 138(13): floor(16764 / 31, 2) x 16 = 8652.32.
        # Employee disability: floor(8652.32 x 3%, 2) = 259.56.
        self.assertAlmostEqual(slip.get_salary_line_total("DISABILITY"), -259.56, places=2)
        self.assertAlmostEqual(
            slip.get_salary_line_total("DISABILITYEMPLOYER"), 502.92, places=2
        )

    def test_health_allowance_reduced_for_a_part_month(self):
        contract, employee = self._part_month_contract(400.0, l10n_sk_health_oop_claim=True)
        p = self._make_payslip(contract, employee, date(2026, 11, 1), date(2026, 11, 30))
        self.assertAlmostEqual(p.get_salary_line_total("HEALTH"), -11.5, places=2)

    def test_sick_pay_counts_calendar_days(self):
        contract, employee, _cal = self._abs_setup(wage=1500.0)
        self._make_leave(
            employee, "l10n_sk_leave_type_pn", date(2026, 6, 8), date(2026, 6, 21)
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30),
            inputs=[("PN_DVZ", 60.0)],
        )
        self.assertAlmostEqual(p.get_salary_line_total("SICK_COMP"), 408.0, places=2)


    # ---- cssk-public#39: employment boundary, onset terms, statutory rounding
    def test_sickness_calendar_employer_stops_at_employment_end(self):
        contract, employee, _calendar = self._abs_setup(wage=1500)
        contract.date_end = date(2026, 6, 9)
        self._make_leave(
            employee, "l10n_sk_leave_type_pn", date(2026, 6, 5), date(2026, 6, 18)
        )
        slip = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30),
            inputs=[("PN_DVZ", 20)],
        )
        # Employer pays only 5-9 June: 3 x 25 % + 2 x 55 % of 20 = 37.
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 37)

    def test_sickness_calendar_2025_claim_keeps_ten_day_limit_in_2026(self):
        contract, employee, _calendar = self._abs_setup(wage=1500)
        self._make_leave(
            employee, "l10n_sk_leave_type_pn", date(2025, 12, 30), date(2026, 1, 12)
        )
        slip = self._worked_payslip(
            contract, employee, date(2026, 1, 1), date(2026, 1, 31),
            inputs=[("PN_DVZ", 20)],
        )
        # 1 January is day 3; only 2-8 January (days 4-10) use the second rate.
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 82)

    def test_sickness_calendar_2025_claim_keeps_its_daily_cap_and_rounds_up(self):
        contract, employee, _calendar = self._abs_setup(wage=1500)
        self._make_leave(
            employee, "l10n_sk_leave_type_pn", date(2025, 12, 30), date(2026, 1, 12)
        )
        slip = self._worked_payslip(
            contract, employee, date(2026, 1, 1), date(2026, 1, 31),
            inputs=[("PN_DVZ", 100)],
        )
        # 2025 cap 94.0274 x (one day 25 % + seven days 55 %) = 385.51234;
        # § 10 ods. 2 rounds up, hence 385.52.
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 385.52)

    def test_sickness_calendar_zero_after_termination_does_not_use_manual_fallback(
        self,
    ):
        contract, employee, _calendar = self._abs_setup(wage=1500)
        contract.date_end = date(2026, 6, 9)
        self._make_leave(
            employee, "l10n_sk_leave_type_pn", date(2026, 6, 10), date(2026, 6, 23)
        )
        slip = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30),
            inputs=[("PN_DVZ", 20), ("PN_DAYS", 14)],
        )
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 0)

    def test_sickness_manual_compensation_uses_statutory_upward_rounding(self):
        contract, employee = self._make_plain_worker(1500)
        slip = self._payslip_with_inputs(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30),
            [("PN_DAYS", 1), ("PN_DVZ", 20.00019)],
        )
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 5.01)

    def test_leave_starter_upgrade_preserves_approved_absence_and_configuration(self):
        """cssk-public#40: the starter types are noupdate, so a module update
        keeps approved absences and a company's own settings."""
        checked_fields = ["date_from", "date_to", "state", "number_of_days"]
        for xmlid in ("l10n_sk_leave_type_pn", "l10n_sk_leave_type_dovolenka"):
            with self.subTest(leave_type=xmlid):
                _contract, employee, _calendar = self._abs_setup(wage=1500)
                leave = self._make_leave(
                    employee, xmlid, date(2026, 6, 5), date(2026, 6, 9)
                )
                original = leave.read(checked_fields)
                leave_type = leave.holiday_status_id.with_context(lang="en_US")
                leave_type.name = "Company reviewed absence type"
                convert_file(
                    self.env,
                    "l10n_sk_hr_payroll_oca",
                    "data/hr_leave_type_data.xml",
                    {},
                    mode="update",
                )
                self.env.flush_all()
                leave.invalidate_recordset()
                leave_type.invalidate_recordset()
                self.assertEqual(leave.read(checked_fields), original)
                self.assertEqual(leave_type.name, "Company reviewed absence type")

    # ---- The dated 2027 values (same figures and results as 19.0) ----------
    def _profile_2027(self, wage=1000, declaration=True, year=2027, **vals):
        employee = self.env["hr.employee"].create(
            {"name": "2027 case %s" % wage, "company_id": self.company.id}
        )
        values = {
            "name": "Synthetic 2027 parameter case",
            "employee_id": employee.id,
            "company_id": self.company.id,
            "wage": wage,
            "state": "open",
            "date_start": date(2026, 1, 1),
            "resource_calendar_id": self.calendar.id,
            "struct_id": self.structure.id,
            "l10n_sk_tax_declaration_signed": declaration,
        }
        values.update(vals)
        contract = self.env["hr.contract"].create(values)
        slip = self._make_payslip(
            contract, employee, date(year, 1, 1), date(year, 1, 31)
        )
        return employee, contract, slip

    def test_dated_parameter_table_2027(self):
        _employee, _contract, slip = self._profile_2027()
        expected = {
            "l10n_sk_monthly_taxable_max": 17820,
            "l10n_sk_health_min_base": 295.22,
            "l10n_sk_nczd_monthly": 516.64,
            "l10n_sk_nczd_annual": 6199.62,
            "l10n_sk_nczd_taper_threshold": 27101.20,
            "l10n_sk_nczd_taper_const": 15233.35,
            "l10n_sk_child_bonus_taper_threshold": 29160,
            "l10n_sk_min_hourly_wage": 5.586,
            "l10n_sk_pn_max_dvz": 106.5206,
            "l10n_sk_dohoda_oop_seasonal": 810,
            "l10n_sk_dohoda_oop": 300,
        }
        for code, value in expected.items():
            with self.subTest(code=code):
                self.assertAlmostEqual(slip.rule_parameter(code), value, places=4)

    def test_monthly_nczd_2027_changes_net(self):
        _employee, _contract, slip = self._profile_2027()
        self.assertAlmostEqual(slip.get_salary_line_total("TAXBASE"), 856)
        self.assertAlmostEqual(slip.get_salary_line_total("INCOMETAX"), -64.48, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total("NET"), 791.52, places=2)

    def test_2026_recalculation_keeps_old_values(self):
        _employee, _contract, old = self._profile_2027(year=2026)
        self.assertEqual(old.rule_parameter("l10n_sk_nczd_monthly"), 497.23)
        self.assertEqual(old.rule_parameter("l10n_sk_monthly_taxable_max"), 16764)
        self.assertAlmostEqual(old.get_salary_line_total("NET"), 787.83, places=2)

    def test_second_monthly_tax_band_2027(self):
        _employee, _contract, slip = self._profile_2027(5200, declaration=False)
        self.assertAlmostEqual(slip.get_salary_line_total("TAXBASE"), 4451.20, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total("INCOMETAX"), -884.30, places=2)

    def test_social_cap_and_uncapped_health_accident_2027(self):
        _employee, _contract, slip = self._profile_2027(20000, declaration=False)
        for code, value in {"SICK": -249.48, "PENSION": -712.80,
                            "DISABILITY": -534.60, "UNEMPLOYMENT": -178.20,
                            "HEALTH": -1000, "HEALTHEMPLOYER": 2200,
                            "ACCIDENT": 160}.items():
            self.assertAlmostEqual(
                slip.get_salary_line_total(code), value, places=2, msg=code
            )

    def test_child_bonus_taper_2027(self):
        _employee, _contract, slip = self._profile_2027(
            2950, l10n_sk_children_under_15=1
        )
        self.assertAlmostEqual(slip.get_salary_line_total("TAXBASE"), 2525.20, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total("CHILD_BONUS"), 90.48, places=2)

    # ---- 19.0 ffd67cd0c: 2026 NČZD, child bonus, DoBPŠ, health minimum -----
    def _make_contract(self, name, wage, date_start, calendar, **vals):
        """Employee + running hr.contract on the Slovak structure.

        The 19.0 helper of the same name writes an ``hr.version``; on 18.0 the
        contract is its own record, created ``open`` so the payslip finds it.
        """
        employee = self.env["hr.employee"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "resource_calendar_id": calendar.id,
            }
        )
        values = {
            "name": "%s contract" % name,
            "employee_id": employee.id,
            "company_id": self.company.id,
            "wage": wage,
            "state": "open",
            "date_start": date_start,
            "resource_calendar_id": calendar.id,
            "struct_id": self.structure.id,
        }
        values.update(vals)
        return self.env["hr.contract"].create(values), employee

    def test_rz_2026_nczd_taper_is_a_third(self):
        """§ 11 ods. 2 písm. b) ZDP as of 1. 1. 2026: 51,6 × ŽM − ⅓ base.

        Base 40 000 > 26 083,13: NČZD = 14 661,11 − 40 000/3 = 1 327,78.
        The 2025 shape carried over (12 487,51 − ¼ base) gave 2 487,51.
        Taxable 38 672,22 × 19 % = 7 347,72.
        """
        rz = self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": self.employee_nodecl.id,
                "company_id": self.company.id,
                "year": 2026,
                "gather_from_payslips": False,
                "annual_tax_base": 40000.0,
                "annual_advance_tax": 7000.0,
            }
        )
        self.assertAlmostEqual(rz.nczd_taxpayer, 1327.78, places=2)
        self.assertAlmostEqual(rz.annual_tax, 7347.72, places=2)
        self.assertAlmostEqual(rz.result_amount, -347.72, places=2)
        # ...and it reaches zero at 3 × 14 661,11 = 43 983,33.
        rz.annual_tax_base = 43983.33
        self.assertAlmostEqual(rz.nczd_taxpayer, 0.0, places=2)
        # 2025 keeps the quarter: 12 110,36 − 30 000/4 = 4 610,36.
        rz.write({"year": 2025, "annual_tax_base": 30000.0})
        self.assertAlmostEqual(rz.nczd_taxpayer, 4610.36, places=2)

    def test_2026_annual_bands_are_the_zm_multiples(self):
        """§ 15 písm. a) bod 1: 154,8× / 212,4× / 264× ŽM 284,13."""
        bands = self.env["hr.rule.parameter"]._get_parameter_value(
            "l10n_sk_income_tax_bands_annual", date(2026, 12, 31)
        )
        self.assertEqual(
            [c for _r, c in bands[:3]], [43983.32, 60349.21, 75010.32]
        )

    def test_child_bonus_taper_applies_per_child(self):
        """§ 33 ods. 11: the 1/10 reduction is taken from EACH child.

        2026, wage 3 500: TAXBASE = 3 500 − 329 − 175 = 2 996, monthly
        threshold 27 432 / 12 = 2 286, reduction 0,1 × 710 = 71 per child,
        so 2 × (100 − 71) = 58 — not 200 − 71 = 129.
        """
        contract, employee = self._make_contract(
            "Vysoky Prijem", 3500.0, date(2024, 1, 1), self.calendar,
            l10n_sk_tax_declaration_signed=True,
            l10n_sk_children_under_15=2,
        )
        p = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertAlmostEqual(p.get_salary_line_total("TAXBASE"), 2996.0, 2)
        self.assertAlmostEqual(p.get_salary_line_total("CHILD_BONUS"), 58.0, 2)

    def test_rz_child_bonus_taper_applies_per_child(self):
        """Annual: base 35 000, two children < 15 (2026).

        Reduction 0,1 × (35 000 − 27 432) = 756,80 per child:
        2 × (1 200 − 756,80) = 886,40 (once in total gave 1 643,20).
        """
        rz = self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": self.employee.id,
                "company_id": self.company.id,
                "year": 2026,
                "gather_from_payslips": False,
                "annual_tax_base": 35000.0,
            }
        )
        self.assertAlmostEqual(rz.child_bonus_entitlement, 886.40, places=2)

    def _two_hour_calendar(self):
        """Two hours a week: 100 € stays above the pro-rated minimum wage,
        so the minimum-wage top-up (when installed) cannot lift the gross."""
        return self.env["resource.calendar"].create(
            {
                "name": "SK 2h/week",
                "company_id": self.company.id,
                "hours_per_day": 2.0,
                "attendance_ids": [
                    (0, 0, {
                        "name": "Mon",
                        "dayofweek": "0",
                        "hour_from": 8.0,
                        "hour_to": 10.0,
                        "day_period": "morning",
                    })
                ],
            }
        )

    def _tiny_part_timer(self, **vals):
        """€100 a month on two hours a week — below the životné minimum,
        yet above the pro-rated minimum wage (≈ 8,7 h × 5,259 €)."""
        calendar = self._two_hour_calendar()
        return self._make_contract(
            "Minimalny Preddavok", 100.0, date(2024, 1, 1), calendar, **vals
        )

    def test_health_minimum_preddavok(self):
        """§ 16a zákona 580/2004 (2026, ŽM 284,13).

        Minimum = ⌊284,13 × 5 %⌋ + ⌊284,13 × 11 %⌋ = 14,20 + 31,25 = 45,45;
        actual 5,00 + 11,00 → top-up 29,45.
        """
        contract, employee = self._tiny_part_timer()
        p = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertAlmostEqual(p.get_salary_line_total("HEALTH"), -5.0, 2)
        self.assertAlmostEqual(
            p.get_salary_line_total("HEALTHDOPLATOK"), -29.45, 2)

    def test_health_minimum_preddavok_not_for_ztp(self):
        """§ 16a ods. 2 písm. c): every ZP day removes its share — a ZŤP
        employee for the whole month owes no minimum at all."""
        contract, employee = self._tiny_part_timer(l10n_sk_ztp=True)
        p = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertAlmostEqual(
            p.get_salary_line_total("HEALTHDOPLATOK"), 0.0, 2)

    def test_health_minimum_preddavok_reduced_by_pn_days(self):
        """§ 16a ods. 2 + § 11 ods. 7: PN days are poistenec-štátu days.

        10 of 30 calendar days: 45,45 × 20/30 = 30,30 − 16,00 = 14,30.
        """
        contract, employee = self._tiny_part_timer()
        p = self._payslip_with_inputs(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30),
            [("PN_DAYS", 10.0)],
        )
        self.assertAlmostEqual(
            p.get_salary_line_total("HEALTHDOPLATOK"), -14.30, 2)

    def test_health_minimum_preddavok_outside_the_contract(self):
        """§ 16a ods. 2: days before the contract starts shrink the minimum.

        Hired 16 June 2026: 15 of 30 days, 45,45 × 15/30 = 22,72 (floored)."""
        contract, employee = self._tiny_part_timer()
        contract.date_start = date(2026, 6, 16)
        p = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        health = -p.get_salary_line_total("HEALTH")
        health_er = p.get_salary_line_total("HEALTHEMPLOYER")
        self.assertAlmostEqual(
            p.get_salary_line_total("HEALTHDOPLATOK"),
            -max(0.0, round(22.72 - health - health_er, 2)), 2)

    # ---- The two 2027 tests held back from 18.0.2.10.0 ---------------------
    def test_health_minimum_2027(self):
        """2027: ⌊295,22 × 5 %⌋ + ⌊295,22 × 11 %⌋ = 14,76 + 32,47 = 47,23;
        actual on 100 € is 5,00 + 11,00, so the top-up is 31,23 (not 31,24,
        the unfloored 47,2352 − 16)."""
        _employee, _contract, slip = self._profile_2027(
            100, resource_calendar_id=self._two_hour_calendar().id
        )
        self.assertAlmostEqual(
            slip.get_salary_line_total("HEALTHDOPLATOK"), -31.23, places=2)

    def test_annual_nczd_and_taper_2027(self):
        """2027 RZ: full 6 199,62 up to 27 101,20; then 15 233,35 − ⅓ base."""
        for base, nczd, tax in ((24000, 6199.62, 3382.07),
                                (30000, 5233.35, 4705.66),
                                (50000, 0, 9758.00)):
            with self.subTest(base=base):
                employee, _contract, _slip = self._profile_2027()
                annual = self.env["l10n.sk.tax.reconciliation"].create({
                    "company_id": self.company.id, "employee_id": employee.id,
                    "year": 2027, "gather_from_payslips": False,
                    "annual_tax_base": base})
                annual.action_compute()
                self.assertAlmostEqual(annual.nczd_taxpayer, nczd, places=2)
                self.assertAlmostEqual(annual.annual_tax, tax, places=2)
