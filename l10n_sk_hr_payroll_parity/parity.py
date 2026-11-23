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
#   form      — optional agreement form (``dovp``, ``dopc``, ``dobps``): the
#               OCA structure and the Enterprise structure type of that name.
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
# = 40 h at the § 142 ods. 2 rate of 50 % = 227.272, so 227.28. Paid at the
# full rate — the behaviour before the § 142 split — it would be 454.55.
#
# Every wage component is rounded UP to the cent, once (owner's decision of
# 2026-11-21, ``l10n_sk_hr_payroll_base.wage_rounding``): base pay
# 2000 x 136 / 176 = 1545.4545 is 1545.46.
#
# Two components each rounded up can make GROSS a cent more than the salary
# (1886.37 + 113.64 = 2000.01 below; a day of leave in May 2026:
# 1904.77 + 95.24 = 2000.01). That is the rule working, not a defect.

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
            "BASIC": 1545.46,
            "EMPLOYER_OBSTACLE": 227.28,
            "GROSS": 1772.74,
        },
    },
    {
        "key": "employer_obstacle_uneven_calendar",
        "doc": "The same § 142 obstacle on a 40-hour week that is NOT 8 hours "
        "every day. A náhrada pays HOURS x priemerný hodinový zárobok, so a "
        "wage prorated by DAY fractions only makes GROSS whole when every "
        "working day is the same length — the classic kratší piatok schedule "
        "broke it. Absent the LONG day (Tue 9 June 2026, 10 h) against the "
        "100 % prestoj rate, GROSS must come out at the full wage: the two "
        "components, each rounded up to the cent, give one cent more.",
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
            # 2000 x 166/176 scheduled hours = 1886.3636
            "BASIC": 1886.37,
            # 10 h x 11.3636 = 113.636
            "EMPLOYER_OBSTACLE": 113.64,
            # a 100 % reason leaves the wage untouched, up to the rounding
            # of its two components
            "GROSS": 2000.01,
        },
    },
    {
        "key": "two_unpaid_leave_types",
        "doc": "Unpaid leave on 2 June and unpaid leave for education on "
        "4 June 2026: two leave types of one payroll code. Both days are "
        "unpaid: 2 000 x 160 / 176 = 1 818.1818.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_neplatene", (2026, 6, 2), (2026, 6, 2)),
            ("l10n_sk_leave_type_vzdelavanie_unpaid", (2026, 6, 4), (2026, 6, 4)),
        ],
        "expected": {"BASIC": 1818.19, "GROSS": 1818.19},
    },
    {
        "key": "sickness_and_quarantine",
        "doc": "Sick on 8 and 9 June, in quarantine from 15 to 17 June 2026: "
        "two leave types of one payroll code, five scheduled days. "
        "2 000 x 136 / 176 = 1 545.4545; the sick pay is not wage.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {"PN_DVZ": 40.0},
        "leaves": [
            ("l10n_sk_leave_type_pn", (2026, 6, 8), (2026, 6, 9)),
            ("l10n_sk_leave_type_karantena", (2026, 6, 15), (2026, 6, 17)),
        ],
        "expected": {"BASIC": 1545.46, "GROSS": 1545.46},
    },
    {
        "key": "three_paid_obstacle_types",
        "doc": "A paid obstacle, a blood donation and paid leave for "
        "education on 22, 23 and 24 June 2026: three leave types of one "
        "payroll code. The salary is 2 000 x 152 / 176 = 1 727.2727 and the "
        "24 hours are paid at the probable average of 11.3636, 272.7264, so "
        "the gross is the wage up to the rounding of its two components.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_obstacle", (2026, 6, 22), (2026, 6, 22)),
            ("l10n_sk_leave_type_darovanie_krvi", (2026, 6, 23), (2026, 6, 23)),
            ("l10n_sk_leave_type_vzdelavanie", (2026, 6, 24), (2026, 6, 24)),
        ],
        "expected": {"BASIC": 1727.28, "GROSS": 2000.01},
    },
]


# ---------------------------------------------------------------------------
# Part months and whole cents
# ---------------------------------------------------------------------------
# Driven like the leave scenarios, with real worked days. ``contract_start``
# and ``contract_end`` put the employment boundary inside the period;
# ``public_holidays`` puts public holidays into a calendar of the scenario's
# own; ``calendar_closures`` does the same for a part of a day, as
# ``(date, hour from, hour to)``: the employer's own closure, entered in the
# calendar the way a public holiday is. A leave may carry a fourth element,
# ``{"half": "am"}`` or ``{"hours": (8.0, 10.0)}``, for a part of the day.
# ``worked_days`` asks for real worked days where nothing else does.
#
# June 2026 schedules 22 working days (176 hours), March 2026 the same; May
# 2026 schedules 21 (168 hours), one of them the holiday of 1 May.
#
# A wage component is the exact result of its formula for the whole period,
# rounded UP to the cent once; a whole-cent result stays as it is.

PART_MONTH_SCENARIOS = [
    {
        "key": "contract_ends_mid_month",
        "doc": "The employment ends on 15 June 2026, after 11 of the 22 "
        "working days: half the monthly salary.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "contract_end": (2026, 6, 15),
        "version": {},
        "inputs": {},
        "expected": {"BASIC": 1000.00, "GROSS": 1000.00},
    },
    {
        "key": "hire_mid_month_whole_cents",
        "doc": "Hired on 10 March 2026: 1000 x 128 / 176 = 727.2727. The wage "
        "is 727.28 for every levy and for the tax (19 % of 622.57 is "
        "118.2883), so the lines add up to NET: 727.28 - 104.71 - 118.29.",
        "requires": [],
        "wage": 1000.0,
        "period": ((2026, 3, 1), (2026, 3, 31)),
        "contract_start": (2026, 3, 10),
        "version": {},
        "inputs": {},
        "expected": {
            "BASIC": 727.28,
            "SOCIAL_EE_TOTAL": -104.71,
            "TAXBASE": 622.57,
            "INCOME_TAX": -118.29,
            "NET": 504.28,
        },
    },
    {
        "key": "unpaid_day_whole_cent_gross",
        "doc": "One unpaid day in June 2026: 2005 x 168 / 176 = 1913.8636, "
        "a wage component, so 1913.87. Every levy reads that amount and is "
        "cut down to the cent: the employer's health premium is 11 % of "
        "1913.87, which is 210.5257 and so 210.52.",
        "requires": [],
        "wage": 2005.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_neplatene", (2026, 6, 9), (2026, 6, 9)),
        ],
        "expected": {"BASIC": 1913.87, "GROSS": 1913.87, "HEALTH_ER": 210.52},
    },
    {
        "key": "full_month_is_exactly_the_salary",
        "doc": "A whole month worked, on real worked days: exactly the "
        "salary, with no cent added by the rounding.",
        "requires": [],
        "wage": 1234.57,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "contract_start": (2024, 1, 1),
        "version": {},
        "inputs": {},
        "expected": {"BASIC": 1234.57, "GROSS": 1234.57},
    },
    {
        "key": "leave_day_base_and_leave_pay_round_up",
        "doc": "May 2026 with the public holiday of 1 May, one day of "
        "leave: base pay 2000 x 160 / 168 = 1904.7619, so 1904.77. No "
        "payslips before, so the leave is paid at 2000 / 168 = 11.9048: "
        "8 h = 95.2384, so 95.24. GROSS is the two components added.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 5, 1), (2026, 5, 31)),
        "public_holidays": [(2026, 5, 1)],
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_dovolenka", (2026, 5, 12), (2026, 5, 12)),
        ],
        "expected": {"BASIC": 1904.77, "GROSS": 2000.01},
    },
    {
        "key": "unpaid_day_below_the_minimum_wage",
        "doc": "900 EUR with one unpaid day (8 of 168 hours) in May 2026: "
        "base pay 900 x 160 / 168 = 857.142857, so 857.15. The minimum wage "
        "claim for the time worked is 915 x 160 / 168 = 871.428571, and the "
        "top-up 14.278571 is rounded up as well: 14.28.",
        "requires": ["l10n_sk_hr_payroll_surcharges"],
        "wage": 900.0,
        "period": ((2026, 5, 1), (2026, 5, 31)),
        "public_holidays": [(2026, 5, 1)],
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_neplatene", (2026, 5, 12), (2026, 5, 12)),
        ],
        "expected": {"BASIC": 857.15, "MIN_WAGE_TOPUP": 14.28, "GROSS": 871.43},
    },
    {
        "key": "meal_days_are_days_worked",
        "doc": "§ 152 ods. 2 Zákonníka práce: the meal contribution is owed "
        "for a shift worked. With no meal days set on the contract and five "
        "of June's 22 working days on leave, 17 days x 5.12.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_meal_allowance_type": "financial"},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_dovolenka", (2026, 6, 8), (2026, 6, 12)),
        ],
        "expected": {},
        "expected_abs": {"MEAL_EMPLOYER": 87.04},
    },
    # A meal day is a day with MORE than four hours worked (§ 152 ods. 2
    # Zákonníka práce: „... ktorý v rámci pracovnej zmeny vykonáva prácu viac
    # ako štyri hodiny“). Each day is decided alone; the contribution is 5.12.
    {
        "key": "meal_full_month",
        "doc": "A whole June on real worked days: 22 shifts of eight hours, "
        "22 x 5.12.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "worked_days": True,
        "version": {"l10n_sk_meal_allowance_type": "financial"},
        "inputs": {},
        "expected": {"BASIC": 2000.00},
        "expected_abs": {"MEAL_EMPLOYER": 112.64},
    },
    {
        "key": "meal_afternoon_closed_in_the_calendar",
        "doc": "The employer closes on the afternoon of 29 June 2026. The "
        "salary is whole, but four hours worked that day are not more than "
        "four: 21 x 5.12.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "calendar_closures": [((2026, 6, 29), 12, 21)],
        "version": {"l10n_sk_meal_allowance_type": "financial"},
        "inputs": {},
        "expected": {"BASIC": 2000.00},
        "expected_abs": {"MEAL_EMPLOYER": 107.52},
    },
    {
        "key": "meal_half_day_of_leave",
        "doc": "Half a day of leave on an eight-hour day: four hours worked, "
        "no meal for that day, 21 x 5.12. Base pay 2000 x 172 / 176 = "
        "1954.5455, 1954.55.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_meal_allowance_type": "financial"},
        "inputs": {},
        "leaves": [
            (
                "l10n_sk_leave_type_dovolenka",
                (2026, 6, 8),
                (2026, 6, 8),
                {"half": "am"},
            ),
        ],
        "expected": {"BASIC": 1954.55},
        "expected_abs": {"MEAL_EMPLOYER": 107.52},
    },
    {
        "key": "meal_two_half_days_do_not_add_up",
        "doc": "Half a day of leave on two days: 21 days worked in all, but "
        "on 20 of them more than four hours, 20 x 5.12. Base pay 2000 x 168 "
        "/ 176 = 1909.0909, 1909.10.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_meal_allowance_type": "financial"},
        "inputs": {},
        "leaves": [
            (
                "l10n_sk_leave_type_dovolenka",
                (2026, 6, 8),
                (2026, 6, 8),
                {"half": "am"},
            ),
            (
                "l10n_sk_leave_type_dovolenka",
                (2026, 6, 9),
                (2026, 6, 9),
                {"half": "pm"},
            ),
        ],
        "expected": {"BASIC": 1909.10},
        "expected_abs": {"MEAL_EMPLOYER": 102.40},
    },
    {
        "key": "meal_two_hours_at_the_doctor",
        "doc": "Two hours at the doctor's on an eight-hour day: six hours "
        "worked, the meal is due, 22 x 5.12. Base pay 2000 x 174 / 176 = "
        "1977.2727, 1977.28.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_meal_allowance_type": "financial"},
        "inputs": {},
        "leaves": [
            (
                "l10n_sk_leave_type_obstacle",
                (2026, 6, 8),
                (2026, 6, 8),
                {"hours": (8.0, 10.0)},
            ),
        ],
        "expected": {"BASIC": 1977.28},
        "expected_abs": {"MEAL_EMPLOYER": 112.64},
    },
    {
        "key": "meal_schedule_of_four_hours_a_day",
        "doc": "A part-time schedule of four hours a day: no shift has more "
        "than four hours of work, so no meal is owed.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "worked_days": True,
        "calendar_hours": {"0": 4.0, "1": 4.0, "2": 4.0, "3": 4.0, "4": 4.0},
        "version": {"l10n_sk_meal_allowance_type": "financial"},
        "inputs": {},
        "expected": {"BASIC": 2000.00},
        "expected_abs": {"MEAL_EMPLOYER": 0.00},
    },
    {
        "key": "meal_days_on_the_contract_win",
        "doc": "Meal days set on the contract are taken as they are, here "
        "with the afternoon of 29 June closed: 20 x 5.12.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "calendar_closures": [((2026, 6, 29), 12, 21)],
        "version": {
            "l10n_sk_meal_allowance_type": "financial",
            "l10n_sk_meal_days": 20,
        },
        "inputs": {},
        "expected": {"BASIC": 2000.00},
        "expected_abs": {"MEAL_EMPLOYER": 102.40},
    },
    # § 152 ods. 9 Zákonníka práce: the employer may provide the meal more
    # widely. With ``l10n_sk_meal_short_shift`` on the contract a day earns
    # the meal when any work was done on it.
    {
        "key": "meal_short_shift_option_four_hour_schedule",
        "doc": "A schedule of four hours a day with the option: every one of "
        "June's 22 days has work on it, 22 x 5.12 (none without the option).",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "worked_days": True,
        "calendar_hours": {"0": 4.0, "1": 4.0, "2": 4.0, "3": 4.0, "4": 4.0},
        "version": {
            "l10n_sk_meal_allowance_type": "financial",
            "l10n_sk_meal_short_shift": True,
        },
        "inputs": {},
        "expected": {"BASIC": 2000.00},
        "expected_abs": {"MEAL_EMPLOYER": 112.64},
    },
    {
        "key": "meal_short_shift_option_half_day_of_leave",
        "doc": "Half a day of leave on an eight-hour day with the option: "
        "four hours worked earn the meal, 22 x 5.12 (21 without the option).",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_meal_allowance_type": "financial",
            "l10n_sk_meal_short_shift": True,
        },
        "inputs": {},
        "leaves": [
            (
                "l10n_sk_leave_type_dovolenka",
                (2026, 6, 8),
                (2026, 6, 8),
                {"half": "am"},
            ),
        ],
        "expected": {"BASIC": 1954.55},
        "expected_abs": {"MEAL_EMPLOYER": 112.64},
    },
    {
        "key": "meal_short_shift_option_day_of_leave",
        "doc": "A whole day of leave with the option: no work that day, no "
        "meal, 21 x 5.12. Base pay 2000 x 168 / 176 = 1909.0909, 1909.10.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_meal_allowance_type": "financial",
            "l10n_sk_meal_short_shift": True,
        },
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_dovolenka", (2026, 6, 8), (2026, 6, 8)),
        ],
        "expected": {"BASIC": 1909.10},
        "expected_abs": {"MEAL_EMPLOYER": 107.52},
    },
    {
        "key": "parental_leave_owes_no_topup",
        "doc": "§ 120 ods. 6 Zákonníka práce: the monthly minimum wage claim "
        "follows the time worked. A whole month of parental leave has no "
        "wage and no hours worked, so no top-up.",
        "requires": ["l10n_sk_hr_payroll_surcharges"],
        "wage": 800.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_rodicovska", (2026, 6, 1), (2026, 6, 30)),
        ],
        "expected": {"BASIC": 0.00, "MIN_WAGE_TOPUP": 0.00, "GROSS": 0.00},
    },
    {
        "key": "hourly_rate_three_decimals",
        "doc": "§ 2 ods. 2 zákona 663/2007 rounds the minimum hourly wage to "
        "three decimals, so an agreed hourly rate has them too. 176 hours of "
        "June 2026 at the 2026 minimum of 5.259: 925.584, a wage component "
        "rounded up once. A rate held to the cent (5.26) would pay 925.76.",
        "requires": [],
        "wage": 0.0,
        "hourly_rate": 5.259,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "expected": {"BASIC": 925.59, "GROSS": 925.59},
    },
    {
        "key": "hourly_rate_fractional_hours",
        "doc": "The same rate on a 7.5-hour day: 22 days are 165 hours, "
        "165 x 5.259 = 867.735, rounded up to 867.74.",
        "requires": [],
        "wage": 0.0,
        "hourly_rate": 5.259,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {},
        "calendar_hours": {"0": 7.5, "1": 7.5, "2": 7.5, "3": 7.5, "4": 7.5},
        "expected": {"BASIC": 867.74},
    },
]


# ---------------------------------------------------------------------------
# Overtime: the hours at the wage achieved, the premium on average earnings
# ---------------------------------------------------------------------------
# § 121 ods. 1 Zákonníka práce: „Za prácu nadčas patrí zamestnancovi
# dosiahnutá mzda a mzdové zvýhodnenie najmenej v sume 25 % jeho priemerného
# zárobku." The hours are paid from the wage of the month they were worked
# in: a monthly salary over the hours the working schedule holds in that
# month, or the exact hourly rate. Only the premium is on average earnings.
#
# ``history`` confirms payslips of earlier months first, at the wage or
# hourly rate it names, so that the average of the quarter before differs
# from the wage of the month: January to March 2026 hold 176 + 160 + 176 =
# 512 hours. ``expected_lines`` holds payslip lines by rule code, for the
# lines both engines' surcharge modules name alike.

OVERTIME_SCENARIOS = [
    {
        "key": "overtime_after_a_raise",
        "doc": "1 600 a month in the first quarter of 2026: average earnings "
        "4 800 / 512 = 9.375. 2 100 from April and eight overtime hours in "
        "April (176 hours): 2 100 x 8 / 176 = 95.4545 for the hours, "
        "8 x 9.375 x 25 % = 18.75 on top.",
        "requires": ["l10n_sk_hr_payroll_surcharges"],
        "wage": 2100.0,
        "history": {"months": [(2026, 1), (2026, 2), (2026, 3)], "wage": 1600.0},
        "period": ((2026, 4, 1), (2026, 4, 30)),
        "version": {},
        "inputs": {"NADCAS": 8.0},
        "worked_days": True,
        "expected": {"BASIC": 2100.00, "GROSS": 2214.21},
        "expected_lines": {"NADCAS_MZDA": 95.46, "PRIPLATOK_NADCAS": 18.75},
    },
    {
        "key": "overtime_hourly_rate_three_decimals",
        "doc": "6.125 an hour in the first quarter of 2026, 7.333 from April. "
        "The 176 hours of April are 1 290.608; eight overtime hours are "
        "8 x 7.333 = 58.664, and the premium 8 x 6.125 x 25 % = 12.25.",
        "requires": ["l10n_sk_hr_payroll_surcharges"],
        "wage": 0.0,
        "hourly_rate": 7.333,
        "history": {
            "months": [(2026, 1), (2026, 2), (2026, 3)],
            "hourly_rate": 6.125,
        },
        "period": ((2026, 4, 1), (2026, 4, 30)),
        "version": {},
        "inputs": {"NADCAS": 8.0},
        "expected": {"BASIC": 1290.61, "GROSS": 1361.53},
        "expected_lines": {"NADCAS_MZDA": 58.67, "PRIPLATOK_NADCAS": 12.25},
    },
    {
        "key": "overtime_in_a_month_with_an_unpaid_day",
        "doc": "June 2026, 2 000 and one unpaid day: the salary is "
        "2 000 x 168 / 176 = 1 909.0909. The overtime hours are paid from "
        "the salary over the 176 hours of the month, not over the 168 "
        "worked: 2 000 x 8 / 176 = 90.9091 (over 168 they would be 95.24). "
        "No payslips in the quarter before: the probable average 11.3636, "
        "8 x 11.3636 x 25 % = 22.7272.",
        "requires": ["l10n_sk_hr_payroll_surcharges"],
        "wage": 2000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {},
        "inputs": {"NADCAS": 8.0},
        "leaves": [
            ("l10n_sk_leave_type_neplatene", (2026, 6, 2), (2026, 6, 2)),
        ],
        "expected": {"BASIC": 1909.10, "GROSS": 2022.74},
        "expected_lines": {"NADCAS_MZDA": 90.91, "PRIPLATOK_NADCAS": 22.73},
    },
]


# ---------------------------------------------------------------------------
# A public holiday inside an absence
# ---------------------------------------------------------------------------
# Run like the part-month scenarios, with the holidays entered as public
# holidays of the scenario's calendar. Monthly salary 2000; April 2026 has
# 176 hours with Good Friday (3rd) and Easter Monday (6th), May 2026 has 168
# hours with 1 May on a Friday.
#
# Which of the two the day is depends on the absence
# (``l10n_sk_hr_payroll_base.public_holiday``): sickness, nursing, maternity,
# paternity, parental and unpaid leave keep the day and no wage is due for
# it; in paid leave the holiday is not a day of leave (§ 112 ods. 3
# Zákonníka práce) and stays inside the monthly wage (§ 122 ods. 3).

HOLIDAY_SCENARIOS = [
    {
        "key": "sickness_from_a_public_holiday",
        "doc": "Sick from 1 to 15 May 2026: 11 scheduled days, the holiday "
        "among them, so base pay is 2000 x 80 / 168 = 952.3810, 952.39. The "
        "employer's sick pay runs by calendar day (§ 7 ods. 2 zákona "
        "462/2003): 14 days on a daily base of 40, 3 x 10 + 11 x 22 = 272.00, "
        "outside GROSS and inside NET: 952.39 - 137.12 - 154.90 + 272.00.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 5, 1), (2026, 5, 31)),
        "public_holidays": [(2026, 5, 1)],
        "version": {},
        "inputs": {"PN_DVZ": 40.0},
        "leaves": [
            ("l10n_sk_leave_type_pn", (2026, 5, 1), (2026, 5, 15)),
        ],
        "expected": {
            "BASIC": 952.39,
            "GROSS": 952.39,
            "SOCIAL_EE_TOTAL": -137.12,
            "INCOME_TAX": -154.90,
            "NET": 932.37,
        },
    },
    {
        "key": "unpaid_leave_from_a_public_holiday",
        "doc": "Unpaid leave from 1 to 15 May 2026: the holiday is a day of "
        "the leave and no wage is due for it. 2000 x 80 / 168 = 952.39.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 5, 1), (2026, 5, 31)),
        "public_holidays": [(2026, 5, 1)],
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_neplatene", (2026, 5, 1), (2026, 5, 15)),
        ],
        "expected": {"BASIC": 952.39, "GROSS": 952.39},
    },
    {
        "key": "parental_leave_from_a_public_holiday",
        "doc": "Parental leave for the whole of May 2026, beginning on the "
        "holiday: no wage at all.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 5, 1), (2026, 5, 31)),
        "public_holidays": [(2026, 5, 1)],
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_rodicovska", (2026, 5, 1), (2026, 5, 31)),
        ],
        "expected": {"BASIC": 0.00, "GROSS": 0.00},
    },
    {
        "key": "leave_from_a_public_holiday",
        "doc": "Leave booked from Good Friday 3 April to 10 April 2026: the "
        "two holidays are not days of leave, the leave is 7 to 10 April. "
        "Base pay 2000 x 144 / 176 = 1636.3636, 1636.37; leave pay 32 h x "
        "11.3636 = 363.6352, 363.64.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 4, 1), (2026, 4, 30)),
        "public_holidays": [(2026, 4, 3), (2026, 4, 6)],
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_dovolenka", (2026, 4, 3), (2026, 4, 10)),
        ],
        "expected": {"BASIC": 1636.37, "GROSS": 2000.01},
    },
    {
        "key": "public_holiday_inside_leave",
        "doc": "Leave from 27 April to 5 May 2026, May payslip: 1 May is not "
        "a day of leave, so two days of leave. Base pay 2000 x 152 / 168 = "
        "1809.5238, 1809.53; leave pay 16 h x 11.9048 = 190.4768, 190.48.",
        "requires": [],
        "wage": 2000.0,
        "period": ((2026, 5, 1), (2026, 5, 31)),
        "public_holidays": [(2026, 5, 1)],
        "version": {},
        "inputs": {},
        "leaves": [
            ("l10n_sk_leave_type_dovolenka", (2026, 4, 27), (2026, 5, 5)),
        ],
        "expected": {"BASIC": 1809.53, "GROSS": 2000.01},
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
        "key": "net_is_income_less_the_rounded_tax",
        "doc": "1238 EUR with the declaration, March 2026: levies 178.27, "
        "taxable wage 1059.73 - 497.23 = 562.50, 19 % is 106.875. § 47 ZDP "
        "rounds the advance to 106.88, and NET is the income less the "
        "amounts withheld: 1238 - 178.27 - 106.88.",
        "requires": [],
        "wage": 1238.0,
        "period": ((2026, 3, 1), (2026, 3, 31)),
        "version": {"l10n_sk_tax_declaration_signed": True},
        "inputs": {},
        "expected": {
            "SOCIAL_EE_TOTAL": -178.27,
            "TAXBASE": 1059.73,
            "INCOME_TAX": -106.88,
            "NET": 952.85,
        },
    },
    {
        "key": "net_is_income_less_rounded_tax_plus_rounded_bonus",
        "doc": "918 EUR with four children under 15, March 2026: tax base "
        "785.81, tax 54.8302, bonus capped at 50 % of the base (§ 33 ods. 6 "
        "ZDP) = 392.905. Both are rounded by § 47 before NET reads them: "
        "918 - 132.19 - 54.83 + 392.91.",
        "requires": [],
        "wage": 918.0,
        "period": ((2026, 3, 1), (2026, 3, 31)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 4,
        },
        "inputs": {},
        "expected": {
            "TAXBASE": 785.81,
            "INCOME_TAX": -54.83,
            "CHILD_BONUS": 392.91,
            "NET": 1123.89,
        },
    },
    {
        "key": "child_of_18_or_over_december_2024",
        "doc": "§ 52zzp ods. 4 and 5 ZDP: from January 2023 to December 2024 "
        "the bonus is 140 for a child under 18 and 50 for a dependent child "
        "of 18 or over, who counts for the percentage limit like any other "
        "vyživované dieťa. 1000 EUR in December 2024: tax base 866.00; "
        "140 + 140 + 50 = 330 is limited to 34 % for three children, 294.44 "
        "(27 % for two would be 233.82).",
        "requires": [],
        "wage": 1000.0,
        "period": ((2024, 12, 1), (2024, 12, 31)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 2,
            "l10n_sk_children_over_18": 1,
        },
        "inputs": {},
        "expected": {"TAXBASE": 866.00, "CHILD_BONUS": 294.44},
    },
    {
        "key": "count_of_18_or_over_ignored_from_2025",
        "doc": "From January 2025 the bonus ends with the month of the 18th "
        "birthday (§ 33 ods. 1 písm. a) ZDP), so a number of children of 18 "
        "or over left on the contract gives nothing and does not raise the "
        "limit. 850 EUR in January 2025: tax base 736.10; four children under "
        "15, 400, limited to 50 % for four: 368.05 (57 % for five would give "
        "the whole 400).",
        "requires": [],
        "wage": 850.0,
        "period": ((2025, 1, 1), (2025, 1, 31)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 4,
            "l10n_sk_children_over_18": 1,
        },
        "inputs": {},
        "expected": {"TAXBASE": 736.10, "CHILD_BONUS": 368.05},
    },
    {
        "key": "child_bonus_taper_per_child",
        "doc": "§ 33 ods. 11 ZDP: above 1,5 × 12 × the average wage the bonus "
        "of EACH child is cut by 1/10 of the excess. TAXBASE 2 996 against a "
        "monthly threshold of 27 432 / 12 = 2 286 takes 71 off each child: "
        "2 × (100 − 71) = 58. Both engines used to take 71 off the total.",
        "requires": [],
        "wage": 3500.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 2,
        },
        "inputs": {},
        "expected": {
            "TAXBASE": 2996.00,
            "CHILD_BONUS": 58.00,
        },
    },
    # Several employee records of one person taxed together (§ 35 ods. 1
    # zákona 595/2003 Z. z.: the taxable wage is the total the employer pays
    # the employee in the month, less the premiums and ONE non-taxable
    # amount). ``linked`` are the records whose base is taxed on the
    # scenario's own payslip; their payslips are computed first.
    # ``expected_lines`` names lines whose rule code both engines share.
    {
        "key": "joint_tax_month_taxed_once",
        "doc": "Two agreements of one person, 400 with the declaration and "
        "300 linked to it. Bases 400 - 57.60 = 342.40 and 300 - 43.20 = "
        "256.80. Each alone: 0.00 and 48.79. Together (342.40 + 256.80 - "
        "497.23) x 19 % = 19.3743, so 19.37 on the principal's payslip and "
        "nothing on the linked one.",
        "requires": [],
        "form": "dopc",
        "wage": 400.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_tax_declaration_signed": True},
        "inputs": {},
        "linked": [
            {
                "key": "joint_tax_month_taxed_once_linked",
                "requires": [],
                "form": "dopc",
                "wage": 300.0,
                "version": {},
                "inputs": {},
                "expected": {"TAXBASE": 256.80, "INCOME_TAX": 0.00, "NET": 256.80},
                "expected_lines": {"TAXBASE_MOVED": 256.80},
            },
        ],
        "expected": {"TAXBASE": 342.40, "INCOME_TAX": -19.37, "NET": 323.03},
        "expected_lines": {"TAXBASE_TAKEN": 256.80},
    },
    {
        "key": "joint_tax_child_bonus_cap_on_the_month",
        "doc": "The same pair with one child under 15 on the principal: the "
        "bonus of 100.00 is capped at 29 % of the month's base, 599.20 x 29 % "
        "= 173.77, so it is whole (on 342.40 alone it would be 99.30). NET "
        "400 - 57.60 - 19.37 + 100.00.",
        "requires": [],
        "form": "dopc",
        "wage": 400.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 1,
        },
        "inputs": {},
        "linked": [
            {
                "key": "joint_tax_child_bonus_cap_on_the_month_linked",
                "requires": [],
                "form": "dopc",
                "wage": 300.0,
                "version": {"l10n_sk_children_under_15": 1},
                "inputs": {},
                "expected": {"INCOME_TAX": 0.00, "CHILD_BONUS": 0.00, "NET": 256.80},
                "expected_lines": {"TAXBASE_MOVED": 256.80},
            },
        ],
        "expected": {"INCOME_TAX": -19.37, "CHILD_BONUS": 100.00, "NET": 423.03},
        "expected_lines": {"TAXBASE_TAKEN": 256.80},
    },
    {
        "key": "joint_tax_second_band_on_the_month",
        "doc": "An employment of 3 000 with the declaration and an agreement "
        "of 2 500: bases 2 568.00 and 2 140.00, each under the first band's "
        "3 665.28 (alone 393.45 and 406.60). Together 4 708.00 - 497.23 = "
        "4 210.77: 3 665.28 x 19 % + 545.49 x 25 % = 832.7757, so 832.78.",
        "requires": [],
        "wage": 3000.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_tax_declaration_signed": True},
        "inputs": {},
        "linked": [
            {
                "key": "joint_tax_second_band_on_the_month_linked",
                "requires": [],
                "form": "dopc",
                "wage": 2500.0,
                "version": {},
                "inputs": {},
                "expected": {"TAXBASE": 2140.00, "INCOME_TAX": 0.00, "NET": 2140.00},
                "expected_lines": {"TAXBASE_MOVED": 2140.00},
            },
        ],
        "expected": {"TAXBASE": 2568.00, "INCOME_TAX": -832.78, "NET": 1735.22},
        "expected_lines": {"TAXBASE_TAKEN": 2140.00},
    },
    {
        "key": "surcharges",
        "doc": "Night, Saturday and Sunday hours at the 2026 minimum hourly wage "
        "of 5.259. Also proves the surcharges reach GROSS on both engines, "
        "which is what makes them insurable and taxable.",
        "requires": ["l10n_sk_hr_payroll_surcharges"],
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
        "requires": ["l10n_sk_hr_payroll_surcharges"],
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
        "requires": ["l10n_sk_hr_payroll_surcharges"],
        "wage": 915.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {"l10n_sk_tax_declaration_signed": True},
        "inputs": {},
        "expected": {"MIN_WAGE_TOPUP": 0.00, "GROSS": 915.00},
    },
    {
        "key": "dohoda_pension_oop_above_maximum",
        "doc": "A DoVP with the pension OOP claimed and 17,100 EUR in June 2026. "
        "§ 138 ods. 1 zákona 461/2003 takes the OOP (200, § 138a) off the "
        "income BEFORE the 16,764 maximum, so the five reduced funds use "
        "min(17,100 - 200, 16,764) = 16,764, not 16,764 - 200. Both engines "
        "used to cap first and charged 662.56 old-age instead of 670.56.",
        "requires": [],
        "form": "dovp",
        "wage": 17100.0,
        "period": ((2026, 6, 1), (2026, 6, 30)),
        "version": {
            "l10n_sk_agreement_type": "dovp",
            "l10n_sk_agreement_oop": True,
        },
        "inputs": {},
        "expected": {
            "GROSS": 17100.00,
            # Irregular income: old-age 4 % 670.56 + disability 3 % 502.92 on
            # 16,764, plus health 5 % of the full 17,100 (no health OOP on a
            # dohoda) 855.00.
            "SOCIAL_EE_TOTAL": -2028.48,
            # Old-age 14 % 2346.96 + disability 3 % 502.92 + reserve 4.75 %
            # 796.29 on 16,764; guarantee 0.25 % on the capped income 41.91
            # (not reduced by the OOP); accident 0.8 % uncapped 136.80; health
            # 11 % 1881.00.
            "SOCIAL_ER_TOTAL": 5705.88,
        },
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
        "requires": ["l10n_sk_hr_payroll_annual_tax_report"],
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
        "requires": ["l10n_sk_hr_payroll_monthly_tax_overview"],
        "model": "l10n.sk.prehlad",
        "create": {"year": "2026", "month": "3"},
        "expected": {
            "telo/cast1/r00": 2000.00,
            "telo/cast1/r01/suma": 230.81,
            "telo/cast1/r04": 230.81,
        },
    },
]


# ---------------------------------------------------------------------------
# Recorded fund bases — what each engine's payslip records and its reader
# hands to the insurance declarations
# ---------------------------------------------------------------------------
# March 2026. Each fund rule records the base it charged on, the rate and the
# amount; the declarations read those rows through the engine's reader
# (``_cssk_recorded_fund_bases``). The rows of the same payslip must be the
# same on both engines, or a statement that reads them would differ between
# them. ``short_week`` puts the employee on five hours a week, so that a low
# wage stays above the minimum wage claim.
#
# ``rows`` maps (fund, side) to (base, rate %, amount), for the eleven social
# funds and health:
#   employee  sickness 1.4, pension 4, disability 3, unemployment 1, health 5
#   employer  sickness 1.4, pension 14, disability 3, unemployment 0.5,
#             shorttime 0.5, guarantee 0.25, accident 0.8, reserve 4.75,
#             health 11
# ``statement`` are figures of the dávka 514 generated from that one payslip,
# for the scenario where a recorded base differs from gross on that form.


def _fund_rows(social_base, employee_health, employer_health, accident_base):
    """The fourteen rows of an employment at the 2026 rates.

    ``social_base`` is the base of every social fund but accident (§ 138
    zákona 461/2003 Z. z. caps it), ``accident_base`` the uncapped one, and
    the two health arguments are (base, amount) of each side.
    """
    def row(base, rate):
        return (base, rate, int(round(base * rate, 6)) / 100.0)

    return {
        ("sickness", "employee"): row(social_base, 1.4),
        ("sickness", "employer"): row(social_base, 1.4),
        ("pension", "employee"): row(social_base, 4),
        ("pension", "employer"): row(social_base, 14),
        ("disability", "employee"): row(social_base, 3),
        ("disability", "employer"): row(social_base, 3),
        ("unemployment", "employee"): row(social_base, 1),
        ("unemployment", "employer"): row(social_base, 0.5),
        ("shorttime", "employer"): row(social_base, 0.5),
        ("guarantee", "employer"): row(social_base, 0.25),
        ("reserve", "employer"): row(social_base, 4.75),
        ("accident", "employer"): row(accident_base, 0.8),
        ("health", "employee"): (employee_health[0], 5, employee_health[1]),
        ("health", "employer"): (employer_health[0], 11, employer_health[1]),
    }


RECORDED_FUND_PERIOD = ((2026, 3, 1), (2026, 3, 31))

RECORDED_FUND_SCENARIOS = [
    {
        "key": "employment_2000",
        "doc": "Every base is the gross wage.",
        "wage": 2000.0,
        "short_week": False,
        "version": {},
        "rows": _fund_rows(2000.0, (2000.0, 100.0), (2000.0, 220.0), 2000.0),
    },
    {
        "key": "above_the_maximum_base",
        "doc": "20 000: the social funds stop at the maximum base of 16 764, "
        "accident and health insurance have none.",
        "wage": 20000.0,
        "short_week": False,
        "version": {},
        "rows": _fund_rows(
            16764.0, (20000.0, 1000.0), (20000.0, 2200.0), 20000.0),
    },
    {
        "key": "health_deductible_item",
        "doc": "400 with the health deductible item claimed: 380 - 2 x (400 "
        "- 380) = 340 comes off the employee's health base only (§ 16 ods. "
        "16 and 17 zákona 580/2004 Z. z.), 5 % of 60 is 3.00; the employer "
        "pays on 400.",
        "wage": 400.0,
        "short_week": True,
        "version": {"l10n_sk_health_oop_claim": True},
        "rows": _fund_rows(400.0, (60.0, 3.0), (400.0, 44.0), 400.0),
        "statement": {
            "PersonData/TotalReceiptOfEmployee": 400.00,
            "PersonData/OP": 340.00,
            "PersonData/BaseOfAssessOfEmployee": 60.00,
            "PersonData/TariffOfDeposit1": 11.00,
            "PersonData/TariffOfDeposit2": 5.00,
            "PersonData/DepositOfEmployer": 44.00,
            "PersonData/DepositOfEmployee": 3.00,
            "InsuranceBody/BaseOfAssess1": 60.00,
        },
    },
    {
        "key": "health_minimum_top_up",
        "doc": "200: the employee's health row carries the advance with the "
        "top-up to the minimum advance, 10.00 + 13.45 (§ 16a ods. 4 zákona "
        "580/2004 Z. z.), on the base of 200.",
        "wage": 200.0,
        "short_week": True,
        "version": {},
        "rows": _fund_rows(200.0, (200.0, 23.45), (200.0, 22.0), 200.0),
    },
]
