=========
Changelog
=========

All notable changes to **l10n_cz_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.2] — 2026-08-26
------------------------

Changed
~~~~~~~

- **Renamed ``l10n_cz_dd`` → ``l10n_cz_base``.** Reason: ``_dd`` was overloaded — "Enterprise variant" on the payroll modules, "Data Dance" here. Mirrors the same rename on 19.0 so the two
  branches keep one module naming, and ``tools/check_module_parity.py`` can trust the
  suffix (``EE_SUFFIXES`` dropped ``_dd``). Installed 18.0 databases need
  ``tools/rename_dd_to_ee.sql`` run against them **before** the server starts on this
  code — Odoo does not rename a module by itself.

[18.0.1.0.1] — 2026-07-18
-------------------------

Changed
~~~~~~~

- ``variable_symbol`` / ``constant_symbol`` / ``specific_symbol`` are now
  stored related aliases of the canonical ``l10n_cssk_payment_symbols``
  fields (new dependency). A pre-migration merges previously entered legacy
  values into the canonical columns; the aliases stay writable for one
  release before removal.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Czech base localization building blocks (depends only on ``account``): bidirectional Czech
  IBAN ↔ legacy "prefix-number/bankcode" conversion on ``res.partner.bank`` (legacy account
  number, prefix and bank code computed from the IBAN, which stays primary storage).
- Variable / Constant / Specific symbol fields (VS / KS / SS) on ``account.move``.
- cs_CZ jsonb translations (i18n sweep, 2026-06-30).
