=========
Changelog
=========

Unreleased
==========

* **19.0.1.8.8 (2026-11-21):** ``OVERTIME_SCENARIOS``: the overtime hours at
  the wage achieved and the premium on average earnings (§ 121 ods. 1
  Zákonníka práce), with the same figures on both engines:
  *overtime_after_a_raise* (1 600 in the first quarter of 2026, 2 100 and
  eight hours in April: 95.46 and 18.75, GROSS 2 214.21),
  *overtime_hourly_rate_three_decimals* (6.125 raised to 7.333: 58.67 and
  12.25, BASIC 1 290.61) and *overtime_in_a_month_with_an_unpaid_day* (June
  2026 on 2 000: 90.91 and 22.73, BASIC 1 909.10). New scenario keys:
  ``history`` confirms payslips of earlier months at an earlier wage or
  hourly rate, and ``expected_lines`` compares payslip lines by rule code.
  Not yet on 18.0.

* **19.0.1.8.7 (2026-11-21):** ``RECORDED_FUND_SCENARIOS``: the fund rows a
  really computed payslip records and each engine's reader returns (base,
  rate and amount of the fourteen fund sides) for a wage of 2 000, one above
  the maximum base, one with the health deductible item and one with the
  health minimum top-up, and the figures of the dávka 514 generated from the
  deductible-item payslip. Both engines must give the same rows, or a
  statement that reads them would differ between them.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.9.0] — 2026-11-21
=========================

**Added**

- Scenarios of several employee records of one person taxed together (§ 35 ods. 1 zákona 595/2003 Z. z.), June 2026: *joint_tax_month_taxed_once* (two agreements, 400 with the declaration and 300 linked to it: bases 342.40 and 256.80, advance 19.37 on the principal's payslip and 0.00 on the linked one, NET 323.03 and 256.80), *joint_tax_child_bonus_cap_on_the_month* (one child under 15: the bonus is whole, 100.00, where 29 % of 342.40 alone would give 99.30) and *joint_tax_second_band_on_the_month* (3 000 and 2 500: 3 665.28 at 19 % and 545.49 at 25 %, 832.78).
- Scenario key ``linked`` (further employee records of the person, whose payslips of the period are computed first) with its own ``expected``, and ``expected_lines`` for lines whose rule code both engines share (``TAXBASE_MOVED``, ``TAXBASE_TAKEN``).

**Carry-over to 18.0**

- Not yet on 18.0: port the scenarios with the joint taxation of both engines.

[19.0.1.8.7] — 2026-11-21
=========================

**Added**

- ``PART_MONTH_SCENARIOS`` for the contract option *Meal also for a Shift of Four Hours or Less* (§ 152 ods. 9 Zákonníka práce), June 2026 at 5.12 a day: *meal_short_shift_option_four_hour_schedule* (22 days, 112.64; none without the option), *meal_short_shift_option_half_day_of_leave* (22 days, 112.64, BASIC 1 954.55; 21 without) and *meal_short_shift_option_day_of_leave* (a day without work earns none: 21 days, 107.52, BASIC 1 909.10).

**Carry-over to 18.0**

- Not yet on 18.0: port the scenarios with the option on both engines.

[19.0.1.8.6] — 2026-11-21
=========================

**Added**

- ``PART_MONTH_SCENARIOS`` for the meal days of § 152 ods. 2 Zákonníka práce, a day with more than four hours worked, June 2026 at 5.12 a day: *meal_full_month* (22 days, 112.64), *meal_afternoon_closed_in_the_calendar* (21 days, 107.52), *meal_half_day_of_leave* (21 days, 107.52, BASIC 1 954.55), *meal_two_half_days_do_not_add_up* (20 days, 102.40, BASIC 1 909.10), *meal_two_hours_at_the_doctor* (22 days, 112.64, BASIC 1 977.28), *meal_schedule_of_four_hours_a_day* (0.00) and *meal_days_on_the_contract_win* (20 days set on the contract, 102.40).
- ``LEAVE_SCENARIOS`` with several leave types of one payroll code in one payslip, June 2026 on 2 000: *two_unpaid_leave_types* (unpaid leave and unpaid leave for education, a day each: BASIC 1 818.19), *sickness_and_quarantine* (two and three scheduled days: BASIC 1 545.46) and *three_paid_obstacle_types* (a day each: BASIC 1 727.28, GROSS 2 000.01).
- Scenario keys ``calendar_closures`` (a part of a day closed in the calendar, ``(date, hour from, hour to)``) and ``worked_days`` (real worked days where no absence asks for them), and a fourth element of a leave, ``{"half": "am"}`` or ``{"hours": (8.0, 10.0)}``, booked on a copy of the starter leave type that takes half days or hours.

**Carry-over to 18.0**

- Not yet on 18.0: port the scenarios with the meal-day count of both engines.

[19.0.1.8.5] — 2026-11-21
=========================

**Added**

- Scenarios *child_of_18_or_over_december_2024* (§ 52zzp ods. 4 and 5 zákona 595/2003 Z. z.: 1 000 € with two children under 18 and one over, bonus 294.44 at 34 % for three children) and *count_of_18_or_over_ignored_from_2025* (850 € in January 2025 with four children under 15 and the number left filled: 368.05 at 50 % for four).
- ``PART_MONTH_SCENARIOS`` *hourly_rate_three_decimals* (new optional ``hourly_rate`` key: 176 hours at 5.259 €, BASIC 925.59) and *hourly_rate_fractional_hours* (165 hours of a 7.5-hour day, BASIC 867.74).

**Carry-over to 18.0**

- Not yet on 18.0: port the scenarios with the third child counter and the four decimals of the hourly rate.

[19.0.1.8.4] — 2026-11-21
=========================

**Added**

- ``HOLIDAY_SCENARIOS``, a public holiday of the calendar inside an absence, monthly salary 2 000 €: *sickness_from_a_public_holiday* (sick 1 to 15 May 2026, daily base 40: BASIC 952.39, employee levies 137.12, tax 154.90, NET 932.37 with 272.00 of sick pay), *unpaid_leave_from_a_public_holiday* (BASIC 952.39), *parental_leave_from_a_public_holiday* (whole May: BASIC 0.00), *leave_from_a_public_holiday* (leave booked 3 to 10 April 2026: BASIC 1 636.37, GROSS 2 000.01) and *public_holiday_inside_leave* (leave 27 April to 5 May 2026, May: BASIC 1 809.53, GROSS 2 000.01).

**Carry-over to 18.0**

- Not yet on 18.0: port the scenarios with the public-holiday handling of both engines.

[19.0.1.8.3] — 2026-11-21
=========================

**Added**

- Scenarios *net_is_income_less_the_rounded_tax* and *net_is_income_less_rounded_tax_plus_rounded_bonus*: NET is the income less the tax advance and plus the child bonus as rounded by § 47 zákona 595/2003 Z. z. (1 238 € in March 2026: 952.85; 918 € with four children: 1 123.89).
- ``PART_MONTH_SCENARIOS``, run with real worked days (new optional ``contract_start`` and ``contract_end`` keys): *contract_ends_mid_month* (2 000 € ending 15 June 2026: BASIC 1 000.00), *hire_mid_month_whole_cents* (1 000 € from 10 March 2026: BASIC 727.28, NET 504.28), *unpaid_day_whole_cent_gross* (2 005 € with one unpaid day in June 2026: BASIC 1 913.87, employer health 210.52), *full_month_is_exactly_the_salary*, *leave_day_base_and_leave_pay_round_up* (2 000 € with one day of leave in May 2026: BASIC 1 904.77, GROSS 2 000.01), *unpaid_day_below_the_minimum_wage* (900 € with one unpaid day in May 2026: BASIC 857.15, top-up 14.28), *meal_days_are_days_worked* (17 days with five days of leave in June 2026, § 152 ods. 2 Zákonníka práce) and *parental_leave_owes_no_topup* (§ 120 ods. 6).
- The leave test also checks ``expected_abs``.
- New optional ``public_holidays`` key: the dates become plain public holidays of a calendar of the scenario's own.

**Changed**

- Wage components are rounded up to the cent, once (owner's decision of 2026-11-21; § 130 ods. 1 Zákonníka práce rounds the wage paid out upward and has no rule for a single component). *employer_obstacle_weather*: BASIC 1 545.45 → 1 545.46, compensation 227.27 → 227.28, GROSS 1 772.72 → 1 772.74. *employer_obstacle_uneven_calendar*: BASIC 1 886.36 → 1 886.37, GROSS 2 000.00 → 2 000.01: two components each rounded up can make GROSS a cent more than the salary.

**Carry-over to 18.0**

- Not yet on 18.0: port the scenarios together with the corresponding fixes of both engines; until then they would fail there.

[19.0.1.8.2] — 2026-11-16
=========================

**Added**

- Scenario *dohoda_pension_oop_above_maximum*, the first on an agreement form (new optional ``form`` key: the OCA structure or the Enterprise structure type of that name): a DoVP with the pension OOP and 17,100 € in June 2026 must give the same social totals on both engines, with the OOP taken off before the maximum (cssk-public#48 and its Enterprise mirror). Both engines used to cap first.

**Carry-over to 18.0**

- Not yet on 18.0: port the scenario and the ``form`` key together with the 18.0 OOP-before-maximum fix of both engines; until then it would fail there.

[19.0.1.8.1] — 2026-10-27
=========================

**Added**

- Scenario *child_bonus_taper_per_child*: the § 33 ods. 11 reduction taken from each child must agree on both engines.

**Fixed**

- The declaration tests use a checksum-valid IČO; the old fixture was rejected by the IČO validation and no declaration parity test ran.

19.0.1.8.0 (2026-08-07)
=======================

* Scenarios can assert a MAGNITUDE via ``expected_abs``. Some lines carry
  opposite signs on the two engines for structural reasons — each assembles
  NET its own way — so a signed assertion would fail for something that is not
  a bug, while asserting nothing lets the amount drift unnoticed.
  ``meal_financial_contribution`` uses it to pin the employer contribution at
  102.40. Negative-tested: a 10 % drift on one engine fails with
  "magnitude 112.64, expected 102.40".

19.0.1.7.0 (2026-08-07)
=======================

* ``meal_financial_contribution`` now asserts NET as well as GROSS. Both are
  hand-derived: 2000 - 188.00 social - 100.00 health - 230.81 tax + 102.40
  meal. The ten-cent divergence the scenario was added to investigate is
  fixed; only the line's SIGN still differs between engines, which is recorded
  in the ROADMAP.

19.0.1.6.0 (2026-08-07)
=======================

* Added meal_financial_contribution: the finančný príspevok na stravovanie
  instead of vouchers. It asserts GROSS, which is hand-derivable — the
  contribution is exempt, so the taxable side must be untouched.
* Recorded an OPEN divergence found while adding it. On identical parameters
  the employer contribution comes out +102.40 on OCA and -102.30 on
  Enterprise: opposite signs, and ten cents apart, where both rule bodies use
  the same formula and the same rounding. NET and GROSS agree on both engines,
  so net pay is not affected and nothing is known to be wrong — but a consumer
  summing that line by code would get opposite answers. See the ROADMAP; it is
  not asserted either way, because neither number is understood yet.

19.0.1.5.0 (2026-08-06)
=======================

* The annual forms are covered. The ELDP and the Hlásenie report a whole year,
  so they need twelve payslips rather than the single March one the monthly
  scenarios share — built inside their own test, since an annual figure sums
  everything in the company and would otherwise move the monthly constants.
  Both are pinned to twelve times a monthly figure already asserted by hand:
  24 000.00 of base and 2 769.72 of tax advance.
* Pinned a KNOWN GAP: the ELDP emits no ``dniVyluc`` at all. It is a hardcoded
  0 in the model and QWeb drops a falsy ``t-att``, so the attribute never
  reaches the XML. Vylúčené doby are real — materská, rodičovská and PN days
  all produce them — so a test now asserts the absence and fails the day it is
  derived, rather than the change slipping through unnoticed.
* The scenario counter moved out of the ``subTest``: a scenario that ran and
  failed has still been covered, and counting it as "did not run" piled a
  second, misleading failure on top of the real one.

19.0.1.4.0 (2026-08-06)
=======================

* The declaration harness covers the VPP as well. Its scenario table
  aggregates over the whole company, so a second employee moves every figure
  in it — adding a dohodár there took the MVP total from 692.00 to 811.20 and
  the Prehľad base from 2000 to 2400. The VPP/MVP population split therefore
  gets its own fixture inside its own test, where the rollback keeps the
  hand-derived constants next door untouched.
* The Sociálna poisťovňa splits its two monthly forms by income regularity —
  regular on the MVP, irregular (dohody) on the VPP — and nothing asserted it.
  A DoPČ on irregular income must appear on the VPP, and the ordinary employee
  must not. Negative-tested: removing the scope filter fails with
  "2 != 1 : the regular-income employee must not be on the VPP".
* findtext_local reads attributes via a trailing @name. The VPP annex
  carries its per-employee figures as attributes, so without it the only
  assertable parts of that form were its totals.

19.0.1.3.0 (2026-08-05)
=======================

* Scenarios can now pin their own working-time calendar via ``calendar_hours``.
  Every scenario shared one 8-hours-every-day calendar, which is precisely the
  shape where proration by days and payment by hours agree — so an 11 EUR
  make-whole bug and an 11 EUR engine divergence both sat inside the harness's
  blind spot. The new ``employer_obstacle_uneven_calendar`` scenario uses a
  40-hour week of 6/10/8/8/8.

19.0.1.2.0 (2026-08-05)
=======================

* Added leave-driven scenarios. Absence is the seam where the engines differ
  most — worked-day codes on OCA, work-entry types on Enterprise — and no
  scenario booked a leave at all, so none of that path was compared.
  ``LEAVE_SCENARIOS`` now does, starting with the § 142 employer obstacle.
* The driver also had to populate OCA worked-day lines explicitly: they come
  from an onchange that does not fire on ``create()`` in a test, so an absence
  scenario would otherwise have compared two untouched full-month payslips and
  passed.

19.0.1.1.0 (2026-08-05)
=======================

* Added an average-earnings scenario. The harness compared payslip lines only,
  and no scenario reached the §134 ods. 3 probable-earnings fallback, so it
  stayed green through a real divergence in the divisor every náhrada is built
  from. ``AVG_EARNINGS_SCENARIOS`` now asserts
  ``l10n_sk_average_hourly_earnings()`` itself on both engines.

19.0.1.0.0 (2026-08-03)
-----------------------

* Initial release.
* ``parity.py`` — one engine-independent set of payroll scenarios and expected
  figures, plus ``CANONICAL_CODES`` mapping each concept to the rule codes that
  carry it on each engine, and ``NOT_COMPARABLE`` for the concepts that
  genuinely cannot be compared.
* One test drives every scenario through whichever engine is installed and
  asserts against the shared figures. Installed in both payroll databases, a
  divergence fails on whichever side moved.
* Skipped scenarios FAIL the run rather than passing quietly: a scenario
  skipped for want of a module is indistinguishable from a passing one, which
  is the failure mode the module exists to remove.
* A second test asserts every rule code named in ``CANONICAL_CODES`` actually
  exists on the engine under test, so a renamed rule cannot read as a silent
  0.00 that agrees with the other engine's 0.00.

19.0.1.0.1 (2026-08-03)
-----------------------

* Declaration-level parity: generate a fixed scenario's statutory filings on
  whichever engine is installed and assert the reported figures against shared
  constants derived by hand from the statutory rates. Payslip parity is not
  sufficient — every declaration module reads payslip lines BY RULE CODE, and
  the codes differ per engine, so a module resolving only one spelling would
  emit a plausible 0.00 that its own test could not catch.
* Found a real defect on its first run: the MVP reported health premiums to
  the Sociálna poisťovňa. See that module's changelog.
* The rule-code map moved to ``l10n_cssk_payroll_declaration_base.rule_codes``.
  Production code needs it at runtime, and a test harness has no business
  owning knowledge production depends on; the parity assertions and the
  declarations now read the same map.
