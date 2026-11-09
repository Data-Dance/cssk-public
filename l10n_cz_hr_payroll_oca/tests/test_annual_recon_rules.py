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

    def _recon_for(self, employee):
        recon = self.env["hr.payroll.cz.annual.tax.recon"].create({
            "employee_id": employee.id,
            "company_id": self.company.id,
            "year": 2026,
        })
        recon.action_compute()
        return recon

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
