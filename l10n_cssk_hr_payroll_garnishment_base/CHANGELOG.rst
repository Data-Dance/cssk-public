=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.3.0] — 2026-10-27
-------------------------

Added
~~~~~

- **Two thirds with four or more executions (§ 279 odst. 4–6 o. s. ř.).**
  When at least four executions (court, bailiff or administrative) run
  against the wage, the second third no longer stays with the employee:
  priority claims take it first, as before, and what they leave joins the
  first third for everyone by rank. Agreements on wage deductions and
  insolvency deductions are not counted.
- The exception of § 279 odst. 5 applies to an employee marked *Pension
  Recipient* while one third stays below the insolvency trustee's monthly
  amount — a new rate field, 1 089 Kč for 2026 ((750 + 150) × 1.21, vyhl.
  313/2007 Sb.).

Fixed
~~~~~

- **A payslip whose deduction was already remitted can no longer be
  cancelled** (it already could not be reset to draft): the correction would
  have deducted the month again.
- **Notice citations.** Joining is notified under § 294 odst. 2 o. s. ř. and
  leaving under § 295 odst. 2 (both cited § 294 odst. 1, the duty to ask the
  previous employer for a certificate); an enquiry is answered under § 128
  o. s. ř. / § 33 odst. 5 exekučního řádu. A Slovak company's notices cite
  § 84 ods. 2 / § 85 ods. 2 Exekučného poriadku instead of the Czech code.

[19.0.1.2.2] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Czech deductions started a month early.** *Start Date* defaulted to the
  day the order was delivered, so the wage for the month of delivery was
  already garnished. Under § 282a o. s. ř. deductions start from the first
  day of the month after delivery; the default is now that day. Slovak orders
  are unchanged. Orders already registered keep their stored start date —
  check those delivered in the current month.
- **Czech amounts were taken from the wrong year.** The protected amount and
  the unlimited-seizure limit were looked up for the end of the wage period;
  NV 595/2006 § 4 takes them as at 1 January of the year in which the wage is
  paid. A December wage paid in January now uses the new year's amounts (the
  payslip's payment date is used when the payroll engine records one;
  otherwise the wage is taken as paid in the following month).
- **Dependants recorded on the contract were ignored.** When *Maintained
  Persons* on the employee is left at zero, the number of dependants kept on
  the Czech or Slovak payroll contract is used.
- **Slovak amounts were rounded half up.** NV 268/2006 § 4 rounds the
  protected amounts and the unlimited-seizure limit down to whole cents.

19.0.1.2.1 (2026-09-07)
-----------------------

* **Orders leaked across companies.** ``_active_orders`` and
  ``_payslip_has_orders`` searched on employee and state alone. The
  multi-company record rule does not stand in for a company filter —
  ``company_ids`` in a rule resolves to the user's ALLOWED companies, not to
  ``env.company`` — so a payroll officer entitled to A and B was shown B's
  orders while computing an A payslip. The line's ``company_id`` is
  ``related=garnishment_id.company_id``, so the deduction then belonged to B
  and the remittance was booked in B's journal against an A payslip. Both are
  scoped now, and ``_active_orders`` **resolves** the company rather than
  merely honouring it when passed: a filter that vanishes when an argument is
  omitted is not a fix, it is one every future caller has to remember.
* **A remitted payslip could be reset, and the ledger then counted twice.**
  ``_cssk_garnishment_unregister`` keeps ``done`` lines (right — the money has
  gone) while ``_register_allocation`` clears only ``state != 'done'`` before
  writing fresh ones, so re-confirming left a ``done`` and a ``computed`` line
  on the same ``payslip_ref``. The employee was still debited once; what broke
  was the bailiff-facing ledger — ``paid_amount`` inflated,
  ``remaining_amount`` understated, which on a nearly settled order ends an
  exekúcia early. The draft transition is refused instead, in both engine
  bridges, before anything is reset.
* **The payee bank account was enforced only by a form domain.** A domain does
  not run on import, on a server action, or on any write that did not pass
  through that form, and the account is copied onto the remittance entry and
  paid into. A constraint now requires it to belong to the payee's commercial
  partner.
* ``amount_unlimited`` is no longer displayed. It has always been zero: both
  ``compute_cz`` and ``compute_sk`` merge the fully seizable amount above the
  statutory limit into the two third-pools before allocating, so a per-line
  share of it is not something the waterfall produces — only pool totals are.
  Totals and debtor protection were never affected. The field stays (existing
  rows unchanged) and now says so in its help; the column is gone from the two
  payslip views, the deduction list and the settlement report, because a column
  reading zero is read as "nothing came from there" rather than "not tracked".
  Deliberately NOT "fixed" by producing the split: the pools are floored to the
  currency unit before distribution, so splitting them to attribute a source
  would move real amounts by up to a unit — the wrong trade for a display
  column, in a calculator awaiting practitioner sign-off.

19.0.1.0.0 (2026-07-27)
-----------------------

* Initial release.
* ``hr.wage.garnishment`` — engine-neutral register of Czech and Slovak
  wage-garnishment orders (exekuční / exekučný príkaz) with creditor, bailiff,
  remittance bank account and payment symbols, delivery date establishing the
  rank, running balance and a ``draft → running → settled`` state machine.
* ``hr.wage.garnishment.line`` — per-payslip deduction ledger recording which
  third each amount came from.
* ``hr.wage.garnishment.rate`` — dated statutory figures for CZ (2026) and SK
  (2024, 2025, 2026 subsistence-minimum vintages).
* ``garnishment_calc`` — pure-Python allocator implementing the multi-claim
  waterfall of ``§ 279``/``§ 280 o. s. ř.`` and ``NV 268/2006 Z. z.``,
  including maintenance precedence, pro-rata distribution at equal rank and
  the fully seizable part above the statutory limit. Money is apportioned by
  the largest-remainder method with every grant floored to the currency unit,
  so the grants of several claims can never sum past the third they came out
  of and no sub-unit residue is lost. 22 worked-example unit tests plus
  seeded property tests asserting that no claim exceeds its outstanding
  balance, that the total never exceeds two thirds plus the unlimited part,
  and that the debtor always keeps the non-attachable amount.
* Rounding is deliberate throughout: currency scaling rounds to a fixed
  precision before flooring (so ``0.30 * 100`` does not lose a cent) rather
  than adding a one-sided epsilon that would bias every grant upwards, and
  the Slovak protective-floor correction rounds UP, since rounding a
  correction down could leave a residual breach of the limit it enforces.
* The Slovak protective floor is iterated to a fixpoint: trimming can zero
  out the only claim of the deepest-reaching class, which raises the floor.
* ``date_start`` defaults to the day the order was served rather than to
  today: under ``§ 282(1) o. s. ř.`` the employer must begin deducting from
  delivery, and a today-default silently excluded the order from any earlier
  period being (re)computed.
* The link to the remittance journal entry lives in the accounting bridge,
  not here — this module must stay installable without ``account``.
* Statutory notice wizard and QWeb reports for ``§ 294``/``§ 295 o. s. ř.``
  notifications and the account of deductions.
