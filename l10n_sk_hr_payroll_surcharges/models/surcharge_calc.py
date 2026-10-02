# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Slovak wage-surcharge arithmetic — deliberately free of Odoo imports.

Everything the Zákonník práce actually mandates about *mzdové zvýhodnenia* is
tiny: an hourly base, a percentage, and a number of hours. Keeping it here
rather than in the salary rules means it can be unit tested on its own and
that both payroll engines run byte-identical arithmetic.

Two different hourly bases are in play, and mixing them up is the classic
Slovak payroll error:

* **Minimum hourly wage** (``minimálna mzda v eurách za hodinu``) — the *base*
  first-degree figure, NOT the employee's own stupeň náročnosti. Drives the
  night / Saturday / Sunday / difficult-conditions / standby surcharges
  (§ 122a–§ 123, § 96 ods. 5).
* **Average earnings** (``priemerný zárobok``, § 134) — drives the holiday and
  overtime surcharges (§ 121, § 122).

Rounding is one-directional on purpose. Every figure here is a statutory
*floor* ("najmenej 40 %"), so a half-up rounding that happened to go down
would pay less than the law requires. Amounts are therefore rounded UP to the
cent: at most €0.005 per line in the employee's favour, never a breach.
"""

import math

# --- surcharge codes ------------------------------------------------------
# The code is also the work-entry-type / payslip-input code the engines use,
# so it doubles as the key in every dict below.
CODE_NIGHT = "NOC"
CODE_SATURDAY = "SOBOTA"
CODE_SUNDAY = "NEDELA"
CODE_DIFFICULT = "STAZENY"
CODE_STANDBY = "POHOTOVOST"
CODE_HOLIDAY = "SVIATOK"
CODE_OVERTIME = "NADCAS"

# --- which hourly base each surcharge is a percentage OF ------------------
BASE_MIN_WAGE = "min_wage"
BASE_AVG_EARNINGS = "avg_earnings"

SURCHARGE_BASE = {
    CODE_NIGHT: BASE_MIN_WAGE,
    CODE_SATURDAY: BASE_MIN_WAGE,
    CODE_SUNDAY: BASE_MIN_WAGE,
    CODE_DIFFICULT: BASE_MIN_WAGE,
    CODE_STANDBY: BASE_MIN_WAGE,
    CODE_HOLIDAY: BASE_AVG_EARNINGS,
    CODE_OVERTIME: BASE_AVG_EARNINGS,
}

# Codes in the order they should appear on the payslip.
SURCHARGE_CODES = (
    CODE_NIGHT,
    CODE_SATURDAY,
    CODE_SUNDAY,
    CODE_HOLIDAY,
    CODE_OVERTIME,
    CODE_DIFFICULT,
    CODE_STANDBY,
)

# Statutory reference per code, for the payslip line help and the tests.
SURCHARGE_SECTION = {
    CODE_NIGHT: "§ 122a",
    CODE_SATURDAY: "§ 122b",
    CODE_SUNDAY: "§ 122c",
    CODE_DIFFICULT: "§ 123",
    CODE_STANDBY: "§ 96 ods. 5",
    CODE_HOLIDAY: "§ 122",
    CODE_OVERTIME: "§ 121",
}

# Which flags may move a given surcharge off its standard percentage.
#   "risk"    — riziková práca (§ 122a ods. 2, § 121 ods. 1)
#   "reduced" — a lower rate agreed in a collective agreement where the nature
#               of the work requires regular work at that time
#               (§ 122a ods. 3, § 122b ods. 2, § 122c ods. 2)
SUPPORTS_RISK = (CODE_NIGHT, CODE_OVERTIME)
SUPPORTS_REDUCED = (CODE_NIGHT, CODE_SATURDAY, CODE_SUNDAY)

# Standard weekly working time the hourly minimum-wage claims are quoted at.
STANDARD_WEEKLY_HOURS = 40.0


def _ceil_cents(value, digits=2):
    """Round *value* UP to *digits* decimals.

    ``value * 100`` is not exact in IEEE-754 — ``4.69 * 0.4 * 100`` lands on
    ``187.60000000000002``, and a naive ceil would turn €1.876 into €1.88 in
    one case and €1.89 in another. Snap to a fixed precision first, exactly
    as the garnishment kernel does, then ceil.
    """
    if value <= 0.0:
        return 0.0
    scale = 10**digits
    return math.ceil(round(value * scale, 9)) / scale


def surcharge_pct(rates, code, risk=False, reduced=False):
    """Percentage for *code*, honouring the risk / collective-agreement flags.

    *rates* is a plain dict keyed ``<code>_pct`` plus the optional
    ``<code>_risk_pct`` / ``<code>_reduced_pct`` variants. The risk rate wins
    over the reduced rate: § 122a ods. 3 allows the lower night rate only for
    work that is *not* classified as risky, so the two can never both apply.

    A missing base percentage raises rather than defaulting to zero. Every
    figure here is a statutory minimum, so silently paying nothing because a
    rate record predates a newly added surcharge code would be an unlawful
    underpayment that no test and no payslip would flag. The optional risk and
    reduced variants may legitimately be absent, and fall back to the base.
    """
    if code not in SURCHARGE_BASE:
        raise KeyError("Unknown Slovak wage-surcharge code %r" % (code,))
    key = code.lower()
    if risk and code in SUPPORTS_RISK:
        pct = rates.get("%s_risk_pct" % key)
        if pct:
            return pct
    if reduced and code in SUPPORTS_REDUCED:
        pct = rates.get("%s_reduced_pct" % key)
        if pct:
            return pct
    base_key = "%s_pct" % key
    if base_key not in rates:
        raise KeyError(
            "No %s configured on the Slovak wage-surcharge rate record; "
            "refusing to fall back to 0 %% for a statutory minimum" % base_key
        )
    return rates[base_key]


def surcharge_amount(hours, hourly_base, pct, digits=2):
    """Money for *hours* at *pct* of *hourly_base*, rounded up to the cent."""
    if hours <= 0.0 or hourly_base <= 0.0 or pct <= 0.0:
        return 0.0
    return _ceil_cents(hours * hourly_base * pct / 100.0, digits)


def min_wage_hourly(
    hourly_claim, full_time_weekly_hours,
    standard_weekly_hours=STANDARD_WEEKLY_HOURS,
):
    """Adjust an hourly minimum-wage claim for a shorter working week.

    § 120 ods. 5: where the *employer's established* weekly working time is
    below 40 hours, the hourly claims rise in proportion (the 38.75 h and
    37.5 h weeks common in Slovakia give the familiar ×1.0323 and ×1.0667).
    The statute only ever raises the figure — a longer week does not lower it,
    so the multiplier is clamped at 1.

    Note this keys off the *calendar's* full-time reference, not the
    employee's own hours: an individually part-time employee still earns the
    ordinary hourly claim, they simply work fewer hours of it.

    ``standard_weekly_hours`` is the § 85 ods. 5 ustanovený týždenný pracovný
    čas. It defaults to 40 so the kernel stays callable on its own, but the
    Odoo layer passes the dated value off the wage-surcharge rate record — a
    statutory change must be a data change, not an edit here.
    """
    if hourly_claim <= 0.0:
        return 0.0
    if not standard_weekly_hours:
        return hourly_claim
    if not full_time_weekly_hours or full_time_weekly_hours >= standard_weekly_hours:
        return hourly_claim
    return hourly_claim * standard_weekly_hours / full_time_weekly_hours


def min_wage_topup_hourly(qualifying_wage, hours_worked, hourly_claim, digits=2):
    """Doplatok for an HOURLY-paid employee (§ 120 ods. 1 a 3).

    The comparison is made per hour, which makes part-time and mid-month
    starters fall out for free: whatever fraction of the month was worked
    appears on both sides of the division.

    *qualifying_wage* must already EXCLUDE everything § 120 ods. 3 keeps out
    of the comparison — overtime pay, every mzdové zvýhodnenie computed by
    this module, and wage replacements (náhrady). Including them would let a
    night-shift surcharge paper over a sub-minimum base wage, which is the
    precise abuse the exclusion exists to stop.

    Returns the amount to add, never negative.
    """
    if hours_worked <= 0.0 or hourly_claim <= 0.0:
        return 0.0
    achieved_hourly = qualifying_wage / hours_worked
    if achieved_hourly >= hourly_claim:
        return 0.0
    return _ceil_cents((hourly_claim - achieved_hourly) * hours_worked, digits)


def min_wage_topup_monthly(
    qualifying_wage, hours_worked, full_time_hours, monthly_claim, digits=2
):
    """Doplatok for a MONTHLY-paid employee (§ 120 ods. 1, 3 a 4).

    A monthly-paid employee is measured against the MONTHLY claim, not the
    hourly one, and the two genuinely disagree: the published hourly figures
    are the monthly amount over the statutory 174 hours, so in a month that
    schedules more than 174 hours (June 2026 schedules 176) an employee paid
    exactly the monthly minimum falls short of the hourly minimum. They are
    nonetheless lawfully paid — dividing their salary by the month's hours and
    comparing against the hourly claim would invent a top-up that no employer
    owes.

    § 120 ods. 4 reduces the monthly claim in proportion where the employee
    did not work the whole month or works a shorter week. *full_time_hours*
    must therefore be what a FULL-TIME contract would have worked in the same
    period, not what this employee was scheduled: dividing a part-timer's
    hours by their own schedule always gives 1 and would hold them to the
    undiminished monthly minimum. The ratio is clamped at 1 — overtime is
    already excluded from *hours_worked*, and no amount of extra time raises
    the monthly minimum.

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
    return _ceil_cents(claim - qualifying_wage, digits)
