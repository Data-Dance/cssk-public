# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Czech wage-surcharge arithmetic — deliberately free of Odoo imports.

The Slovak sibling (``l10n_sk_hr_payroll_priplatky``) is the model for this
file, and the two look alike on purpose: an hourly base, a percentage, and a
number of hours. What is NOT alike is which base each surcharge takes, and
that is the whole reason the Slovak kernel could not simply be reused.

**In Slovakia the majority of surcharges are a percentage of the minimum
hourly wage. In Czechia it is the other way round**: § 114–§ 116 and § 118 are
percentages of *průměrný výdělek* (§ 351 an.), and only § 117 (ztížené
pracovní prostředí) is a percentage of the minimum wage. Porting the Slovak
percentages onto the Slovak bases would have produced plausible figures that
are wrong for every employee whose average earnings differ from the minimum
wage — which is almost all of them.

Statutory basis, zákoník práce (zákon č. 262/2006 Sb.), private-sector *mzda*:

* § 114 práce přesčas — at least **25 %** of average earnings, unless
  compensatory time off (náhradní volno) is agreed instead.
* § 115 práce ve svátek — náhradní volno plus wage replacement, or, if agreed,
  a supplement of at least **100 %** of average earnings.
* § 116 noční práce — at least **10 %** of average earnings. A different
  minimum may be agreed (``Je však možné sjednat jinou minimální výši``).
* § 117 ztížené pracovní prostředí — at least **10 % of the basic minimum wage
  rate**, per aggravating factor (nařízení vlády č. 567/2006 Sb. defines the
  factors), NOT of average earnings.
* § 118 práce v sobotu a v neděli — at least **10 %** of average earnings, and
  again a different minimum may be agreed.

Saturday and Sunday share one section and one rate here, unlike Slovakia where
§ 122b and § 122c set them apart (50 % / 100 %). They are therefore one code.

Surcharges COMBINE: an overtime hour worked on a Saturday night carries § 114
+ § 116 + § 118. That falls out of recording hours per code and summing, so
there is no combination logic here — but it is why each code must count only
its own hours and never "the hour" as a whole.

Rounding is one-directional, exactly as in the Slovak kernel: every figure is
a statutory *floor* ("nejméně"), so a half-up rounding that happened to go
down would underpay. Amounts round UP — at most CZK 0.005 per line in the
employee's favour, never a breach.
"""

import math

# --- surcharge codes ------------------------------------------------------
# The code doubles as the work-entry-type / payslip-input code in both engine
# bridges, so it is the key in every dict below.
CODE_OVERTIME = "PRESCAS"
CODE_HOLIDAY = "SVATEK"
CODE_NIGHT = "NOCNI"
CODE_DIFFICULT = "ZTIZENE"
CODE_WEEKEND = "VIKEND"

# --- which hourly base each surcharge is a percentage OF ------------------
BASE_MIN_WAGE = "min_wage"
BASE_AVG_EARNINGS = "avg_earnings"

SURCHARGE_BASE = {
    CODE_OVERTIME: BASE_AVG_EARNINGS,
    CODE_HOLIDAY: BASE_AVG_EARNINGS,
    CODE_NIGHT: BASE_AVG_EARNINGS,
    CODE_WEEKEND: BASE_AVG_EARNINGS,
    CODE_DIFFICULT: BASE_MIN_WAGE,
}

# Codes in the order they should appear on the payslip.
SURCHARGE_CODES = (
    CODE_OVERTIME,
    CODE_HOLIDAY,
    CODE_NIGHT,
    CODE_WEEKEND,
    CODE_DIFFICULT,
)

# Statutory reference per code, for the payslip line help and the tests.
SURCHARGE_SECTION = {
    CODE_OVERTIME: "§ 114",
    CODE_HOLIDAY: "§ 115",
    CODE_NIGHT: "§ 116",
    CODE_DIFFICULT: "§ 117",
    CODE_WEEKEND: "§ 118",
}

# § 116 and § 118 both end with "Je však možné sjednat jinou minimální výši a
# způsob určení příplatku" — a collective or individual agreement may set a
# different minimum. No such sentence appears in § 114, § 115 or § 117, so an
# agreed rate is accepted only for these two.
SUPPORTS_AGREED = (CODE_NIGHT, CODE_WEEKEND)

# § 117 is owed per aggravating factor, so its hours carry a multiplier the
# other codes do not have.
SUPPORTS_FACTORS = (CODE_DIFFICULT,)

# The weekly working time the published hourly minimum wage is quoted at
# (§ 79 odst. 1 — stanovená týdenní pracovní doba).
STANDARD_WEEKLY_HOURS = 40.0


def _ceil_haleru(value, digits=2):
    """Round *value* UP to *digits* decimals.

    ``value * 100`` is not exact in IEEE-754, so a naive ceil turns the same
    arithmetic into two different answers depending on the operands. Snap to a
    fixed precision first — as the Slovak kernel and the garnishment kernel
    both do — and only then ceil.
    """
    if value <= 0.0:
        return 0.0
    scale = 10**digits
    return math.ceil(round(value * scale, 9)) / scale


def surcharge_pct(rates, code, agreed=False):
    """Percentage for *code*, honouring an agreed alternative minimum.

    *rates* is a plain dict keyed ``<code>_pct`` plus the optional
    ``<code>_agreed_pct`` variant.

    A missing base percentage raises rather than defaulting to zero. Every
    figure here is a statutory minimum, so silently paying nothing because a
    rate record predates a newly added code would be an unlawful underpayment
    that neither a test nor a payslip would show. The agreed variant may
    legitimately be absent and falls back to the statutory figure.
    """
    if code not in SURCHARGE_BASE:
        raise KeyError("Unknown Czech wage-surcharge code %r" % (code,))
    key = code.lower()
    if agreed and code in SUPPORTS_AGREED:
        pct = rates.get("%s_agreed_pct" % key)
        if pct:
            return pct
    base_key = "%s_pct" % key
    if base_key not in rates:
        raise KeyError(
            "No %s configured on the Czech wage-surcharge rate record; "
            "refusing to fall back to 0 %% for a statutory minimum" % base_key
        )
    return rates[base_key]


def surcharge_amount(hours, hourly_base, pct, factors=1, digits=2):
    """Money for *hours* at *pct* of *hourly_base*, rounded up to the haléř.

    *factors* is the § 117 multiplier — the number of aggravating influences
    present, each of which earns its own 10 %. It is 1 for every other code,
    and a caller passing 0 or a negative gets nothing rather than a credit.
    """
    if hours <= 0.0 or hourly_base <= 0.0 or pct <= 0.0 or factors <= 0:
        return 0.0
    return _ceil_haleru(hours * hourly_base * pct * factors / 100.0, digits)


def min_wage_hourly(
    hourly_claim, full_time_weekly_hours,
    standard_weekly_hours=STANDARD_WEEKLY_HOURS,
):
    """Adjust the hourly minimum-wage claim for a shorter working week.

    The published hourly figure (134.40 Kč for 2026) assumes the § 79 odst. 1
    forty-hour week. Where the employer's *stanovená* weekly working time is
    shorter — the 37.5 h and 38.75 h weeks of § 79 odst. 2 — the hourly claim
    rises in proportion, so that a full month still reaches the monthly
    minimum. The statute only ever raises the figure, so the multiplier is
    clamped at 1.

    This keys off the employer's full-time reference, not the employee's own
    hours: someone individually part-time still earns the ordinary hourly
    claim, they simply work fewer hours of it.
    """
    if hourly_claim <= 0.0:
        return 0.0
    if not standard_weekly_hours:
        return hourly_claim
    if not full_time_weekly_hours or full_time_weekly_hours >= standard_weekly_hours:
        return hourly_claim
    return hourly_claim * standard_weekly_hours / full_time_weekly_hours


def min_wage_topup_hourly(qualifying_wage, hours_worked, hourly_claim, digits=2):
    """Doplatek to the minimum wage for an HOURLY-paid employee (§ 111 odst. 3).

    The comparison is per hour, which makes part-timers and mid-month starters
    fall out for free: the fraction of the month worked appears on both sides.

    *qualifying_wage* must already EXCLUDE what § 111 odst. 3 keeps out of the
    comparison — mzda za práci přesčas and the příplatky for svátek, noční
    práce, ztížené pracovní prostředí and sobota/neděle, i.e. every surcharge
    this module computes. Including them would let a night shift paper over a
    sub-minimum base wage, which is the precise abuse the exclusion exists to
    prevent.

    Returns the amount to add, never negative.
    """
    if hours_worked <= 0.0 or hourly_claim <= 0.0:
        return 0.0
    achieved_hourly = qualifying_wage / hours_worked
    if achieved_hourly >= hourly_claim:
        return 0.0
    return _ceil_haleru((hourly_claim - achieved_hourly) * hours_worked, digits)


def min_wage_topup_monthly(
    qualifying_wage, hours_worked, full_time_hours, monthly_claim, digits=2
):
    """Doplatek for a MONTHLY-paid employee (§ 111 odst. 3).

    A monthly-paid employee is measured against the MONTHLY claim, not the
    hourly one, and the two genuinely disagree: the published hourly figure is
    the monthly amount over a nominal month, so in a month that schedules more
    hours than that nominal an employee paid exactly the monthly minimum falls
    short of the hourly minimum while being lawfully paid. Dividing their
    salary by the month's hours and comparing against the hourly claim would
    invent a top-up no employer owes.

    *full_time_hours* must be what a FULL-TIME contract would have worked in
    the same period, not what this employee was scheduled: dividing a
    part-timer's hours by their own schedule always gives 1 and would hold
    them to the undiminished monthly minimum. The ratio is clamped at 1 —
    overtime is excluded from *hours_worked* and no amount of extra time
    raises the monthly minimum.

    *qualifying_wage* carries the same exclusions as the hourly variant.
    """
    if monthly_claim <= 0.0 or full_time_hours <= 0.0:
        return 0.0
    ratio = min(1.0, hours_worked / full_time_hours)
    if ratio <= 0.0:
        return 0.0
    claim = monthly_claim * ratio
    if qualifying_wage >= claim:
        return 0.0
    return _ceil_haleru(claim - qualifying_wage, digits)
