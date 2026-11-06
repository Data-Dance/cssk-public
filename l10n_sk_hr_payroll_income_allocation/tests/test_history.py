# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, AccessError, ValidationError
from .test_allocation import TestAllocation, ledger


@tagged('post_install', '-at_install')
class TestEditableHistory(TransactionCase):
    def record(self):
        return TestAllocation.record(self)

    def test_ui_history_produces_same_bases_and_premiums_as_api(self):
        rec = self.record()
        source = ledger()
        rec.ledger = False
        rec.action_prepare_history()
        self.assertEqual(len(rec.history_ids), 36)
        with self.assertRaises(UserError): rec.action_calculate()
        sources = {(entry['month'], channel): values for entry in source
                   for channel, values in entry['funds'].items()}
        for row in rec.history_ids:
            values = dict(sources[(row.month.strftime('%Y-%m'), row.channel)])
            cap = values.pop('cap')
            row.write(dict(values, cap=cap or 0, uncapped=cap is None, evidence='SYNTHETIC reviewed payroll and payment'))
        rec.action_calculate()
        self.assertEqual(rec.result['funds']['sp_ee']['additional_base'], '99.99')
        rec.premium_evidence = 'SYNTHETIC standard coverage and rates reviewed'
        rec.action_calculate_standard_premiums()
        self.assertEqual(rec.result['total_social'], '26.88')
        with self.assertRaises(UserError): rec.history_ids[0].raw_before = '123'
        with self.assertRaises(UserError): rec.history_ids[0].unlink()
        with self.assertRaises(UserError): rec.history_ids[0].copy({'month': '2027-04-01'})
        rec.action_reset()
        rec.history_ids[0].evidence = 'SYNTHETIC reviewed correction'

    def test_ui_rows_and_api_ledger_cannot_conflict(self):
        rec = self.record()
        with self.assertRaises(UserError): rec.action_prepare_history()
        rec.ledger = False
        rec.action_prepare_history()
        rec.ledger = ledger()
        with self.assertRaises(UserError): rec.action_calculate()

    def test_dated_parameter_changes_invalidate_calculation(self):
        rec = self.record()
        rec.action_calculate()
        parameter = self.env.ref('l10n_sk_hr_payroll_oca.rule_parameter_social_pension_er')
        self.env['hr.rule.parameter.value'].create({
            'rule_parameter_id': parameter.id, 'date_from': '2027-02-01', 'parameter_value': '20'})
        with self.assertRaises(UserError): rec.action_calculate()

    def test_future_year_uses_dated_native_values_without_vintage_lock(self):
        rec = self.record()
        rec.write({'insurance_start': '2028-01-01', 'insurance_end': '2028-03-31',
                   'settled_on': '2029-02-10', 'amount': 300,
                   'ledger': ledger(('2028-01', '2028-02', '2028-03'), raw='1000', oop='0')})
        Value = self.env['hr.rule.parameter.value']
        for xml_id, value, effective in (
                ('rule_parameter_monthly_taxable_max', '20000', '2028-01-01'),
                ('rule_parameter_dohoda_oop', '500', '2028-01-01'),
                ('rule_parameter_social_pension_er', '20', '2028-02-01')):
            Value.create({'rule_parameter_id': self.env.ref('l10n_sk_hr_payroll_oca.' + xml_id).id,
                          'date_from': effective, 'parameter_value': value})
        rec.action_calculate()
        rec.premium_evidence = 'SYNTHETIC future parameter scenario, not statutory 2028 values'
        rec.action_calculate_standard_premiums()
        self.assertEqual(rec.result['funds']['sp_er']['premium'], '54.00')
        self.assertEqual([row['rate'] for row in rec.result['funds']['sp_er']['rows']], ['14', '20', '20'])
        source = rec._inputs()['statutory']['2028-01']
        self.assertEqual(source['maximum'], '20000')
        self.assertEqual(source['oop'], '500')

    def test_form_exposes_editable_history_not_a_required_json_editor(self):
        rec = self.record()
        arch = rec.get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('editable="bottom"', arch)
        self.assertIn('name="history_ids"', arch)
        self.assertIn('name="action_prepare_history"', arch)
        self.assertFalse(rec._fields['ledger'].required)

    def test_history_operator_access_and_integrity(self):
        rec = self.record()
        rec.ledger = False
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic history operator', 'login': 'history.operator@example.invalid',
            'company_id': rec.company_id.id, 'company_ids': [(6, 0, rec.company_id.ids)],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('hr.group_hr_user').id,
                                  self.env.ref('payroll.group_payroll_user').id])]})
        operated = rec.with_user(user).with_company(rec.company_id)
        operated.action_prepare_history()
        row = operated.history_ids[0]
        row.evidence = 'SYNTHETIC operator review'
        with self.assertRaises(UserError): row.company_id = rec.company_id.id
        with self.assertRaises(ValidationError), self.cr.savepoint(): row.month = '2027-01-02'
        other = self.env['res.company'].create({'name': 'Other SYNTHETIC history company'})
        with self.assertRaises(AccessError): row.with_context(allowed_company_ids=other.ids).read(['raw_before'])
