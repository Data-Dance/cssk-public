=========
Changelog
=========

Unreleased
==========

* A June 2027 parity scenario: a DPP without a declaration, taxed by the
  advance on the separate base of § 6 odst. 4 ZDP (``SEPARATE_TAX_BASE``).

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.2.6] — 2026-11-21
=========================

Added
~~~~~

- Four scenarios for a public holiday inside an absence: a sickness and a
  quarantine of 1 to 9 January 2026 over New Year's Day (§ 192 odst. 1 ZP:
  56 hours compensated, wage for 120 of 176 hours), a sickness whose first
  14 days ended before the holiday (no wage and no compensation for it),
  and unpaid leave over the holiday, which no provision settles and which
  stays the paid holiday on both engines.
- A scenario for a meal allowance of 150 Kč a shift against the exempt
  129.50 (§ 6 odst. 9 písm. b) ZDP): the part above the limit is paid, taxed
  and in both insurance bases. New concepts ``MEAL_TAXABLE`` and
  ``TAX_BASE``.

[19.0.1.2.5] — 2026-11-21
=========================

Added
~~~~~

- Thirteen scenarios on the seams where the two engines paid differently: a
  contract ending inside the month, with and without a public holiday on
  the calendar; a full month, a sickness and dovolená beside or over a
  public holiday (New Year's Day, Easter 2026); the meal allowance per shift
  worked; the bases of a wage made whole by a náhrada; the minimum wage
  top-up in a month with a public holiday; two deductions and two
  reimbursements; typed attachment, child support and assignment inputs;
  the disability relief of a contract version dated inside the month.
- Three scenarios for the statutory whole-crown rounding: the employee's
  social premium (§ 7 odst. 3 zák. 589/1992 Sb.), the assessment base (§ 5d)
  and the tax advance above the 23 % threshold (§ 38h odst. 3 ZDP).
- Sickness compensation is exempt from income tax (§ 6 odst. 9 písm. p) ZDP):
  the month-long sick leave scenario expects no tax and the whole 8 640 Kč
  paid out, and a new scenario, a week of sickness in a worked month with a
  declaration, expects the advance on the wage alone.
- The driver puts public holidays on a scenario's own calendar, ends a
  contract, adds a later contract version and types inputs on the saved
  payslip (``holidays``, ``contract_end``, ``later_version``, ``inputs``;
  ``seed: False`` skips the seeded March).

Changed
~~~~~~~

- A payslip is computed on the contract version in force on its last day,
  not on the employee's current one.

[19.0.1.2.3] — 2026-10-27
=========================

Added
~~~~~

- Two scenarios: a month-long sick leave (only 14 days of compensation,
  taxed, no health minimum base) and the health premium rounding on a wage of
  30 001 Kč.

Changed
~~~~~~~

- The DPP scenario works four hours a week, so the new minimum wage top-up of
  the surcharge bridges has nothing to top up.

[19.0.1.2.2] — 2026-10-27
=========================

Added
~~~~~

- A DPP scenario: 8 000 Kč in 2026 is above the DPČ rozhodný příjem but
  below the 12 000 Kč DPP amount, so neither engine may charge insurance or an
  advance tax. Both engines once did, for a DPP not ticked as "notified".

19.0.1.2.0 (2026-08-06)
=======================

* The CZ ELDP is covered: ``inc`` is the annual pension assessment base, held
  to twelve times the 50 000.00 monthly gross the payroll suite already
  asserts. The twelve-payslip fixture lives in its own test, since an annual
  figure sums everything in the company and would otherwise move the monthly
  constants.
* The Vyúčtování is deliberately NOT asserted. Its Part I reports 7 500 a
  month — 15 % of the base — where the payslip withholds 4 930, the same
  figure less the 2 570 sleva na poplatníka. Which of the two the form wants
  is question 6 in ``docs/cz-otazky-pro-mzdoveho-odbornika.md``; asserting the
  current figure would bless a number nobody has checked, and this is money
  reported to the finanční úřad.

19.0.1.1.0 (2026-08-06)
=======================

* Added the declaration harness. Every declaration module reads payslip lines
  BY RULE CODE, and a module that resolved only one engine's spelling would
  emit a plausible 0.00 while its own test — comparing against the payslip
  next to it in the same database — passed. The PVPOJ is asserted against
  fixed constants derived by hand from the statutory rates: a 50 000.00 base
  with 3 550.00 employee and 12 400.00 employer premiums.
* Negative-tested by moving the employee social rate from 7.1 % to 6.5 %,
  which a read-back test would have accepted silently: the harness fails with
  3250.0 != 3550.0.

19.0.1.0.0 (2026-08-06)
=======================

* Initial release. One shared set of Czech payroll scenarios, driven through
  whichever engine is installed and asserted against the same expected figures,
  so a cross-engine divergence fails a test instead of reaching a payslip.
* Scenarios book REAL leaves rather than only payslip inputs, because absence
  is the seam where the two engines differ most — worked-day codes on OCA,
  work-entry types on Enterprise.
* Includes a scenario on a full-time week that is NOT the same length every day
  (6/10/8/8/8). That shape is ordinary in practice and is precisely where a
  wage prorated by day fractions stops agreeing with a náhrada paid by hours —
  the bug that had to be fixed on the Slovak side.
* Both guards are negative-tested: diverging one engine's § 207 a) rate fails
  with 11363.64 != 9090.91, and switching the proration to a day basis fails
  the uneven-calendar scenario with 47435.90 != 47159.09.
