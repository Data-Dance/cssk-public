# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Assessment BASES under 461/2003 §139b; no premium/tax/posting inference.

The caller supplies reviewed historical insurance, unreduced bases, deductions
and effective fund ceilings. No pension type implies eligibility here. All
channels are explicit, including uninsured ones and the employee/employer
split needed for concurrent-employment exceptions.
"""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from fractions import Fraction

CHANNELS = ('np_ee', 'np_er', 'sp_ee', 'sp_er', 'ip_ee', 'ip_er',
            'pvn_ee', 'pvn_er', 'up_er', 'gp_er', 'rfs_er', 'pfp_er')
OOP_CHANNELS = frozenset(('sp_ee', 'sp_er', 'ip_ee', 'ip_er', 'rfs_er'))
CENT = Decimal('.01')


def decimal(value):
    if isinstance(value, bool):
        raise ValueError('A monetary value cannot be a boolean.')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError('Invalid decimal value.') from exc
    if not result.is_finite() or result < 0:
        raise ValueError('Values must be finite and nonnegative.')
    return result


def floor_cent(value):
    return value.quantize(CENT, rounding=ROUND_DOWN)


def rational(value):
    if isinstance(value, str) and '/' in value:
        try:
            result = Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError('Invalid historical exact fraction.') from exc
        if result < 0:
            raise ValueError('Historical unreduced bases must be nonnegative.')
        return result
    return Fraction(decimal(value))


def floor_fraction(value):
    return Decimal(value.numerator * 100 // value.denominator) / 100


def months(start, end):
    start = max(start, date(end.year, 1, 1)).replace(day=1)
    result = []
    while start <= end:
        result.append(start.strftime('%Y-%m'))
        start = date(start.year + start.month // 12, start.month % 12 + 1, 1)
    return result


def allocate(amount, start, end, settled_on, ledger):
    """Equal exact shares per eligible insurance month, then floor BASES.

    Full-cap months are excluded independently per channel (§139b(2)). A
    near-cap month keeps its equal share; excess is not redistributed.
    The residual cent of the gross is NOT assigned to the last month.
    Actual pay date is deliberately not an input to the legal classification.
    """
    amount = decimal(amount)
    if not amount or amount != floor_cent(amount):
        raise ValueError('Provide a positive cent-denominated gross amount.')
    if not all(isinstance(day, date) for day in (start, end, settled_on)):
        raise ValueError('Provide insurance and settlement dates.')
    if start > end or settled_on <= end:
        raise ValueError('Settlement must follow the end of the insurance relationship.')
    if settled_on.year != 2027 or end.year not in (2026, 2027):
        raise ValueError('This reviewed rule vintage covers 2027 settlement and the 2026/2027 last insurance year.')
    expected = months(start, end)
    if not isinstance(ledger, list) or len(ledger) != len(expected):
        raise ValueError('The complete last insurance year must be covered explicitly.')
    sources = {}
    for row in ledger:
        if not isinstance(row, dict) or row.get('month') not in expected or row['month'] in sources:
            raise ValueError('Unexpected or duplicate insurance month.')
        funds = row.get('funds')
        if not isinstance(funds, dict) or set(funds) != set(CHANNELS):
            raise ValueError('Every employee/employer fund channel must be supplied explicitly.')
        sources[row['month']] = funds
    result = {'version': 1, 'scope': 'assessment_bases_only',
              'gross': str(amount), 'insurance_start': start.isoformat(),
              'insurance_end': end.isoformat(), 'settled_on': settled_on.isoformat(),
              'last_insurance_year': end.year, 'funds': {}}
    with localcontext() as context:
        context.prec = 48
        for channel in CHANNELS:
            values = {}
            eligible = []
            for month in expected:
                source = sources[month][channel]
                keys = {'insured', 'raw_before', 'base_before', 'oop', 'cap', 'paid_at_cap'}
                if (not isinstance(source, dict) or set(source) != keys
                        or type(source['insured']) is not bool or type(source['paid_at_cap']) is not bool):
                    raise ValueError('Invalid or incomplete historical fund facts.')
                raw = rational(source['raw_before'])
                base, oop = (decimal(source[key]) for key in ('base_before', 'oop'))
                cap = None if source['cap'] is None else decimal(source['cap'])
                nominal_oop = {2026: Decimal(200), 2027: Decimal(300)}[end.year]
                maximum = {2026: Decimal(16764), 2027: Decimal(17820)}[end.year]
                if oop not in (Decimal(0), nominal_oop):
                    raise ValueError('Supply zero or the nominal claimed agreement OOP for the historical year, not the deduction used up by the original income.')
                if cap is not None and (cap != floor_cent(cap) or cap > maximum):
                    raise ValueError('The reviewed effective fund ceiling exceeds the statutory year maximum or is not cent-rounded.')
                if channel not in OOP_CHANNELS and oop:
                    raise ValueError('Agreement OOP cannot reduce this insurance fund.')
                if channel == 'up_er' and cap is not None:
                    raise ValueError('Accident insurance must remain uncapped.')
                if source['insured'] and channel != 'up_er' and (cap is None or not cap):
                    raise ValueError('Supply the reviewed effective ceiling for this fund.')
                if not source['insured']:
                    if raw or base or oop or source['paid_at_cap']:
                        raise ValueError('An uninsured channel must have zero historical bases/deduction.')
                else:
                    old = max(Fraction(0), raw - Fraction(oop))
                    if cap is not None:
                        old = min(old, Fraction(cap))
                    if floor_fraction(old) != base:
                        raise ValueError('The historical base does not reconcile with gross/OOP/ceiling.')
                    if source['paid_at_cap'] and (cap is None or base != floor_cent(cap)):
                        raise ValueError('Payment at the ceiling must reconcile with the reviewed historical base.')
                    if not source['paid_at_cap']:
                        eligible.append(month)
                values[month] = (source['insured'], raw, base, oop, cap)
            share = Fraction(amount) / len(eligible) if eligible else Fraction(0)
            rows = []
            for month in expected:
                insured, raw, before, oop, cap = values[month]
                assigned = share if month in eligible else Fraction(0)
                after = before
                if assigned:
                    after = max(Fraction(0), Fraction(raw) + assigned - Fraction(oop))
                    if cap is not None:
                        after = min(after, Fraction(cap))
                    after = floor_fraction(after)
                rows.append({'month': month, 'insured': insured,
                             'excluded_at_cap': bool(insured and month not in eligible),
                             'exact_share': str(assigned), 'raw_before': str(raw),
                             'raw_after': str(raw + assigned), 'base_before': f'{before:.2f}',
                             'base_after': f'{after:.2f}', 'additional_base': f'{after-before:.2f}'})
            result['funds'][channel] = {
                'eligible_months': len(eligible), 'rows': rows,
                'additional_base': f"{sum((Decimal(row['additional_base']) for row in rows), Decimal(0)):.2f}",
                'unallocated_gross_when_no_eligible_month': str(amount if not eligible else Decimal(0)),
            }
    return result
