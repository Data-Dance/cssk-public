=========
Changelog
=========

All notable changes to **l10n_sk_account_loan_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Baseline: applies the Slovak leasing account roles to the OCA ``account_loan`` /
  ``account_leasing`` engine, via ``default_get`` and ``_onchange_company``.
- ``_onchange_company`` is overridden because the engine clears the liability and
  interest accounts on a company change; the bridge refills them from the new
  company's Slovak defaults rather than leaving blanks.
- Declares ``excludes: ["account_loans"]`` so the exclusivity is visible on the module
  a user actually installs (``account_loan`` also carries it).
- AGPL-3 (depends on the AGPL OCA engine).

[19.0.1.1.0] — 2026-08-06
-------------------------

Added
~~~~~

- The lease's DPH classification now drives posting instead of merely recording a
  choice: on a lease that is a supply of **goods** (§ 8 ods. 1 písm. c), the
  generated instalments carry **no VAT**. The whole VAT fell due once, on the day
  of handover, from the entire agreed price; taxing the instalments as well would
  tax the same supply repeatedly. A lease treated as a supply of **services** is
  untouched — the service is progressively delivered, so each instalment is taxed,
  which is the engine's own behaviour.
- Implemented on ``account.move.line._get_computed_taxes``, the point at which the
  engine assigns taxes to a generated instalment invoice.
- The goods test uses a product that DOES carry a purchase tax, so it fails if the
  override is removed rather than passing vacuously; negative-tested.
