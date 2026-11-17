# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Annual source isolation; no banking or tax-authority transport."""
from datetime import date
from unittest.mock import patch

from odoo.exceptions import UserError
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
            'name': 'Synthetic RZD employee', 'company_id': cls.company.id,
            'date_version': '2025-01-01', 'contract_date_start': '2025-01-01'})
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

    def _ended_employee_with_january_fact(self, pension=False):
        employee = self.env['hr.employee'].create({
            'name': 'Synthetic former employee with annual tax fact',
            'company_id': self.company.id, 'date_version': '2025-01-01',
            'contract_date_start': '2025-01-01',
            'contract_date_end': '2025-12-31'})
        employee.create_version({
            'date_version': '2026-01-01',
            'contract_date_start': '2025-01-01',
            'contract_date_end': '2025-12-31',
            'l10n_sk_tax_pensioner': pension,
            'l10n_sk_pension_type': 'old_age' if pension else False,
            'l10n_sk_nczd_pension_annual': 6000 if pension else 0})
        return employee, employee._get_version(date(2026, 1, 1))

    def _manual_annual(self, employee):
        return self.env['l10n.sk.tax.reconciliation'].create({
            'employee_id': employee.id, 'company_id': self.company.id,
            'year': 2026, 'gather_from_payslips': False,
            'annual_tax_base': 10000, 'annual_advance_tax': 2000})

    def test_default_january_reader_preserves_active_declaration(self):
        expected = self.employee._l10n_sk_january_tax_version(
            2026, self.company, date(2026, 12, 31))
        self.assertEqual(self.rec._l10n_sk_annual_january_tax_version(), expected)
        self.rec.write({'gather_from_payslips': False,
                        'annual_tax_base': 10000, 'annual_advance_tax': 2000})
        self.rec.action_compute()
        self.assertAlmostEqual(self.rec.nczd_taxpayer, 5966.73)
        self.assertAlmostEqual(self.rec.annual_tax, 766.32)
        self.assertAlmostEqual(self.rec.result_amount, 1233.68)

    def test_default_january_reader_still_refuses_ended_employment(self):
        employee, version = self._ended_employee_with_january_fact(pension=True)
        rec = self._manual_annual(employee)
        # The existing pension default fallback remains available in draft;
        # it does not make the ended employment an accepted annual source.
        self.assertEqual(rec.pension_annual, 6000)
        with self.assertRaises(UserError):
            rec._l10n_sk_annual_january_tax_version()
        with self.assertRaises(UserError):
            rec.action_compute()
        self.assertEqual(rec.state, 'draft')
        self.assertEqual(version.contract_date_end, date(2025, 12, 31))

    def _compute_with_reviewed_january_fact(self, pension):
        employee, version = self._ended_employee_with_january_fact(pension)
        original = type(self.rec)._l10n_sk_annual_january_tax_version

        def reviewed_fact(rec):
            if rec.employee_id != employee:
                return original(rec)
            self.assertEqual(rec.company_id, version.company_id)
            self.assertEqual(rec.year, version.date_version.year)
            self.assertEqual(version.date_version, date(rec.year, 1, 1))
            self.assertEqual(version.contract_date_start, date(2025, 1, 1))
            self.assertEqual(version.contract_date_end, date(2025, 12, 31))
            return version

        with patch.object(type(self.rec), '_l10n_sk_annual_january_tax_version',
                          reviewed_fact):
            rec = self._manual_annual(employee)
            self.assertEqual(rec.pension_annual, 6000 if pension else 0)
            rec.action_compute()
        self.assertEqual(rec.state, 'computed')
        self.assertEqual(version.contract_date_end, date(2025, 12, 31))
        self.assertEqual(employee.version_ids.mapped('contract_date_start'),
                         [date(2025, 1, 1)] * 2)
        return rec

    def test_reviewed_annual_fact_computes_without_reopening_employment(self):
        rec = self._compute_with_reviewed_january_fact(pension=False)
        self.assertAlmostEqual(rec.nczd_taxpayer, 5966.73)
        self.assertAlmostEqual(rec.taxable_base, 4033.27)
        self.assertAlmostEqual(rec.annual_tax, 766.32)
        self.assertAlmostEqual(rec.result_amount, 1233.68)

    def test_reviewed_annual_fact_also_supplies_the_pension_default(self):
        rec = self._compute_with_reviewed_january_fact(pension=True)
        self.assertEqual(rec.nczd_taxpayer, 0)
        self.assertEqual(rec.taxable_base, 10000)
        self.assertEqual(rec.annual_tax, 1900)
        self.assertEqual(rec.result_amount, 100)

    def test_annual_fact_extension_cannot_skip_company_check(self):
        employee = self.env['hr.employee'].create({
            'name': 'Synthetic other company January fact',
            'company_id': self.other.id, 'date_version': '2025-01-01',
            'contract_date_start': '2025-01-01'})
        rec = self.rec
        rec.write({'gather_from_payslips': False,
                   'annual_tax_base': 10000, 'annual_advance_tax': 2000})
        with patch.object(type(rec), '_l10n_sk_annual_january_tax_version',
                          return_value=employee.version_id):
            with self.assertRaises(UserError):
                rec.action_compute()
        self.assertEqual(rec.state, 'draft')

    def test_annual_fact_extension_retains_pension_consistency_check(self):
        employee, version = self._ended_employee_with_january_fact(pension=True)
        with patch.object(type(self.rec), '_l10n_sk_annual_january_tax_version',
                          return_value=version):
            rec = self._manual_annual(employee)
            rec.pension_annual = 0
            with self.assertRaises(UserError):
                rec.action_compute()
        self.assertEqual(rec.state, 'draft')
