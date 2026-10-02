# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# These tests assert the Slovak payroll behaviour on the 19.0 engine, where a
# contract is an ``hr.version`` record owned by the employee:
#   * TAXBASE = gross − employee social − employee health
#   * NČZD applied (and gated on the signed declaration)
#   * income tax matches a hand-computed monthly advance
#   * CHILD_BONUS credited for an employee with children
#   * dated parameters exercised by one 2025-dated and one 2026-dated payslip
#     (health rate 4% -> 5%, NČZD 479.48 -> 497.23).

from datetime import date

from odoo.tests import TransactionCase, tagged


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
        # Declaration signed, 2 children < 15, standard (non-ZŤP), no meal.
        cls.contract, cls.employee = cls._make_contract(
            "Jozko Mrkvicka",
            2000.0,
            date(2024, 1, 1),
            cls.calendar,
            l10n_sk_tax_declaration_signed=True,
            l10n_sk_children_under_15=2,
        )
        # Employee without a signed declaration (to prove NČZD gating).
        cls.contract_nodecl, cls.employee_nodecl = cls._make_contract(
            "Anna Bezvyhlasenia",
            2000.0,
            date(2024, 1, 1),
            cls.calendar,
            l10n_sk_tax_declaration_signed=False,
        )

    @classmethod
    def _structure_for(cls, agreement_type):
        """The structure representing a Slovak employment form.

        The structure decides the form now, and a contract may not disagree
        with it, so a fixture asking for a dohoda has to sit on the matching
        structure rather than setting the agreement type underneath one that
        says "employment".
        """
        by_form = {
            "dovp": "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dovp",
            "dopc": "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dopc",
            "dobps": "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dobps",
        }
        xmlid = by_form.get(agreement_type)
        return cls.env.ref(xmlid) if xmlid else cls.structure

    @classmethod
    def _make_contract(cls, name, wage, date_start, calendar, struct=None, **l10n):
        if struct is None and l10n.get("l10n_sk_agreement_type"):
            struct = cls._structure_for(l10n["l10n_sk_agreement_type"])
        """Create an employee and populate its current version (the "contract").

        On 19.0 the payslip ``contract_id`` is an ``hr.version``; the Slovak
        payroll fields live on that version.  Returns ``(version, employee)`` to
        keep the ``(contract, employee)`` call sites unchanged.
        """
        employee = cls.env["hr.employee"].create(
            {
                "name": name,
                "company_id": cls.company.id,
                "resource_calendar_id": calendar.id,
            }
        )
        version = employee.version_id
        vals = {
            "contract_date_start": date_start,
            "date_version": date_start,
            "wage": wage,
            "resource_calendar_id": calendar.id,
            "struct_id": (struct or cls.structure).id,
        }
        vals.update(l10n)
        version.write(vals)
        return version, employee

    def _make_payslip(self, contract, employee, date_from, date_to):
        payslip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip %s" % date_from,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    # The contract's own structure, so a dohoda fixture is paid
                    # through the structure that declares its form.
                    "struct_id": (contract.struct_id or self.structure).id,
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
        return self._make_contract(
            "Maly Zarobok", 500.0, date(2024, 1, 1), calendar, **vals
        )

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
        return self._make_contract(
            "Dohodar Peter", 1000.0, date(2024, 1, 1), self.calendar, **vals
        )

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
        # Hired mid-month (16 June 2026), so ~half the working days are worked.
        contract, employee = self._make_contract(
            "Novy Zamestnanec", 2000.0, date(2026, 6, 16), calendar
        )
        p = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Proration slip",
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    # The contract's own structure, so a dohoda fixture is paid
                    # through the structure that declares its form.
                    "struct_id": (contract.struct_id or self.structure).id,
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
        return self._make_contract(
            "Dlznik Pavol", wage, date(2024, 1, 1), self.calendar, **vals
        )

    def _payslip_with_inputs(self, contract, employee, date_from, date_to, inputs):
        p = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Slip %s" % date_from,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    # The contract's own structure, so a dohoda fixture is paid
                    # through the structure that declares its form.
                    "struct_id": (contract.struct_id or self.structure).id,
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
        """Prednostná exekúcia (výživné/dane): 2/3 of the remainder.

        A priority creditor reaches deeper than an ordinary one: under
        § 2 ods. 2 NV 268/2006 the base that must be left to the debtor is
        100 % ŽM (284.13), not the ordinary 140 % (397.78). Remainder
        693.36 − 284.13 = 409.23, already divisible by three → 1/3 = 136.41
        → 2/3 = 272.82.
        """
        contract, employee = self._make_plain_worker(1000.0)
        p = self._payslip_with_inputs(
            contract,
            employee,
            date(2026, 6, 1),
            date(2026, 6, 30),
            [("GARNISHMENT_PRIORITY", 500.0)],
        )
        self.assertAlmostEqual(p.get_salary_line_total("GARNISHMENT"), -272.82, places=2)

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
        contract, employee = self._make_contract(
            "Absenter Adam", wage, date(2024, 1, 1), calendar
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
                    # The contract's own structure, so a dohoda fixture is paid
                    # through the structure that declares its form.
                    "struct_id": (contract.struct_id or self.structure).id,
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
        leave.action_approve()
        return leave

    def _seed_prior_quarter(self, contract, employee, bonus=0.0):
        """A full worked March 2026 (Q1): GROSS 2000 over 176 worked hours.

        priemerný hodinový zárobok = 2000 / 176 = 11.3636 — which is also what
        the pravdepodobný-zárobok fallback produces for this contract, so a
        test that needs to prove the SEEDED quarter was used must pass a
        ``bonus`` to move the two apart.
        """
        # A higher wage for the seeded month only, restored afterwards: it
        # moves the counted gross without needing an input rule the base
        # structure does not have.
        original = contract.wage
        if bonus:
            contract.wage = original + bonus
        p = self._worked_payslip(
            contract, employee, date(2026, 3, 1), date(2026, 3, 31)
        )
        self.assertAlmostEqual(
            p.get_salary_line_total("GROSS"), original + bonus, places=2)
        # CONFIRM it. §134 counts the wage "zúčtovaná" in the determining
        # period, and compute_sheet leaves the payslip in the engine's
        # "verify" (Waiting) state — computed, not confirmed. A seed left
        # there is not a filed month and must not feed the average.
        #
        # Before restoring the wage, because action_payslip_done recomputes
        # the sheet: confirming after the restore would quietly recompute the
        # seed at the ORIGINAL wage and undo the whole point of the bonus.
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
        2400 over 176 hours = 13.6364 — deliberately DIFFERENT from
        the pravdepodobný-zárobok fallback of 2000/176 = 11.3636. Without the
        bonus the two branches produce the same number and the test cannot
        tell them apart: it passed with the payslip-state filter set to
        "cancel", which selects nothing at all.
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
                    # The contract's own structure, so a dohoda fixture is paid
                    # through the structure that declares its form.
                    "struct_id": (contract.struct_id or self.structure).id,
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

        compute_sheet leaves an OCA payslip in "verify" (Waiting) — computed
        but not confirmed. Until 2026-08-06 the search counted it, so a
        half-finished month moved every náhrada in the next quarter; the
        Czech side had always filtered on "done" alone. This is the guard: a
        seeded quarter left unconfirmed must fall back to the pravdepodobný
        zárobok, not be treated as a filed month.
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
        # The fallback (2000/176), not the unconfirmed seed (2400/176).
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
                    # The contract's own structure, so a dohoda fixture is paid
                    # through the structure that declares its form.
                    "struct_id": (contract.struct_id or self.structure).id,
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

    # ---- Feature: income regularity drives the fund set -------------------
    def test_dovp_with_regular_income_pays_the_full_set(self):
        """The fund set follows income regularity, not the agreement kind.

        A DoVP agreed as a regular monthly income is a zamestnanec s
        pravidelným príjmom and owes sickness and unemployment insurance like
        anyone else. Keying the fund set off the agreement TYPE — which this
        module did until now — under-charged every such worker.
        """
        contract, employee = self._make_dohodar(
            l10n_sk_agreement_type="dovp", l10n_sk_income_regular=True
        )
        p = self._make_payslip(
            contract, employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        line = p.get_salary_line_total
        self.assertAlmostEqual(line("SICK"), -14.0, places=2)
        self.assertAlmostEqual(line("UNEMPLOYMENT"), -10.0, places=2)
        self.assertAlmostEqual(line("SHORTTIMEEMPLOYER"), 5.0, places=2)

    def test_dopc_with_irregular_income_pays_the_reduced_set(self):
        """...and the converse: a DoPČ paid once on completion."""
        contract, employee = self._make_dohodar(
            l10n_sk_agreement_type="dopc", l10n_sk_income_regular=False
        )
        p = self._make_payslip(
            contract, employee, date(2025, 6, 1), date(2025, 6, 30)
        )
        line = p.get_salary_line_total
        self.assertAlmostEqual(line("SICK"), 0.0, places=2)
        self.assertAlmostEqual(line("UNEMPLOYMENT"), 0.0, places=2)
        self.assertAlmostEqual(line("PENSION"), -40.0, places=2)

    def test_regularity_defaults_from_the_agreement_kind(self):
        """Programmatic creation must get the usual treatment for its kind."""
        dovp, _e1 = self._make_dohodar(l10n_sk_agreement_type="dovp")
        dopc, _e2 = self._make_dohodar(l10n_sk_agreement_type="dopc")
        self.assertFalse(dovp.l10n_sk_income_regular)
        self.assertTrue(dopc.l10n_sk_income_regular)

    def test_employment_is_always_regular(self):
        contract, _employee = self._make_dohodar(l10n_sk_agreement_type="none")
        self.assertTrue(contract.l10n_sk_income_regular)

    # ------------------------------------------------------------------
    # § 142 — prekážky na strane ZAMESTNÁVATEĽA
    # ------------------------------------------------------------------
    def test_employer_obstacle_weather_is_paid_at_half(self):
        """§ 142 ods. 2: adverse weather is náhrada at 50 % of priemerný
        zárobok. Booked against the generic § 141 obstacle it would be paid in
        full — which is exactly what used to happen, overpaying by half."""
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee)
        self._make_leave(
            employee,
            "l10n_sk_leave_type_employer_pocasie",
            date(2026, 6, 8),
            date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total
        # BASIC prorated for the 5 absent days exactly as for any other absence
        self.assertAlmostEqual(line("BASIC"), 2000.0 * 17 / 22, places=2)
        # 40 h x PHZ 11.3636 x 50 % = 227.27, NOT the 454.54 a full-rate
        # obstacle would have paid.
        self.assertAlmostEqual(line("PREKAZKA_NAHRADA"), 227.27, places=2)

    def test_employer_obstacle_each_reason_has_its_own_rate(self):
        """All four § 142 reasons in one month, each at its own statutory
        percentage, summed by the one rule."""
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
        line = p.get_salary_line_total
        phz = 11.3636
        expected = round(
            8 * phz * 1.0        # prestoj      § 142 ods. 1 — 100 %
            + 8 * phz * 0.5      # weather      § 142 ods. 2 —  50 %
            + 8 * phz * 1.0      # other        § 142 ods. 3 — 100 %
            + 8 * phz * 0.6,     # serious ops  § 142 ods. 4 —  60 %
            2,
        )
        self.assertAlmostEqual(line("PREKAZKA_NAHRADA"), expected, places=2)
        # 4 absent days out of 22
        self.assertAlmostEqual(line("BASIC"), 2000.0 * 18 / 22, places=2)

    def test_employer_obstacle_is_insurable_and_taxable(self):
        """Náhrada mzdy is regular wage income: it must reach GROSS, so it is
        assessed for contributions and tax like the holiday náhrada."""
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee)
        self._make_leave(
            employee,
            "l10n_sk_leave_type_employer_prestoj",
            date(2026, 6, 8),
            date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total
        self.assertAlmostEqual(line("PREKAZKA_NAHRADA"), 454.54, places=2)
        # prestoj is the 100 % reason, so GROSS is made whole like a holiday
        self.assertAlmostEqual(line("GROSS"), 2000.0, places=1)

    def test_employer_obstacle_rates_are_data_not_code(self):
        """The percentages come from dated rule parameters: change one and the
        payslip follows, without touching a rule body."""
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee)
        param = self.env.ref(
            "l10n_sk_hr_payroll_oca.rule_parameter_prekazka_pocasie_pct"
        )
        self.env["hr.rule.parameter.value"].create(
            {
                "rule_parameter_id": param.id,
                "parameter_value": "80",
                "date_from": date(2026, 6, 1),
            }
        )
        self._make_leave(
            employee,
            "l10n_sk_leave_type_employer_pocasie",
            date(2026, 6, 8),
            date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        # 40 h x 11.3636 x 80 % = 363.64
        self.assertAlmostEqual(p.get_salary_line_total("PREKAZKA_NAHRADA"),
                               363.64, places=2)

    # ------------------------------------------------------------------
    # § 166 — materská / rodičovská / otcovská
    # ------------------------------------------------------------------
    def test_family_leave_is_unpaid_by_the_employer(self):
        """Materské / rodičovský príspevok / otcovské are dávky of the Sociálna
        poisťovňa. The employer records the absence, prorates the wage down and
        pays nothing — no náhrada of any kind."""
        for xmlid, code in (
            ("l10n_sk_leave_type_materska", "MATERSKA"),
            ("l10n_sk_leave_type_rodicovska", "RODICOVSKA"),
            ("l10n_sk_leave_type_otcovska", "OTCOVSKA"),
        ):
            with self.subTest(code=code):
                contract, employee, _cal = self._abs_setup()
                self._make_leave(
                    employee, xmlid, date(2026, 6, 8), date(2026, 6, 12)
                )
                p = self._worked_payslip(
                    contract, employee, date(2026, 6, 1), date(2026, 6, 30)
                )
                hours = sum(
                    abs(w.number_of_hours)
                    for w in p.worked_days_line_ids
                    if w.code == code
                )
                self.assertEqual(hours, 40.0, "%s must keep its own line" % code)
                line = p.get_salary_line_total
                # BASIC prorated exactly like any other absence
                self.assertAlmostEqual(line("BASIC"), 2000.0 * 17 / 22, places=2)
                # ... and nothing paid back
                self.assertAlmostEqual(line("DOVOLENKA_NAHRADA"), 0.0, places=2)
                self.assertAlmostEqual(line("OBSTACLE_NAHRADA"), 0.0, places=2)
                self.assertAlmostEqual(line("PREKAZKA_NAHRADA"), 0.0, places=2)
                self.assertAlmostEqual(line("GROSS"), 2000.0 * 17 / 22, places=2)

    def test_family_leave_is_not_folded_into_ocr(self):
        """The SP filings must tell them apart — rodičovská drives a prerušenie
        poistenia — so they may not share OČR's code."""
        for xmlid, code in (
            ("l10n_sk_leave_type_materska", "MATERSKA"),
            ("l10n_sk_leave_type_rodicovska", "RODICOVSKA"),
            ("l10n_sk_leave_type_otcovska", "OTCOVSKA"),
        ):
            ltype = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
            self.assertEqual(ltype.l10n_sk_payroll_code, code)
            self.assertFalse(ltype.requires_allocation)

    # ------------------------------------------------------------------
    # Further statutory absences riding existing payroll codes
    # ------------------------------------------------------------------
    def test_further_absences_use_the_right_bucket(self):
        """Each new type carries an EXISTING code, so the money is whatever
        that bucket already pays. The separate type is for recording."""
        for xmlid, code in (
            ("l10n_sk_leave_type_darovanie_krvi", "OBSTACLE"),
            ("l10n_sk_leave_type_vzdelavanie", "OBSTACLE"),
            ("l10n_sk_leave_type_vzdelavanie_unpaid", "NEPLATENE"),
            ("l10n_sk_leave_type_karantena", "PN"),
        ):
            with self.subTest(xmlid=xmlid):
                ltype = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
                self.assertEqual(ltype.l10n_sk_payroll_code, code)
                self.assertFalse(ltype.requires_allocation)

    def test_blood_donation_is_paid_at_average_earnings(self):
        """§ 138 is a paid obstacle, so it must reach OBSTACLE_NAHRADA and
        leave GROSS whole — the same treatment as a doctor's visit."""
        contract, employee, _cal = self._abs_setup()
        self._seed_prior_quarter(contract, employee)
        self._make_leave(
            employee, "l10n_sk_leave_type_darovanie_krvi",
            date(2026, 6, 8), date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total
        self.assertAlmostEqual(line("BASIC"), 2000.0 * 17 / 22, places=2)
        # 40 h x PHZ 13.6364 (the seed runs at 2400) = 545.46
        self.assertGreater(line("OBSTACLE_NAHRADA"), 0.0)
        self.assertAlmostEqual(
            line("GROSS"), line("BASIC") + line("OBSTACLE_NAHRADA"), places=2)

    def test_unpaid_study_leave_pays_nothing(self):
        """§ 140 leaves paid study leave to the employer, so the unpaid
        variant must prorate the wage and add nothing back."""
        contract, employee, _cal = self._abs_setup()
        self._make_leave(
            employee, "l10n_sk_leave_type_vzdelavanie_unpaid",
            date(2026, 6, 8), date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        line = p.get_salary_line_total
        self.assertAlmostEqual(line("BASIC"), 2000.0 * 17 / 22, places=2)
        self.assertAlmostEqual(line("OBSTACLE_NAHRADA"), 0.0, places=2)
        self.assertAlmostEqual(line("GROSS"), line("BASIC"), places=2)

    def test_quarantine_is_paid_as_a_sickness(self):
        """Karanténa carries the PN code, so it drives the employer sick-pay
        náhrada exactly as a DPN does."""
        contract, employee, _cal = self._abs_setup()
        self._make_leave(
            employee, "l10n_sk_leave_type_karantena",
            date(2026, 6, 8), date(2026, 6, 12),
        )
        p = self._worked_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30),
            inputs=[("PN_DVZ", 50.0)],
        )
        pn_days = sum(
            abs(w.number_of_days) for w in p.worked_days_line_ids
            if w.code == "PN"
        )
        self.assertAlmostEqual(pn_days, 5.0, places=2)
        self.assertGreater(p.get_salary_line_total("SICK_COMP"), 0.0)

    def test_general_interest_absences_ride_the_obstacle_bucket(self):
        """§§ 136-138 are paid at priemerný zárobok, so they carry OBSTACLE.
        The separate types exist because the legal reason differs and an
        employer has to record which it was."""
        for xmlid in ("l10n_sk_leave_type_verejna_funkcia",
                      "l10n_sk_leave_type_obcianska_povinnost",
                      "l10n_sk_leave_type_darovanie_krvi"):
            with self.subTest(xmlid=xmlid):
                ltype = self.env.ref("l10n_sk_hr_payroll_oca." + xmlid)
                self.assertEqual(ltype.l10n_sk_payroll_code, "OBSTACLE")
                self.assertFalse(ltype.requires_allocation)
