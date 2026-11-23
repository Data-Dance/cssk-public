# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Roční zúčtování on the OCA engine: the 50 / 100 Kč minimums, previous
employers' Potvrzení, the uniqueness rule and the post-to-payslip button."""
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCzAnnualReconRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "CZ Recon Rules Co", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary"
        )

    def _slip(self, employee, month, done=True):
        d_from = date(2026, month, 1)
        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Slip %s/2026" % month,
            "employee_id": employee.id,
            "contract_id": employee.version_id.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": d_from,
            "date_to": d_from + relativedelta(day=31),
        })
        if done:
            slip.compute_sheet()
            slip.write({"state": "done"})
        return slip

    def _recon_employee(self):
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "Rocni Zuctovani Pravidla",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": 50000.0,
            "struct_id": self.structure.id,
        })
        employee.version_id.write({"l10n_cz_tax_declaration": True})
        for m in range(1, 13):
            self._slip(employee, m)
        return employee

    def _recon_draft_march(self, employee):
        return self._slip(employee, 3, done=False)

    # -- roční zúčtování: statutory minimums, previous employers, posting ---

    def _recon_year(self, **recon_vals):
        employee = self._recon_employee()
        recon = self.env["hr.payroll.cz.annual.tax.recon"].create(dict({
            "employee_id": employee.id,
            "company_id": self.company.id,
            "year": 2026,
        }, **recon_vals))
        recon.action_compute()
        return employee, recon

    def test_refund_of_50_kc_or_less_is_not_paid(self):
        """§ 38ch odst. 5 / § 35d odst. 8 ZDP: the přeplatek is paid only
        when MORE than 50 Kč. 300 Kč of pension contributions -> 45 Kč
        refund, not paid; 400 Kč -> 60 Kč, paid."""
        _emp, recon = self._recon_year(l10n_cz_pension_contrib=300.0)
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 45.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 0.0, 2)
        recon.l10n_cz_pension_contrib = 400.0
        recon.action_compute()
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 60.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 60.0, 2)

    def test_previous_employer_potvrzeni_is_included(self):
        """§ 38ch odst. 4: income and advances from the previous employers'
        Potvrzení count as if paid here. +100 000 income, +16 000 advances:
        base 700 000, tax 105 000 - 30 840 = 74 160; advances 59 160 +
        16 000 = 75 160 -> refund 1 000."""
        _emp, recon = self._recon_year(
            l10n_cz_prev_income=100000.0, l10n_cz_prev_advances=16000.0)
        self.assertAlmostEqual(recon.l10n_cz_annual_gross_base, 700000.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_advances_withheld, 75160.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 1000.0, 2)

    def test_one_reconciliation_per_employee_and_year(self):
        """The uniqueness rule was a dropped _sql_constraints list on 19.0."""
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        employee, _recon = self._recon_year()
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), \
                self.env.cr.savepoint():
            self.env["hr.payroll.cz.annual.tax.recon"].create({
                "employee_id": employee.id,
                "company_id": self.company.id,
                "year": 2026,
            })
            self.env.flush_all()

    def test_post_settlement_button(self):
        """The form posts onto the payslip chosen on the record; before,
        action_post_to_payslip needed an argument no button could pass."""
        from odoo.exceptions import UserError
        employee, recon = self._recon_year(l10n_cz_pension_contrib=24000.0)
        with self.assertRaises(UserError):
            recon.action_post_settlement()
        march = self._recon_draft_march(employee)
        recon.l10n_cz_settlement_payslip_id = march
        recon.action_post_settlement()
        self.assertEqual(recon.state, "done")
        lines = {line.code: line.total for line in march.line_ids}
        self.assertAlmostEqual(lines["ANNUAL_TAX_SETTLEMENT"], 3600.0, 2)
        arch = self.env["hr.payroll.cz.annual.tax.recon"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="action_post_settlement"', arch)
        self.assertIn('name="l10n_cz_prev_income"', arch)

    # -- the child tax benefit, month by month (§ 35c ZDP) --------------------

    def _child_employee(self):
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "Rodic Zuctovani",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": 50000.0,
            "struct_id": self.structure.id,
        })
        employee.version_id.write({"l10n_cz_tax_declaration": True})
        return employee

    def _child_amount(self, month):
        return self.env["hr.rule.parameter"]._get_parameter_value(
            "l10n_cz_child_1", date(2026, month, 1))

    def _recon_for(self, employee, **recon_vals):
        recon = self.env["hr.payroll.cz.annual.tax.recon"].create(dict({
            "employee_id": employee.id,
            "company_id": self.company.id,
            "year": 2026,
        }, **recon_vals))
        recon.action_compute()
        return recon

    def _low_hours_employee(self, wage, **version_vals):
        """Five hours a week, so that a small wage stays above the hourly
        minimum wage and the § 111 top-up of the surcharge bridge cannot
        fire."""
        calendar = self.env["resource.calendar"].create({
            "name": "CZ 5h/week", "company_id": self.company.id,
            "hours_per_day": 5.0, "full_time_required_hours": 40.0,
            "attendance_ids": [(0, 0, {
                "name": "Monday", "dayofweek": "0", "hour_from": 8.0,
                "hour_to": 13.0, "day_period": "morning"})],
        })
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "Maly Uvazek Zuctovani",
            "company_id": self.company.id,
            "resource_calendar_id": calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": wage,
            "struct_id": self.structure.id,
        })
        if version_vals:
            employee.version_id.write(version_vals)
        return employee

    def _child_employee_one(self):
        employee = self._child_employee()
        employee.version_id.l10n_cz_children_t1 = 1
        return employee

    def test_child_born_in_september_is_claimed_from_september(self):
        """The payslips claim the child from the month of birth, and the
        reconciliation counts those four months, not the whole year."""
        employee = self._child_employee()
        self.env["l10n.cz.employee.child"].create({
            "employee_id": employee.id, "first_name": "Novorozenec",
            "surname": "Zuctovani", "birthday": date(2026, 9, 15),
        })
        slips = {m: self._slip(employee, m) for m in range(1, 13)}
        lines = {m: {line.code: line.total for line in s.line_ids}
                 for m, s in slips.items()}
        self.assertNotIn("CHILDBEN", lines[8])
        self.assertAlmostEqual(lines[9]["CHILDBEN"], self._child_amount(9), 2)
        recon = self._recon_for(employee)
        expected = sum(self._child_amount(m) for m in range(9, 13))
        self.assertAlmostEqual(recon.l10n_cz_annual_child_benefit, expected, 2)
        # Paid monthly in full, so the reconciliation owes nothing for it.
        self.assertAlmostEqual(recon.l10n_cz_bonus_paid, 0.0, 2)

    def test_child_counts_follow_the_version_of_each_month(self):
        """Without child records the counts of the version in force on each
        month's first day decide: a child added on a version from July is
        six months."""
        employee = self._child_employee()
        employee.create_version({
            "date_version": date(2026, 7, 1),
            "l10n_cz_children_t1": 1,
        })
        for m in range(1, 13):
            slip = self._slip(employee, m, done=False)
            slip.contract_id = employee._get_version(date(2026, m, 1))
            slip.compute_sheet()
            slip.write({"state": "done"})
        recon = self._recon_for(employee)
        expected = sum(self._child_amount(m) for m in range(7, 13))
        self.assertAlmostEqual(recon.l10n_cz_annual_child_benefit, expected, 2)

    # -- § 35d odst. 6-8 ZDP: monthly bonuses set off against the tax --------

    def test_monthly_bonuses_paid_reduce_the_overpayment(self):
        """§ 35d odst. 7 ZDP, rows 28-31 of the form 25 5460/1. One child,
        six months at 15 000 (no tax, monthly bonus 1 267 paid) and six at
        60 000 (advance 9 000 - 2 570 - 1 267 = 5 163). Year: base 450 000,
        tax 67 500 - 30 840 - 15 204 = 21 456, no annual bonus. Difference on
        tax 30 978 - 21 456 = 9 522, on the bonus 0 - 7 602: paid 1 920, which
        is the tax of the year less what was really paid in (30 978 - 7 602).
        The two differences used to be floored at zero each: 9 522."""
        employee = self._low_hours_employee(
            15000.0, l10n_cz_tax_declaration=True, l10n_cz_children_t1=1)
        for month in range(1, 13):
            employee.version_id.wage = 15000.0 if month <= 6 else 60000.0
            self._slip(employee, month)
        recon = self._recon_for(employee)
        self.assertAlmostEqual(recon.l10n_cz_annual_gross_base, 450000.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_annual_final_tax, 21456.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_annual_bonus, 0.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_advances_withheld, 30978.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_bonus_paid, 7602.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 1920.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_bonus_doplatek, 0.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 1920.0, 2)

    def test_set_off_of_the_two_differences(self):
        """§ 35d odst. 7 ZDP sentence by sentence: (difference on tax,
        difference on the bonus) -> (overpayment, bonus top-up)."""
        set_off = self.env["hr.payroll.cz.annual.tax.recon"]._l10n_cz_set_off
        # Both positive: each is paid.
        self.assertEqual(set_off(200.0, 300.0), (200.0, 300.0))
        # Bonuses overpaid: they reduce the positive difference on tax ...
        self.assertEqual(set_off(100.0, -60.0), (40.0, 0.0))
        # ... and what they exceed it by is not collected (odst. 8).
        self.assertEqual(set_off(50.0, -80.0), (0.0, 0.0))
        # Bonus owed, tax underpaid: the top-up is reduced by the underpayment.
        self.assertEqual(set_off(-30.0, 100.0), (0.0, 70.0))
        self.assertEqual(set_off(-10.0, -5.0), (0.0, 0.0))

    def test_below_six_minimum_wages_the_monthly_bonuses_are_kept(self):
        """§ 35d odst. 6 ZDP, row 30 of the form ("uveďte 0"): with a year's
        income under six minimum wages (134 400 in 2026) there is no annual
        bonus, but the monthly bonuses paid are kept. Two months at 50 000
        (advance 7 500 - 2 570 - 1 267 = 3 663 each) and 20 000 with 5 000 of
        bonuses from a previous employer: income 120 000, tax 18 000 under the
        taxpayer credit, so the 7 326 of advances come back in full. The
        bonuses paid must not be set off against them."""
        employee = self._child_employee_one()
        for month in (1, 2):
            self._slip(employee, month)
        recon = self._recon_for(
            employee, l10n_cz_prev_income=20000.0,
            l10n_cz_prev_bonus_paid=5000.0)
        self.assertAlmostEqual(recon.l10n_cz_annual_gross_base, 120000.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_annual_bonus, 0.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_bonus_paid, 5000.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 7326.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_bonus_doplatek, 0.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 7326.0, 2)

    def test_annual_bonus_under_100_and_the_50_kc_limit_on_the_sum(self):
        """§ 35c odst. 3 ZDP: an annual bonus under 100 Kč cannot be claimed,
        so monthly bonuses paid are overpaid in full. Income 306 600 from a
        previous employer: tax 45 990 - 30 840 = 15 150, child benefit 15 204,
        bonus 54 -> 0. Advances 1 000, bonuses paid 500: 1 000 - 500 = 500.
        With 960 paid the sum is 40, which § 35d odst. 8 does not pay out
        (only "více než 50 Kč"), although the tax difference alone is 1 000."""
        employee = self._child_employee_one()
        recon = self._recon_for(
            employee, l10n_cz_prev_income=306600.0,
            l10n_cz_prev_advances=1000.0, l10n_cz_prev_bonus_paid=500.0)
        self.assertAlmostEqual(recon.l10n_cz_annual_tax_after_slevy, 15150.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_annual_bonus, 0.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 500.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 500.0, 2)
        recon.l10n_cz_prev_bonus_paid = 960.0
        recon.action_compute()
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 40.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 0.0, 2)

    # -- § 6 odst. 4 ZDP: income taxed by the withholding tax ----------------

    def test_withheld_payslips_stay_out_of_the_reconciliation(self):
        """§ 6 odst. 4 ZDP: income taxed by the withholding tax is a separate
        tax base, and row 1 of the form 25 5460/1 leaves it out. Three months
        at 4 000 without a declaration (600 withheld each), then nine at
        40 000 with one (advance 6 000 - 2 570 = 3 430). Year: base 360 000,
        tax 54 000 - 30 840 = 23 160, advances 30 870, refund 7 710. The
        12 000 used to enter the base while its 1 800 of tax did not count:
        refund 5 910.

        § 38k odst. 7: with the declaration made after the year the withheld
        income enters and its tax counts with the advances: base 372 000, tax
        24 960, advances 32 670."""
        employee = self._low_hours_employee(4000.0)
        for month in range(1, 13):
            if month == 4:
                employee.version_id.write(
                    {"wage": 40000.0, "l10n_cz_tax_declaration": True})
            slip = self._slip(employee, month)
            if month == 1:
                lines = {line.code: line.total for line in slip.line_ids}
                self.assertAlmostEqual(lines["WHTAX"], -600.0, 2)
                self.assertFalse(lines.get("INCOMETAX"))
        recon = self._recon_for(employee)
        self.assertAlmostEqual(recon.l10n_cz_annual_gross_base, 360000.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_annual_final_tax, 23160.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_advances_withheld, 30870.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 7710.0, 2)
        recon.l10n_cz_retro_declaration = True
        recon.action_compute()
        self.assertAlmostEqual(recon.l10n_cz_annual_gross_base, 372000.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_annual_final_tax, 24960.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_advances_withheld, 32670.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 7710.0, 2)

    def test_declaration_made_after_the_year_returns_the_withheld_tax(self):
        """§ 38k odst. 7 ZDP: three months at 4 000, never a declaration
        during the year. Without the later declaration nothing is reconciled;
        with it the income is 12 000, the tax 1 800 falls under the taxpayer
        credit and the 1 800 withheld comes back."""
        employee = self._low_hours_employee(4000.0)
        for month in (1, 2, 3):
            self._slip(employee, month)
        recon = self._recon_for(employee)
        self.assertAlmostEqual(recon.l10n_cz_annual_gross_base, 0.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_advances_withheld, 0.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 0.0, 2)
        recon.l10n_cz_retro_declaration = True
        recon.action_compute()
        self.assertAlmostEqual(recon.l10n_cz_annual_gross_base, 12000.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_advances_withheld, 1800.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_overpayment, 1800.0, 2)
        self.assertAlmostEqual(recon.l10n_cz_settlement_total, 1800.0, 2)
