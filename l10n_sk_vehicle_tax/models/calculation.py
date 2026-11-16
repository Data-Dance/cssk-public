# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""361/2014 sections5–8,10,12: monthly liability, rate segments, floor cents.

Dates and vehicle classification are reviewed documentary facts. This engine
does not infer registration, taxpayer status, actual payments or submission.
The caller supplies a dated statutory schedule, never an undated fallback.
"""
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_DOWN

CENT = Decimal('.01')
PROPULSIONS = {'combustion', 'lpg', 'hybrid', 'cng', 'lng', 'hydrogen', 'electric'}
SCHEDULE_KEYS = {'valid_from', 'valid_to', 'car_bands', 'n1_bands', 'age_bands',
    'eco_percent', 'payment_threshold', 'quarterly_threshold', 'monthly_threshold'}


def number(value):
    if isinstance(value, bool):
        raise ValueError('A tax measurement or amount cannot be a boolean.')
    try:
        result = Decimal(str(value))
    except (ValueError, InvalidOperation, TypeError) as error:
        raise ValueError('Supply a valid tax measurement or amount.') from error
    if not result.is_finite() or result < 0:
        raise ValueError('Tax measurements and amounts must be finite and nonnegative.')
    return result


def floor_cent(value):
    return value.quantize(CENT, rounding=ROUND_DOWN)


def cents(value):
    result = number(value)
    if result != floor_cent(result):
        raise ValueError('Supply monetary amounts in whole eurocents.')
    return result


def band(value, rows):
    """Upper bound inclusive; a final unbounded band is explicit data."""
    if not isinstance(rows, list) or not rows:
        raise ValueError('Supply the statutory bands for this vehicle.')
    previous = Decimal(-1)
    selected = None
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError('Invalid statutory rate band.')
        ceiling, amount = row
        amount = number(amount)
        if ceiling is None:
            if index != len(rows)-1:
                raise ValueError('An unbounded statutory band must be last.')
        else:
            ceiling = number(ceiling)
            if ceiling <= previous:
                raise ValueError('Statutory band ceilings must increase.')
            previous = ceiling
        if selected is None and (ceiling is None or value <= ceiling):
            selected = amount
    if selected is None:
        raise ValueError('The measurement exceeds the reviewed statutory bands.')
    return selected


def validate_schedule(schedule, year):
    if not isinstance(schedule, dict) or set(schedule) != SCHEDULE_KEYS:
        raise ValueError('Supply the complete dated vehicle-tax schedule.')
    first = date.fromisoformat(schedule['valid_from'])
    last = date.fromisoformat(schedule['valid_to']) if schedule['valid_to'] else None
    if first > date(year, 1, 1) or (last and last < date(year, 12, 31)):
        raise ValueError('This statutory schedule does not cover the entire tax year.')
    if not (number(schedule['payment_threshold']) < number(schedule['quarterly_threshold'])
            < number(schedule['monthly_threshold'])):
        raise ValueError('Review the dated payment and advance thresholds.')
    if number(schedule['eco_percent']) > 100:
        raise ValueError('Invalid statutory ecological reduction.')


def calculate_vehicle(*, year, category, first_registered, liability_from,
        liability_to, propulsion, engine_cm3, power_kw, weight_kg, schedule, allow_empty_year=False):
    """L/M1/N1 ordinary month-based liability on the post2025 schedule.

    Liability dates are the actual REVIEWED tax obligation, not necessarily
    the invoice or first-business-trip dates. A transfer between taxpayers
    can shift the first month under section8(5). No mileage/PHL/VAT percentage
    belongs in the vehicle-tax calculation.
    """
    if type(year) is not int or not 1 <= year <= 9999:
        raise ValueError('Supply a valid calendar tax year.')
    validate_schedule(schedule, year)
    if category not in {'L', 'M1', 'N1'} or propulsion not in PROPULSIONS:
        raise ValueError('Review an L, M1 or N1 vehicle and its documented propulsion.')
    if (not isinstance(first_registered, date) or not isinstance(liability_from, date)
            or (liability_to is not None and not isinstance(liability_to, date))):
        raise ValueError('Use the first and last calendar days of the reviewed liability months.')
    if liability_to and liability_to < liability_from:
        raise ValueError('Liability dates must reconcile with first registration and their order.')
    liability_from = liability_from.replace(day=1)
    liability_to = liability_to.replace(day=monthrange(liability_to.year, liability_to.month)[1]) if liability_to else None
    first_month = first_registered.replace(day=1)
    if liability_from < first_month or (liability_to and liability_to < liability_from):
        raise ValueError('Liability dates must reconcile with first registration and their order.')
    start = max(liability_from, date(year, 1, 1))
    end = min(liability_to or date(year, 12, 31), date(year, 12, 31))
    if start > end and not allow_empty_year:
        raise ValueError('This vehicle has no reviewed taxable month in the return year.')
    cm3, kw, kg = map(number, (engine_cm3, power_kw, weight_kg))
    if category == 'N1' and not 0 < kg <= 3500:
        raise ValueError('An N1 vehicle requires its documented maximum permissible mass.')
    electric = propulsion == 'electric'
    if electric:
        if not kw:
            raise ValueError('An electric vehicle requires its documented motor power.')
        annual = Decimal(0)
    elif category in {'L', 'M1'}:
        if not cm3:
            raise ValueError('An L or M1 combustion/hybrid vehicle requires documented cylinder capacity.')
        annual = cents(band(cm3, schedule['car_bands']))
    else:
        if not kg:
            raise ValueError('An N1 vehicle requires its documented maximum permissible mass.')
        annual = cents(band(kg, schedule['n1_bands']))
    if start > end:
        return {'policy': 'sk-vehicle-tax-monthly-segments-v1', 'year': year,
            'category': category, 'propulsion': propulsion, 'annual_base': f'{annual:.2f}',
            'liability_from': str(liability_from), 'liability_to': str(liability_to) if liability_to else None,
            'segments': [], 'tax': '0.00', 'actual_payment': False, 'actual_submission': False}
    groups = []
    for month in range(start.month, end.month+1):
        age = (year-first_registered.year)*12 + month-first_registered.month+1
        increase = Decimal(0) if electric else band(Decimal(age), schedule['age_bands'])
        if increase > 100:
            raise ValueError('Review the statutory vehicle-age increase.')
        adjusted = floor_cent(annual * (1+increase/100))
        eco = number(schedule['eco_percent']) if propulsion in {'hybrid', 'cng', 'lng', 'hydrogen'} else Decimal(0)
        final = floor_cent(adjusted*(1-eco/100))
        if not groups or groups[-1]['increase_percent'] != str(increase):
            groups.append({'increase_percent': str(increase), 'annual_after_age': f'{adjusted:.2f}',
                'annual_final': f'{final:.2f}', 'eco_percent': str(eco), 'months': []})
        groups[-1]['months'].append(f'{year}-{month:02d}')
    total = Decimal(0)
    for group in groups:
        # Floor EACH rate segment, not each monthly share or their unrounded
        # annual sum. FS2026 example5: 416.66+91.66=508.32, not508.33.
        tax = floor_cent(Decimal(group['annual_final'])*len(group['months'])/12)
        group.update(month_count=len(group['months']), tax=f'{tax:.2f}')
        total += tax
    return {'policy': 'sk-vehicle-tax-monthly-segments-v1', 'year': year,
        'category': category, 'propulsion': propulsion, 'annual_base': f'{annual:.2f}',
        'liability_from': str(liability_from), 'liability_to': str(liability_to) if liability_to else None,
        'segments': groups, 'tax': f'{total:.2f}', 'actual_payment': False, 'actual_submission': False}


def settle_return(tax, paid_advances, projected_next_year, schedule):
    tax, advances, projected = map(cents, (tax, paid_advances, projected_next_year))
    difference = tax-advances
    due = difference if difference > number(schedule['payment_threshold']) else Decimal(0)
    refund = max(Decimal(0), -difference)
    if projected > number(schedule['monthly_threshold']):
        frequency, count = 'monthly', 12
    elif projected > number(schedule['quarterly_threshold']):
        frequency, count = 'quarterly', 4
    else:
        frequency, count = 'none', 0
    return {'tax': f'{tax:.2f}', 'paid_advances': f'{advances:.2f}',
        'tax_difference': f'{difference:.2f}', 'amount_to_pay': f'{due:.2f}',
        'overpayment': f'{refund:.2f}', 'projected_next_year': f'{projected:.2f}',
        'next_year_advance_frequency': frequency,
        'next_year_advance_amount': f'{floor_cent(projected/count) if count else Decimal(0):.2f}'}
