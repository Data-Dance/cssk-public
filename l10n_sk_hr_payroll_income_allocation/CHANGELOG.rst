=========
Changelog
=========

Unreleased
~~~~~~~~~~

*18.0 carry-over:* not on ``l10n_cssk-18.0`` yet. There the payslip's contract
is ``hr.contract`` (``contract_id``), not ``hr.version``.

[19.0.1.2.0] — 2026-11-06
-------------------------

Changed
^^^^^^^

* The OOP, the maximum base and every premium rate are read from the dated
  rule parameters of ``l10n_sk_hr_payroll_oca`` for each historical month. The
  2027-only lock is gone, and the resolved values are part of the input digest,
  so a changed parameter invalidates a retry.
* The register is entered as editable month × fund rows, each with its own
  evidence, created by *Prepare editable history*. Every row must be reviewed
  before the calculation. The JSON ledger stays optional for API use and cannot
  be mixed with the rows.
* Exact fractions, monthly rounding, archives, retries and the company and
  access rules are kept.
* The documentation states the intended path to the paying payslip and the
  ``ZECN`` row of the VPP, and what is not covered yet.

[19.0.1.1.0] — 2026-11-06
-------------------------

Added
^^^^^

* A register of historical social-insurance assessment bases for income paid
  after the insurance relationship ended (§ 139b of 461/2003), with the
  standard premiums on each newly assessed fund/month base.

Contributed by votrelec (cssk-public#18).
