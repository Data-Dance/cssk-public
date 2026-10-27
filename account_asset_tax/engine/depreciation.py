"""Pure-Python tax-depreciation engine for the Czech and Slovak income-tax acts.

This module has **no Odoo dependency** on purpose: it takes primitive inputs
(an entry value, an in-service date, a depreciation class and a method) and
returns a list of :class:`ScheduleLine` objects. That makes the statutory maths
unit-testable in isolation and reusable from either the Enterprise
(``account_asset``) or the OCA (``account_asset_management``) bridge, which only
differ in *where* they read the entry value / start date from.

Verified against the 2026 consolidated texts (see ``docs/`` and the project
research memory):

* CZ — zákon 586/1992 Sb. §31 (rovnoměrné), §32 (zrychlené), §30a (mimořádné).
  First year gets the **full** table rate regardless of in-service month; the
  method is immutable per asset; disposal year allows only half the annual
  charge (handled by the caller, not here).
* SK — zákon 595/2003 Z.z. §27 (rovnomerné), §28 (zrýchlené). First year is
  **prorated by whole months** from the month of putting into use; the unclaimed
  first-year remainder is deducted in the year *after* the end of the
  depreciation period. Accelerated subsequent years use a residual computed as
  if the **full** (un-prorated) first-year charge had been taken (§28(2)).

The engine deliberately computes the *clean* schedule (no interruptions / no
technical improvements). Those lifecycle events re-invoke the engine from an
event date with an adjusted entry value / residual and a starting year offset;
that orchestration lives in the Odoo layer.
"""

import math
from dataclasses import dataclass, field
from datetime import date

# Country codes used throughout the stack.
CZ = "CZ"
SK = "SK"

# Method keys (also the selection values on ``account.asset`` in the bridges).
METHOD_LINEAR = "linear"            # CZ rovnoměrné / SK rovnomerné
METHOD_ACCELERATED = "accelerated"  # CZ zrychlené / SK zrýchlené
METHOD_EXTRAORDINARY = "extraordinary"  # CZ §30a only

# Rounding:
# * CZ — every odpis is rounded UP to whole koruny: § 31 odst. 9 (rovnoměrné),
#   § 32 odst. 5 (zrychlené), § 30a odst. 2 (mimořádné) zákona 586/1992 Sb.
#   The engine does that itself (``_ceil_czk``); the residual of the next year
#   is computed from the rounded figures, and the last line takes whatever is
#   left, so the board never exceeds the entry price (§ 30 odst. 3).
# * SK — § 47 rounds mathematically to eurocent; the engine returns unrounded
#   floats and the caller applies the company-currency rounding.

# Float tolerance used when deciding whether a statutory remainder is real or
# just IEEE noise (e.g. `annual - annual * 12 / 12.0` can be ±1e-14).
_EPS = 1e-9


def _ceil_czk(amount):
    """Round a CZ odpis UP to whole koruny (§ 31/9, § 32/5, § 30a/2 ZDP).

    The tolerance keeps IEEE noise (``22250.000000000004``) from adding a
    koruna that the statute does not.
    """
    return float(math.ceil(amount - 1e-6))


@dataclass
class ScheduleLine:
    """One row of a tax-depreciation schedule (never posted to the GL)."""

    year_index: int            # 1-based ordinal within the schedule
    fiscal_year: int           # calendar year the charge falls into
    date_from: date
    date_to: date
    amount: float              # tax depreciation deductible in this period
    cumulative: float          # depreciation taken up to & including this line
    residual: float            # tax residual value after this line
    note: str = ""             # human hint, e.g. "prorated 10/12", "remainder"
    # Share of the line's full statutory charge actually taken (1.0 except on
    # a disposal-year line cut to whole months). Lets a comparison schedule
    # (SK § 17 ods. 34) be cut the same way.
    fraction: float = 1.0


@dataclass
class TaxClass:
    """Statutory depreciation group parameters (country agnostic container)."""

    country: str
    group_number: int
    useful_life_years: int
    # CZ straight-line maximum rates (% of entry price). Unused for SK.
    linear_rate_first: float = 0.0
    linear_rate_next: float = 0.0
    linear_rate_increased: float = 0.0      # after technical improvement
    # Accelerated coefficients (both countries). Unused for groups that may not
    # use the accelerated method.
    accel_coeff_first: int = 0
    accel_coeff_next: int = 0
    accel_coeff_increased: int = 0


@dataclass
class TaxAssetSpec:
    """Everything the engine needs to lay out a clean schedule for one asset."""

    country: str
    method: str
    entry_value: float
    in_service_date: date
    tax_class: TaxClass
    # Extraordinary (§30a) needs a precise monthly anchor; ignored otherwise.
    monthly: bool = False
    # Year-1 increase elected by a first depreciator (CZ only, groups 1–3):
    # 0 = none, or 10 / 15 / 20. Straight-line takes the § 31 odst. 1
    # písm. d) / c) / b) table; accelerated adds that share of the entry
    # price to the year-1 charge (§ 32 odst. 2 písm. a) body 3 / 2 / 1).
    # Which variant an asset may use (§ 31 odst. 2–5) is the caller's call.
    increased_first_year: int = 0
    # Passenger-vehicle limit (0 = none).
    # * CZ § 30e: only the share cap / entry price of each odpis of an M1
    #   vehicle is deductible (cap 2 000 000 Kč) — the board is computed on
    #   the cap, which gives exactly that share.
    # * SK § 17 ods. 34 is NOT a limit on the board: a car of 48 000 € or more
    #   is depreciated in full, and the excess over a § 27 schedule on 48 000 €
    #   is added back to the tax base only when that base is low. The engine
    #   leaves the SK board alone; see :func:`sk_vehicle_addbacks`.
    entry_cap: float = 0.0
    # SK § 22 ods. 12: assets that keep a whole-month charge in the year of
    # disposal — § 26 ods. 6 and 7 assets (always) and, from 1. 1. 2016, at the
    # taxpayer's option, assets whose residual is deductible only up to the
    # sale proceeds (§ 19 ods. 3 písm. b) prvý bod: passenger cars, boats,
    # aircraft, motorcycles, group-6 buildings sold …). Every other SK asset
    # gets no depreciation in the year it leaves (§ 22 ods. 11).
    sk_disposal_months: bool = False
    notes: list = field(default_factory=list)


# CZ §31 increased-first-year rate tables — (first-year %, subsequent-years %)
# keyed by [increment percent][group]. Verified against zákon 586/1992 Sb. 2026;
# each row sums to 100 % over the statutory life. Only groups 1–3 qualify.
CZ_INCREASED_FIRST_YEAR = {
    10: {1: (30, 35),   2: (21, 19.75), 3: (15.4, 9.4)},
    15: {1: (35, 32.5), 2: (26, 18.5),  3: (19, 9)},
    20: {1: (40, 30),   2: (31, 17.25), 3: (24.4, 8.4)},
}


def _months_in_first_year(in_service_date):
    """Whole calendar months from the in-service month to year end (inclusive).

    SK §27(2): the first-year charge is the annual amount × this / 12. An asset
    put into use in January gets 12 (a full year); one put into use in December
    gets 1.
    """
    return 13 - in_service_date.month


def _yearly_dates(in_service_date, year_index):
    """Calendar-year window for ``year_index`` (1-based).

    Tax depreciation is an annual operation keyed to the calendar/fiscal year of
    the in-service date. Year 1 is the in-service year; the period runs the whole
    calendar year (the proration is in the *amount*, not the dates, mirroring how
    the local packages present the register).
    """
    y = in_service_date.year + (year_index - 1)
    return date(y, 1, 1), date(y, 12, 31)


# ---------------------------------------------------------------------------
# Czech Republic — zákon 586/1992 Sb.
# ---------------------------------------------------------------------------
def _schedule_cz_linear(spec):
    """CZ §31 straight-line. Full first-year rate, no monthly proration.

    Honours the increased-first-year election (§31(1)(b)/(c)/(d), +10/15/20 %)
    for first depreciators of groups 1–3.
    """
    tc = spec.tax_class
    base = spec.entry_value
    variant = spec.increased_first_year
    first_rate, next_rate = tc.linear_rate_first, tc.linear_rate_next
    note_first = "§31 first-year rate"
    if variant and tc.group_number in CZ_INCREASED_FIRST_YEAR.get(variant, {}):
        first_rate, next_rate = CZ_INCREASED_FIRST_YEAR[variant][tc.group_number]
        note_first = "§31 +%d%% first year" % variant
    lines = []
    cumulative = 0.0
    years = tc.useful_life_years
    for i in range(1, years + 1):
        rate = first_rate if i == 1 else next_rate
        # § 31 odst. 9: rounded up to whole koruny, never past the entry price
        amount = min(_ceil_czk(base * rate / 100.0), base - cumulative)
        if i == years:
            # the last year takes what is left, so the board clears the base
            amount = base - cumulative
        cumulative += amount
        df, dt = _yearly_dates(spec.in_service_date, i)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=df.year, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note=note_first if i == 1 else "§31",
        ))
    return lines


def _schedule_cz_accelerated(spec):
    """CZ §32 accelerated. Year 1 = base/k1; year n = 2·residual/(kn−(n−1)).

    § 32 odst. 2 písm. a): a first depreciator may raise the year-1 charge by
    20 / 15 / 10 % of the entry price (bod 1 / 2 / 3); the later years then
    run the ordinary formula on the lower residual.
    """
    tc = spec.tax_class
    base = spec.entry_value
    k1 = tc.accel_coeff_first
    kn = tc.accel_coeff_next
    increase = 0.0
    note_first = "§32 1/k1"
    variant = spec.increased_first_year
    if variant and tc.group_number in CZ_INCREASED_FIRST_YEAR.get(variant, {}):
        increase = base * variant / 100.0
        note_first = "§32 1/k1 +%d%% of entry price" % variant
    lines = []
    cumulative = 0.0
    residual = base
    years = tc.useful_life_years
    for i in range(1, years + 1):
        # § 32 odst. 5: rounded up to whole koruny; the next year's residual
        # (zůstatková cena) is what the ROUNDED charges leave
        if i == 1:
            amount = min(_ceil_czk(base / k1 + increase), residual)
        elif i == years:
            amount = residual
        else:
            amount = min(_ceil_czk(2.0 * residual / (kn - (i - 1))), residual)
        cumulative += amount
        residual = base - cumulative
        df, dt = _yearly_dates(spec.in_service_date, i)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=df.year, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=residual,
            note=note_first if i == 1 else "§32 2·ZC/(k−n)",
        ))
    return lines


def _schedule_cz_extraordinary(spec):
    """CZ §30a extraordinary: emission-free vehicles, 24 months, 60% then 40%.

    Produces 24 monthly lines: months 1–12 carry 60% of the base spread evenly,
    months 13–24 carry the remaining 40%. Starts the month *after* the asset is
    put into use (the caller is responsible for eligibility: vehicle acquired
    1.1.2024–31.12.2028, first depreciator).
    """
    base = spec.entry_value
    lines = []
    cumulative = 0.0
    start = spec.in_service_date
    # first depreciated month = the month after in-service
    m = start.month + 1
    y = start.year
    if m > 12:
        m = 1
        y += 1
    # § 30a odst. 2: each odpis rounded up to whole koruny. The first twelve
    # months may reach "do výše 60 %" and no further, so month 12 takes what
    # the rounded months 1–11 leave of 60 %; month 24 clears the base.
    cap_60 = base * 0.60
    first_12 = _ceil_czk(base * 0.60 / 12.0)
    next_12 = _ceil_czk(base * 0.40 / 12.0)
    for i in range(1, 25):
        amount = first_12 if i <= 12 else next_12
        if i <= 12:
            amount = min(amount, cap_60 - cumulative)
        if i == 12:
            # whole koruny that still fit under 60 %; any haléř left over
            # moves into the 40 % half
            amount = float(math.floor(cap_60 - cumulative + 1e-6))
        amount = min(amount, base - cumulative)
        if i == 24:
            amount = base - cumulative
        cumulative += amount
        df = date(y, m, 1)
        # last day of month
        if m == 12:
            dt = date(y, 12, 31)
        else:
            dt = date(y, m + 1, 1).replace(day=1)
            from datetime import timedelta
            dt = dt - timedelta(days=1)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=y, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note="§30a 60%" if i <= 12 else "§30a 40%",
        ))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return lines


# ---------------------------------------------------------------------------
# Slovakia — zákon 595/2003 Z.z.
# ---------------------------------------------------------------------------
def _schedule_sk_linear(spec):
    """SK §27 straight-line. Year 1 prorated by months; remainder after life."""
    tc = spec.tax_class
    base = spec.entry_value
    years = tc.useful_life_years
    annual = base / years
    months = _months_in_first_year(spec.in_service_date)
    first = annual * months / 12.0
    remainder = annual - first  # deducted in the year following end of life

    lines = []
    cumulative = 0.0
    for i in range(1, years + 1):
        if i == 1:
            amount = first
            note = "§27 prorated %d/12" % months
        elif i == years and remainder <= _EPS:
            # no (real) remainder year: snap the last line to clear the base.
            # Tolerance-based like the §28 branch — an exact 0.0 test let IEEE
            # noise (annual*12/12.0 != annual) create a spurious remainder line.
            amount = base - cumulative
            note = "§27"
        else:
            amount = annual
            note = "§27"
        cumulative += amount
        df, dt = _yearly_dates(spec.in_service_date, i)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=df.year, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note=note,
        ))
    if remainder > _EPS:
        i = years + 1
        amount = base - cumulative  # snap to exactly clear the base
        cumulative += amount
        df, dt = _yearly_dates(spec.in_service_date, i)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=df.year, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note="§27 first-year remainder",
        ))
    return lines


def _schedule_sk_accelerated(spec):
    """SK §28 accelerated (groups 2 & 3 only).

    Year 1 actual charge is prorated by months, but the residual feeding the
    year-2 formula is computed as if the **full** first-year charge had been
    taken (§28(2)). The prorated remainder is deducted in the year after the end
    of the depreciation period.
    """
    tc = spec.tax_class
    base = spec.entry_value
    k1 = tc.accel_coeff_first
    kn = tc.accel_coeff_next
    years = tc.useful_life_years
    months = _months_in_first_year(spec.in_service_date)

    full_first = base / k1
    actual_first = full_first * months / 12.0
    remainder = full_first - actual_first

    lines = []
    cumulative = 0.0
    # residual used by the statutory formula (full first-year charge removed)
    formula_residual = base - full_first

    # Year 1 (actual, prorated)
    cumulative += actual_first
    df, dt = _yearly_dates(spec.in_service_date, 1)
    lines.append(ScheduleLine(
        year_index=1, fiscal_year=df.year, date_from=df, date_to=dt,
        amount=actual_first, cumulative=cumulative, residual=base - cumulative,
        note="§28 prorated %d/12 (formula uses full 1/k1)" % months,
    ))

    # Years 2..N (full formula amounts)
    for i in range(2, years + 1):
        if i == years:
            amount = formula_residual
        else:
            amount = 2.0 * formula_residual / (kn - (i - 1))
        formula_residual -= amount
        cumulative += amount
        df, dt = _yearly_dates(spec.in_service_date, i)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=df.year, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note="§28 2·ZC/(k−n)",
        ))

    # First-year remainder, deducted in the year after the end of life
    if remainder > _EPS:
        i = years + 1
        amount = base - cumulative
        cumulative += amount
        df, dt = _yearly_dates(spec.in_service_date, i)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=df.year, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note="§28 first-year remainder",
        ))
    return lines


_DISPATCH = {
    (CZ, METHOD_LINEAR): _schedule_cz_linear,
    (CZ, METHOD_ACCELERATED): _schedule_cz_accelerated,
    (CZ, METHOD_EXTRAORDINARY): _schedule_cz_extraordinary,
    (SK, METHOD_LINEAR): _schedule_sk_linear,
    (SK, METHOD_ACCELERATED): _schedule_sk_accelerated,
}


def compute_schedule(spec):
    """Return the clean tax-depreciation schedule for ``spec``.

    :param TaxAssetSpec spec: the asset's tax parameters.
    :returns: list[ScheduleLine] ordered by ``year_index``.
    :raises ValueError: for an unsupported (country, method) combination.
    """
    key = (spec.country, spec.method)
    fn = _DISPATCH.get(key)
    if fn is None:
        raise ValueError("Unsupported tax depreciation (%s, %s)" % key)
    # CZ § 30e: depreciate on the cap (= the deductible share of each odpis).
    # SK § 17 ods. 34 is a conditional add-back, not a cap: the board stays on
    # the full entry price (§ 25 counts the full § 27/§ 28 charge as taken
    # even in a year the excess is added back) — see sk_vehicle_addbacks().
    if spec.country == CZ and 0 < spec.entry_cap < spec.entry_value:
        spec.entry_value = spec.entry_cap
    if spec.entry_value <= 0:
        return []
    return fn(spec)


# SK § 17 ods. 34 has applied since 1. 1. 2015 (zákon 333/2014 Z. z.).
SK_VEHICLE_ADDBACK_FROM_YEAR = 2015


def sk_vehicle_addbacks(lines, spec, cap):
    """SK § 17 ods. 34: the potential add-back for a car of ``cap`` € or more.

    Returns one amount per line of ``lines``: the positive difference between
    the depreciation actually on the line and the § 27 (straight-line)
    depreciation of the same car computed from an entry price of ``cap``
    (48 000 €), including its first-year months and its first-year remainder.

    Whether the add-back is actually made depends on the taxpayer's whole tax
    base for the year (it applies only when that base is lower than the number
    of such cars × the annual § 27 charge on 48 000 €) and is not made by a
    lessor for cars leased without a purchase option — neither is known here,
    so this is the amount to add back *if* the condition is met.

    The comparison schedule is matched to the charged lines in order (a
    suspended year carries nothing and does not consume a comparison year),
    and a disposal-year line cut to whole months is compared with the same
    share of the comparison year.
    """
    if spec.country != SK or not cap or spec.entry_value < cap:
        return [0.0] * len(lines)
    reference = _schedule_sk_linear(TaxAssetSpec(
        country=SK, method=METHOD_LINEAR, entry_value=cap,
        in_service_date=spec.in_service_date, tax_class=spec.tax_class,
    ))
    ref_amounts = [l.amount for l in reference]
    out = []
    k = 0
    for line in lines:
        if line.amount <= _EPS:
            out.append(0.0)
            continue
        ref = ref_amounts[k] * line.fraction if k < len(ref_amounts) else 0.0
        k += 1
        if line.fiscal_year < SK_VEHICLE_ADDBACK_FROM_YEAR:
            out.append(0.0)
            continue
        out.append(max(line.amount - ref, 0.0))
    return out


# ---------------------------------------------------------------------------
# Lifecycle events
#
# Each event takes the clean schedule and rewrites the *open tail* from the
# event year onward. The Odoo layer maps a calendar/event date to the relevant
# ``year_index`` and preserves any already-filed lines.
# ---------------------------------------------------------------------------
def _reindex(prefix, tail_amounts, in_service_date, base, start_year_index,
             notes=None, start_fiscal_year=None):
    """Rebuild ScheduleLines for ``tail_amounts`` appended after ``prefix``.

    Running cumulative/residual are recomputed against ``base`` so the whole
    board stays internally consistent.
    """
    lines = list(prefix)
    cumulative = prefix[-1].cumulative if prefix else 0.0
    if start_fiscal_year is None:
        start_fiscal_year = in_service_date.year + (start_year_index - 1)
    for offset, amount in enumerate(tail_amounts):
        yi = start_year_index + offset
        fy = start_fiscal_year + offset
        cumulative += amount
        note = notes[offset] if notes and offset < len(notes) else ""
        lines.append(ScheduleLine(
            year_index=yi, fiscal_year=fy,
            date_from=date(fy, 1, 1), date_to=date(fy, 12, 31),
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note=note,
        ))
    return lines


def _accel_tail_amounts(residual, k_increased, rounding=None):
    """Return accelerated post-improvement amounts until the residual is cleared.

    Year of improvement: 2·ZC_increased / k_increased.
    Following years:      2·ZC / (k_increased − n), n = years since improvement.
    The final year clears whatever residual remains. ``rounding`` (CZ:
    ``_ceil_czk``, § 32 odst. 5) is applied to each year's charge.
    """
    amounts = []
    res = residual
    n = 0
    while res > 1e-6 and n < k_increased:
        denom = k_increased if n == 0 else (k_increased - n)
        amt = 2.0 * res / denom if denom > 0 else res
        if rounding:
            amt = rounding(amt)
        # once the formula would over-shoot, or we reach the last coefficient
        # step, take the whole remaining residual
        if amt >= res or denom <= 1:
            amt = res
        amounts.append(amt)
        res -= amt
        n += 1
    if res > 1e-6:  # safety: clear any rounding tail
        amounts.append(res)
    return amounts


def apply_technical_improvement(lines, spec, improvement_year_index, amount):
    """Recompute the board after a technical improvement (TZ).

    * CZ — the entry price is *increased*; straight-line then uses the
      increased-price rate (§31), accelerated the increased-residual coefficient
      (§32(3)).
    * SK — the residual is *increased*; straight-line uses increased-price / life
      (§26(5)), accelerated the increased-residual coefficient (§28(3)).

    ``improvement_year_index`` is the 1-based schedule year in which the TZ is
    completed; the increase applies from that year on. Lines before it are kept.
    """
    # TODO(accountant): a TZ completed in the FIRST year of depreciation is,
    # statutorily, simply part of the entry price (CZ §29(1) vstupní cena /
    # SK §25), i.e. year 1 should already be computed on entry + TZ with the
    # *first-year* rate, not with the increased-price rate this event applies.
    # Confirm the desired handling (fold into tax_entry_value vs. event) with
    # the accountant before special-casing improvement_year_index == 1 here.
    tc = spec.tax_class
    # Derive the current base from the lines themselves so that chained events
    # (a second improvement on an already-improved asset) compound correctly.
    base = (lines[0].amount + lines[0].residual) if lines else spec.entry_value
    prefix = [l for l in lines if l.year_index < improvement_year_index]
    cumulative_before = prefix[-1].cumulative if prefix else 0.0
    residual_before = base - cumulative_before
    new_base = base + amount          # increased entry/acquisition price
    new_residual = residual_before + amount
    # Continue the fiscal-year sequence from the kept prefix, NOT from the
    # in-service year: a prior suspension (or any transform that shifted the
    # tail without re-indexing) means ``in_service.year + (year_index - 1)``
    # would rebuild the tail on stale years, duplicating fiscal_year values
    # that downstream per-year folding silently collapses.
    if prefix:
        start_fy = prefix[-1].fiscal_year + 1
    elif lines:
        start_fy = lines[0].fiscal_year
    else:
        start_fy = spec.in_service_date.year + (improvement_year_index - 1)

    tail = []
    if spec.method == METHOD_LINEAR:
        if spec.country == CZ:
            # § 31 odst. 8 and 9: increased-price rate, rounded up to koruny
            annual = _ceil_czk(new_base * tc.linear_rate_increased / 100.0)
        else:  # SK: increased price spread over the statutory life
            annual = new_base / tc.useful_life_years
        res = new_residual
        while res > 1e-6:
            amt = annual if annual < res else res
            tail.append(amt)
            res -= amt
        notes = ["TZ §31 increased rate" if spec.country == CZ else "TZ §26(5) increased price"] * len(tail)
    elif spec.method == METHOD_ACCELERATED:
        k_incr = tc.accel_coeff_increased or tc.accel_coeff_next
        tail = _accel_tail_amounts(
            new_residual, k_incr,
            rounding=_ceil_czk if spec.country == CZ else None)
        notes = ["TZ accelerated 2·ZC/k_incr"] + ["TZ accelerated 2·ZC/(k_incr−n)"] * (len(tail) - 1)
    elif spec.method == METHOD_EXTRAORDINARY:
        # §30a(3): a technical improvement of an extraordinary-depreciation asset
        # is NOT added to its base — it is depreciated as a *separate* asset in
        # the asset's normal group. The caller must create a new asset for it.
        raise ValueError(
            "Technical improvement of a §30a asset is depreciated as a separate "
            "asset (§30a(3)); create a new asset for it instead of an improvement "
            "event.")
    else:
        raise ValueError("Technical improvement not supported for method %s" % spec.method)

    # rebuild against the increased base so residual columns are correct
    rebuilt_prefix = _rebuild_prefix_residuals(prefix, new_base)
    return _reindex(rebuilt_prefix, tail, spec.in_service_date, new_base,
                    improvement_year_index, notes=notes, start_fiscal_year=start_fy)


def _rebuild_prefix_residuals(prefix, new_base):
    """Recompute residual columns of ``prefix`` against a new (increased) base."""
    out = []
    cumulative = 0.0
    for l in prefix:
        cumulative += l.amount
        out.append(ScheduleLine(
            year_index=l.year_index, fiscal_year=l.fiscal_year,
            date_from=l.date_from, date_to=l.date_to,
            amount=l.amount, cumulative=cumulative, residual=new_base - cumulative,
            note=l.note,
        ))
    return out


def apply_suspension(lines, suspended_year_indices):
    """Interrupt depreciation for the given schedule years.

    A suspended year becomes a zero line and every later year is pushed out by
    one calendar year — matching both CZ §26(8) ("continue as if uninterrupted")
    and SK §22(9) ("the total depreciation period is extended").
    """
    suspended = sorted(set(suspended_year_indices))
    if not suspended:
        return lines
    base = (lines[0].residual + lines[0].amount) if lines else 0.0  # = entry value
    # The ordered amounts that still have to be charged, in sequence.
    pending = [l.amount for l in lines]
    pending_notes = [l.note for l in lines]
    out = []
    cumulative = 0.0
    src = 0
    yi = 1
    fy = lines[0].fiscal_year if lines else 0
    while src < len(pending) or yi in suspended:
        if yi in suspended:
            amount, note = 0.0, "suspended"
        else:
            amount, note = pending[src], pending_notes[src]
            src += 1
        cumulative += amount
        out.append(ScheduleLine(
            year_index=yi, fiscal_year=fy,
            date_from=date(fy, 1, 1), date_to=date(fy, 12, 31),
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note=note,
        ))
        yi += 1
        fy += 1
    return out


def apply_disposal(lines, spec, disposal_date):
    """Truncate the board at disposal.

    * CZ annual — § 26 odst. 7 písm. a) bod 1: only **half** the annual charge
      (§ 31/§ 32, itself rounded up to koruny; the half is rounded up as well)
      and only for an asset that was already registered at the start of the
      tax period. An asset put into use and disposed of in the same year gets
      nothing. The rest of the board is dropped.
    * CZ §30a monthly — depreciation runs with whole-month precision (§30a(2)):
      the monthly charges through the disposal *month* stay, the rest is
      dropped; the half-year rule does not apply to a monthly board.
    * SK — § 22 ods. 11: the annual charge may be claimed only for an asset
      still recorded on the last day of the tax period, so the disposal year
      carries **no** depreciation; the tax residual is then expensed under
      § 19 ods. 3 písm. b) (capped at the sale proceeds for the assets listed
      in its first point). Exception, § 22 ods. 12: assets flagged
      ``sk_disposal_months`` keep the charge for the whole months they were
      recorded in that year.

    Returns ``(truncated_lines, tax_residual_at_disposal)``.
    """
    disposal_fy = disposal_date.year
    base = (lines[0].residual + lines[0].amount) if lines else 0.0

    # Monthly (§30a) board: keep every monthly line up to and including the
    # disposal month; the annual half-year/proration branches below would
    # wrongly grab the first month-line of the disposal year and halve it.
    if spec.monthly or spec.method == METHOD_EXTRAORDINARY:
        cutoff = (disposal_date.year, disposal_date.month)
        kept = [l for l in lines
                if (l.date_from.year, l.date_from.month) <= cutoff]
        out = _rebuild_prefix_residuals(kept, base)
        cumulative = out[-1].cumulative if out else 0.0
        if out:
            last = out[-1]
            out[-1] = ScheduleLine(
                year_index=last.year_index, fiscal_year=last.fiscal_year,
                date_from=last.date_from, date_to=last.date_to,
                amount=last.amount, cumulative=last.cumulative,
                residual=last.residual,
                note=(last.note + "; §30a through disposal month").strip("; "),
            )
        return out, base - cumulative

    prefix = [l for l in lines if l.fiscal_year < disposal_fy]
    disposal_line = next((l for l in lines if l.fiscal_year == disposal_fy), None)

    out = list(_rebuild_prefix_residuals(prefix, base))
    cumulative = out[-1].cumulative if out else 0.0
    if disposal_line is not None:
        first_year = disposal_fy == spec.in_service_date.year
        fraction = 0.0
        if spec.country == CZ:
            if first_year:
                amount = 0.0
                note = ("§26(7)(a) none on disposal: not registered at the "
                        "start of the tax period")
            else:
                amount = min(_ceil_czk(disposal_line.amount / 2.0),
                             base - cumulative)
                fraction = (amount / disposal_line.amount
                            if disposal_line.amount else 0.0)
                note = "§26(7) half-year on disposal"
        elif spec.sk_disposal_months:
            # § 22 ods. 12: whole calendar months recorded in the year
            # (the disposal month is not a whole month). In the in-service
            # year the line already holds months/12 of the annual charge.
            if first_year:
                months_held = _months_in_first_year(spec.in_service_date)
                months_used = max(disposal_date.month
                                  - spec.in_service_date.month, 0)
            else:
                months_held = 12
                months_used = max(disposal_date.month - 1, 0)
            fraction = months_used / float(months_held) if months_held else 0.0
            amount = disposal_line.amount * fraction
            note = "§22(12) %d whole months on disposal" % months_used
        else:
            amount = 0.0
            note = ("§22(11) none in the year of disposal; residual is a "
                    "§19(3)(b) expense")
        cumulative += amount
        out.append(ScheduleLine(
            year_index=disposal_line.year_index, fiscal_year=disposal_fy,
            date_from=date(disposal_fy, 1, 1), date_to=disposal_date,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note=note, fraction=fraction,
        ))
    tax_residual = base - cumulative
    return out, tax_residual
