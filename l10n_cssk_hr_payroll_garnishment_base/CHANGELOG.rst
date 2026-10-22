=========
Changelog
=========

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
