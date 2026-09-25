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

from dataclasses import dataclass, field
from datetime import date

# Country codes used throughout the stack.
CZ = "CZ"
SK = "SK"

# Method keys (also the selection values on ``account.asset`` in the bridges).
METHOD_LINEAR = "linear"            # CZ rovnoměrné / SK rovnomerné
METHOD_ACCELERATED = "accelerated"  # CZ zrychlené / SK zrýchlené
METHOD_EXTRAORDINARY = "extraordinary"  # CZ §30a only

# Rounding: CZ rounds the annual charge up to whole CZK (§ rounding rules);
# SK rounds mathematically to eurocent. The engine returns unrounded floats and
# lets the caller apply the company-currency rounding, except that we snap the
# final line so the schedule sums exactly to the depreciable base.
# TODO(accountant): CZ statutorily rounds each annual charge UP to whole CZK
# (§26(8)-adjacent practice; zaokrouhlení na celé koruny nahoru). The engine
# currently leaves rounding to the caller's company currency (0.01). Confirm
# with the accountant whether the register must show whole-CZK round-up per
# year (and where the compensating difference lands) before changing.

# Float tolerance used when deciding whether a statutory remainder is real or
# just IEEE noise (e.g. `annual - annual * 12 / 12.0` can be ±1e-14).
_EPS = 1e-9


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
    # Year-1 increased-rate election (CZ §31, first depreciator of groups 1–3):
    # 0 = none (basic table), or 10 / 15 / 20 for the +10/+15/+20 % variants.
    increased_first_year: int = 0
    # Passenger-vehicle base cap (0 = none). CZ §30e caps the deductible base of
    # an M1 vehicle at 2,000,000 CZK; SK §17(34) limits cars from 48,000 EUR.
    # When set and below the entry value, the schedule is computed on the cap.
    entry_cap: float = 0.0
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
        amount = base * rate / 100.0
        if i == years:
            # snap the last line so rounding never leaves a residual
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
    """CZ §32 accelerated. Year 1 = base/k1; year n = 2·residual/(kn−(n−1))."""
    tc = spec.tax_class
    base = spec.entry_value
    k1 = tc.accel_coeff_first
    kn = tc.accel_coeff_next
    lines = []
    cumulative = 0.0
    residual = base
    years = tc.useful_life_years
    for i in range(1, years + 1):
        if i == 1:
            amount = base / k1
        elif i == years:
            amount = residual
        else:
            amount = 2.0 * residual / (kn - (i - 1))
        cumulative += amount
        residual = base - cumulative
        df, dt = _yearly_dates(spec.in_service_date, i)
        lines.append(ScheduleLine(
            year_index=i, fiscal_year=df.year, date_from=df, date_to=dt,
            amount=amount, cumulative=cumulative, residual=residual,
            note="§32 1/k1" if i == 1 else "§32 2·ZC/(k−n)",
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
    first_12 = base * 0.60 / 12.0
    next_12 = base * 0.40 / 12.0
    for i in range(1, 25):
        amount = first_12 if i <= 12 else next_12
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
    # Passenger-vehicle base cap (CZ §30e / SK §17(34)): depreciate on the cap.
    # TODO(accountant): SK §17(34) is NOT a hard base cap like CZ §30e — the
    # depreciation of a >48k EUR car is claimed in full and only *conditionally*
    # added back to the tax base (pripočítateľná položka) when the taxpayer's
    # base is too low / lease conditions apply. Capping the board here matches
    # CZ semantics; the SK conditional add-back belongs in the DPPO
    # reconciliation. Confirm the SK presentation with the accountant.
    if 0 < spec.entry_cap < spec.entry_value:
        spec.entry_value = spec.entry_cap
    if spec.entry_value <= 0:
        return []
    return fn(spec)


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


def _accel_tail_amounts(residual, k_increased):
    """Return accelerated post-improvement amounts until the residual is cleared.

    Year of improvement: 2·ZC_increased / k_increased.
    Following years:      2·ZC / (k_increased − n), n = years since improvement.
    The final year clears whatever residual remains.
    """
    amounts = []
    res = residual
    n = 0
    while res > 1e-6 and n < k_increased:
        denom = k_increased if n == 0 else (k_increased - n)
        amt = 2.0 * res / denom if denom > 0 else res
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
            annual = new_base * tc.linear_rate_increased / 100.0
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
        tail = _accel_tail_amounts(new_residual, k_incr)
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

    * CZ annual — only **half** the annual charge is deductible in the disposal
      year (§26(7)); the rest of the board is dropped.
    * CZ §30a monthly — depreciation runs with whole-month precision (§30a(4)):
      the monthly charges through the disposal *month* stay, the rest is
      dropped; the half-year rule does not apply to a monthly board.
    * SK — the disposal year is prorated to the month before disposal; the rest
      is dropped.

    Returns ``(truncated_lines, tax_residual_at_disposal)``.

    TODO(accountant): CZ §26(7)(a) grants the half-year charge only when the
    asset was registered at the start of the tax period — an asset acquired and
    disposed of in the SAME year gets no depreciation at all. Confirm before
    zeroing the disposal-year line for same-year acquisition+disposal.
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
    cumulative = prefix[-1].cumulative if prefix else 0.0

    out = list(_rebuild_prefix_residuals(prefix, base))
    cumulative = out[-1].cumulative if out else 0.0
    if disposal_line is not None:
        if spec.country == CZ:
            amount = disposal_line.amount / 2.0
            note = "§26(7) half-year on disposal"
        else:  # SK: prorate to the month of disposal (months Jan..disposal-1)
            months_used = max(disposal_date.month - 1, 0)
            annual = disposal_line.amount
            amount = annual * months_used / 12.0
            note = "§22 prorated %d/12 on disposal" % months_used
        cumulative += amount
        out.append(ScheduleLine(
            year_index=disposal_line.year_index, fiscal_year=disposal_fy,
            date_from=date(disposal_fy, 1, 1), date_to=disposal_date,
            amount=amount, cumulative=cumulative, residual=base - cumulative,
            note=note,
        ))
    tax_residual = base - cumulative
    return out, tax_residual
