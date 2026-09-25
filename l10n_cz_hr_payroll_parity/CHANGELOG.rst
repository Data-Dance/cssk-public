=========
Changelog
=========

Unreleased
==========

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
