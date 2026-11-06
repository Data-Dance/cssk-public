# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from copy import deepcopy
from datetime import date
from decimal import Decimal
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, AccessError
from odoo.addons.l10n_sk_hr_payroll_income_allocation.models.allocation import CHANNELS
from odoo.addons.l10n_sk_hr_payroll_income_allocation.tests.test_allocation import ledger, TestAllocation, allocate
from odoo.addons.l10n_sk_hr_payroll_income_allocation.tests.test_premiums import calculate_standard_premiums
from ..models.settlement import calculate_settlement, monthly_tax, PENSIONS

PARAMETERS = {'l10n_sk_health_min_base': 295.22, 'l10n_sk_health_rate_employee': 5,
              'l10n_sk_health_rate_employer': 11, 'l10n_sk_nczd_monthly': 516.64,
              'l10n_sk_income_tax_bands': [[.19, 3808.34], [.25, 5225.39], [.30, 6494.84], [.35, 1000000000]]}


def facts(**updates):
    values = {'paid_on': '2027-05-10', 'agreement': 'none', 'pension': 'none',
              'disabled': False, 'minimum_exception': 'none', 'tax_declaration': False,
              'pension_at_jan1': False, 'no_child_bonus': True, 'no_other_adjustments': True,
              'other_tax_base': '0', 'other_tax_withheld': '0', 'other_health_base': '0',
              'other_health_employee': '0', 'other_health_employer': '0', 'other_health_topup': '0',
              'only_2y_health_day': True}
    values.update(updates)
    return values


def social(amount='300', profile='ordinary'):
    rows = ledger(raw='1000', oop='0')
    if profile in ('ordinary', 'director'):
        for row in rows:
            for key in CHANNELS:
                insured = not (profile == 'director' and key in ('up_er', 'gp_er', 'pfp_er'))
                row['funds'][key] = {'insured': insured, 'raw_before': '1000' if insured else '0',
                                     'base_before': '1000' if insured else '0', 'oop': '0',
                                     'cap': None if key == 'up_er' else '17820', 'paid_at_cap': False}
    elif profile == 'pension':
        rows = ledger()
    return calculate_standard_premiums(allocate(amount, date(2027, 1, 1), date(2027, 3, 31),
                                                date(2027, 4, 10), rows))


@tagged('post_install', '-at_install')
class TestSettlement(TransactionCase):
    def calculate(self, amount='300', profile='ordinary', **updates):
        return calculate_settlement(social(amount, profile), facts(**updates), PARAMETERS)

    def record(self):
        allocation = TestAllocation.record(self)
        allocation.action_calculate()
        allocation.premium_evidence = 'SYNTHETIC standard coverage and absence of relief reviewed'
        allocation.action_calculate_standard_premiums()
        return self.env['l10n.sk.income.settlement'].with_company(allocation.company_id).create({
            'name': 'SYNTHETIC pension agreement settlement', 'allocation_id': allocation.id,
            'facts': facts(agreement='dopc', pension='old_age', pension_at_jan1=True,
                           minimum_exception='state_insured'),
            'evidence': 'SYNTHETIC review of pension award, no tax declaration, no other monthly income'})

    def test_ordinary_employee_complete_gross_to_net(self):
        result = self.calculate()
        amounts = result['salary_amounts']
        for code, value in {'GROSS': '300.00', 'HEALTH': '-15.00', 'HEALTHEMPLOYER': '33.00',
                            'TAXBASE': '256.80', 'INCOMETAX': '-48.79', 'NET': '208.01'}.items():
            self.assertEqual(amounts[code], value)
        self.assertEqual(result['employer_cost'], '408.60')
        self.assertEqual(result['health_2y_date'], '2027-04-30')
        self.assertFalse(result['payroll_posted'])

    def test_director_retains_historical_funds(self):
        result = self.calculate(profile='director')
        self.assertEqual(result['salary_amounts']['NET'], '208.01')
        self.assertEqual(result['employer_cost'], '405.45')
        self.assertEqual(result['salary_amounts']['ACCIDENT'], '0.00')
        self.assertEqual(result['salary_amounts']['UNEMPLOYMENTEMPLOYER'], '3.00')

    def test_pensioner_agreement_health_excluded_but_taxed(self):
        result = self.calculate('400', 'pension', agreement='dopc', pension='old_age',
                                pension_at_jan1=True, minimum_exception='state_insured')
        self.assertTrue(result['health_excluded'])
        self.assertIsNone(result['health_2y_date'])
        self.assertEqual(result['salary_amounts']['TAXBASE'], '396.01')
        self.assertEqual(result['salary_amounts']['INCOMETAX'], '-75.24')
        self.assertEqual(result['salary_amounts']['NET'], '320.77')
        self.assertEqual(result['employer_cost'], '422.89')

    def test_all_seven_pensions_exclude_agreements_not_employment(self):
        for pension in PENSIONS - {'none'}:
            for agreement in ('dopc', 'dovp'):
                with self.subTest(pension=pension, agreement=agreement):
                    result = self.calculate(agreement=agreement, pension=pension, minimum_exception='state_insured')
                    self.assertEqual(result['salary_amounts']['HEALTH'], '0.00')
            ordinary = self.calculate(pension=pension, minimum_exception='state_insured')
            self.assertFalse(ordinary['health_excluded'])
            self.assertEqual(ordinary['salary_amounts']['HEALTH'], '-15.00')
        self.assertTrue(self.calculate(agreement='dobps', minimum_exception='state_insured')['health_excluded'])

    def test_declaration_and_january_pension_are_independent_reviewed_facts(self):
        self.assertEqual(self.calculate(tax_declaration=True)['salary_amounts']['NET'], '256.80')
        pension = self.calculate(tax_declaration=True, pension_at_jan1=True)
        self.assertEqual(pension['nczd_monthly_total'], '0.00')
        self.assertEqual(pension['salary_amounts']['NET'], '208.01')

    def test_another_monthly_payment_uses_remaining_band_not_new_low_band(self):
        result = self.calculate(other_tax_base='4000', other_tax_withheld='771.50')
        self.assertEqual(result['monthly_tax_base_total'], '4256.80')
        self.assertEqual(result['salary_amounts']['INCOMETAX'], '-64.20')
        self.assertEqual(result['salary_amounts']['NET'], '192.60')

    def test_nczd_is_not_claimed_twice(self):
        result = self.calculate(tax_declaration=True, other_tax_base='500', other_tax_withheld='0')
        self.assertEqual(result['salary_amounts']['INCOMETAX'], '-45.63')
        self.assertEqual(result['nczd_monthly_total'], '516.64')

    def test_health_minimum_one_day_not_full_month(self):
        result = self.calculate('2')
        self.assertEqual(result['health_minimum'], '1.57')
        self.assertEqual(result['salary_amounts']['HEALTHDOPLATOK'], '-1.25')
        self.assertEqual(result['salary_amounts']['NET'], '0.45')
        with self.assertRaises(ValueError): self.calculate('1')

    def test_disabled_and_state_insured_minimum_exceptions(self):
        disabled = self.calculate(disabled=True, minimum_exception='disabled')
        self.assertEqual(disabled['salary_amounts']['HEALTH'], '-7.50')
        self.assertEqual(disabled['salary_amounts']['HEALTHEMPLOYER'], '16.50')
        self.assertEqual(disabled['health_minimum'], '0.00')
        self.assertEqual(self.calculate(minimum_exception='state_insured')['health_minimum'], '0.00')
        with self.assertRaises(ValueError): self.calculate(disabled=True)

    def test_previous_health_rounding_is_consolidated_and_topup_can_be_refunded(self):
        result = self.calculate('10', other_health_base='2', other_health_employee='.10',
                                other_health_employer='.22', other_health_topup='1.25',
                                other_tax_base='.56', other_tax_withheld='.11')
        self.assertEqual(result['salary_amounts']['HEALTHDOPLATOK'], '1.25')
        self.assertEqual(result['salary_amounts']['HEALTH'], '-0.50')

    def test_tax_rounds_half_up_and_crosses_all_bands(self):
        bands = PARAMETERS['l10n_sk_income_tax_bands']
        self.assertEqual(monthly_tax(Decimal('1.50'), Decimal(0), bands), Decimal('.29'))
        self.assertEqual(monthly_tax(Decimal('7000'), Decimal(0), bands), Decimal('1635.49'))

    def test_wrong_dates_missing_facts_and_other_adjustments_block(self):
        for updates in ({'paid_on': '2027-04-20'}, {'paid_on': '2027-06-10'},
                        {'paid_on': '2028-05-10'}, {'no_child_bonus': False},
                        {'no_other_adjustments': False}, {'tax_declaration': 'false'},
                        {'pension': 'unknown'}, {'other_tax_withheld': '10'},
                        {'other_health_employee': '1'}):
            with self.subTest(updates=updates), self.assertRaises(ValueError): self.calculate(**updates)
        missing = facts()
        del missing['other_tax_base']
        with self.assertRaises(ValueError): calculate_settlement(social(), missing, PARAMETERS)

    def test_mutated_fund_totals_block_and_parameters_are_supplied(self):
        source = social()
        source['employee_social'] = '20'
        with self.assertRaises(ValueError): calculate_settlement(source, facts(), PARAMETERS)
        values = deepcopy(PARAMETERS)
        values['l10n_sk_nczd_monthly'] = 600
        result = calculate_settlement(social(), facts(tax_declaration=True), values)
        self.assertEqual(result['nczd_monthly_total'], '600.00')

    def test_odoo_archive_retry_and_dependency_reset(self):
        rec = self.record()
        rec.action_calculate()
        saved, attachment = deepcopy(rec.result), rec.attachment_id
        rec.action_calculate()
        self.assertEqual(rec.result, saved)
        self.assertEqual(rec.attachment_id, attachment)
        self.assertEqual(saved['salary_amounts']['NET'], '320.77')
        with self.assertRaises(UserError): rec.facts = facts()
        with self.assertRaises(UserError): rec.result = saved
        with self.assertRaises(UserError): rec.allocation_id.action_reset()
        rec.action_reset()
        rec.allocation_id.action_reset()
        self.assertTrue(attachment.exists())

    def test_dated_parameter_change_invalidates_retry(self):
        rec = self.record()
        rec.action_calculate()
        parameter = self.env['hr.rule.parameter'].search([('code', '=', 'l10n_sk_nczd_monthly')])
        self.env['hr.rule.parameter.value'].create({
            'rule_parameter_id': parameter.id, 'date_from': '2027-04-01', 'parameter_value': '600'})
        with self.assertRaises(UserError): rec.action_calculate()

    def test_editable_form_fields_produce_same_result_as_api_facts(self):
        rec = self.record()
        values = dict(rec.facts)
        rec.write(dict(values, facts=False))
        rec.action_calculate()
        self.assertEqual(rec.result['salary_amounts']['NET'], '320.77')
        arch = rec.get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('name="paid_on"', arch)
        self.assertFalse(rec._fields['facts'].required)

    def test_mixed_form_and_api_facts_are_rejected(self):
        rec = self.record()
        rec.paid_on = '2027-05-10'
        with self.assertRaises(UserError): rec.action_calculate()

    def test_payroll_operator_can_calculate_but_not_forge_result(self):
        rec = self.record()
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic settlement operator', 'login': 'settlement.operator@example.invalid',
            'company_id': rec.company_id.id, 'company_ids': [(6, 0, rec.company_id.ids)],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('hr.group_hr_user').id,
                                  self.env.ref('payroll.group_payroll_user').id])]})
        operated = rec.with_user(user).with_company(rec.company_id)
        operated.action_calculate()
        self.assertEqual(operated.result['salary_amounts']['NET'], '320.77')
        with self.assertRaises(UserError): operated.write({'state': 'draft'})
        other = self.env['res.company'].create({'name': 'Other SYNTHETIC settlement company'})
        with self.assertRaises(AccessError): rec.with_user(user).with_context(allowed_company_ids=other.ids).read(['facts'])
