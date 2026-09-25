# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Shared, engine-independent definition of what the Slovak payslip must produce.

The Slovak localisation exists in two engine flavours — ``l10n_sk_hr_payroll_oca``
on the OCA ``payroll`` engine and ``l10n_sk_hr_payroll_ee`` overlaying Enterprise
``hr_payroll`` — and they are meant to be interchangeable. Until now that was a
convention, not a checked property: each suite asserted its own numbers in its
own database, so a divergence introduced on one side would surface as a wrong
payslip rather than as a failing test. Two such divergences were found by hand
in as many days, both in the seam between the engines.

This module holds ONE set of expected figures. Both engines are driven through
the same scenarios and asserted against it, so a divergence fails somewhere
instead of shipping.

Deliberately free of Odoo imports: it is a specification, and it should be
readable (and diffable) without an Odoo install.

Canonical codes
---------------
The engines agree on the money but not always on how they present it — one
splits income tax across two rules, the other emits a single line; one spells
the health top-up ``HEALTHDOPLATOK``, the other ``HEALTH_DOPLATOK``. Asserting
raw rule codes would therefore fail for cosmetic reasons and hide the real
question, which is whether the AMOUNTS agree.

That mapping is NOT defined here. It lives in
``l10n_cssk_payroll_declaration_base.rule_codes``, because the declaration
modules need it at runtime and a test harness has no business owning knowledge
that production code depends on. This module imports ``codes_for`` from there,
which also means the parity assertions and the declarations are reading the
same map — if it is wrong, both fail together rather than one quietly
disagreeing with the other.
"""

from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import (  # noqa: F401
    ENGINE_EE,
    ENGINE_OCA,
    ENGINES,
    NOT_COMPARABLE,
    codes_for,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
# Every expected figure below is one that BOTH engine suites already assert
# independently, or that was verified against a hand-computed worked example.
# Nothing here is a value read back out of the implementation.
#
#   requires  — module names that must be installed for the scenario to run.
#               A scenario whose modules are absent is skipped LOUDLY.
#   version   — values written onto the employee's hr.version.
#   inputs    — canonical input code -> quantity (hours, for the surcharges).
#   expected  — canonical concept -> amount, in EUR, to 2 decimals.

# ---------------------------------------------------------------------------
# Average earnings (§ 134) — the probable-earnings fallback
# ---------------------------------------------------------------------------
# Asserted on ``l10n_sk_average_hourly_earnings()`` directly rather than on a
# payslip line, because the divergence this pins was in the DIVISOR, and every
# náhrada inherits it: the two engines disagreed by the gap between a flat 174
# and the month's real schedule.
#
# The scenario deliberately has NO prior-quarter payslips, so the ≥168-hours
# test of § 134 ods. 3 fails and the pravdepodobný zárobok is used. June 2026
# schedules 22 working days = 176 hours on a standard 40 h week, so a 2000 EUR
# monthly wage gives 2000 / 176 = 11.3636 EUR/hour. The old Enterprise code
# divided by 174 and produced 11.4943 — 1.1 % high, silently, on every náhrada.

AVG_EARNINGS_SCENARIOS = [
    {
        "key": "phz_no_prior_quarter",
        "doc": "No history in the determining period: probable earnings are "
        "the wage over THIS period's scheduled hours (§ 134 ods. 3).",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "expected_hourly": 11.3636,
    },
]


# ---------------------------------------------------------------------------
# Leave-driven scenarios
# ---------------------------------------------------------------------------
# The scenarios above are input-driven, which left the whole absence path — the
# seam where the engines differ MOST, worked-day codes on OCA versus work-entry
# types on Enterprise — outside the harness. These book real leaves instead.
#
# ``leaves`` entries are (leave-type record name, date_from, date_to). The
# record NAME is shared; only the module prefix differs per engine, so the
# driver resolves it against whichever localisation is installed.
#
# No prior-quarter payslips exist here, so § 134 ods. 3 falls back to probable
# earnings: 2000 / 176 scheduled June hours = 11.3636 EUR/h. Five weather days
# = 40 h at the § 142 ods. 2 rate of 50 % = 227.27. Paid at the full rate — the
# behaviour before the § 142 split — it would be 454.54.

LEAVE_SCENARIOS = [
    {
        "key": "employer_obstacle_weather",
        "doc": "§ 142 ods. 2 nepriaznivé poveternostné vplyvy: náhrada at 50 % "
        "of average earnings, and BASIC prorated for the absent days.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_employer_pocasie", (2026, 6, 8), (2026, 6, 12)),
        ],
        "expected": {
            "BASIC": 1545.45,
            "EMPLOYER_OBSTACLE": 227.27,
            "GROSS": 1772.72,
        },
    },
    {
        "key": "employer_obstacle_uneven_calendar",
        "doc": "The same § 142 obstacle on a 40-hour week that is NOT 8 hours "
        "every day. A náhrada pays HOURS x priemerný hodinový zárobok, so a "
        "wage prorated by DAY fractions only makes GROSS whole when every "
        "working day is the same length — the classic kratší piatok schedule "
        "broke it. Absent the LONG day (Tue 9 June 2026, 10 h) against the "
        "100 % prestoj rate, GROSS must come out exactly at the full wage.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        # Mon 6, Tue 10, Wed 8, Thu 8, Fri 8 = 40 h, 176 h in June 2026.
        "calendar_hours": {"0": 6.0, "1": 10.0, "2": 8.0, "3": 8.0, "4": 8.0},
        "leaves": [
            ("l10n_sk_leave_type_employer_prestoj", (2026, 6, 9), (2026, 6, 9)),
        ],
        "expected": {
            # 2000 x 166/176 scheduled hours
            "BASIC": 1886.36,
            # 10 h x 11.3636
            "EMPLOYER_OBSTACLE": 113.64,
            # a 100 % reason leaves the wage untouched
            "GROSS": 2000.00,
        },
    },
]


SCENARIOS = [
    {
        "key": "base_2026",
        "doc": "Full month, 2000 EUR, declaration signed, two children under 15. "
        "Exercises the 2026 dated parameters: health 5 %, NCZD 497.23.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 2,
        },
        "inputs": {},
        "expected": {
            "GROSS": 2000.00,
            "SOCIAL_EE_TOTAL": -288.00,
            "HEALTH_EE": -100.00,
            "HEALTH_ER": 220.00,
            "TAXBASE": 1712.00,
            "INCOME_TAX": -230.81,
            "CHILD_BONUS": 200.00,
            "NET": 1681.19,
        },
    },
    {
        "key": "meal_financial_contribution",
        "doc": "Finančný príspevok na stravovanie instead of vouchers. The "
        "employer's cash contribution is exempt from GROSS but IS paid with "
        "the wage, so it must reach NET.\n"
        "\n"
        "Added because a sweep for enumerated values nothing produces found "
        "that 'financial' is branched on by the OCA NET rule and referenced "
        "nowhere at all in the Enterprise module. Whether that is a real "
        "divergence depends on the upstream Enterprise NET rule, which source "
        "reading cannot settle — so it is asked here instead.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_meal_allowance_type": "financial",
            "l10n_sk_meal_days": 20,
        },
        "inputs": {},
        "expected": {
            # The contribution is exempt, so the taxable side is untouched.
            "GROSS": 2000.00,
            # ... and it is paid in cash with the wage, so it reaches NET:
            # 2000 - 188.00 social - 100.00 health - 230.81 tax + 102.40 meal.
            # The 102.40 is 20 days x 55 % of the 9.30 stravné rounded UP to
            # the cent (5.115 -> 5.12), which is what § 152 requires of a
            # minimum and what keeps the two engines on the same figure.
            "NET": 1583.59,
        },
        # Signed comparison is not available for this line: OCA emits the
        # employer contribution positive and Enterprise negative, each with a
        # NET assembly to match. The magnitude is the part that must agree.
        "expected_abs": {
            "MEAL_EMPLOYER": 102.40,
        },
    },
    {
        "key": "base_2025",
        "doc": "The same contract a year earlier. Proves both engines read the "
        "SAME dated parameters: health 4 %, NCZD 479.48.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2025, 6, 1), (2025, 6, 30)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 2,
        },
        "inputs": {},
        "expected": {
            "GROSS": 2000.00,
            "HEALTH_EE": -80.00,
            "TAXBASE": 1732.00,
            "INCOME_TAX": -237.98,
            "CHILD_BONUS": 200.00,
            "NET": 1694.02,
        },
    },
    {
        "key": "no_declaration",
        "doc": "Children on file but no signed declaration: neither the NCZD nor "
        "the child bonus may be applied. Gating must agree across engines.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_tax_declaration_signed": False,
            "l10n_sk_children_under_15": 2,
        },
        "inputs": {},
        "expected": {
            "TAXBASE": 1712.00,
            "INCOME_TAX": -325.28,
            "CHILD_BONUS": 0.00,
            "NET": 1386.72,
        },
    },
    {
        "key": "ztp",
        "doc": "Disabled employee: the halved health rate (2.5 % in 2026).",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_tax_declaration_signed": True, "l10n_sk_ztp": True},
        "inputs": {},
        "expected": {"HEALTH_EE": -50.00},
    },
    {
        "key": "surcharges",
        "doc": "Night, Saturday and Sunday hours at the 2026 minimum hourly wage "
        "of 5.259. Also proves the surcharges reach GROSS on both engines, "
        "which is what makes them insurable and taxable.",
        "requires": ["l10n_sk_hr_payroll_priplatky"],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_tax_declaration_signed": True},
        "inputs": {"NOC": 10.0, "SOBOTA": 8.0, "NEDELA": 4.0},
        "expected": {
            # 10 h x 40 % / 8 h x 50 % / 4 h x 100 %, each 21.036 -> 21.04
            "PRIPLATOK_NOC": 21.04,
            "PRIPLATOK_SOBOTA": 21.04,
            "PRIPLATOK_NEDELA": 21.04,
            "GROSS": 2063.12,
        },
    },
    {
        "key": "min_wage_topup",
        "doc": "A sub-minimum salary in a full month: the doplatok brings 800 EUR "
        "up to the 2026 monthly minimum of 915.",
        "requires": ["l10n_sk_hr_payroll_priplatky"],
        "wage": 800.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_tax_declaration_signed": True},
        "inputs": {},
        "expected": {"MIN_WAGE_TOPUP": 115.00, "GROSS": 915.00},
    },
    {
        "key": "minimum_wage_exactly",
        "doc": "Exactly the monthly minimum wage in a 176-hour month. Nothing is "
        "owed, even though 915/176 falls under the 5.259 hourly figure — the "
        "monthly-versus-hourly trap, asserted on both engines.",
        "requires": ["l10n_sk_hr_payroll_priplatky"],
        "wage": 915.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_tax_declaration_signed": True},
        "inputs": {},
        "expected": {"MIN_WAGE_TOPUP": 0.00, "GROSS": 915.00},
    },
]


# ---------------------------------------------------------------------------
# Declaration scenarios
# ---------------------------------------------------------------------------
# The payroll scenarios above prove the two engines compute the same payslip.
# These prove the declaration modules then REPORT the same figures — which is a
# separate property, because every declaration module reads payslip lines by
# rule code and the codes differ per engine.
#
# The expected figures are fixed constants, deliberately NOT read back from the
# payslip in the same database. Each module's own test already compares its
# output against the payslip beside it, which cannot detect the two engines
# agreeing with themselves and disagreeing with each other.
#
# Element paths are given as slash-separated LOCAL names, so the same notation
# works for the namespaced and un-namespaced schemas in the family.

# One employee, 2000 EUR, declaration signed, no children, March 2026.
# Derived by hand from the statutory rates:
#   employee social  9.40 % (1.4 sick + 4 pension + 3 disability + 1 unemp) = 188.00
#   -> social-insurance premium owed to the Sociálna poisťovňa              = 692.00
#   employer social 25.20 % (1.4 sick + 14 pension + 3 disability
#                            + 0.5 unemployment + 0.25 guarantee + 0.8 accident
#                            + 4.75 reserve + 0.5 shorttime)                = 504.00
#   employee health  5.00 %                                                 = 100.00
#   employer health 11.00 %                                                 = 220.00
#   income-tax advance 19 % x (2000 - 188 - 100 - 497.23 NCZD)              = 230.81
DECLARATION_WAGE = 2000.0
# A second employee on a DoPČ with irregular income. The Sociálna poisťovňa
# splits its two monthly forms by exactly that: regular income belongs on the
# MVP, irregular on the VPP. One of each in the fixture makes the split
# assertable rather than assumed.
DECLARATION_DOHODA_WAGE = 400.0

# The VPP is NOT in DECLARATION_SCENARIOS. Those aggregate over the whole
# company for the period, so every employee in the fixture moves every one of
# their figures; adding a dohodár there changed the MVP total from 692 to
# 811.20 and the Prehľad base from 2000 to 2400. The VPP/MVP split therefore
# gets its own fixture inside its own test, where the rollback keeps it from
# touching the hand-derived constants next door.
DECLARATION_PERIOD = ((2026, 3, 1), (2026, 3, 31))

# ---------------------------------------------------------------------------
# Annual declarations
# ---------------------------------------------------------------------------
# The ELDP and the Hlásenie report a whole year, so they need twelve payslips
# rather than the single March one the monthly scenarios share. That fixture
# is built inside its own test for the same reason the VPP one is: a figure
# here is a sum over everything in the company for the year, so seeding it
# alongside the monthly scenarios would move their constants too.
#
# Every expectation below is twelve times a monthly figure the monthly
# scenarios already assert independently — 2000.00 gross and a 230.81 tax
# advance — so the annual forms are pinned to the same hand-derived numbers
# rather than to whatever the annual code happens to produce.
ANNUAL_DECLARATION_MONTHS = 12

ANNUAL_DECLARATION_SCENARIOS = [
    {
        "key": "eldp_2026",
        "doc": "Evidenčný list dôchodkového poistenia. vzDP is the pension "
        "assessment base for the whole year: 12 x 2000.00.",
        "requires": ["l10n_sk_hr_payroll_eldp"],
        "model": "l10n.sk.eldp",
        "create": {"year": "2026"},
        "expected": {
            "obdobiaPoist/vzZaObdobiePoist@vzDP": 24000.00,
            # dniVyluc is deliberately NOT here. It is a hardcoded 0 in the
            # model, and QWeb omits a falsy t-att entirely, so the attribute
            # never reaches the XML at all. A dedicated assertion in the test
            # pins that absence, so the day vylúčené doby start being derived
            # the harness says so instead of the change slipping through.
        },
    },
    {
        "key": "hlasenie_2026",
        "doc": "Annual income-tax report. r00 and r01 are the yearly sums of "
        "the same base and advance the monthly Prehľad reports.",
        "requires": ["l10n_sk_hr_payroll_hlasenie"],
        "model": "l10n.sk.hlasenie",
        "create": {"year": "2026"},
        "expected": {
            "r00": 24000.00,
            "r01": 2769.72,
        },
    },
]


DECLARATION_SCENARIOS = [
    {
        "key": "mvp_2026_03",
        "doc": "Sociálna poisťovňa monthly statement. spoluPoistne is SOCIAL "
        "insurance only — health premiums go to the health insurers on dávka "
        "514 and must not appear here.",
        "requires": ["l10n_sk_hr_payroll_mvp"],
        "model": "l10n.sk.mvp",
        "create": {"year": "2026", "month": "3"},
        "expected": {
            "poistne/spoluPoistne": 692.00,
        },
    },
    {
        "key": "health_2026_03",
        "doc": "Dávka 514. The employee/employer health advances, which are "
        "exactly what must NOT be in the MVP total.",
        "requires": ["l10n_sk_hr_payroll_health"],
        "model": "l10n.sk.health",
        "create": {"year": "2026", "month": "3"},
        "expected": {
            "PersonData/DepositOfEmployee": 100.00,
            "PersonData/DepositOfEmployer": 220.00,
            "InsuranceBody/DepositOfInsurance1": 220.00,
        },
    },
    {
        "key": "prehlad_2026_03",
        "doc": "Monthly income-tax overview. r01 is the concept whose rule "
        "codes differ per engine, so it is the one most at risk.",
        "requires": ["l10n_sk_hr_payroll_prehlad"],
        "model": "l10n.sk.prehlad",
        "create": {"year": "2026", "month": "3"},
        "expected": {
            "telo/cast1/r00": 2000.00,
            "telo/cast1/r01/suma": 230.81,
            "telo/cast1/r04": 230.81,
        },
    },
]
