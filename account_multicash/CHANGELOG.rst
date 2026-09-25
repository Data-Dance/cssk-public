=========
Changelog
=========

All notable changes to **account_multicash** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.2.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Export of payments in the MultiCash formats used by Czech banks, generated on an
  OCA ``account.payment.order`` (CE-clean — no Enterprise dependency):

  - **CFD** — domestic Czech credit transfers and direct debits (inkasa)
  - **CFU** — urgent domestic Czech credit transfers
  - **CFA** — foreign (cross-border) payments
  - **MT101** — SWIFT Request For Transfer

- File building delegated to the shared ``account_cz_bankfile_base`` MultiCash
  builder; MultiCash payment method registered via ``data/account_payment_method.xml``.
