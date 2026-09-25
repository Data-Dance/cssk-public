* Slovak only. The Czech localisation has the same two-engine split and no
  parity harness; ``parity.py`` is structured so a ``parity_cz.py`` alongside
  it would need only its own scenarios.
* Scenario coverage is the monthly payslip: dated parameters, NČZD and child
  bonus gating, ZŤP, the wage surcharges and the minimum-wage top-up. Not yet
  covered — dohody, sickness compensation, holiday náhrada, the annual tax
  reconciliation, and the garnishment waterfall driven from the order register.
* The comparison is on payslip line TOTALS. Two engines could agree on every
  total while disagreeing on quantities or rates within a line; nothing here
  would notice.
* Parity of the statutory reporting family is untested. Those modules are
  engine-neutral by construction and detect the engine the same way, but no
  test asserts that a declaration generated on one engine is byte-identical to
  the other's. That is the natural next scenario set.
* ``NOT_COMPARABLE`` records concepts that genuinely cannot be compared, with
  the reason. Check it before concluding something was forgotten.

Engine-seam audit, 2026-08-06
=============================

Every method defined by BOTH ``l10n_sk_hr_payroll_oca`` and
``l10n_sk_hr_payroll_ee`` was extracted and diffed, with the engines' own
vocabulary (``contract_id`` / ``version_id``, ``rule_parameter`` /
``_rule_parameter``, and so on) normalised away so that only semantic drift
showed. Fourteen shared methods across three paired model files.

Result: no wrong numbers, one capability gap and one stale comment.

* ``l10n_sk_hourly_wage`` exists only on the OCA side, and its BASIC rule
  branches on it to pay hours x rate with no proration. Enterprise has no such
  field and always prorates a monthly wage, so it cannot express hourly pay
  through this module. Recorded in ``NOT_COMPARABLE``; closing it is a feature,
  not a fix.
* The Enterprise ``l10n_sk_average_hourly_earnings`` docstring still described
  the flat 174-hour divisor removed in 22f68e1, including a SIMPLIFICATION note
  claiming the constant was still in use. Corrected.
* The remaining differences are the engines' own vocabulary — ``verify/done``
  against ``validated`` for payslip states, ``_get_parameter_value`` against
  ``_get_parameter_from_code``, ``contract`` against ``version`` — and are
  correct as they stand.

Worth repeating whenever a method is added to both sides. The script lives in
the commit that introduced this note; it is short enough to rewrite.

Resolved: MEALEMPLOYER disagreed across engines
==============================================

Measured on a 2000 EUR contract with the financial meal contribution, both
engines resolving the same parameters, the employer line came out ``+102.40``
on OCA and ``-102.30`` on Enterprise — opposite signs and ten cents apart.

The ten cents: 55 % of the 2026 stravné is exactly 5.115, a third decimal a
payslip line cannot hold. Both engines store ``amount`` rounded to 5.12, but
they derive the line TOTAL differently — OCA from the rounded amount
(20 x 5.12 = 102.40), Enterprise from the unrounded value (102.30). Our rule
handed them a three-decimal per-day figure, which is what exposed it.

Fixed by rounding the per-day contribution UP to the cent in both rules, as
the surcharge kernel already does for statutory floors: § 152 sets a MINIMUM
the employer must meet, so up is the only direction that cannot breach it, and
it leaves both engines the same number to work from. Both now report 102.40
and a NET of 1583.59, which the parity scenario asserts.

The SIGN still differs — OCA emits the contribution positive, Enterprise
negative — and the two engines assemble NET differently to compensate. That is
deliberate on both sides and the employee is paid the same, but anything
summing this line by code across engines must take the absolute value.


Why the RLFO has no declaration-parity scenario
===============================================

The other Slovak forms are payslip-derived, so the two engines can disagree
about them and the harness exists to catch that. The RLFO is not: it renders
from the employee and the ``hr.version`` lifecycle — birth number, insurance
dates, agreement type, income regularity — none of which is engine-specific.
Both engines produce identical output by construction, so a scenario
comparing them would assert nothing.

Its own suite covers what actually matters there: that ``typ_zec`` follows
both the agreement type and the income regularity (see the bug fixed in
bbd5d05, where the two ``N`` codes were declared and unreachable).
