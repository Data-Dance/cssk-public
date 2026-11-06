# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Standard 2027 social premiums on each newly assessed fund/month base.

§129 floors EACH premium, not the aggregate. Coverage is reviewed historical
input; this does not decide a person's entitlement, relief or contribution
waiver. It deliberately does not calculate health insurance or income tax.
"""
from copy import deepcopy
from decimal import Decimal
from .allocation import CHANNELS, decimal, floor_cent

def calculate_standard_premiums(bases, statutory):
    if (bases.get('version') != 1 or bases.get('scope') != 'assessment_bases_only'
            or set(bases.get('funds', {})) != set(CHANNELS)):
        raise ValueError('Provide the reviewed assessment-base calculation.')
    result = deepcopy(bases)
    pfp = {row['month']: row for row in result['funds']['pfp_er']['rows']}
    ee = er = Decimal(0)
    months = None
    for channel in CHANNELS:
        fund = result['funds'][channel]
        row_months = [row['month'] for row in fund['rows']]
        if months is None:
            months = row_months
        if row_months != months or len(set(row_months)) != len(row_months):
            raise ValueError('Premium rows must match the historical month ledger.')
        total = Decimal(0)
        for row in fund['rows']:
            base = decimal(row['additional_base'])
            if base != floor_cent(base) or (not row['insured'] and base):
                raise ValueError('A premium needs a reconciled cent-rounded insured base.')
            if row['month'] not in statutory:
                raise ValueError('Supply dated premium rates for every historical month.')
            rates = statutory[row['month']]['rates']
            if set(rates) != set(CHANNELS) | {'pvn_er_no_shorttime'}:
                raise ValueError('Supply the complete dated premium-rate set.')
            rate = decimal(rates[channel])
            if channel == 'pvn_er':
                rate = decimal(rates['pvn_er'] if pfp[row['month']]['insured'] else rates['pvn_er_no_shorttime'])
            if rate > 100:
                raise ValueError('A premium percentage cannot exceed 100.')
            if not row['insured']:
                rate = Decimal(0)
            amount = floor_cent(base * rate / 100)
            row.update(rate=str(rate), premium=f'{amount:.2f}')
            total += amount
        if sum((decimal(row['additional_base']) for row in fund['rows']), Decimal(0)) != decimal(fund['additional_base']):
            raise ValueError('Monthly bases must reconcile to the fund aggregate.')
        fund['premium'] = f'{total:.2f}'
        if channel.endswith('_ee'):
            ee += total
        else:
            er += total
    result.update(scope='assessment_bases_and_standard_social_premiums',
                  premium_policy='dated-standard-no-relief-v2',
                  employee_social=f'{ee:.2f}', employer_social=f'{er:.2f}',
                  total_social=f'{ee+er:.2f}', premiums_calculated=True,
                  payroll_posted=False, official_submission=False)
    return result
