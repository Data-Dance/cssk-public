# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from copy import deepcopy
from datetime import date
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from ..models.allocation import CHANNELS, allocate as allocate_raw


def statutory(rows):
    # Independent test fixtures, never runtime defaults.
    rates = {'np_ee': '1.4', 'np_er': '1.4', 'sp_ee': '4', 'sp_er': '14',
             'ip_ee': '3', 'ip_er': '3', 'pvn_ee': '1', 'pvn_er': '.5',
             'pvn_er_no_shorttime': '1', 'up_er': '.8', 'gp_er': '.25',
             'rfs_er': '4.75', 'pfp_er': '.5'}
    return {row['month']: {'oop': '200' if row['month'].startswith('2026') else '300',
                           'maximum': '16764' if row['month'].startswith('2026') else '17820',
                           'rates': dict(rates)} for row in rows}


def allocate(amount, start, end, settled, rows):
    return allocate_raw(amount, start, end, settled, rows, statutory(rows))


def ledger(months=('2027-01', '2027-02', '2027-03'), raw='200', oop='300'):
    rows = []
    for month in months:
        ceiling = '16764' if month.startswith('2026') else '17820'
        funds = {code: {'insured': False, 'raw_before': '0', 'base_before': '0',
                        'oop': '0', 'cap': None, 'paid_at_cap': False} for code in CHANNELS}
        for code in ('sp_ee', 'sp_er', 'rfs_er'):
            funds[code] = {'insured': True, 'raw_before': raw,
                           'base_before': str(max(0, float(raw)-float(oop))),
                           'oop': oop, 'cap': ceiling, 'paid_at_cap': False}
        for code in ('up_er', 'gp_er'):
            funds[code] = {'insured': True, 'raw_before': raw, 'base_before': raw,
                           'oop': '0', 'cap': None if code == 'up_er' else ceiling, 'paid_at_cap': False}
        rows.append({'month': month, 'funds': funds})
    return rows


@tagged('post_install', '-at_install')
class TestAllocation(TransactionCase):
    def calc(self, amount='400', rows=None, start=date(2027, 1, 1), end=date(2027, 3, 31)):
        return allocate(amount, start, end, date(2027, 4, 10), ledger() if rows is None else rows)

    def test_oop_is_not_claimed_a_second_time(self):
        result = self.calc()
        for code in ('sp_ee', 'sp_er', 'rfs_er'):
            self.assertEqual(result['funds'][code]['additional_base'], '99.99')
            self.assertEqual([row['additional_base'] for row in result['funds'][code]['rows']], ['33.33']*3)
        self.assertEqual(result['funds']['up_er']['additional_base'], '399.99')
        self.assertEqual(result['funds']['np_ee']['additional_base'], '0.00')

    def test_equal_share_is_not_cent_balanced_into_the_last_month(self):
        result = self.calc('1000', ledger(raw='1000', oop='0'))
        self.assertEqual([row['additional_base'] for row in result['funds']['sp_ee']['rows']], ['333.33']*3)
        self.assertEqual(result['funds']['sp_ee']['additional_base'], '999.99')
        self.assertEqual(result['gross'], '1000')

    def test_fully_capped_month_excluded_but_near_cap_excess_not_redistributed(self):
        rows = ledger(raw='1000', oop='0')
        rows[0]['funds']['sp_ee'].update(raw_before='17820', base_before='17820', paid_at_cap=True)
        rows[1]['funds']['sp_ee'].update(raw_before='17800', base_before='17800')
        result = self.calc('300', rows)['funds']['sp_ee']
        self.assertEqual(result['eligible_months'], 2)
        self.assertEqual([row['additional_base'] for row in result['rows']], ['0.00', '20.00', '150.00'])
        self.assertEqual(self.calc('300', rows)['funds']['sp_er']['additional_base'], '300.00')

    def test_previous_insurance_year_not_settlement_year(self):
        result = self.calc(rows=ledger(tuple(f'2026-{m:02d}' for m in range(1, 13)), oop='200'), start=date(2025, 2, 1), end=date(2026, 12, 20))
        self.assertEqual(result['last_insurance_year'], 2026)
        self.assertEqual([row['month'] for row in result['funds']['sp_ee']['rows']], [f'2026-{m:02d}' for m in range(1, 13)])

    def test_missing_and_duplicate_months_rejected(self):
        for rows in (ledger()[:2], [ledger()[0]]*3):
            with self.assertRaises(ValueError): self.calc(rows=rows)

    def test_missing_fund_and_inconsistent_history_rejected(self):
        rows = ledger()
        del rows[0]['funds']['ip_er']
        with self.assertRaises(ValueError): self.calc(rows=rows)
        rows = ledger()
        rows[0]['funds']['sp_ee']['base_before'] = '200'
        with self.assertRaises(ValueError): self.calc(rows=rows)

    def test_oop_cannot_reduce_accident_and_accident_cannot_be_capped(self):
        rows = ledger()
        rows[0]['funds']['up_er']['oop'] = '300'
        with self.assertRaises(ValueError): self.calc(rows=rows)
        rows = ledger()
        rows[0]['funds']['up_er']['cap'] = '17820'
        with self.assertRaises(ValueError): self.calc(rows=rows)

    def test_invalid_amounts_and_settlement_dates_rejected(self):
        for amount in ('-1', 'NaN', 'Infinity', '0', '1.001', True):
            with self.assertRaises(ValueError): self.calc(amount)
        with self.assertRaises(ValueError):
            allocate('100', date(2027, 1, 1), date(2027, 3, 31), date(2027, 3, 31), ledger())

    def test_repeated_additions_preserve_exact_history_and_cumulative_deduction(self):
        rows = ledger()
        totals = []
        for _index in range(3):
            result = self.calc('400', rows)
            totals.append(result['funds']['sp_ee']['additional_base'])
            for channel in CHANNELS:
                for source, calculated in zip(rows, result['funds'][channel]['rows']):
                    source['funds'][channel].update(raw_before=calculated['raw_after'],
                                                   base_before=calculated['base_after'])
        self.assertEqual(totals, ['99.99', '399.99', '400.02'])
        self.assertEqual([row['base_after'] for row in result['funds']['sp_ee']['rows']], ['300.00']*3)

    def test_all_fund_channels_and_uninsured_month_are_explicit(self):
        rows = ledger(raw='1000', oop='0')
        for row in rows:
            for code in CHANNELS:
                row['funds'][code] = {'insured': True, 'raw_before': '1000', 'base_before': '1000',
                                      'oop': '0', 'cap': None if code == 'up_er' else '17820', 'paid_at_cap': False}
        rows[0]['funds']['np_ee'].update(insured=False, raw_before='0', base_before='0')
        result = self.calc('300', rows)
        self.assertEqual(result['funds']['np_ee']['eligible_months'], 2)
        self.assertEqual([row['additional_base'] for row in result['funds']['np_ee']['rows']], ['0.00', '150.00', '150.00'])
        for code in CHANNELS:
            self.assertEqual(result['funds'][code]['additional_base'], '300.00')

    def test_ceiling_payment_is_a_fact_not_inferred_from_computed_base(self):
        rows = ledger(raw='1000', oop='0')
        rows[0]['funds']['sp_ee'].update(raw_before='17820', base_before='17820')
        self.assertEqual(self.calc('300', rows)['funds']['sp_ee']['additional_base'], '200.00')
        rows[0]['funds']['sp_ee']['paid_at_cap'] = True
        self.assertEqual(self.calc('300', rows)['funds']['sp_ee']['additional_base'], '300.00')

    def test_nominal_oop_and_ceiling_match_the_historical_year(self):
        rows = ledger(('2026-11', '2026-12'), oop='300')
        with self.assertRaises(ValueError):
            self.calc(rows=rows, start=date(2026, 11, 1), end=date(2026, 12, 31))
        rows = ledger()
        rows[0]['funds']['sp_ee']['oop'] = '200'
        with self.assertRaises(ValueError): self.calc(rows=rows)
        rows = ledger()
        rows[0]['funds']['sp_ee']['cap'] = '20000'
        with self.assertRaises(ValueError): self.calc(rows=rows)
        result = allocate('100', date(2027, 1, 1), date(2027, 3, 31), date(2028, 1, 1), ledger())
        self.assertEqual(result['settled_on'], '2028-01-01')

    def test_non_euro_register_is_rejected(self):
        rec = self.record()
        rec.company_id.currency_id = self.env.ref('base.USD')
        with self.assertRaises(UserError): rec.action_calculate()

    def record(self):
        company = self.env['res.company'].create({'name': 'Allocation SYNTHETIC', 'country_id': self.env.ref('base.sk').id,
                                                   'currency_id': self.env.ref('base.EUR').id})
        self.env.user.company_ids |= company
        employee = self.env['hr.employee'].with_company(company).create({'name': 'Synthetic allocation worker', 'company_id': company.id})
        return self.env['l10n.sk.income.allocation'].with_company(company).create({
            'name': 'Synthetic late income', 'employee_id': employee.id, 'icpv': '100000000001',
            'insurance_start': '2027-01-01', 'insurance_end': '2027-03-31', 'settled_on': '2027-04-10',
            'amount': 400, 'evidence': 'Synthetic termination and additional-income decision',
            'history_evidence': 'Synthetic reviewed monthly insurance and ceiling ledger', 'ledger': ledger()})

    def test_odoo_calculation_is_idempotent_and_not_posted_payroll(self):
        rec = self.record()
        rec.action_calculate()
        before = deepcopy(rec.result)
        attachment = rec.calculation_attachment_id
        rec.action_calculate()
        self.assertEqual(rec.result, before)
        self.assertEqual(rec.calculation_attachment_id, attachment)
        self.assertEqual(len(rec.line_ids), 36)
        self.assertEqual(rec.result['funds']['sp_ee']['additional_base'], '99.99')
        self.assertFalse(rec.result['payroll_posted'])
        self.assertFalse(rec.result['premiums_calculated'])
        self.assertEqual(rec.result['icpv'], '100000000001')

    def test_source_edit_requires_explicit_reset(self):
        rec = self.record()
        rec.action_calculate()
        with self.assertRaises(UserError): rec.amount = 500
        with self.assertRaises(UserError): rec.unlink()
        with self.assertRaises(UserError): rec.line_ids[:1].additional_base = 999
        attachment = rec.calculation_attachment_id
        rec.action_reset()
        self.assertTrue(attachment.exists())
        self.assertFalse(rec.line_ids)
        rec.amount = 500
        rec.action_calculate()
        self.assertEqual(rec.result['gross'], '500.0')

    def test_fake_result_and_missing_evidence_rejected(self):
        rec = self.record()
        with self.assertRaises(UserError): rec.result = {'scope': 'pretend'}
        rec.history_evidence = ' '
        with self.assertRaises(UserError): rec.action_calculate()

    def test_cross_company_execution_rejected(self):
        rec = self.record()
        other = self.env['res.company'].create({'name': 'Other synthetic scope'})
        self.env.user.company_ids |= other
        with self.assertRaises(UserError):
            rec.with_context(allowed_company_ids=other.ids).action_calculate()

    def test_payroll_operator_can_calculate_and_reset_generated_rows(self):
        rec = self.record()
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic payroll allocation operator',
            'login': 'allocation.operator@example.invalid',
            'company_id': rec.company_id.id, 'company_ids': [(6, 0, rec.company_id.ids)],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id,
                                  self.env.ref('payroll.group_payroll_user').id])]})
        operator_rec = rec.with_user(user).with_company(rec.company_id)
        operator_rec.action_calculate()
        self.assertEqual(len(operator_rec.line_ids), 36)
        operator_rec.action_reset()
        self.assertFalse(operator_rec.line_ids)
        self.assertEqual(operator_rec.state, 'draft')
