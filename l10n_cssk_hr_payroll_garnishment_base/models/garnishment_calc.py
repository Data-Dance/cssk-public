# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Pure-Python allocator for Czech and Slovak wage garnishments.

This module deliberately imports NOTHING from Odoo. It is the compliance
kernel: given a net wage, the statutory rates valid for the period and the
list of claims registered against the employee, it returns how much each
claim gets this month. Keeping it Odoo-free means the legal rules are unit
testable in isolation and reusable from either payroll engine.

Czech Republic
--------------
``§ 276-§ 302 občanského soudního řádu`` (zákon 99/1963 Sb.) +
``nařízení vlády 595/2006 Sb.`` (nařízení o nezabavitelných částkách).

* ``§ 278`` + NV 595/2006 ``§ 1``: the debtor must keep the *nezabavitelná
  částka* — 85 % of the sum of (životní minimum jednotlivce + normativní
  nájemné + energetický paušál), plus one quarter of that per dependent.
  NV 595/2006 ``§ 3``: the resulting **total** is rounded up to whole crowns.
* NV 595/2006 ``§ 2``: everything above 1.9× that same sum is seized without
  limitation (2026: 31 521 Kč).
* ``§ 279(1)``: the rest (*zbytek čisté mzdy*), rounded **down** to an amount
  divisible by three, splits into thirds. Ordinary claims reach one third,
  priority claims two. The third third always stays with the employee, as
  does the 0-2 Kč rounding remainder.
* ``§ 279(1)`` second sentence: priority claims are satisfied **first from
  the second third**; only what the second third cannot cover competes with
  ordinary claims in the first third.
* ``§ 280(1)``: the first third is distributed strictly by *pořadí*,
  regardless of whether a claim is priority or not.
* ``§ 280(2)``: in the second third *výživné* comes first **ignoring
  pořadí**; if the second third does not cover the current maintenance of
  all beneficiaries it is split pro rata by the **current** maintenance,
  disregarding arrears. Other priority claims follow by pořadí.
* ``§ 280(3)``: pořadí is the day the order was delivered to the payer of
  the wage; same day means equal rank and pro-rata satisfaction.
* Official methodology for the fully seizable part (exekuce.justice.cz):
  *"Plně zabavitelná část zbytku čisté mzdy se připočte ke druhé třetině v
  rozsahu, který je potřebný k uspokojení přednostních pohledávek; zbývající
  část se připočte k první třetině."*

Slovakia
--------
``nariadenie vlády 268/2006 Z. z.`` + ``zákon 233/1995 Z. z.`` (Exekučný
poriadok).

Unlike the Czech rules, the protected *základná suma* depends on **what is
being collected** — a priority creditor may legally reach deeper:

============================== ============================ =====================
Claim class                    Základná suma na povinného   Na vyživovanú osobu
============================== ============================ =====================
neprednostná (§ 1)             140 % ŽM                     25 % of that
prednostná (§ 2 ods. 2)        100 % ŽM                     25 % ŽM
výživné na maloleté (§ 2/1)    70 % of 60 % ŽM              70 % of 25 % ŽM
pokuta za priestupok (§ 2a)    50 % ŽM                      25 % ŽM
============================== ============================ =====================

For a *poberateľ dôchodkových dávok* the per-dependant coefficient is 50 %
instead of 25 %. ``§ 3``: the part of the remainder above 3× the § 1 ods. 1
basic sum is seized without limitation. The remainder is rounded down to a
sum divisible by three (in cents).

Modelling choice (documented deviation)
+++++++++++++++++++++++++++++++++++++++
Because each claim class carries its own protected base, the thirds are not
a single pot. This allocator computes the thirds **once per claim class
present** and then applies the Czech-style waterfall: priority claims draw
from their own second third (plus the unlimited part as needed), and only
the unsatisfied rest competes with ordinary claims in the first third. Two
global invariants keep this conservative — it can never deduct more than any
single claim could legally reach on its own, and the employee always retains
at least the smallest protected base among the claims actually deducted.
"""

import math
from collections import defaultdict

# --- claim classes ---------------------------------------------------------
# 'maintenance' is výživné (CZ: absolute precedence inside the second third;
# SK: výživné na maloleté dieťa, which carries its own deeper base).
CLASS_MAINTENANCE = "maintenance"
CLASS_PRIORITY = "priority"
CLASS_FINE = "fine"  # SK only — pokuty za priestupky (NV 268/2006 § 2a)
CLASS_ORDINARY = "ordinary"

PRIORITY_CLASSES = (CLASS_MAINTENANCE, CLASS_PRIORITY, CLASS_FINE)

# Where an allocated crown/cent came from — kept per claim so the payslip and
# the vyúčtování srážek can show the legal reasoning.
SOURCE_SECOND = "second"
SOURCE_FIRST = "first"
SOURCE_UNLIMITED = "unlimited"

_EPS = 1e-9


class Claim:
    """One registered garnishment order, reduced to what the maths needs.

    :param key: opaque identifier echoed back in the result (the record id).
    :param claim_class: one of the ``CLASS_*`` constants.
    :param order_key: sortable *pořadí* key, normally
        ``(date_delivered, sequence, key)``. Claims comparing equal on the
        first element share a rank and are satisfied pro rata.
    :param due: the most that may be taken this month — the outstanding
        balance, or for recurring maintenance the current month plus arrears.
    :param current_maintenance: the *current* monthly maintenance, used as
        the pro-rata weight in the second third per CZ § 280(2). Zero for
        anything that is not maintenance.
    """

    __slots__ = ("key", "claim_class", "order_key", "due", "current_maintenance")

    def __init__(
        self, key, claim_class, order_key, due, current_maintenance=0.0
    ):
        self.key = key
        self.claim_class = claim_class
        self.order_key = order_key
        self.due = max(0.0, float(due))
        self.current_maintenance = max(0.0, float(current_maintenance or 0.0))

    @property
    def rank(self):
        """The part of ``order_key`` that establishes equal rank (same day)."""
        return self.order_key[0] if isinstance(self.order_key, tuple) else self.order_key

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"<Claim {self.key} {self.claim_class} due={self.due}>"


class Result:
    """Outcome of one allocation run."""

    __slots__ = (
        "protected",
        "remainder",
        "third",
        "unlimited",
        "allocations",
        "breakdown",
        "detail",
    )

    def __init__(self, protected, remainder, third, unlimited, allocations, breakdown, detail):
        #: the amount the employee may not be deprived of (nezabavitelná částka)
        self.protected = protected
        #: zbytek čisté mzdy after the protected amount
        self.remainder = remainder
        #: one third of the (rounded) seizable remainder
        self.third = third
        #: the fully seizable part above the statutory limit
        self.unlimited = unlimited
        #: ``{claim key: amount}``
        self.allocations = allocations
        #: ``{claim key: {source: amount}}`` — which third the money came from
        self.breakdown = breakdown
        #: free-form dict of intermediate figures, for the payslip explanation
        self.detail = detail

    @property
    def total(self):
        return sum(self.allocations.values())


# ---------------------------------------------------------------------------
# generic distribution helpers
# ---------------------------------------------------------------------------
def _round(value, digits):
    """Round half up, and squash the float noise that ``-0.0`` produces."""
    factor = 10**digits
    return math.floor(abs(value) * factor + 0.5) / factor * (1 if value >= 0 else -1)


def _to_units(value, digits):
    """Scale *value* to whole currency units, absorbing float noise.

    ``0.30 * 100`` is ``29.999999999999996`` in IEEE-754, so flooring the raw
    product would lose a cent. Rounding to a fixed precision first fixes that
    without the upward bias a one-sided ``+ epsilon`` would introduce on every
    single grant.
    """
    return round(value * 10**digits, 9)


def _floor_unit(value, digits):
    """Round *value* DOWN to the currency unit (whole crowns / cents)."""
    scale = 10**digits
    return max(0.0, math.floor(_to_units(value, digits)) / scale)


def _ceil_unit(value, digits):
    """Round *value* UP to the currency unit."""
    scale = 10**digits
    return max(0.0, math.ceil(_to_units(value, digits)) / scale)


def _round_down_divisible_by_three(value, digits):
    """Round *value* down to an amount divisible by three.

    CZ § 279(1) works in whole crowns (``digits=0``); SK NV 268/2006 works in
    cents (``digits=2``). The 0-2 unit remainder stays with the employee.
    """
    units = math.floor(_to_units(value, digits))
    units -= units % 3
    return max(0.0, units / 10**digits)


def _take(claim, amount, alloc, breakdown, source, digits, cap=None):
    """Give *amount* to *claim*, capped by what is still due and by *cap*.

    Rounds DOWN to the currency unit. Rounding a grant *up* would let the
    grants of several claims sum past the third they came out of — deducting
    more than the law allows — so every rounding here goes in the debtor's
    favour, as it does throughout § 279. The sub-unit residue is handed out
    deterministically by :func:`_distribute_pro_rata`, so nothing is lost.
    """
    allowed = min(max(0.0, amount), claim.due - alloc[claim.key])
    if cap is not None:
        allowed = min(allowed, cap)
    granted = _floor_unit(allowed, digits)
    if granted <= _EPS:
        return 0.0
    alloc[claim.key] += granted
    breakdown[claim.key][source] += granted
    return granted


def _distribute_by_rank(claims, pool, alloc, breakdown, source, digits):
    """Satisfy *claims* in pořadí; equal rank shares pro rata (CZ § 280(3)).

    Returns the unused part of *pool*.
    """
    if pool <= _EPS:
        return pool
    groups = defaultdict(list)
    for claim in claims:
        groups[claim.rank].append(claim)
    for rank in sorted(groups):
        if pool <= _EPS:
            break
        group = groups[rank]
        need = sum(c.due - alloc[c.key] for c in group)
        if need <= _EPS:
            continue
        if len(group) == 1 or need <= pool + _EPS:
            for claim in group:
                pool -= _take(claim, pool, alloc, breakdown, source, digits)
        else:
            pool = _distribute_pro_rata(
                group, pool, alloc, breakdown, source, digits,
                weights={c.key: c.due - alloc[c.key] for c in group},
            )
    return pool


def _distribute_pro_rata(claims, pool, alloc, breakdown, source, digits, weights):
    """Split *pool* among *claims* proportionally to *weights*.

    Uses largest-remainder apportionment: every share is floored to the
    currency unit, then the leftover units go to the largest fractional parts
    (ties broken by rank). That distributes the pool exactly — never a unit
    more, never a unit silently lost — which plain rounding cannot promise.

    Anything a claim cannot absorb (because it is capped by ``due``) is
    redistributed over the remaining claims until the pool or the demand runs
    out.
    """
    unit = 1.0 / (10**digits)
    active = [c for c in claims if c.due - alloc[c.key] > _EPS]
    while active and pool > _EPS:
        raw_weight = sum(weights.get(c.key, 0.0) for c in active)
        # No usable weights (e.g. every current maintenance is zero) — fall
        # back to an equal split so the pool still gets distributed.
        use_equal = raw_weight <= _EPS
        total_weight = float(len(active)) if use_equal else raw_weight

        granted_total = 0.0
        remainders = []
        for claim in active:
            weight = 1.0 if use_equal else weights.get(claim.key, 0.0)
            want = min(
                pool * weight / total_weight, claim.due - alloc[claim.key]
            )
            floored = _floor_unit(want, digits)
            granted_total += _take(
                claim, floored, alloc, breakdown, source, digits,
                cap=pool - granted_total,
            )
            remainders.append((want - floored, claim))
        pool -= granted_total
        progressed = granted_total > _EPS

        # Largest remainder first, then by rank, so the outcome is stable.
        for _frac, claim in sorted(
            remainders, key=lambda item: (-item[0], item[1].order_key)
        ):
            if pool < unit - _EPS:
                break
            taken = _take(claim, unit, alloc, breakdown, source, digits, cap=pool)
            if taken:
                pool -= taken
                progressed = True

        active = [c for c in active if c.due - alloc[c.key] > _EPS]
        if not progressed:
            break
    return pool


def _split(claims):
    maintenance = [c for c in claims if c.claim_class == CLASS_MAINTENANCE]
    other_priority = [
        c for c in claims if c.claim_class in (CLASS_PRIORITY, CLASS_FINE)
    ]
    ordinary = [c for c in claims if c.claim_class == CLASS_ORDINARY]
    return maintenance, other_priority, ordinary


def _empty_result(protected, remainder, claims, detail):
    return Result(
        protected=protected,
        remainder=max(0.0, remainder),
        third=0.0,
        unlimited=0.0,
        allocations={c.key: 0.0 for c in claims},
        breakdown={c.key: defaultdict(float) for c in claims},
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Czech Republic
# ---------------------------------------------------------------------------
def cz_protected_amount(rates, dependents):
    """Nezabavitelná částka per NV 595/2006 § 1 + § 3.

    The per-dependent quarter is added to the debtor's amount and only the
    **total** is rounded up to whole crowns (§ 3 speaks of "základní částka,
    která nesmí být povinnému sražena", i.e. the aggregate).
    """
    base_sum = (
        rates["subsistence"] + rates["normative_rent"] + rates["energy"]
    )
    debtor = base_sum * rates["base_pct"] / 100.0
    total = debtor + dependents * debtor * rates["dependent_fraction"]
    return math.ceil(total - _EPS)


def compute_cz(net, rates, dependents, claims, digits=0):
    """Allocate a Czech payslip's seizable amount across *claims*.

    :param net: čistá mzda for the period.
    :param rates: dict with ``subsistence``, ``normative_rent``, ``energy``,
        ``base_pct``, ``dependent_fraction`` and ``unlimited_limit``.
    :param dependents: number of persons the debtor must maintain.
    :param claims: list of :class:`Claim`.
    :param digits: currency precision — 0, since CZK garnishments work in
        whole crowns.
    """
    claims = [c for c in claims if c.due > _EPS]
    protected = cz_protected_amount(rates, dependents)
    remainder = net - protected
    detail = {"protected": protected, "net": net, "dependents": dependents}
    if remainder <= _EPS or not claims:
        return _empty_result(protected, remainder, claims, detail)

    limit = _round_down_divisible_by_three(rates["unlimited_limit"], digits)
    if remainder >= limit:
        # NV 595/2006 § 2 — everything past the limit is seized in full.
        unlimited = remainder - limit
        thirds_base = limit
    else:
        unlimited = 0.0
        thirds_base = _round_down_divisible_by_three(remainder, digits)
    third = thirds_base / 3.0

    alloc = {c.key: 0.0 for c in claims}
    breakdown = {c.key: defaultdict(float) for c in claims}
    maintenance, other_priority, ordinary = _split(claims)
    priority = maintenance + other_priority

    # The fully seizable part joins the SECOND third only as far as the
    # priority claims need it; whatever is left joins the FIRST third.
    priority_need = sum(c.due for c in priority)
    unlimited_for_priority = min(unlimited, max(0.0, priority_need - third))
    # Floor the pools to whole crowns: a fractional pool would otherwise leak
    # sub-crown amounts into the allocations.
    second_pool = _floor_unit(third + unlimited_for_priority, digits)
    first_pool = _floor_unit(third + (unlimited - unlimited_for_priority), digits)

    # --- second third: výživné first, ignoring pořadí (§ 280(2)) ----------
    pool = second_pool
    if maintenance:
        need = sum(c.due for c in maintenance)
        if need <= pool + _EPS:
            for claim in maintenance:
                pool -= _take(claim, claim.due, alloc, breakdown, SOURCE_SECOND, digits)
        else:
            # Pro rata by CURRENT maintenance, disregarding arrears. Claims
            # with no current maintenance recorded fall back to their due.
            pool = _distribute_pro_rata(
                maintenance, pool, alloc, breakdown, SOURCE_SECOND, digits,
                weights={
                    c.key: (c.current_maintenance or c.due) for c in maintenance
                },
            )
    # --- second third: other priority claims by pořadí (§ 280(2)) ---------
    pool = _distribute_by_rank(
        other_priority, pool, alloc, breakdown, SOURCE_SECOND, digits
    )
    # The unused part of the second third is NOT moved to the first third —
    # § 279(1) leaves it with the employee.
    second_unused = pool

    # --- first third: everything still unpaid, strictly by pořadí ---------
    first_unused = _distribute_by_rank(
        priority + ordinary, first_pool, alloc, breakdown, SOURCE_FIRST, digits
    )

    detail.update(
        {
            "limit": limit,
            "thirds_base": thirds_base,
            "third": third,
            "unlimited": unlimited,
            "unlimited_for_priority": unlimited_for_priority,
            "second_pool": second_pool,
            "first_pool": first_pool,
            "second_unused": second_unused,
            "first_unused": first_unused,
        }
    )
    return Result(protected, remainder, third, unlimited, alloc, breakdown, detail)


# ---------------------------------------------------------------------------
# Slovakia
# ---------------------------------------------------------------------------
def sk_protected_amount(rates, dependents, claim_class, is_pensioner=False, digits=2):
    """Základná suma for one claim class per NV 268/2006 § 1, § 2, § 2a."""
    zm = rates["zivotne_minimum"]
    dep_coeff = (
        rates["dependent_coeff_pensioner"] if is_pensioner else rates["dependent_coeff"]
    )
    if claim_class == CLASS_ORDINARY:
        debtor = zm * rates["basic_coeff"]
        per_dependent = debtor * dep_coeff
    elif claim_class == CLASS_MAINTENANCE:
        # § 2 ods. 1 — výživné na maloleté dieťa: 70 % of 60 % ŽM, and the
        # per-dependant amount is 70 % of the ordinary 25 % of ŽM.
        debtor = zm * rates["maintenance_outer_coeff"] * rates["maintenance_inner_coeff"]
        per_dependent = zm * rates["maintenance_outer_coeff"] * dep_coeff
    elif claim_class == CLASS_FINE:
        debtor = zm * rates["fine_coeff"]
        per_dependent = zm * dep_coeff
    else:  # CLASS_PRIORITY — § 2 ods. 2
        debtor = zm * rates["priority_coeff"]
        per_dependent = zm * rates["priority_coeff"] * dep_coeff
    return _round(debtor, digits) + dependents * _round(per_dependent, digits)


def compute_sk(net, rates, dependents, claims, is_pensioner=False, digits=2):
    """Allocate a Slovak payslip's seizable amount across *claims*.

    :param rates: dict with ``zivotne_minimum``, ``basic_coeff``,
        ``priority_coeff``, ``maintenance_outer_coeff``,
        ``maintenance_inner_coeff``, ``fine_coeff``, ``dependent_coeff``,
        ``dependent_coeff_pensioner`` and ``unlimited_mult``.
    :param is_pensioner: poberateľ dôchodkových dávok — doubles the
        per-dependant protection to 50 %.
    """
    claims = [c for c in claims if c.due > _EPS]
    ordinary_base = sk_protected_amount(
        rates, dependents, CLASS_ORDINARY, is_pensioner, digits
    )
    detail = {"net": net, "dependents": dependents, "is_pensioner": is_pensioner}
    if not claims:
        return _empty_result(ordinary_base, net - ordinary_base, claims, detail)

    # § 3 — the unlimited-seizure threshold always keys off the § 1 ods. 1
    # basic sum, regardless of which claim is being collected.
    threshold = _round(rates["zivotne_minimum"] * rates["basic_coeff"], digits) * rates[
        "unlimited_mult"
    ]

    bases = {}
    pools = {}
    for claim_class in {c.claim_class for c in claims}:
        base = sk_protected_amount(rates, dependents, claim_class, is_pensioner, digits)
        bases[claim_class] = base
        rest = net - base
        if rest <= _EPS:
            pools[claim_class] = (0.0, 0.0)
            continue
        over = max(0.0, rest - threshold)
        thirds_base = _round_down_divisible_by_three(rest - over, digits)
        pools[claim_class] = (thirds_base / 3.0, over)

    alloc = {c.key: 0.0 for c in claims}
    breakdown = {c.key: defaultdict(float) for c in claims}
    maintenance, other_priority, ordinary = _split(claims)
    priority = maintenance + other_priority

    # --- second third + unlimited part: priority claims only --------------
    # Each priority class brings its own third; the deepest-reaching class
    # present sets the shared second-third budget, and no claim may exceed
    # what its own class would allow on its own.
    def _class_reach(claim):
        third, over = pools.get(claim.claim_class, (0.0, 0.0))
        thirds = 1.0 if claim.claim_class == CLASS_ORDINARY else 2.0
        return thirds * third + over

    priority_classes = {c.claim_class for c in priority}
    second_budget = max(
        (pools.get(cls, (0.0, 0.0))[0] for cls in priority_classes), default=0.0
    )
    priority_over = max(
        (pools.get(cls, (0.0, 0.0))[1] for cls in priority_classes), default=0.0
    )
    # § 3 — the part above the threshold is seized without limitation. Like
    # the Czech rule it joins the second third only as far as the priority
    # claims need it; the rest falls through to the first third.
    priority_need = sum(c.due for c in priority)
    unlimited_for_priority = min(
        priority_over, max(0.0, priority_need - second_budget)
    )
    unlimited_budget = priority_over
    pool = _floor_unit(second_budget + unlimited_for_priority, digits)

    if maintenance:
        need = sum(c.due for c in maintenance)
        if need <= pool + _EPS:
            for claim in maintenance:
                pool -= _take(claim, claim.due, alloc, breakdown, SOURCE_SECOND, digits)
        else:
            pool = _distribute_pro_rata(
                maintenance, pool, alloc, breakdown, SOURCE_SECOND, digits,
                weights={c.key: (c.current_maintenance or c.due) for c in maintenance},
            )
    pool = _distribute_by_rank(
        other_priority, pool, alloc, breakdown, SOURCE_SECOND, digits
    )
    second_unused = pool

    # --- first third: unsatisfied priority + ordinary, by poradie ---------
    # An ordinary claim is capped by the third computed on the 140 % base; a
    # priority claim falling back here keeps its own (deeper) reach. Whatever
    # of the unlimited part the priority claims did not need lands here.
    if ordinary:
        first_third, first_over = pools.get(CLASS_ORDINARY, (0.0, 0.0))
    else:
        first_third, first_over = second_budget, priority_over
    first_budget = _floor_unit(
        first_third + max(0.0, first_over - unlimited_for_priority), digits
    )
    first_unused = _distribute_by_rank(
        priority + ordinary, first_budget, alloc, breakdown, SOURCE_FIRST, digits
    )

    # --- global invariants -------------------------------------------------
    # 1. no claim may exceed what its own class could legally reach alone;
    # 2. the employee always retains at least the smallest base among the
    #    classes actually deducted.
    for claim in claims:
        reach = _class_reach(claim)
        if alloc[claim.key] > reach + _EPS:
            _shrink(claim, alloc[claim.key] - reach, alloc, breakdown, digits)
    # Iterated to a fixpoint: trimming can zero out a claim, and if that was
    # the only claim of the deepest-reaching class then that class no longer
    # applies and the floor rises. Computing the floor once would leave the
    # debtor below the amount actually protected. Each pass either settles or
    # drops a class, so the loop is bounded by the number of classes.
    for _pass in range(len(bases) + 1):
        used_classes = {c.claim_class for c in claims if alloc[c.key] > _EPS}
        if not used_classes:
            break
        floor = min(bases[cls] for cls in used_classes)
        excess = sum(alloc.values()) - (net - floor)
        if excess <= _EPS:
            break
        # Trim from the lowest-ranked claims first — they are the ones
        # legally last in line.
        for claim in sorted(claims, key=lambda c: c.order_key, reverse=True):
            if excess <= _EPS:
                break
            excess -= _shrink(claim, excess, alloc, breakdown, digits)

    detail.update(
        {
            "protected": ordinary_base,
            "bases": bases,
            "threshold": threshold,
            "second_budget": second_budget,
            "unlimited_budget": unlimited_budget,
            "first_budget": first_budget,
            "second_unused": second_unused,
            "first_unused": first_unused,
        }
    )
    third = pools.get(CLASS_ORDINARY, (second_budget, 0.0))[0]
    return Result(
        ordinary_base,
        max(0.0, net - ordinary_base),
        third,
        unlimited_budget,
        alloc,
        breakdown,
        detail,
    )


def _shrink(claim, amount, alloc, breakdown, digits):
    """Reduce *claim*'s allocation by at least *amount*, cheapest source first.

    Rounds the reduction UP to the currency unit. The grants being corrected
    were floored, so rounding the correction down could leave a residual
    breach of the very limit this is enforcing; rounding up over-corrects by
    less than one unit and does so in the debtor's favour, which is the right
    direction for a protective floor.
    """
    reduce_by = min(_ceil_unit(amount, digits), alloc[claim.key])
    if reduce_by <= _EPS:
        return 0.0
    # Clamp at zero: the rounding above can leave a sub-picoscale negative
    # residue, which has no business reaching a payslip line.
    alloc[claim.key] = max(0.0, alloc[claim.key] - reduce_by)
    left = reduce_by
    for source in (SOURCE_FIRST, SOURCE_UNLIMITED, SOURCE_SECOND):
        if left <= _EPS:
            break
        taken = min(left, breakdown[claim.key].get(source, 0.0))
        breakdown[claim.key][source] = max(
            0.0, breakdown[claim.key][source] - taken
        )
        left -= taken
    return reduce_by
