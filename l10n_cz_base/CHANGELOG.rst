=========
Changelog
=========

All notable changes to **l10n_cz_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.2.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Czech screen. The template and the catalogues now carry them,
  and the Czech is written.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.2.0.1] — 2026-08-26
-------------------------

Changed
~~~~~~~

- **Renamed ``l10n_cz_dd`` → ``l10n_cz_base``.** Reason: ``_dd`` was overloaded — it meant "Enterprise variant" on the payroll modules and "Data Dance" here. All Enterprise-side modules in the
  collection now carry a single ``_ee`` suffix, so ``tools/check_module_parity.py``
  can trust the name again (``EE_SUFFIXES`` dropped ``_dd``). Installed databases
  need ``tools/rename_dd_to_ee.sql`` run against them **before** the server starts
  on this code — Odoo does not rename a module by itself.

[19.0.2.0.0] — 2026-07-14
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
