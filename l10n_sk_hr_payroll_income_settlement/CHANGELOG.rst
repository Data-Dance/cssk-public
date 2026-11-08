=========
Changelog
=========

Unreleased
----------

- *18.0 carry-over:* not on ``l10n_cssk-18.0`` yet, like
  ``l10n_sk_hr_payroll_income_allocation`` it builds on. There the contract
  is ``hr.contract`` (``contract_id``), not ``hr.version``.

[19.0.1.0.2] — 2026-11-08
-------------------------

Added
~~~~~

- **New module: the tax and health side of a cash payment made after the
  employment ended.** It takes the social premiums from the reviewed
  historical register of ``l10n_sk_hr_payroll_income_allocation`` and
  computes, for the month of payment, the health insurance from the current
  income and the monthly tax advance with the dated parameters of
  ``l10n_sk_hr_payroll_oca``. The facts it needs (tax declaration, health
  profile, other payments of the month) are entered on an editable form with
  their evidence, and the result is kept as evidence with an input digest.
- **Earlier payments of the month are consolidated** before the NČZD and the
  tax bands are applied, so a second payment cannot use the allowance or the
  lowest band again. Amounts are rounded to the cent, half up (§ 47 ZDP).
- **A pensioner at 1 January gets no monthly NČZD** (§ 11 ods. 6 and § 36
  ods. 6 písm. c) ZDP, Finančná správa NČZD FAQ 7 and 9); the difference for
  a small pension is left to the annual reconciliation.
- **DoBPŠ income is not health-insured** (§ 10b ods. 1 písm. a) bod 1 of
  580/2004), and the pensioner agreements follow the fund sets of
  ``l10n_sk_hr_payroll_oca``.
- Calculation only: it creates no payslip, accounting entry or authority
  report; those are separate integrations.

Contributed by votrelec (cssk-public#21).
