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
#   holidays  — public holidays (y, m, d) put on the scenario's working
#               calendar as time off that belongs to no employee.
#   contract_end — last day of the employment.
#   later_version — {"date": (y, m, d), "values": {...}}: a second contract
#               version inside the employment.
#   inputs    — (input code, amount) lines typed on the saved payslip.
#   seed      — False to skip the worked March 2026 that seeds the average
#               earnings (a scenario outside it, or one that pins its own).
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
# January 2026: 22 working days, 176 hours, New Year's Day on a Thursday.
JANUARY = ((2026, 1, 1), (2026, 1, 31))
NEW_YEAR = (2026, 1, 1)
# April 2026: 22 working days, 176 hours, Good Friday on the 3rd and Easter
# Monday on the 6th.
APRIL = ((2026, 4, 1), (2026, 4, 30))
EASTER = [(2026, 4, 3), (2026, 4, 6)]
# May 2026: 21 working days, 168 hours, on a calendar without the holidays
# of 1 and 8 May.
MAY = ((2026, 5, 1), (2026, 5, 31))

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
        "key": "social_premium_whole_crowns",
        "doc": "§ 7 odst. 3 zák. 589/1992 Sb.: the employee's premium is "
        "rounded up to whole crowns, 51 263 x 7.1 % = 3 639.673 -> 3 640. The "
        "employer's line keeps its heller share (12 713.22); the law rounds "
        "that premium on the company's sum of bases. Health 6 921 of which a "
        "third 2 307; advance 15 % of 51 300 = 7 695 less 2 570. NET is whole.",
        "requires": [],
        "wage": 51263.0,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "expected": {
            "GROSS": 51263.00,
            "SOCIAL_EE_TOTAL": -3640.00,
            "SOCIAL_ER_TOTAL": 12713.22,
            "INCOME_TAX": -7695.00,
            "NET": 40191.00,
        },
    },
    {
        "key": "assessment_base_whole_crowns",
        "doc": "§ 5d zák. 589/1992 Sb.: the assessment base is rounded up to "
        "whole crowns, so a gross of 30 000.40 is insured on 30 001: employee "
        "2 130.071 -> 2 131, employer 7 440.25. Health has no base rounding: "
        "13.5 % of 30 000.40 = 4 050.054 -> 4 051, a third 1 351. Advance "
        "15 % of 30 100 = 4 515 less 2 570. NET 30 000.40 - 2 131 - 1 351 - "
        "1 945.",
        "requires": [],
        "wage": 30000.40,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "expected": {
            "GROSS": 30000.40,
            "SOCIAL_EE_TOTAL": -2131.00,
            "SOCIAL_ER_TOTAL": 7440.25,
            "HEALTH_EE": -1351.00,
            "HEALTH_ER": 2700.00,
            "INCOME_TAX": -4515.00,
            "NET": 24573.40,
        },
    },
    {
        "key": "tax_advance_whole_crowns",
        "doc": "§ 38h odst. 3 ZDP: the advance is rounded up to whole crowns, "
        "which shows above the 23 % threshold (146 901 in 2026): 22 035.15 + "
        "23 % of 3 099 = 22 747.92 -> 22 748. NET 150 000 - 10 650 - 6 750 - "
        "(22 748 - 2 570).",
        "requires": [],
        "wage": 150000.0,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "expected": {
            "GROSS": 150000.00,
            "SOCIAL_EE_TOTAL": -10650.00,
            "INCOME_TAX": -22748.00,
            "INCOME_TAX_TOTAL": 22748.00,
            "NET": 112422.00,
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
    {
        "key": "dpp_below_dpp_threshold",
        "doc": "A DPP paying 8 000 CZK in 2026: above the 4 500 DPČ rozhodný "
        "příjem but below the 12 000 DPP amount of § 7a odst. 1 zák. "
        "187/2006 Sb. Not insured at all, and without a declaration taxed by "
        "the 15 % srážková daň of § 6 odst. 4 písm. a) ZDP. Both engines once "
        "fell back to the DPČ threshold for a DPP not ticked as 'notified' — "
        "a distinction the law does not make.",
        "requires": [],
        "wage": 8000.0,
        "period": PERIOD,
        "version": {
            "l10n_cz_agreement_type": "dpp",
            "l10n_cz_tax_declaration": False,
        },
        # Four hours on Mondays: 8000 for 16 hours is well above the hourly
        # minimum wage, so the § 111 top-up of the surcharge bridges cannot
        # fire. On the full-time calendar this DPP would be paid 85 Kč an
        # hour and topped up to 134.40 - correctly.
        "calendar_hours": {"0": 4.0},
        "leaves": [],
        # No insurance, no advance; NET = 8000 - int(8000 x 15 %) = 6800.
        "expected": {
            "GROSS": 8000.00,
            "SOCIAL_EE_TOTAL": 0.00,
            "SOCIAL_ER_TOTAL": 0.00,
            "HEALTH_EE": 0.00,
            "HEALTH_ER": 0.00,
            "INCOME_TAX": 0.00,
            "NET": 6800.00,
        },
    },
    {
        "key": "dpp_without_declaration_2027",
        "doc": "The same DPP in June 2027. Act No. 360/2025 Sb. rewords § 6 "
        "odst. 4 ZDP: the income stays a separate base, but for the advance "
        "at the § 38h rate instead of the srážková daň, so the 15 % moves to "
        "INCOMETAX (base rounded up to whole hundreds, 8 000 already is) and "
        "the payslip marks the separate base the JMHZ reports apart.",
        "requires": [],
        "wage": 8000.0,
        "period": ((2027, 6, 1), (2027, 6, 30)),
        "version": {
            "l10n_cz_agreement_type": "dpp",
            "l10n_cz_tax_declaration": False,
        },
        "calendar_hours": {"0": 4.0},
        "leaves": [],
        "expected": {
            "GROSS": 8000.00,
            "SOCIAL_EE_TOTAL": 0.00,
            "HEALTH_EE": 0.00,
            "INCOME_TAX": -1200.00,
            "SEPARATE_TAX_BASE": 8000.00,
            "NET": 6800.00,
        },
    },
    {
        "key": "sick_beyond_fourteen_days",
        "doc": "A DPN lasting all June. § 192 odst. 1 ZP: the employer pays "
        "náhrada mzdy for the first 14 calendar days only (1-14 June, 80 h); "
        "the rest is nemocenské from ČSSZ. The náhrada is exempt from income "
        "tax (§ 6 odst. 9 písm. p) ZDP) and not insured, and a whole month of "
        "DPN leaves no minimum health base (§ 3 odst. 9 písm. b) zák. "
        "592/1992). Both engines once paid all 176 hours and charged a "
        "3 024 Kč health top-up, and later taxed the náhrada.",
        "requires": [],
        "wage": WAGE,
        "period": PERIOD,
        "version": {
            "l10n_cz_tax_declaration": False,
            "l10n_cz_avg_hourly_earnings": 200.0,
        },
        "leaves": [
            ("leave_type_cz_sick", (2026, 6, 1), (2026, 6, 30)),
        ],
        # PHV 200 -> reduced 180; 0.60 x 180 x 80 = 8640, all of it paid out.
        "expected": {
            "BASIC": 0.00,
            "GROSS": 0.00,
            "HEALTH_EE": 0.00,
            "HEALTH_ER": 0.00,
            "INCOME_TAX": 0.00,
            "NET": 8640.00,
        },
    },
    {
        "key": "sick_pay_outside_the_tax_base",
        "doc": "A week of DPN in a worked month, declaration signed. § 6 odst. "
        "9 písm. p) ZDP exempts the náhrada mzdy up to the statutory minimum, "
        "which is all the engines pay, and § 38h odst. 1 keeps exempt income "
        "out of the base for the advance: the tax is on the wage alone. Both "
        "engines once taxed the náhrada too (43 000 x 15 % = 6 450).",
        "requires": [],
        "wage": WAGE,
        "period": PERIOD,
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_avg_hourly_earnings": 200.0,
        },
        "leaves": [
            ("leave_type_cz_sick", (2026, 6, 1), (2026, 6, 5)),
        ],
        # 176 scheduled June hours, 40 of sickness: BASIC 50000 x 136/176 =
        # 38636.36. Advance base 38700 x 15 % = 5805.
        "expected": {
            "BASIC": 38636.36,
            "GROSS": 38636.36,
            "INCOME_TAX": -5805.00,
        },
    },
    {
        "key": "health_premium_rounding",
        "doc": "§ 2 odst. 2 zák. 592/1992: 13.5 % rounded UP per employee, "
        "and the employee's third (§ 9 odst. 2 zák. 48/1997) rounded up too. "
        "Both engines once booked 4.5 % and 9 % unrounded.",
        "requires": [],
        "wage": 30001.0,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        # 30001 x 13.5 % = 4050.135 -> 4051; ceil(4051 / 3) = 1351; 2700.
        "expected": {
            "GROSS": 30001.00,
            "HEALTH_EE": -1351.00,
            "HEALTH_ER": 2700.00,
        },
    },
    # -----------------------------------------------------------------
    # The seams of the working time: the end of the employment, public
    # holidays, several inputs. Each of these gave two different payslips on
    # the two engines before it was written down here.
    # -----------------------------------------------------------------
    {
        "key": "leaver_mid_month",
        "doc": "The employment ends on 15 January: the wage is due for the "
        "time inside it only, 11 of the month's 22 working days. One engine "
        "ran the worked days to the end of the period and paid the month.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "contract_end": (2026, 1, 15),
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        # 88 of 176 hours.
        "expected": {
            "BASIC": 25000.00,
            "GROSS": 25000.00,
        },
    },
    {
        "key": "leaver_public_holiday",
        "doc": "The same leaver with New Year's Day on the calendar. A "
        "monthly wage is not reduced for a public holiday on a usual working "
        "day (§ 115 odst. 3 ZP), so the holiday is paid time and stays in the "
        "month's hours: 88 of 176 again, not 80 of 168.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "contract_end": (2026, 1, 15),
        "holidays": [NEW_YEAR],
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "expected": {
            "BASIC": 25000.00,
            "GROSS": 25000.00,
        },
    },
    {
        "key": "public_holiday_full_month",
        "doc": "A whole worked January with New Year's Day on the calendar: "
        "the full wage (§ 115 odst. 3 ZP), and the meal allowance for the 21 "
        "shifts worked, not for the holiday (§ 6 odst. 9 písm. b) ZDP: 'za "
        "jednu směnu').",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_meal_allowance": 100.0,
        },
        "leaves": [],
        "expected": {
            "BASIC": 50000.00,
            "GROSS": 50000.00,
            "MEAL": 2100.00,
        },
    },
    {
        "key": "sick_beside_public_holiday",
        "doc": "A sickness of 2-9 January beside New Year's Day on the "
        "calendar. The 48 hours of sickness come off a month of 176 hours "
        "that includes the paid holiday; one engine divided by 168.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_avg_hourly_earnings": 300.0,
        },
        "leaves": [
            ("leave_type_cz_sick", (2026, 1, 2), (2026, 1, 9)),
        ],
        # BASIC 50000 x 128/176 = 36363.64. Sick pay, § 192 odst. 2 ZP:
        # reduced average 285.78 x 90 % + 14.22 x 60 % = 265.734;
        # x 60 % x 48 h = 7653.14, up to 7654.
        "expected": {
            "BASIC": 36363.64,
            "GROSS": 36363.64,
            "SICK_NAHRADA": 7654.00,
        },
    },
    {
        "key": "sick_over_public_holiday",
        "doc": "A sickness of 1-9 January with New Year's Day on the "
        "calendar. § 192 odst. 1 ZP: the compensation is due for the working "
        "days and for the public holidays whose wage is otherwise not "
        "reduced, so the holiday inside the sickness is a day of sickness: "
        "56 hours compensated, no wage for it. Both engines paid the holiday "
        "as wage and compensated 48 hours.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_avg_hourly_earnings": 300.0,
        },
        "leaves": [
            ("leave_type_cz_sick", (2026, 1, 1), (2026, 1, 9)),
        ],
        # BASIC 50000 x 120/176 = 34090.91. Sick pay, § 192 odst. 2 ZP:
        # reduced average 265.734 (see sick_beside_public_holiday);
        # x 60 % x 56 h = 8928.66, up to 8929.
        "expected": {
            "BASIC": 34090.91,
            "GROSS": 34090.91,
            "SICK_NAHRADA": 8929.00,
        },
    },
    {
        "key": "quarantine_over_public_holiday",
        "doc": "§ 192 odst. 1 ZP names quarantine beside the temporary "
        "incapacity for work in the same sentence: the public holiday inside "
        "an ordered quarantine is compensated the same way.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_avg_hourly_earnings": 300.0,
        },
        "leaves": [
            ("leave_type_cz_karantena", (2026, 1, 1), (2026, 1, 9)),
        ],
        "expected": {
            "BASIC": 34090.91,
            "GROSS": 34090.91,
            "SICK_NAHRADA": 8929.00,
        },
    },
    {
        "key": "sick_public_holiday_after_fourteen_days",
        "doc": "A sickness from 15 December 2025 to 9 January 2026. The "
        "employer compensates the first 14 calendar days only (§ 192 odst. 1 "
        "ZP), which ended on 28 December: New Year's Day lies inside the "
        "sickness, earns no wage and no compensation either. January is "
        "paid for 120 of 176 hours.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_avg_hourly_earnings": 300.0,
        },
        "leaves": [
            ("leave_type_cz_sick", (2025, 12, 15), (2026, 1, 9)),
        ],
        "expected": {
            "BASIC": 34090.91,
            "GROSS": 34090.91,
            "SICK_NAHRADA": 0.00,
        },
    },
    {
        "key": "unpaid_leave_over_public_holiday",
        "doc": "Unpaid leave of 1-9 January with New Year's Day on the "
        "calendar. Unlike § 192 odst. 1 ZP for a sickness, no provision says "
        "whose day the holiday inside an unpaid leave is, so it stays what "
        "both engines have always made it: the holiday, paid with the wage "
        "(§ 115 odst. 3 ZP), 48 hours unpaid. Pinned so that the two engines "
        "cannot part on it; not a ruling on the question.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [
            ("leave_type_cz_unpaid", (2026, 1, 1), (2026, 1, 9)),
        ],
        "expected": {
            "BASIC": 36363.64,
            "GROSS": 36363.64,
        },
    },
    {
        "key": "leave_from_public_holiday",
        "doc": "Dovolená entered 1-9 January, New Year's Day on the calendar. "
        "A public holiday on a usual working day is not counted into the "
        "leave (§ 219 odst. 2 ZP): 48 hours of leave, the holiday paid with "
        "the wage. One engine filed all 56 hours under the public holiday "
        "and paid the full wage with no leave at all.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_avg_hourly_earnings": 300.0,
        },
        "leaves": [
            ("leave_type_cz_holiday", (2026, 1, 1), (2026, 1, 9)),
        ],
        # BASIC 50000 x 128/176; náhrada 48 x 300.
        "expected": {
            "BASIC": 36363.64,
            "HOLIDAY_NAHRADA": 14400.00,
            "GROSS": 50763.64,
        },
    },
    {
        "key": "leave_over_easter",
        "doc": "Dovolená 30 March - 10 April 2026 across Good Friday and "
        "Easter Monday, on the April payslip: 6 days of leave (1, 2, 7-10 "
        "April), the two holidays are not leave (§ 219 odst. 2 ZP). One "
        "engine counted 64 hours of leave, the other divided by 160.",
        "requires": [],
        "wage": WAGE,
        "period": APRIL,
        "seed": False,
        "holidays": EASTER,
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_avg_hourly_earnings": 300.0,
        },
        "leaves": [
            ("leave_type_cz_holiday", (2026, 3, 30), (2026, 4, 10)),
        ],
        # BASIC 50000 x 128/176; náhrada 48 x 300.
        "expected": {
            "BASIC": 36363.64,
            "HOLIDAY_NAHRADA": 14400.00,
            "GROSS": 50763.64,
        },
    },
    {
        "key": "leave_makes_gross_whole",
        "doc": "30 000 with three days of leave and no typed average: the "
        "náhrada at the average of the seeded March puts back exactly what "
        "the leave took, so the bases are those of 30 000. One engine "
        "carried the unrounded basic wage into the bases, a fraction of a "
        "heller above 30 000, and rounded the premium and the tax base up "
        "from there: health 1 351, tax 4 515.",
        "requires": [],
        "wage": 30000.0,
        "period": PERIOD,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [
            ("leave_type_cz_holiday", (2026, 6, 1), (2026, 6, 3)),
        ],
        # BASIC 30000 x 152/176 = 25909.09; náhrada 24 x 30000/176 = 4090.91.
        # Health: 30000 x 13.5 % = 4050, a third 1350. Tax 15 % of 30000.
        "expected": {
            "BASIC": 25909.09,
            "HOLIDAY_NAHRADA": 4090.91,
            "GROSS": 30000.00,
            "HEALTH_EE": -1350.00,
            "INCOME_TAX": -4500.00,
        },
    },
    {
        "key": "meal_allowance_shifts_worked",
        "doc": "A meal allowance of 129 Kč a shift in June with two days of "
        "leave: 20 shifts worked of 22. The allowance is exempt 'za jednu "
        "směnu' (§ 6 odst. 9 písm. b) ZDP), so a day of leave has none. One "
        "engine paid all 22 scheduled days.",
        "requires": [],
        "wage": WAGE,
        "period": PERIOD,
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_meal_allowance": 129.0,
        },
        "leaves": [
            ("leave_type_cz_holiday", (2026, 6, 1), (2026, 6, 2)),
        ],
        "expected": {
            "MEAL": 2580.00,
        },
    },
    {
        "key": "meal_allowance_above_the_limit",
        "doc": "A meal allowance in money of 150 Kč a shift, 21 shifts in May "
        "2026, against the exempt 129.50 (70 % of the upper meal limit of "
        "185 Kč, § 6 odst. 9 písm. b) ZDP). All 3 150 is paid; 21 x 129.50 = "
        "2 719.50 is exempt and 430.50 is taxable income that also enters "
        "both insurance bases (§ 5 odst. 1 zák. 589/1992 Sb., § 3 odst. 1 "
        "zák. 592/1992 Sb.: income that is not exempt from the tax). The "
        "statute gives the exempt amount no rounding, so the hellers stay. "
        "The allowance is no wage: GROSS stays 50 000. Social base 50 430.50 "
        "up to 50 431 (§ 5d): employee 3 580.601 -> 3 581, employer "
        "12 506.89. Health 13.5 % of 50 430.50 = 6 808.12 -> 6 809, a third "
        "2 270. Advance 15 % of 50 500 = 7 575 less 2 570. NET 50 000 + "
        "3 150 - 3 581 - 2 270 - 5 005. The rule used to pay the exempt part "
        "only, 430.50 short.",
        "requires": [],
        "wage": WAGE,
        "period": MAY,
        "seed": False,
        "version": {
            "l10n_cz_tax_declaration": True,
            "l10n_cz_meal_allowance": 150.0,
        },
        "leaves": [],
        "expected": {
            "GROSS": 50000.00,
            "MEAL": 2719.50,
            "MEAL_TAXABLE": 430.50,
            "TAX_BASE": 50430.50,
            "SOCIAL_EE_TOTAL": -3581.00,
            "SOCIAL_ER_TOTAL": 12506.89,
            "HEALTH_EE": -2270.00,
            "HEALTH_ER": 4539.00,
            "INCOME_TAX": -7575.00,
            "NET": 42294.00,
        },
    },
    {
        "key": "min_wage_topup_public_holiday",
        "doc": "The monthly minimum wage of 22 400 in January with New Year's "
        "Day on the calendar, on the hourly basis that is the default of "
        "§ 111 odst. 2 ZP. The wage is not reduced for the holiday, so it is "
        "the wage for all 176 hours and is compared with 176 x 134.40. "
        "Entering the holiday on the calendar must not change the top-up: "
        "one engine dropped the holiday's hours and kept its wage.",
        "requires": ["l10n_cz_hr_payroll_surcharges"],
        "wage": 22400.0,
        "period": JANUARY,
        "seed": False,
        "holidays": [NEW_YEAR],
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        # 176 x 134.40 = 23654.40, less 22400.
        "expected": {
            "BASIC": 22400.00,
            "MIN_WAGE_TOPUP": 1254.40,
            "GROSS": 23654.40,
        },
    },
    {
        "key": "two_deductions_two_reimbursements",
        "doc": "Two deductions and two reimbursements typed on one payslip "
        "are each added up. One engine handed its rule a single line per "
        "code and deducted 300 of 800.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "inputs": [
            ("DEDUCTION", 500.0),
            ("DEDUCTION", 300.0),
            ("REIMBURSEMENT", 1000.0),
            ("REIMBURSEMENT", 200.0),
        ],
        # NET of 50000 with the declaration is 39270 (social 3550, health
        # 2250, tax 7500 - 2570); - 800 + 1200.
        "expected": {
            "GROSS": 50000.00,
            "DEDUCTION": -800.00,
            "REIMBURSEMENT": 1200.00,
            "NET": 39670.00,
        },
    },
    {
        "key": "typed_attachment_inputs",
        "doc": "An attachment of salary (twice), child support and an "
        "assignment of salary typed on a saved payslip are deducted on both "
        "engines, each code added up.",
        "requires": [],
        "wage": WAGE,
        "period": JANUARY,
        "seed": False,
        "version": {"l10n_cz_tax_declaration": True},
        "leaves": [],
        "inputs": [
            ("ATTACH_SALARY", 300.0),
            ("ATTACH_SALARY", 150.0),
            ("CHILD_SUPPORT", 200.0),
            ("ASSIG_SALARY", 100.0),
        ],
        "expected": {
            "ATTACH_SALARY": -450.00,
            "CHILD_SUPPORT": -200.00,
            "ASSIG_SALARY": -100.00,
            "NET": 38520.00,
        },
    },
    {
        "key": "relief_from_mid_month_version",
        "doc": "A third-degree disability entered on a contract version "
        "dated 15 March. § 35ba odst. 3 ZDP gives the reliefs of odst. 1 "
        "písm. b) to e) for each month 'na jehož počátku' the conditions were "
        "met: on 1 March they were not, so the March payslip computed on the "
        "new version has the taxpayer's relief alone, 2 570. Both engines "
        "read the relief from whichever version the payslip was on.",
        "requires": [],
        "wage": WAGE,
        "period": SEED_PERIOD,
        "seed": False,
        "version": {"l10n_cz_tax_declaration": True},
        "later_version": {
            "date": (2026, 3, 15),
            "values": {"l10n_cz_disability": "3"},
        },
        "leaves": [],
        "expected": {
            "TAX_CREDIT": 2570.00,
        },
    },
    {
        "key": "relief_month_after_the_change",
        "doc": "The same employee in April: the disability held on 1 April, "
        "so the relief is 2 570 + 420.",
        "requires": [],
        "wage": WAGE,
        "period": APRIL,
        "seed": False,
        "version": {"l10n_cz_tax_declaration": True},
        "later_version": {
            "date": (2026, 3, 15),
            "values": {"l10n_cz_disability": "3"},
        },
        "leaves": [],
        "expected": {
            "TAX_CREDIT": 2990.00,
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
# 2025, not 2026: the JMHZ reform (Act No. 323/2025 Coll., transitional
# provisions in Act No. 360/2025 Coll.) ends PVPOJ after 2025 for an employer
# that still employs anyone on 1 April 2026, and the 2026 ELDP covers only
# employees who left before that day. The modules refuse those periods, so a
# 2026 fixture would test the refusal, not the figures.
DECLARATION_PERIOD = ((2025, 3, 1), (2025, 3, 31))

DECLARATION_SCENARIOS = [
    {
        "key": "pvpoj_2025_03",
        "doc": "Přehled o výši pojistného. The employer base is the gross wage "
        "and the two premiums are the statutory percentages of it.",
        "requires": ["l10n_cz_hr_payroll_pvpoj"],
        "model": "l10n.cz.pvpoj",
        "create": {"year": "2025", "month": "3"},
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
        "key": "cz_eldp_2025",
        "doc": "Evidenční list důchodového pojištění. inc is the pension "
        "assessment base for the whole year: 12 x 50 000.",
        "requires": ["l10n_cz_hr_payroll_eldp"],
        "model": "l10n.cz.eldp",
        "create": {"year": "2025"},
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
