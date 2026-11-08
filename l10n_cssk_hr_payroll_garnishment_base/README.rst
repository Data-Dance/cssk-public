===============================
CZ/SK Wage Garnishment — Base
===============================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Engine-neutral register of Czech and Slovak wage-garnishment orders (exekuční / exekučný príkaz) with the statutory multi-claim waterfall and the employer's statutory notices.**

In both the Czech Republic and Slovakia a court, a bailiff or an
administrative authority can order that part of an employee's wage be
withheld and paid straight to the creditor. The employer is not a bystander
in that process: it must rank the orders, apply a statutory waterfall across
all of them, remit the money and answer to the court for what it did.

This module is the engine-neutral foundation for that. It ships:

* **The register** — ``hr.wage.garnishment``, one record per order served on
  the employer: case number, claim class, the *day it was delivered* (which
  is what legally establishes the rank), the creditor, the bailiff, the bank
  account and payment symbols it must be remitted to, the total claim and the
  running balance.
* **The deduction ledger** — ``hr.wage.garnishment.line``, one row per order
  per payslip, recording not just the amount but *which third* it came from,
  so the calculation is auditable years later.
* **The allocator** — a pure-Python, Odoo-free implementation of the statutory
  waterfall, unit tested in isolation:

  * Czech Republic: ``§ 276-§ 302 o. s. ř.`` + ``nařízení vlády 595/2006 Sb.``
    — the nezabavitelná částka, the thirds, maintenance taking absolute
    precedence in the second third (pro rata by *current* maintenance,
    disregarding arrears), everything else strictly by pořadí, and the fully
    seizable part above the limit joining the second third only as far as the
    priority claims need it.
  * Slovakia: ``nariadenie vlády 268/2006 Z. z.`` — including the part most
    implementations get wrong, that the protected *základná suma* depends on
    what is being collected: 140 % ŽM for an ordinary claim, 100 % for a
    priority one, 70 % of 60 % for maintenance of a minor child, 50 % for an
    administrative fine, with the per-dependant addition doubling to 50 % for
    a pension recipient.

* **Dated statutory rates** — ``hr.wage.garnishment.rate``, so a new
  subsistence minimum is a data change, not a code change.
* **The employer's statutory paperwork** — a wizard producing the notices of
  a debtor joining or leaving, the answer to an enquiry about rank and
  amounts (``§ 294``, ``§ 295 o. s. ř.``), and the account of deductions
  (*vyúčtování srážek*).

The base depends on ``hr`` and ``mail`` only — never on a payroll engine. The
bridge modules wire it into the ``payroll`` (OCA) and ``hr_payroll``
(Enterprise) engines, and the accounting bridge turns each deduction into a
payable to the bailiff.

.. rubric:: Known issues / Roadmap

Known limitations and deliberate simplifications, all of which the allocator
documents inline:

* **Czech rate vintages.** Only the 2026 figures are shipped. The 1 January
  2026 reform changed the *shape* of the formula (85 % of a three-component
  sum instead of 3/4 of a two-component one, limit 1.9× instead of 1.5×), so
  pre-2026 periods cannot be expressed in these fields. Add a rate record if
  you need to recompute an older period.

* **Slovak mixed-class waterfall.** Because each Slovak claim class carries
  its own protected base, the thirds are not a single pot. The allocator
  computes them per class and then applies the Czech-style waterfall, held in
  check by two conservative invariants: no claim may exceed what its own
  class could legally reach on its own, and the employee always retains at
  least the smallest protected base among the claims actually deducted. Where
  the statute is silent on how classes with different bases share the first
  third, this errs towards deducting less. When either invariant trims a
  claim, the freed money is deliberately **not** redistributed to other claims
  that could legally absorb it — the hard constraint is never to exceed a
  legal limit, not to maximise creditor recovery.

* **Slovak cent rounding.** ``NV 268/2006 § 4`` rounds the protected sums to
  eurocents; published tables occasionally differ from the computed value by
  one cent depending on whether an intermediate step is rounded. The
  coefficients are data, so a site that must match a particular published
  table exactly can adjust them.

* **Insolvency.** ``insolvency`` is offered as an order type and is computed
  exactly like a priority execution, which matches the ordinary *oddlužení
  plněním splátkového kalendáře* case. The special regimes (lower deductions
  approved by the court, ``§ 398`` IZ variants) are not modelled.

* **Non-wage income.** Only wages are covered. Deductions from sickness
  benefits, pensions or other income paid by third parties are outside the
  employer's payroll and outside this module.

* **Order of statutory deductions.** The allocator starts from the net wage
  the payroll engine hands it. Ensuring that tax and insurance are withheld
  before garnishments is the payroll structure's job, not this module's.

.. rubric:: Module facts

- **Technical name:** ``l10n_cssk_hr_payroll_garnishment_base``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``hr``, ``mail``

Authors: Data Dance s.r.o.
