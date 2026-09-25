=========
Changelog
=========

All notable changes to **account_gpc_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-08-11
-------------------------

Added
~~~~~

- Single source of truth for the GPC (ABO electronic statement) format, split
  out of ``account_statement_import_gpc`` so the Community and Enterprise
  import shims share one parser:

  - ``utils.gpc.parse_gpc`` — file → ``(currency, account, statements)`` triplets
  - ``utils.gpc.is_gpc`` — format sniff for the Enterprise parser chain
  - ``tests.gpc_fixtures`` — record builders both shims assert against

- No models; helpers are imported via
  ``odoo.addons.account_gpc_base.utils.gpc``.
