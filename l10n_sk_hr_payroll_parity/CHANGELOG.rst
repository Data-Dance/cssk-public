=========
Changelog
=========

Unreleased
==========

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
