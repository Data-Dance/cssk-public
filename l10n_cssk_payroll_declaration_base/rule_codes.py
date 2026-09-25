# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The one place that knows which salary-rule codes carry which concept.

The Czech and Slovak payroll each ship for two engines — the OCA ``payroll``
engine and Odoo Enterprise ``hr_payroll`` — and the two do not always present
the same concept the same way. Enterprise splits the Slovak monthly income-tax
advance across one rule per band; the OCA side emits a single line. Enterprise
spells the health minimum-advance top-up ``HEALTH_DOPLATOK``; the OCA side
``HEALTHDOPLATOK``. Garnishment is one rule on one engine and two on the other.

Anything reading payslip lines by rule code therefore has to know all of this,
and every declaration module in the family does read payslip lines by rule
code. Before this module existed each had worked it out privately: two of them
carried byte-identical copies of the income-tax tuple, a third its own tuple
for the health top-up. They were all correct, which is precisely the problem —
being correct by three independent acts of care is not a property you can rely
on for the fourth.

Deliberately free of Odoo imports so it can be read, diffed and unit-tested as
what it is: a specification of a naming difference.

Two ways to consume it:

* ``sum_concept(totals, concept)`` — sums every code that could carry the
  concept, on either engine. This is what the declaration modules want: they
  run against whichever engine is installed and codes that do not exist
  contribute nothing, so the union is both correct and engine-agnostic.
* ``codes_for(concept, engine)`` — the codes for ONE engine. This is what the
  parity harness wants, because it is asserting what a particular engine
  produced and must not silently accept the other engine's answer.
"""

ENGINE_OCA = "oca"
ENGINE_EE = "ee"
ENGINES = (ENGINE_OCA, ENGINE_EE)

COUNTRY_SK = "SK"
COUNTRY_CZ = "CZ"

# country -> concept -> engine -> tuple of salary-rule codes
RULE_CODES = {
    COUNTRY_SK: {
        # --- identical on both engines --------------------------------
        "GROSS": {ENGINE_OCA: ("GROSS",), ENGINE_EE: ("GROSS",)},
        "BASIC": {ENGINE_OCA: ("BASIC",), ENGINE_EE: ("BASIC",)},
        "NET": {ENGINE_OCA: ("NET",), ENGINE_EE: ("NET",)},
        "TAXBASE": {ENGINE_OCA: ("TAXBASE",), ENGINE_EE: ("TAXBASE",)},
        "HEALTH_EE": {ENGINE_OCA: ("HEALTH",), ENGINE_EE: ("HEALTH",)},
        "HEALTH_ER": {
            ENGINE_OCA: ("HEALTHEMPLOYER",), ENGINE_EE: ("HEALTHEMPLOYER",),
        },
        "CHILD_BONUS": {
            ENGINE_OCA: ("CHILD_BONUS",), ENGINE_EE: ("CHILD_BONUS",),
        },
        "SOCIAL_EE_TOTAL": {
            ENGINE_OCA: ("SOCIALEMPLOYEETOTAL",),
            ENGINE_EE: ("SOCIALEMPLOYEETOTAL",),
        },
        "SOCIAL_ER_TOTAL": {
            ENGINE_OCA: ("SOCIALEMPLOYERTOTAL",),
            ENGINE_EE: ("SOCIALEMPLOYERTOTAL",),
        },
        "PRIPLATOK_NOC": {
            ENGINE_OCA: ("PRIPLATOK_NOC",), ENGINE_EE: ("PRIPLATOK_NOC",),
        },
        "PRIPLATOK_SOBOTA": {
            ENGINE_OCA: ("PRIPLATOK_SOBOTA",), ENGINE_EE: ("PRIPLATOK_SOBOTA",),
        },
        "PRIPLATOK_NEDELA": {
            ENGINE_OCA: ("PRIPLATOK_NEDELA",), ENGINE_EE: ("PRIPLATOK_NEDELA",),
        },
        "MIN_WAGE_TOPUP": {
            ENGINE_OCA: ("MIN_WAGE_TOPUP",), ENGINE_EE: ("MIN_WAGE_TOPUP",),
        },
        "EMPLOYER_OBSTACLE": {
            ENGINE_OCA: ("PREKAZKA_NAHRADA",), ENGINE_EE: ("PREKAZKA_NAHRADA",),
        },
        "MEAL_EMPLOYER": {
            ENGINE_OCA: ("MEALEMPLOYER",), ENGINE_EE: ("MEALEMPLOYER",),
        },
        # --- presented differently by the two engines -----------------
        # Enterprise splits the monthly advance one rule per band; the OCA
        # side computes the whole progressive table in a single rule.
        "INCOME_TAX": {
            ENGINE_OCA: ("INCOMETAX",),
            ENGINE_EE: ("INCOMETAX19", "INCOMETAX25"),
        },
        # Same concept, different spelling.
        "HEALTH_TOPUP": {
            ENGINE_OCA: ("HEALTHDOPLATOK",),
            ENGINE_EE: ("HEALTH_DOPLATOK",),
        },
        # Enterprise splits ordinary and priority garnishment.
        "GARNISHMENT": {
            ENGINE_OCA: ("GARNISHMENT",),
            ENGINE_EE: ("GARNISHMENT", "GARNISHMENT_PRIORITY"),
        },
    },
    COUNTRY_CZ: {
        # The Czech modules happen to agree on every code today. Listing them
        # anyway is the point: the map is where a future divergence gets
        # recorded, and an empty CZ section would invite the next author to
        # hardcode instead.
        "GROSS": {ENGINE_OCA: ("GROSS",), ENGINE_EE: ("GROSS",)},
        "NET": {ENGINE_OCA: ("NET",), ENGINE_EE: ("NET",)},
        "INCOME_TAX": {ENGINE_OCA: ("INCOMETAX",), ENGINE_EE: ("INCOMETAX",)},
        "INCOME_TAX_TOTAL": {
            ENGINE_OCA: ("INCOMETAXTOT",), ENGINE_EE: ("INCOMETAXTOT",),
        },
        "SOCIAL_EE_TOTAL": {
            ENGINE_OCA: ("SOCIALEETOT",), ENGINE_EE: ("SOCIALEETOT",),
        },
        "SOCIAL_ER_TOTAL": {
            ENGINE_OCA: ("SOCIALERTOT",), ENGINE_EE: ("SOCIALERTOT",),
        },
        "HEALTH_EE": {ENGINE_OCA: ("HEALTHEE",), ENGINE_EE: ("HEALTHEE",)},
        "HEALTH_ER": {ENGINE_OCA: ("HEALTHER",), ENGINE_EE: ("HEALTHER",)},
        "BASIC": {ENGINE_OCA: ("BASIC",), ENGINE_EE: ("BASIC",)},
        "HOLIDAY_NAHRADA": {
            ENGINE_OCA: ("HOLIDAYNAHRADA",), ENGINE_EE: ("HOLIDAYNAHRADA",),
        },
        "EMPLOYER_OBSTACLE": {
            ENGINE_OCA: ("PREKAZKANAHRADA",), ENGINE_EE: ("PREKAZKANAHRADA",),
        },
    },
}

# Concepts that genuinely cannot be compared across engines, with the reason.
# Named rather than merely absent, so the omission is not mistaken for an
# oversight and "fixed" by someone adding a bogus mapping.
NOT_COMPARABLE = {
    "MEAL_EMPLOYER_SIGNED": "The employer meal contribution has opposite SIGNS "
    "on the two engines — positive on OCA, negative on Enterprise — and each "
    "assembles NET to match, so the employee is paid the same and both report "
    "the same magnitude. Unifying it would mean overriding upstream "
    "Enterprise's NET rule, which is a large intervention for a difference "
    "nothing currently reads. Compare the MAGNITUDE instead: the parity "
    "scenario meal_financial_contribution asserts it through expected_abs. If "
    "a declaration or report ever needs this line, it must take abs() or the "
    "two engines will disagree by twice the amount.",
    "HOURLY_PAY": "The OCA engine has an hourly-pay path the Enterprise one "
    "does not: its BASIC rule branches on l10n_sk_hourly_wage and pays "
    "hours x rate with no proration, for a DoBPŠ student paid per actual "
    "hour. The Enterprise module defines no such field and always prorates a "
    "monthly wage, so an Enterprise deployment cannot express hourly pay "
    "through the SK module at all. This is a CAPABILITY gap rather than a "
    "silently wrong number — there is nothing to configure on the Enterprise "
    "side — but it is a real parity break and it is why no scenario compares "
    "an hourly worker. Found by the engine-seam audit, 2026-08-06.",

    "NCZD": "Enterprise emits the Slovak non-taxable part as its own payslip "
    "line; the OCA rule applies it inside INCOMETAX and never materialises it. "
    "Compare through INCOME_TAX and NET instead.",
    "PN_DVZ": "Both engines take the daily assessment base as an input rather "
    "than deriving it, so comparing it compares the fixture, not the code.",
}


def codes_for(concept, engine, country=COUNTRY_SK):
    """The rule codes carrying *concept* on *engine*.

    Raises rather than returning an empty tuple: summing no codes yields 0.00,
    which reads as a perfectly plausible answer.
    """
    try:
        return RULE_CODES[country][concept][engine]
    except KeyError:
        raise KeyError(
            "No rule-code mapping for concept %r on engine %r in %s. Add it to "
            "RULE_CODES, or to NOT_COMPARABLE with a reason."
            % (concept, engine, country)
        )


def all_codes_for(concept, country=COUNTRY_SK):
    """Every code that could carry *concept*, on either engine."""
    codes = []
    for engine in ENGINES:
        for code in codes_for(concept, engine, country):
            if code not in codes:
                codes.append(code)
    return tuple(codes)


def sum_concept(totals, concept, country=COUNTRY_SK, absolute=True):
    """Sum *concept* out of a ``{rule_code: amount}`` mapping.

    Sums the codes of BOTH engines: only one engine is ever installed, so the
    other's codes are simply absent and contribute nothing. That keeps the
    caller from having to detect the engine at all.

    *absolute* mirrors what the declaration modules want — statutory forms
    report withheld amounts as positive figures, while the payslip carries them
    as negative deductions.
    """
    total = sum(totals.get(code, 0.0) for code in all_codes_for(concept, country))
    return abs(round(total, 2)) if absolute else round(total, 2)
