=========
Changelog
=========

All notable changes to **l10n_cssk_intrastat_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Dependency-free INSTAT (instat62) XML builder for INTRASTAT-SK:
  ``cssk.instat.builder.build_instat_xml(header, lines)`` renders the official
  Finančná správa INTRASTAT-SK message from a normalized header + line dicts.
- Bundled ``data/instat62.xsd`` for validation.
- **LGPL-3** and dependency-only on ``base`` — no OCA ``intrastat_product``, no Odoo
  EE ``account_intrastat`` — so it can be imported by both the AGPL CE adapter
  (``l10n_sk_intrastat``) and the proprietary EE adapter.
- cs_CZ + sk_SK translation catalogues.
