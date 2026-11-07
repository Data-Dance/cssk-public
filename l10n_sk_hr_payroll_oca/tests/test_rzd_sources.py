# Copyright 2026 Projekt Firma SRO
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Annual source isolation; no banking or tax-authority transport."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRzdSources(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic RZD source company'})
        cls.other = cls.env['res.company'].create({'name': 'Synthetic other RZD company'})
        cls.env.user.company_ids |= cls.company | cls.other
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Synthetic RZD employee', 'company_id': cls.company.id})
        cls.rec = cls.env['l10n.sk.tax.reconciliation'].create({
            'employee_id': cls.employee.id, 'company_id': cls.company.id, 'year': 2026})

    def source(self, state='done', company=None, start='2026-06-01', end='2026-06-30'):
        # Selection metadata only, not a claim of actual payroll posting.
        return self.env['hr.payslip'].create({
            'name': 'Synthetic annual source', 'company_id': (company or self.company).id,
            'employee_id': self.employee.id, 'date_from': start, 'date_to': end, 'state': state})

    def test_only_confirmed_own_company_sources_are_selected(self):
        wanted = self.source()
        for state in ('draft', 'verify', 'cancel'):
            self.source(state=state)
        self.source(company=self.other)
        self.assertEqual(self.rec._l10n_sk_year_payslips(), wanted)

    def test_target_is_excluded_even_when_confirmed(self):
        wanted, target = self.source(), self.source()
        self.rec.settlement_payslip_id = target
        self.assertEqual(self.rec._l10n_sk_year_payslips(), wanted)

    def test_period_end_assigns_a_cross_year_payslip_once(self):
        wanted = self.source(start='2025-12-15', end='2026-01-14')
        self.source(start='2026-12-15', end='2027-01-14')
        self.source(start='2025-11-01', end='2025-11-30')
        self.assertEqual(self.rec._l10n_sk_year_payslips(), wanted)

    def test_foreign_or_unconfirmed_lines_do_not_enter_annual_totals(self):
        rule = self.env.ref('l10n_sk_hr_payroll_oca.l10n_sk_income_tax_employee')
        for state, company, total in (('done', self.company, -19),
                                       ('verify', self.company, -99), ('done', self.other, -88)):
            slip = self.source(state=state, company=company)
            self.env['hr.payslip.line'].create({
                'slip_id': slip.id, 'employee_id': self.employee.id, 'salary_rule_id': rule.id,
                'contract_id': self.employee.version_id.id,
                'name': 'Synthetic withheld tax', 'code': 'INCOMETAX',
                'category_id': rule.category_id.id, 'amount': total, 'quantity': 1, 'rate': 100})
        self.rec.action_compute()
        self.assertAlmostEqual(self.rec.annual_advance_tax, 19)
