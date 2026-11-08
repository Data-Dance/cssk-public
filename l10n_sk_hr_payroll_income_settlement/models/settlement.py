# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dated monthly cash remuneration after termination; not a posted payslip.

Social premiums come from the historical register, health from current income,
and tax from the consolidated monthly tax base. Never apply tax bands or NČZD
independently to a second payment in the same month.
"""
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from odoo.addons.l10n_sk_hr_payroll_income_allocation.models.allocation import decimal, floor_cent, CHANNELS

CENT = Decimal('.01')
PENSIONS = {'none', 'old_age', 'early_old_age', 'disability_over_70',
            'disability', 'disability_at_age', 'service_at_age', 'disability_service'}
FACT_KEYS = {'paid_on', 'agreement', 'pension', 'disabled', 'minimum_exception',
             'tax_declaration', 'pension_at_jan1', 'no_child_bonus',
             'no_other_adjustments', 'other_tax_base', 'other_tax_withheld',
             'other_health_base', 'other_health_employee', 'other_health_employer',
             'other_health_topup', 'only_2y_health_day'}
PARAM_CODES = ('l10n_sk_health_min_base', 'l10n_sk_health_rate_employee',
               'l10n_sk_health_rate_employer', 'l10n_sk_nczd_monthly',
               'l10n_sk_income_tax_bands')


def money(value):
    number = decimal(value)
    if number != floor_cent(number):
        raise ValueError('Amounts must be in whole eurocents.')
    return number


def rounded(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def monthly_tax(base, allowance, bands):
    taxable = rounded(max(Decimal(0), base - allowance))
    tax = Decimal(0)
    previous = Decimal(0)
    for rate, ceiling in bands:
        rate, ceiling = decimal(rate), money(ceiling)
        if rate <= 0 or rate > 1 or ceiling <= previous:
            raise ValueError('Tax bands must have increasing ceilings and valid rates.')
        portion = max(Decimal(0), min(taxable, ceiling) - previous)
        tax += portion * rate
        previous = ceiling
    if taxable > previous:
        raise ValueError('The monthly tax base exceeds the reviewed tax bands.')
    return rounded(tax)


def calculate_settlement(social, facts, parameters):
    """Explicitly reviewed facts; standard positive taxable cash payment only.

    This stage supports monthly payroll paid in the next month of the same
    year. Cross-year/late arrears, child bonus, benefits and deductions
    require their own workflow. Pension classification must be reviewed for
    the health period; January pension status is a SEPARATE tax fact.
    """
    if (social.get('scope') != 'assessment_bases_and_standard_social_premiums'
            or not social.get('premiums_calculated')
            or set(social.get('funds', {})) != set(CHANNELS)):
        raise ValueError('Calculate the reviewed historical social premiums first.')
    if not isinstance(facts, dict) or set(facts) != FACT_KEYS:
        raise ValueError('Supply the complete reviewed monthly tax/health facts, without unknown fields.')
    for key in ('disabled', 'tax_declaration', 'pension_at_jan1',
                'no_child_bonus', 'no_other_adjustments', 'only_2y_health_day'):
        if type(facts[key]) is not bool:
            raise ValueError('Review flags must be explicit booleans.')
    if not facts['no_child_bonus'] or not facts['no_other_adjustments'] or not facts['only_2y_health_day']:
        raise ValueError('Child bonuses, other deductions and noncash/exempt benefits need a separate reviewed workflow.')
    if facts['agreement'] not in ('none', 'dopc', 'dovp', 'dobps') or facts['pension'] not in PENSIONS:
        raise ValueError('Review the legal relationship and pension classification.')
    settled = date.fromisoformat(social['settled_on'])
    paid = date.fromisoformat(facts['paid_on'])
    health_date = paid.replace(day=1) - timedelta(days=1)
    if (settled.year != paid.year or settled >= paid
            or health_date.strftime('%Y-%m') != settled.strftime('%Y-%m')
            or health_date.replace(day=1) <= date.fromisoformat(social['insurance_end'])):
        raise ValueError('This workflow requires same-year monthly settlement, payment in the next month, and only the 2Y health day in the reporting month.')
    if set(parameters) != set(PARAM_CODES):
        raise ValueError('Supply all dated statutory parameters.')
    bands = parameters['l10n_sk_income_tax_bands']
    if not bands:
        raise ValueError('Supply dated monthly tax bands.')
    gross = money(social['gross'])
    ee, er = money(social['employee_social']), money(social['employer_social'])
    if (sum((money(social['funds'][key]['premium']) for key in CHANNELS if key.endswith('_ee')), Decimal(0)) != ee
            or sum((money(social['funds'][key]['premium']) for key in CHANNELS if key.endswith('_er')), Decimal(0)) != er):
        raise ValueError('The social fund totals do not reconcile.')
    excluded = (facts['agreement'] == 'dobps' or
                (facts['agreement'] in ('dopc', 'dovp') and facts['pension'] != 'none'))
    exception = facts['minimum_exception']
    if exception not in ('none', 'state_insured', 'multiple_payers_notice', 'disabled'):
        raise ValueError('Review the health-minimum exception and its evidence.')
    if (facts['disabled'] and exception != 'disabled') or (exception == 'disabled' and not facts['disabled']):
        raise ValueError('The disability and health-minimum facts disagree.')
    rate_ee = decimal(parameters['l10n_sk_health_rate_employee'])
    rate_er = decimal(parameters['l10n_sk_health_rate_employer'])
    if not rate_ee or not rate_er or max(rate_ee, rate_er) > 100:
        raise ValueError('Health percentages must be positive and at most 100.')
    if facts['disabled']:
        rate_ee, rate_er = rate_ee / 2, rate_er / 2
    old_base, old_ee, old_er, old_topup = [money(facts[key]) for key in (
        'other_health_base', 'other_health_employee', 'other_health_employer', 'other_health_topup')]
    min_base = money(parameters['l10n_sk_health_min_base'])
    minimum = (floor_cent(min_base * rate_ee / 100)
               + floor_cent(min_base * rate_er / 100))
    # The 2Y relationship exists for ONE calendar day, not the old contract's
    # days or the full settlement month. Exceptions remove its minimum.
    minimum = floor_cent(minimum / monthrange(health_date.year, health_date.month)[1]) if exception == 'none' else Decimal(0)
    if excluded:
        if any((old_base, old_ee, old_er, old_topup)):
            raise ValueError('An excluded agreement cannot use insured health-month totals in this workflow.')
        health_base = health_ee = health_er = topup = Decimal(0)
        minimum = Decimal(0)
    else:
        if (old_ee != floor_cent(old_base * rate_ee / 100)
                or old_er != floor_cent(old_base * rate_er / 100)):
            raise ValueError('The previous health advances do not match the same monthly rate profile.')
        # A previous 2Y payment may already have charged the minimum. Only
        # this contribution's delta is due; it can refund an earlier top-up.
        expected_old_topup = max(Decimal(0), minimum - old_ee - old_er) if old_base else Decimal(0)
        if old_topup != expected_old_topup:
            raise ValueError('The previous minimum top-up does not reconcile.')
        health_base = gross
        health_ee = floor_cent((old_base + gross) * rate_ee / 100) - old_ee
        health_er = floor_cent((old_base + gross) * rate_er / 100) - old_er
        topup = max(Decimal(0), minimum - old_ee - old_er - health_ee - health_er) - old_topup
    allowance = (money(parameters['l10n_sk_nczd_monthly']) if facts['tax_declaration'] and not facts['pension_at_jan1'] else Decimal(0))
    old_tax_base, old_tax = money(facts['other_tax_base']), money(facts['other_tax_withheld'])
    if old_tax != monthly_tax(old_tax_base, allowance, bands):
        raise ValueError('The previous monthly tax does not reconcile; review declaration, tax base and other payments.')
    additional_tax_base = gross - ee - health_ee - topup
    if additional_tax_base < 0:
        raise ValueError('Negative taxable income needs a correction workflow.')
    tax = monthly_tax(old_tax_base + additional_tax_base, allowance, bands) - old_tax
    net = additional_tax_base - tax
    if net < 0:
        raise ValueError('Deductions exceed the cash remuneration.')
    amounts = {'BASIC': gross, 'GROSS': gross, 'HEALTH': -health_ee,
               'HEALTHEMPLOYER': health_er, 'HEALTHDOPLATOK': -topup,
               'TAXBASE': additional_tax_base, 'INCOMETAX': -tax, 'NET': net}
    codes = {'np_ee': 'SICK', 'np_er': 'SICKEMPLOYER', 'sp_ee': 'PENSION',
             'sp_er': 'PENSIONEMPLOYER', 'ip_ee': 'DISABILITY', 'ip_er': 'DISABILITYEMPLOYER',
             'pvn_ee': 'UNEMPLOYMENT', 'pvn_er': 'UNEMPLOYMENTEMPLOYER',
             'up_er': 'ACCIDENT', 'gp_er': 'GUARANTEEEMPLOYER',
             'rfs_er': 'RESERVEFUNDEMPLOYER', 'pfp_er': 'SHORTTIMEEMPLOYER'}
    for key, code in codes.items():
        amounts[code] = money(social['funds'][key]['premium']) * (-1 if key.endswith('_ee') else 1)
    return {'version': 1, 'policy': 'dated-post-income-monthly-cash-v1',
            'scope': 'social_health_tax_settlement_only',
            'tax_month': settled.strftime('%Y-%m'), 'paid_on': str(paid),
            'health_2y_date': None if excluded else str(health_date),
            'health_excluded': excluded, 'health_minimum': f'{minimum:.2f}',
            'nczd_monthly_total': f'{allowance:.2f}',
            'monthly_tax_base_total': f'{old_tax_base + additional_tax_base:.2f}',
            'salary_amounts': {key: f'{value:.2f}' for key, value in amounts.items()},
            'employer_cost': f'{gross + er + health_er:.2f}',
            'payroll_posted': False, 'official_submission': False}
