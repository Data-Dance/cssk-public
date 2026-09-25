# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Asserts the Czech monthly payslip (2026 dated parameters):
#   * GROSS, employee social 7.1 %, employee health 4.5 %
#   * TAXBASE = gross (superhrubá abolished)
#   * 15 % income-tax advance and the taxpayer credit
#   * child tax benefit capped by the tax, and the daňový bonus payout surplus

from datetime import date, datetime, time

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCzPayroll(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "CZ Test Co", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
        cls.env.user.group_ids |= cls.env.ref(
            "hr_holidays.group_hr_holidays_manager"
        )
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary"
        )

    def _employee(self, name, **version_vals):
        # In 19.0 there is no hr.contract model: the "contract" is the
        # employee's working version (hr.version). Create the employee (which
        # auto-creates version_id) with the version fields, then write the
        # remaining Czech attributes on the version.
        date_start = version_vals.pop("date_start", date(2024, 1, 1))
        wage = version_vals.pop("wage", 0.0)
        employee = self.env["hr.employee"].with_company(self.company).create(
            {
                "name": name,
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
                "date_version": date_start,
                "contract_date_start": date_start,
                "wage": wage,
                "struct_id": self.structure.id,
            }
        )
        version = employee.version_id
        if version_vals:
            version.write(version_vals)
        return employee, version

    def _payslip(self, employee, contract):
        payslip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip %s" % employee.name,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 3, 1),
                    "date_to": date(2026, 3, 31),
                }
            )
        )
        payslip.compute_sheet()
        return payslip

    def _payslip_with_inputs(self, employee, contract, inputs):
        payslip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip %s" % employee.name,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 3, 1),
                    "date_to": date(2026, 3, 31),
                    "input_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": i["name"],
                                "code": i["code"],
                                "amount": i["amount"],
                                "contract_id": contract.id,
                            },
                        )
                        for i in inputs
                    ],
                }
            )
        )
        payslip.compute_sheet()
        return payslip

    def _t(self, payslip, code):
        return round(payslip.get_salary_line_total(code), 2)

    def _part_time_calendar(self, hours_per_week):
        """5 equal week-days summing to *hours_per_week* (e.g. 20 -> 4 h/day)."""
        per_day = hours_per_week / 5.0
        return self.env["resource.calendar"].create(
            {
                "name": "CZ Part Time %sh" % hours_per_week,
                "company_id": self.company.id,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Day %s" % d,
                            "dayofweek": str(d),
                            "hour_from": 8.0,
                            "hour_to": 8.0 + per_day,
                            "day_period": "morning",
                        },
                    )
                    for d in range(5)
                ],
            }
        )

    def test_social_discount_part_time(self):
        """20 h/week + category over55, base within 1.5x avg -> 5 % discount."""
        cal = self._part_time_calendar(20)
        emp, con = self._employee(
            "Sleva PT",
            wage=20000.0,
            l10n_cz_tax_declaration=True,
            l10n_cz_social_discount_category="over55",
            resource_calendar_id=cal.id,
        )
        emp.resource_calendar_id = cal.id
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "GROSS"), 20000.0)
        # gross premium unchanged (PVPOJ reads this), discount is a separate line
        self.assertEqual(self._t(p, "SOCIALER"), 4960.0)          # 24.8 %
        self.assertEqual(self._t(p, "SOCIAL_DISCOUNT"), -1000.0)  # -5 % of 20000
        # employer cost reduced: 20000 + 4960 + 1800 - 1000
        self.assertEqual(self._t(p, "EMPLOYERCOST"), 25760.0)

    def test_social_discount_under21_full_time(self):
        """Under-21 is exempt from the 8-30 h/week band -> discount even full-time."""
        emp, con = self._employee(
            "Sleva U21",
            wage=20000.0,
            l10n_cz_tax_declaration=True,
            l10n_cz_social_discount_category="under21",
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "SOCIAL_DISCOUNT"), -1000.0)

    def test_social_discount_full_time_excluded(self):
        """Category set but full-time (40 h/week) and not under 21 -> no discount."""
        emp, con = self._employee(
            "Sleva FT",
            wage=20000.0,
            l10n_cz_tax_declaration=True,
            l10n_cz_social_discount_category="over55",
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "SOCIAL_DISCOUNT"), 0.0)

    def test_social_discount_over_base_cap_excluded(self):
        """Part-time but monthly base above 1.5x avg wage -> no discount."""
        cal = self._part_time_calendar(20)
        emp, con = self._employee(
            "Sleva Cap",
            wage=80000.0,  # > 1.5 * 48967 = 73450.5
            l10n_cz_tax_declaration=True,
            l10n_cz_social_discount_category="over55",
            resource_calendar_id=cal.id,
        )
        emp.resource_calendar_id = cal.id
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "SOCIAL_DISCOUNT"), 0.0)

    def test_standard_employee(self):
        """Wage 50000, declaration signed, no children."""
        emp, con = self._employee(
            "Pavel Novak", wage=50000.0, l10n_cz_tax_declaration=True
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "GROSS"), 50000.0)
        self.assertEqual(self._t(p, "SOCIALEE"), -3550.0)   # 7.1 %
        self.assertEqual(self._t(p, "HEALTHEE"), -2250.0)   # 4.5 %
        self.assertEqual(self._t(p, "TAXBASE"), 50000.0)    # = gross
        self.assertEqual(self._t(p, "INCOMETAX"), -7500.0)  # 15 % of 50000
        self.assertEqual(self._t(p, "TAXCREDIT"), 2570.0)   # sleva na poplatníka
        self.assertEqual(self._t(p, "NET"), 39270.0)

    def test_no_declaration_no_credit(self):
        """Without the signed declaration the tax credit is not applied."""
        emp, con = self._employee(
            "Jana Bezprohlaseni", wage=50000.0, l10n_cz_tax_declaration=False
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "TAXCREDIT"), 0.0)

    def test_dpp_below_threshold_withholding(self):
        """Notified DPP, wage 8000 < 12000 (2026 threshold), no declaration.

        Below the insurance threshold: no social/health insurance, and the income
        is taxed by the 15 % final withholding tax (srážková daň).
        """
        emp, con = self._employee(
            "Karel Dohodar",
            wage=8000.0,
            l10n_cz_agreement_type="dpp",
            l10n_cz_dpp_notified=True,
            l10n_cz_tax_declaration=False,
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "GROSS"), 8000.0)
        self.assertEqual(self._t(p, "SOCIALEE"), 0.0)      # no insurance
        self.assertEqual(self._t(p, "HEALTHEE"), 0.0)
        self.assertEqual(self._t(p, "SOCIALER"), 0.0)
        self.assertEqual(self._t(p, "HEALTHER"), 0.0)
        self.assertEqual(self._t(p, "INCOMETAX"), 0.0)     # replaced by WHTAX
        self.assertEqual(self._t(p, "WHTAX"), -1200.0)     # 15 % of 8000
        self.assertEqual(self._t(p, "NET"), 6800.0)        # 8000 - 1200

    def test_dpc_above_threshold_insured(self):
        """DPČ, wage 10000 >= 4500 threshold, no declaration, not state-insured.

        Above the small-scale threshold: full social + health insurance applies
        (no min-base top-up on a dohoda), taxed by the ordinary advance.
        """
        emp, con = self._employee(
            "Lucie Brigadnice",
            wage=10000.0,
            l10n_cz_agreement_type="dpc",
            l10n_cz_tax_declaration=False,
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "GROSS"), 10000.0)
        self.assertEqual(self._t(p, "SOCIALEE"), -710.0)   # 7.1 %
        self.assertEqual(self._t(p, "HEALTHEE"), -450.0)   # 4.5 %, no top-up
        self.assertEqual(self._t(p, "INCOMETAX"), -1500.0)  # 15 % of 10000
        self.assertEqual(self._t(p, "WHTAX"), 0.0)
        self.assertEqual(self._t(p, "SOCIALER"), 2480.0)   # 24.8 %
        self.assertEqual(self._t(p, "HEALTHER"), 900.0)    # 9 %
        self.assertEqual(self._t(p, "NET"), 7340.0)

    def test_child_bonus_payout(self):
        """Wage 30000, declaration, children 1/1/2 -> benefit exceeds tax -> bonus."""
        emp, con = self._employee(
            "Petr Rodic",
            wage=30000.0,
            l10n_cz_tax_declaration=True,
            l10n_cz_children_t1=1,
            l10n_cz_children_t2=1,
            l10n_cz_children_t3=2,
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "INCOMETAX"), -4500.0)   # 15 % of 30000
        self.assertEqual(self._t(p, "TAXCREDIT"), 2570.0)
        self.assertEqual(self._t(p, "CHILDBEN"), 1930.0)     # capped by tax after credit
        self.assertEqual(self._t(p, "CHILDBONUS"), 5837.0)   # 7767 benefit - 1930

    # -- P3: worked-days proration of BASIC -------------------------------

    def test_basic_proration_half_month(self):
        """Mid-month hire (16 March): BASIC prorated by worked/scheduled time."""
        emp, con = self._employee(
            "Half Mesic", wage=50000.0, date_start=date(2026, 3, 16)
        )
        payslip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip %s" % emp.name,
                    "employee_id": emp.id,
                    "contract_id": con.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 3, 1),
                    "date_to": date(2026, 3, 31),
                }
            )
        )
        # Populate the worked-day lines the way the UI onchange would.
        wd = payslip.get_worked_day_lines(con, date(2026, 3, 1), date(2026, 3, 31))
        payslip.write({"worked_days_line_ids": [(0, 0, line) for line in wd]})
        payslip.compute_sheet()

        scheduled = emp._get_work_days_data_batch(
            datetime(2026, 3, 1),
            datetime(2026, 3, 31, 23, 59, 59),
            calendar=self.calendar,
            compute_leaves=False,
        )[emp.id]["hours"]
        worked = emp._get_work_days_data_batch(
            datetime(2026, 3, 16),
            datetime(2026, 3, 31, 23, 59, 59),
            calendar=self.calendar,
            compute_leaves=False,
        )[emp.id]["hours"]
        self.assertTrue(0 < worked < scheduled)  # genuinely partial month
        expected = round(50000.0 * worked / scheduled, 2)
        self.assertEqual(self._t(payslip, "BASIC"), expected)
        self.assertTrue(0.0 < self._t(payslip, "BASIC") < 50000.0)

    # -- P3: wage garnishment (exekuční srážky) ---------------------------

    def test_garnishment_priority(self):
        """Priority claim capped by 2/3 of the remainder above the 2026
        nezabavitelná částka. Net 39270; neza ceil(14101.5)=14102; zbytek
        25168; thirds_base 25167; third 8389; priority pool 2*8389 = 16778."""
        emp, con = self._employee(
            "Exekuce Prio", wage=50000.0, l10n_cz_tax_declaration=True
        )
        p = self._payslip_with_inputs(
            emp,
            con,
            [{"code": "GARNISHMENT_PREF", "name": "Exekuce", "amount": 20000.0}],
        )
        self.assertEqual(self._t(p, "GARNISHMENT"), -16778.0)
        self.assertEqual(self._t(p, "NET"), 22492.0)  # 39270 - 16778

    def test_garnishment_nonpriority(self):
        """Non-priority claim capped by 1/3 of the remainder (8389)."""
        emp, con = self._employee(
            "Exekuce Neprio", wage=50000.0, l10n_cz_tax_declaration=True
        )
        p = self._payslip_with_inputs(
            emp,
            con,
            [{"code": "GARNISHMENT_NONPREF", "name": "Exekuce", "amount": 20000.0}],
        )
        self.assertEqual(self._t(p, "GARNISHMENT"), -8389.0)
        self.assertEqual(self._t(p, "NET"), 30881.0)  # 39270 - 8389

    def test_garnishment_none_without_input(self):
        """No garnishment input -> no GARNISHMENT line, NET unchanged."""
        emp, con = self._employee(
            "Bez Exekuce", wage=50000.0, l10n_cz_tax_declaration=True
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "GARNISHMENT"), 0.0)
        self.assertEqual(self._t(p, "NET"), 39270.0)

    # -- P3: sickness compensation (náhrada mzdy) -------------------------

    def test_sick_nahrada(self):
        """Náhrada mzdy: PHV 200 (< RH1) reduced to 180; 60% x 180 x 40h = 4320,
        added to NET, outside GROSS/tax/insurance."""
        emp, con = self._employee(
            "Nemocny",
            wage=50000.0,
            l10n_cz_tax_declaration=True,
            l10n_cz_avg_hourly_earnings=200.0,
        )
        p = self._payslip_with_inputs(
            emp,
            con,
            [{"code": "SICK_HOURS", "name": "Nemoc 1.-5. den", "amount": 40.0}],
        )
        self.assertEqual(self._t(p, "SICKNAHRADA"), 4320.0)
        self.assertEqual(self._t(p, "GROSS"), 50000.0)  # sick pay not in gross
        self.assertEqual(self._t(p, "NET"), 43590.0)  # 39270 + 4320

    # -- P3: absence -> payroll (leave-driven) ----------------------------

    def _make_leave(self, employee, xmlid, d_from, d_to):
        """Create a CZ leave; returns the leave record.

        The CZ leave types use ``leave_validation_type='no_validation'``, so in
        19.0 the leave is auto-approved (state ``validate``) on create by
        ``hr.leave.create`` -> ``action_approve`` and no explicit validation
        call is needed.
        """
        lt = self.env.ref("l10n_cz_hr_payroll_oca.%s" % xmlid)
        leave = (
            self.env["hr.leave"]
            .with_company(self.company)
            .create(
                {
                    "name": lt.name,
                    "holiday_status_id": lt.id,
                    "employee_id": employee.id,
                    "request_date_from": d_from,
                    "request_date_to": d_to,
                }
            )
        )
        return leave

    def _payslip_march(self, employee, contract):
        """A March-2026 payslip with worked-day lines populated (incl. leaves)."""
        payslip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip %s" % employee.name,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 3, 1),
                    "date_to": date(2026, 3, 31),
                }
            )
        )
        wd = payslip.get_worked_day_lines(
            contract, date(2026, 3, 1), date(2026, 3, 31)
        )
        payslip.write({"worked_days_line_ids": [(0, 0, line) for line in wd]})
        payslip.compute_sheet()
        return payslip

    def _seed_prior_quarter(self, employee, contract):
        """Seed a done Dec-2025 payslip (rozhodné období for a March slip).

        Returns (phv, counted_basic, worked_hours) computed from the seed so the
        expected průměrný výdělek can be cross-checked exactly.
        """
        seed = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Seed %s" % employee.name,
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2025, 12, 1),
                    "date_to": date(2025, 12, 31),
                }
            )
        )
        wd = seed.get_worked_day_lines(
            contract, date(2025, 12, 1), date(2025, 12, 31)
        )
        seed.write({"worked_days_line_ids": [(0, 0, line) for line in wd]})
        seed.compute_sheet()
        seed.write({"state": "done"})
        counted = seed.get_salary_line_total("BASIC")
        hours = sum(
            line.number_of_hours
            for line in seed.worked_days_line_ids
            if line.code == "WORK100"
        )
        return counted / hours, counted, hours

    def test_holiday_nahrada_from_average_earnings(self):
        """Holiday (dovolená): BASIC prorated down, náhrada added at the computed
        průměrný výdělek (from a seeded prior-quarter payslip), GROSS keeps it."""
        emp, con = self._employee(
            "Dovolenkar", wage=50000.0, l10n_cz_tax_declaration=True
        )
        phv, counted, seed_hours = self._seed_prior_quarter(emp, con)
        self.assertGreater(phv, 134.40)  # above the 2026 hourly minimum floor
        # Holiday Mon 2 - Fri 6 March 2026 (5 working days).
        self._make_leave(emp, "leave_type_cz_holiday", date(2026, 3, 2), date(2026, 3, 6))
        p = self._payslip_march(emp, con)
        holiday_hours = sum(
            abs(line.number_of_hours)
            for line in p.worked_days_line_ids
            if line.code == "CZHOLIDAY"
        )
        self.assertGreater(holiday_hours, 0.0)
        expected_nahrada = round(holiday_hours * phv, 2)
        self.assertEqual(self._t(p, "HOLIDAYNAHRADA"), expected_nahrada)
        # BASIC prorated down by the holiday hours.
        self.assertLess(self._t(p, "BASIC"), 50000.0)
        # Holiday náhrada is insurable + taxable -> inside GROSS.
        self.assertAlmostEqual(
            self._t(p, "GROSS"),
            round(self._t(p, "BASIC") + expected_nahrada, 2),
            2,
        )

    def test_sick_leave_drives_nahrada(self):
        """A sickness leave drives SICKNAHRADA (hours read from the leave line)."""
        emp, con = self._employee(
            "NemocnyLeave",
            wage=50000.0,
            l10n_cz_tax_declaration=True,
            l10n_cz_avg_hourly_earnings=200.0,  # manual PHV override -> reduced 180
        )
        # Sickness Mon 2 - Fri 6 March 2026 (5 working days = 40h at 8h/day).
        self._make_leave(emp, "leave_type_cz_sick", date(2026, 3, 2), date(2026, 3, 6))
        p = self._payslip_march(emp, con)
        sick_hours = sum(
            abs(line.number_of_hours)
            for line in p.worked_days_line_ids
            if line.code == "CZSICK"
        )
        self.assertEqual(sick_hours, 40.0)
        # reduced = min(200,rh1)*0.9 = 180; 0.60 * 180 * 40 = 4320.
        self.assertEqual(self._t(p, "SICKNAHRADA"), 4320.0)
        # Sick absence prorates BASIC down; sick pay stays outside GROSS.
        self.assertLess(self._t(p, "BASIC"), 50000.0)
        self.assertEqual(self._t(p, "GROSS"), self._t(p, "BASIC"))

    def test_unpaid_leave_proration_and_health_topup(self):
        """Unpaid leave prorates BASIC below the minimum health base -> the
        employee bears the 13.5 % min-base top-up."""
        emp, con = self._employee(
            "Neplacene", wage=25000.0, l10n_cz_tax_declaration=False
        )
        # Unpaid Mon 2 - Fri 13 March 2026 (10 working days).
        self._make_leave(emp, "leave_type_cz_unpaid", date(2026, 3, 2), date(2026, 3, 13))
        p = self._payslip_march(emp, con)
        unpaid_hours = sum(
            abs(line.number_of_hours)
            for line in p.worked_days_line_ids
            if line.code == "CZUNPAID"
        )
        self.assertGreater(unpaid_hours, 0.0)
        basic = self._t(p, "BASIC")
        self.assertLess(basic, 25000.0)  # prorated down
        gross = self._t(p, "GROSS")
        self.assertEqual(gross, basic)  # no employer pay for unpaid leave
        self.assertLess(gross, 22400.0)  # below the 2026 min health base
        # Health EE = 4.5% of gross + 13.5% of (22400 - gross) top-up.
        expected_health = -round(
            gross * 0.045 + (22400.0 - gross) * 0.135, 2
        )
        self.assertAlmostEqual(self._t(p, "HEALTHEE"), expected_health, 2)

    def test_full_month_with_leave_types_unchanged(self):
        """A full worked month (leave types installed, no leave taken) is
        identical to the standard payslip."""
        emp, con = self._employee(
            "PlnyMesic", wage=50000.0, l10n_cz_tax_declaration=True
        )
        p = self._payslip_march(emp, con)
        self.assertEqual(self._t(p, "BASIC"), 50000.0)
        self.assertEqual(self._t(p, "GROSS"), 50000.0)
        self.assertEqual(self._t(p, "SOCIALEE"), -3550.0)
        self.assertEqual(self._t(p, "HEALTHEE"), -2250.0)
        self.assertEqual(self._t(p, "NET"), 39270.0)
        self.assertEqual(self._t(p, "HOLIDAYNAHRADA"), 0.0)
        self.assertEqual(self._t(p, "SICKNAHRADA"), 0.0)

    # -- Annual tax reconciliation (roční zúčtování, §38ch/§38ča) ----------

    def _month_slip(self, employee, contract, month):
        d_from = date(2026, month, 1)
        d_to = d_from + relativedelta(day=31)
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Slip %s/2026 %s" % (month, employee.name),
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": d_from,
                    "date_to": d_to,
                }
            )
        )
        slip.compute_sheet()
        slip.write({"state": "done"})
        return slip

    def test_annual_refund_pension_deduction(self):
        """Golden case: wage 50 000, prohlášení, no children, 24 000 §15 pension.

        12 monthly slips: TAXBASE 50 000, INCOMETAX -7 500, TAXCREDIT 2 570 ->
        Σ net advance 59 160. Annual: base 600 000 - 24 000 = 576 000; tax
        86 400; minus poplatník 30 840 = 55 560. Přeplatek 3 600 (= 15 % of
        24 000).
        """
        emp, con = self._employee(
            "Rocni Zuctovani", wage=50000.0, l10n_cz_tax_declaration=True
        )
        for m in range(1, 13):
            self._month_slip(emp, con, m)

        recon = self.env["hr.payroll.cz.annual.tax.recon"].create(
            {
                "employee_id": emp.id,
                "company_id": self.company.id,
                "year": 2026,
                "l10n_cz_pension_contrib": 24000.0,
            }
        )
        recon.action_compute()

        self.assertEqual(recon.l10n_cz_annual_gross_base, 600000.0)
        self.assertEqual(recon.l10n_cz_nontaxable_total, 24000.0)
        self.assertEqual(recon.l10n_cz_annual_tax_base, 576000.0)
        self.assertEqual(recon.l10n_cz_annual_tax, 86400.0)
        self.assertEqual(recon.l10n_cz_annual_slevy, 30840.0)
        self.assertEqual(recon.l10n_cz_annual_final_tax, 55560.0)
        self.assertEqual(recon.l10n_cz_advances_withheld, 59160.0)
        self.assertEqual(recon.l10n_cz_overpayment, 3600.0)
        self.assertEqual(recon.l10n_cz_bonus_doplatek, 0.0)
        self.assertEqual(recon.l10n_cz_settlement_total, 3600.0)

        march = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "March Settlement",
                    "employee_id": emp.id,
                    "contract_id": con.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 3, 1),
                    "date_to": date(2026, 3, 31),
                }
            )
        )
        recon.action_post_to_payslip(march)
        self.assertEqual(self._t(march, "ANNUAL_TAX_SETTLEMENT"), 3600.0)
        # Standard monthly net 39 270 + 3 600 settlement.
        self.assertEqual(self._t(march, "NET"), 42870.0)
        self.assertEqual(recon.state, "done")

    def test_standard_payslip_has_no_settlement_line(self):
        """A monthly payslip without the reconciliation input is unchanged."""
        emp, con = self._employee(
            "Bez Zuctovani", wage=50000.0, l10n_cz_tax_declaration=True
        )
        p = self._payslip(emp, con)
        self.assertEqual(self._t(p, "ANNUAL_TAX_SETTLEMENT"), 0.0)
        self.assertEqual(self._t(p, "NET"), 39270.0)
# -- Multi-company country scoping (config visible only per country) ---

    def test_country_scoping_config(self):
        """CZ salary structure and leave types are country-scoped: a payroll
        user working in a CZ company sees only CZ (and country-global) config,
        never another country's, mirroring the accounting localization."""
        cz = self.env.ref("base.cz")
        sk = self.env.ref("base.sk")
        # Our shipped config carries CZ and is company-global.
        self.assertEqual(self.structure.country_id, cz)
        self.assertFalse(self.structure.company_id)
        leave_cz = self.env.ref("l10n_cz_hr_payroll_oca.leave_type_cz_holiday")
        self.assertEqual(leave_cz.country_id, cz)
        self.assertFalse(leave_cz.company_id)
        # Foreign (SK) config created inline to prove isolation.
        sk_struct = self.env["hr.payroll.structure"].create(
            {"name": "SK Struct", "code": "SKX",
             "country_id": sk.id, "company_id": False}
        )
        sk_leave = self.env["hr.leave.type"].create(
            {"name": "SK Leave", "country_id": sk.id, "company_id": False}
        )
        # A payroll user who works in the CZ company only.
        gfield = "group_ids" if "group_ids" in self.env.user._fields else "groups_id"
        user = self.env["res.users"].create(
            {
                "name": "CZ Scope User",
                "login": "cz_scope_user",
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
        self.assertNotIn(sk_struct, structs)
        leaves = self.env["hr.leave.type"].with_user(user).search([])
        self.assertIn(leave_cz, leaves)
        self.assertNotIn(sk_leave, leaves)
        # An explicit country-filtered search returns only CZ config too.
        cz_only = self.env["hr.payroll.structure"].search(
            ["|", ("country_id", "=", False), ("country_id", "=", cz.id)]
        )
        self.assertIn(self.structure, cz_only)
        self.assertNotIn(sk_struct, cz_only)

    # ------------------------------------------------------------------
    # §§ 207-209 — překážky na straně ZAMĚSTNAVATELE
    # ------------------------------------------------------------------
    def _employer_obstacle_hours(self, payslip, code):
        return sum(
            abs(line.number_of_hours)
            for line in payslip.worked_days_line_ids
            if line.code == code
        )

    def test_employer_obstacle_prostoj_is_paid_at_eighty_percent(self):
        """§ 207 a): prostoj is náhrada at 80 % of průměrný výdělek. Booked as
        the § 199 paid obstacle it would be paid in full — the only way to
        record it before, and a fifth too much."""
        emp, con = self._employee(
            "Prostojar", wage=50000.0, l10n_cz_tax_declaration=True
        )
        phv, _counted, _hours = self._seed_prior_quarter(emp, con)
        self._make_leave(
            emp, "leave_type_cz_employer_prostoj",
            date(2026, 3, 2), date(2026, 3, 6),
        )
        p = self._payslip_march(emp, con)
        hours = self._employer_obstacle_hours(p, "CZPROSTOJ")
        self.assertGreater(hours, 0.0)
        self.assertEqual(
            self._t(p, "PREKAZKANAHRADA"), round(hours * phv * 0.8, 2)
        )
        # and emphatically not the full-rate amount
        self.assertLess(self._t(p, "PREKAZKANAHRADA"), round(hours * phv, 2))

    def test_employer_obstacle_each_reason_has_its_own_rate(self):
        """All four §§ 207-209 reasons in one month, each at its own rate."""
        emp, con = self._employee(
            "Prekazkar", wage=50000.0, l10n_cz_tax_declaration=True
        )
        phv, _counted, _hours = self._seed_prior_quarter(emp, con)
        for xmlid, day in (
            ("leave_type_cz_employer_prostoj", 2),
            ("leave_type_cz_employer_povetrnost", 3),
            ("leave_type_cz_employer_jine", 4),
            ("leave_type_cz_employer_castecna", 5),
        ):
            self._make_leave(emp, xmlid, date(2026, 3, day), date(2026, 3, day))
        p = self._payslip_march(emp, con)
        rates = {
            "CZPROSTOJ": 0.8,
            "CZPOVETRNOST": 0.6,
            "CZJINEPREKAZKY": 1.0,
            "CZCASTECNA": 0.6,
        }
        expected = 0.0
        for code, pct in rates.items():
            hours = self._employer_obstacle_hours(p, code)
            self.assertGreater(hours, 0.0, "%s must keep its own line" % code)
            expected += hours * phv * pct
        self.assertEqual(self._t(p, "PREKAZKANAHRADA"), round(expected, 2))

    def test_employer_obstacle_is_insurable_and_taxable(self):
        """§ 208 is the 100 % reason, so GROSS comes out whole — BASIC is cut by
        the absence hours and the náhrada pays exactly them back."""
        emp, con = self._employee(
            "Jinar", wage=50000.0, l10n_cz_tax_declaration=True
        )
        self._seed_prior_quarter(emp, con)
        self._make_leave(
            emp, "leave_type_cz_employer_jine",
            date(2026, 3, 2), date(2026, 3, 6),
        )
        p = self._payslip_march(emp, con)
        self.assertGreater(self._t(p, "PREKAZKANAHRADA"), 0.0)
        self.assertAlmostEqual(
            self._t(p, "GROSS"),
            round(self._t(p, "BASIC") + self._t(p, "PREKAZKANAHRADA"), 2),
            2,
        )

    def test_employer_obstacle_rates_are_data_not_code(self):
        """The percentages are dated rule parameters: change one and the
        payslip follows, with no edit to a rule body."""
        emp, con = self._employee(
            "Datar", wage=50000.0, l10n_cz_tax_declaration=True
        )
        phv, _counted, _hours = self._seed_prior_quarter(emp, con)
        param = self.env.ref(
            "l10n_cz_hr_payroll_oca.rule_parameter_prekazka_prostoj_pct"
        )
        self.env["hr.rule.parameter.value"].create(
            {
                "rule_parameter_id": param.id,
                "parameter_value": "95",
                "date_from": date(2026, 3, 1),
            }
        )
        self._make_leave(
            emp, "leave_type_cz_employer_prostoj",
            date(2026, 3, 2), date(2026, 3, 6),
        )
        p = self._payslip_march(emp, con)
        hours = self._employer_obstacle_hours(p, "CZPROSTOJ")
        self.assertEqual(
            self._t(p, "PREKAZKANAHRADA"), round(hours * phv * 0.95, 2)
        )

    # ------------------------------------------------------------------
    # §§ 195-196 — mateřská / rodičovská / otcovská
    # ------------------------------------------------------------------
    def test_family_leave_is_unpaid_by_the_employer(self):
        """PPM / rodičovský příspěvek / otcovská are dávky of ČSSZ: the employer
        records the absence, prorates BASIC down and pays nothing."""
        for xmlid, code in (
            ("leave_type_cz_materska", "CZMATERSKA"),
            ("leave_type_cz_rodicovska", "CZRODICOVSKA"),
            ("leave_type_cz_otcovska", "CZOTCOVSKA"),
        ):
            with self.subTest(code=code):
                emp, con = self._employee(
                    "Rodic %s" % code, wage=50000.0,
                    l10n_cz_tax_declaration=True,
                )
                self._make_leave(emp, xmlid, date(2026, 3, 2), date(2026, 3, 6))
                p = self._payslip_march(emp, con)
                hours = sum(
                    abs(line.number_of_hours)
                    for line in p.worked_days_line_ids
                    if line.code == code
                )
                self.assertGreater(hours, 0.0, "%s must keep its own line" % code)
                self.assertLess(self._t(p, "BASIC"), 50000.0)
                self.assertAlmostEqual(self._t(p, "HOLIDAYNAHRADA"), 0.0, 2)
                self.assertAlmostEqual(self._t(p, "PREKAZKANAHRADA"), 0.0, 2)
                self.assertAlmostEqual(
                    self._t(p, "GROSS"), self._t(p, "BASIC"), places=2
                )

    def test_general_interest_absences_ride_the_obstacle_bucket(self):
        """§§ 201-203 are paid at průměrný výdělek, so they carry CZOBSTACLE.
        Dárcovství krve is here because the Slovak § 138 counterpart was added
        first and the two must not drift apart."""
        for xmlid in ("leave_type_cz_darovani_krve",
                      "leave_type_cz_verejna_funkce",
                      "leave_type_cz_obecny_zajem"):
            with self.subTest(xmlid=xmlid):
                ltype = self.env.ref("l10n_cz_hr_payroll_oca." + xmlid)
                self.assertEqual(ltype.l10n_cz_payroll_code, "CZOBSTACLE")
                self.assertFalse(ltype.requires_allocation)

    def test_blood_donation_is_paid_at_average_earnings(self):
        """§ 203: paid, so it must reach OBSTACLENAHRADA and keep GROSS whole."""
        emp, con = self._employee(
            "Darce", wage=50000.0, l10n_cz_tax_declaration=True)
        self._seed_prior_quarter(emp, con)
        self._make_leave(emp, "leave_type_cz_darovani_krve",
                         date(2026, 3, 2), date(2026, 3, 3))
        p = self._payslip_march(emp, con)
        self.assertGreater(self._t(p, "OBSTACLENAHRADA"), 0.0)
        self.assertLess(self._t(p, "BASIC"), 50000.0)
        self.assertAlmostEqual(
            self._t(p, "GROSS"),
            round(self._t(p, "BASIC") + self._t(p, "OBSTACLENAHRADA"), 2), 2)

    def test_cz_absence_set_matches_the_slovak_one(self):
        """Study leave and quarantine went into the Slovak module first. The
        two countries must not drift apart on absences that exist in both
        labour codes — the blood-donation gap was exactly this, one day
        earlier."""
        for xmlid, code in (
            ("leave_type_cz_vzdelavani", "CZOBSTACLE"),
            ("leave_type_cz_vzdelavani_unpaid", "CZUNPAID"),
            ("leave_type_cz_karantena", "CZSICK"),
        ):
            with self.subTest(xmlid=xmlid):
                ltype = self.env.ref("l10n_cz_hr_payroll_oca." + xmlid)
                self.assertEqual(ltype.l10n_cz_payroll_code, code)
                self.assertFalse(ltype.requires_allocation)
