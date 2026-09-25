# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Shared, engine-independent definition of what the Czech payslip must produce.

The Czech localisation exists in two engine flavours — ``l10n_cz_hr_payroll_oca``
on the OCA ``payroll`` engine and ``l10n_cz_hr_payroll_ee`` on Enterprise
``hr_payroll`` — and they are meant to be interchangeable. Each suite asserted
its own numbers in its own database, so a divergence introduced on one side
would surface as a wrong payslip rather than as a failing test.

The Slovak counterpart of this module has now caught three such divergences,
every one of them found by accident first and only afterwards covered:

  * the average-earnings fallback divided by a flat 174 hours on one engine and
    by the period's real schedule on the other — 1.1 % on every náhrada;
  * one engine counted DRAFT payslips in the determining period, the other did
    not;
  * the basic wage was prorated by DAY fractions on one engine and by HOURS on
    the other, so a náhrada stopped making gross whole on any calendar that is
    not the same length every day.

None of the three was exotic. All three sat outside what the scenarios happened
to touch. That is the lesson this file exists to apply to Czechia BEFORE the
same bugs are found in production: a harness proves what it exercises and
nothing else, so the scenarios must reach the seams, not just the happy path.

Deliberately free of Odoo imports: it is a specification, and it should be
readable (and diffable) without an Odoo install.

Canonical codes
---------------
The engines agree on the money but need not agree on how they present it, so
asserting raw rule codes would fail for cosmetic reasons and hide the real
question, which is whether the AMOUNTS agree. That mapping lives in
``l10n_cssk_payroll_declaration_base.rule_codes`` (shared with the declaration
modules), not here.
"""

from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import (  # noqa: F401
    COUNTRY_CZ,
    ENGINE_EE,
    ENGINE_OCA,
    ENGINES,
    NOT_COMPARABLE,
    codes_for,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
#   requires  — module names that must be installed for the scenario to run.
#               A scenario whose modules are absent is skipped LOUDLY.
#   version   — values written onto the employee's hr.version.
#   leaves    — (leave-type record name, date_from, date_to). The record NAME is
#               shared between the two localisations; only the module prefix
#               differs, so the driver resolves it against whichever is present.
#   calendar_hours — dayofweek -> hours, to pin a week that is full-time
#               WITHOUT being the same length every day.
#   expected  — canonical concept -> amount, in CZK, to 2 decimals.
#
# Every figure below is either asserted independently by both engine suites or
# hand-computed from the statute; nothing here is a value read back out of the
# implementation.

WAGE = 50000.0

# A plain worked March 2026 seeds the rozhodné období, so the průměrný výdělek
# is the real computed one rather than the probable-earnings fallback.
SEED_PERIOD = ((2026, 3, 1), (2026, 3, 31))
PERIOD = ((2026, 6, 1), (2026, 6, 30))

SCENARIOS = [
    {
        "key": "full_month",
        "doc": "A plain worked month on a declared tax status: no absence, so "
        "BASIC is the whole wage and GROSS follows it.",
        "requires": [],
        "wage": WAGE,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "expected": {
            "BASIC": 50000.00,
            "GROSS": 50000.00,
        },
    },
    {
        "key": "employer_obstacle_prostoj",
        "doc": "§ 207 a) prostoj — náhrada at 80 % of průměrný výdělek, and "
        "BASIC prorated down for the absent hours. The rate is the point: "
        "recorded as the § 199 obstacle this was paid at 100 %.",
        "requires": [],
        "wage": WAGE,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [
            ("leave_type_cz_employer_prostoj", (2026, 6, 1), (2026, 6, 5)),
        ],
        # 176 scheduled June hours, 40 absent. PHV from the March seed =
        # 50000 / 176 = 284.0909. BASIC 50000 x 136/176 = 38636.36;
        # náhrada 40 x 284.0909 x 80 % = 9090.91.
        "expected": {
            "BASIC": 38636.36,
            "EMPLOYER_OBSTACLE": 9090.91,
            "GROSS": 47727.27,
        },
    },
    {
        "key": "employer_obstacle_uneven_calendar",
        "doc": "The § 208 100 % reason on a full-time week that is NOT the "
        "same length every day. A náhrada pays HOURS x průměrný hodinový "
        "výdělek, so a wage prorated by DAY fractions would stop making GROSS "
        "whole — the bug found on the Slovak side. Absent the LONG day.",
        "requires": [],
        "wage": WAGE,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        # Mon 6, Tue 10, Wed 8, Thu 8, Fri 8 = 40 h, 176 h in June 2026.
        "calendar_hours": {"0": 6.0, "1": 10.0, "2": 8.0, "3": 8.0, "4": 8.0},
        "leaves": [
            # Tuesday 9 June 2026 — the 10-hour day.
            ("leave_type_cz_employer_jine", (2026, 6, 9), (2026, 6, 9)),
        ],
        # BASIC 50000 x 166/176 = 47159.09; náhrada 10 x 284.0909 = 2840.91.
        # A 100 % reason must leave GROSS at exactly the full wage.
        "expected": {
            "BASIC": 47159.09,
            "EMPLOYER_OBSTACLE": 2840.91,
            "GROSS": 50000.00,
        },
    },
]

# ---------------------------------------------------------------------------
# Average earnings (§ 351 a nasl.)
# ---------------------------------------------------------------------------
# Asserted on ``l10n_cz_average_hourly_earnings()`` directly rather than on a
# payslip line, because a divergence in the DIVISOR moves every náhrada at once
# and would otherwise only show up wherever a scenario happens to book one.

AVG_EARNINGS_SCENARIOS = [
    {
        "key": "phv_from_prior_quarter",
        "doc": "With a full worked March seeded, the průměrný hodinový výdělek "
        "is the counted wage over the worked hours: 50000 / 176.",
        "requires": [],
        "wage": WAGE,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "seed_prior_quarter": True,
        "expected_hourly": round(50000.0 / 176.0, 4),
    },
]

# ---------------------------------------------------------------------------
# Declaration scenarios
# ---------------------------------------------------------------------------
# Payroll parity proves the two engines compute the same payslip. That is not
# sufficient: every declaration module reads payslip lines BY RULE CODE, and a
# module that resolved only one engine's spelling would emit a plausible 0.00
# while its own test — comparing against the payslip sitting next to it in the
# same database — passed.
#
# The figures here are therefore fixed constants derived by hand from the
# statutory rates, never read back from a payslip. On the shared 50 000 CZK
# wage: social insurance is 7.1 % employee and 24.8 % employer, so 3 550.00 and
# 12 400.00 against a 50 000.00 base.
DECLARATION_WAGE = 50000.0
DECLARATION_PERIOD = ((2026, 3, 1), (2026, 3, 31))

DECLARATION_SCENARIOS = [
    {
        "key": "pvpoj_2026_03",
        "doc": "Přehled o výši pojistného. The employer base is the gross wage "
        "and the two premiums are the statutory percentages of it.",
        "requires": ["l10n_cz_hr_payroll_pvpoj"],
        "model": "l10n.cz.pvpoj",
        "create": {"year": "2026", "month": "3"},
        "expected": {
            "zakladZamestnavateleA": 50000.00,
            "pojistneZamestnavateleA": 12400.00,
            "pojistneZamestnance": 3550.00,
            "pojistneCelkem": 15950.00,
        },
    },
]

# ---------------------------------------------------------------------------
# Annual declarations
# ---------------------------------------------------------------------------
# The ELDP and the Vyúčtování report a whole year, so they need twelve payslips
# rather than the single March one the monthly scenarios share. That fixture is
# built inside its own test: an annual figure sums everything in the company,
# so seeding it alongside would move the monthly constants.
#
# Both expectations are twelve times a monthly figure the CZ payroll suite
# already asserts by hand — 50 000.00 of gross, and a 4 930 CZK advance from
# 15 % of 50 000 less the 2 570 sleva na poplatníka.
ANNUAL_DECLARATION_MONTHS = 12
MONTHLY_TAX_ADVANCE = 4930  # 15 % of 50000 = 7500, less sleva 2570

ANNUAL_DECLARATION_SCENARIOS = [
    {
        "key": "cz_eldp_2026",
        "doc": "Evidenční list důchodového pojištění. inc is the pension "
        "assessment base for the whole year: 12 x 50 000.",
        "requires": ["l10n_cz_hr_payroll_eldp"],
        "model": "l10n.cz.eldp",
        "create": {"year": "2026"},
        "expected": {
            "items@sinc": 600000.00,
            "items/t1@inc": 600000.00,
        },
    },
    # The Vyúčtování is deliberately NOT here yet.
    #
    # Its Part I reports 7 500 a month — 15 % of the 50 000 base — where the
    # payslip actually withholds 4 930, the same figure less the 2 570 sleva
    # na poplatníka. The module reads INCOMETAX; INCOMETAXTOT is the withheld
    # amount. Part I of the form reports the advances actually withheld from
    # employees, which points at 4 930, but that is a reading of the form and
    # not a checked fact, and this is money reported to the finanční úřad.
    #
    # Asserting either number would bake in a guess, and asserting the current
    # one would quietly bless it. It is question 6 in
    # docs/cz-otazky-pro-mzdoveho-odbornika.md; the scenario lands here once
    # that is answered.
]
