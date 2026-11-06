# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from copy import deepcopy
from datetime import date
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from ..allocation import allocate, CHANNELS
from ..premiums import calculate_standard_premiums
from . import test_allocation as fixtures

ledger = fixtures.ledger


@tagged('post_install', '-at_install')
class TestPremiums(TransactionCase):
    def bases(self, amount='400', rows=None):
        return allocate(amount, date(2027, 1, 1), date(2027, 3, 31), date(2027, 4, 10),
                        ledger() if rows is None else rows)

    def test_pension_agreement_independently_expected_fund_amounts(self):
        result = calculate_standard_premiums(self.bases())
        expected = {'sp_ee': '3.99', 'sp_er': '13.98', 'rfs_er': '4.74',
                    'up_er': '3.18', 'gp_er': '0.99'}
        for code in CHANNELS:
            self.assertEqual(result['funds'][code]['premium'], expected.get(code, '0.00'))
        self.assertEqual(result['employee_social'], '3.99')
        self.assertEqual(result['employer_social'], '22.89')
        self.assertEqual(result['total_social'], '26.88')
        self.assertFalse(result['payroll_posted'])

    def all_insured(self):
        rows = ledger(raw='1000', oop='0')
        for row in rows:
            for code in CHANNELS:
                row['funds'][code] = {'insured': True, 'raw_before': '1000', 'base_before': '1000',
                                      'oop': '0', 'cap': None if code == 'up_er' else '17820', 'paid_at_cap': False}
        return rows

    def test_ordinary_employment_uses_half_percent_split(self):
        result = calculate_standard_premiums(self.bases('300', self.all_insured()))
        self.assertEqual(result['employee_social'], '28.20')
        self.assertEqual(result['employer_social'], '75.60')
        self.assertEqual(result['funds']['pvn_er']['premium'], '1.50')
        self.assertEqual(result['funds']['pfp_er']['premium'], '1.50')

    def test_no_support_fund_uses_full_employer_unemployment_rate(self):
        rows = self.all_insured()
        for row in rows:
            for code in ('up_er', 'gp_er', 'pfp_er'):
                row['funds'][code].update(insured=False, raw_before='0', base_before='0')
        result = calculate_standard_premiums(self.bases('300', rows))
        self.assertEqual(result['employee_social'], '28.20')
        self.assertEqual(result['employer_social'], '72.45')
        self.assertEqual(result['funds']['pvn_er']['premium'], '3.00')

    def test_round_monthly_premiums_before_summing(self):
        result = calculate_standard_premiums(self.bases('1000', ledger(raw='1000', oop='0')))
        self.assertEqual(result['funds']['sp_er']['premium'], '139.98')
        self.assertEqual([row['premium'] for row in result['funds']['sp_er']['rows']], ['46.66']*3)
        self.assertEqual(result['funds']['up_er']['premium'], '7.98')

    def test_premium_calculation_does_not_mutate_assessment_evidence(self):
        bases = self.bases()
        saved = deepcopy(bases)
        result = calculate_standard_premiums(bases)
        self.assertEqual(bases, saved)
        self.assertTrue(result['premiums_calculated'])
        with self.assertRaises(ValueError): calculate_standard_premiums(result)

    def test_changed_month_aggregate_is_rejected(self):
        bases = self.bases()
        bases['funds']['sp_ee']['additional_base'] = '100.00'
        with self.assertRaises(ValueError): calculate_standard_premiums(bases)

    def test_odoo_review_archive_and_retry_are_idempotent(self):
        rec = fixtures.TestAllocation.record(self)
        with self.assertRaises(UserError): rec.action_calculate_standard_premiums()
        rec.action_calculate()
        with self.assertRaises(UserError): rec.action_calculate_standard_premiums()
        base_attachment = rec.calculation_attachment_id
        rec.premium_evidence = 'SYNTHETIC reviewed historical coverage; standard rates; no relief'
        rec.action_calculate_standard_premiums()
        self.assertEqual(rec.state, 'premiums')
        self.assertEqual(rec.result['total_social'], '26.88')
        self.assertAlmostEqual(sum(rec.line_ids.filtered(lambda line: line.channel.endswith('_ee')).mapped('premium')), 3.99, places=2)
        premium_attachment = rec.premium_attachment_id
        saved = deepcopy(rec.result)
        rec.action_calculate_standard_premiums()
        rec.action_calculate()
        self.assertEqual(rec.result, saved)
        self.assertEqual(rec.calculation_attachment_id, base_attachment)
        self.assertEqual(rec.premium_attachment_id, premium_attachment)
        with self.assertRaises(UserError): rec.premium_evidence = 'other'
        rec.action_reset()
        self.assertFalse(rec.premium_attachment_id)
        self.assertTrue(base_attachment.exists())
        self.assertTrue(premium_attachment.exists())

    def test_payroll_user_can_calculate_standard_premiums(self):
        rec = fixtures.TestAllocation.record(self)
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic social premium operator', 'login': 'premium.operator@example.invalid',
            'company_id': rec.company_id.id, 'company_ids': [(6, 0, rec.company_id.ids)],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('hr.group_hr_user').id,
                                  self.env.ref('payroll.group_payroll_user').id])]})
        rec = rec.with_user(user).with_company(rec.company_id)
        rec.action_calculate()
        rec.premium_evidence = 'SYNTHETIC standard coverage/rates and no relief reviewed'
        rec.action_calculate_standard_premiums()
        self.assertEqual(rec.result['total_social'], '26.88')
        self.assertTrue(rec.premium_attachment_id)
        rec.action_reset()
        self.assertFalse(rec.premium_evidence)
