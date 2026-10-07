=========
Changelog
=========

All notable changes to **l10n_cssk_intrastat_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-10-03
-------------------------

Fixed
~~~~~

- **Nature of transaction is split into its A and B codes.** Both engines
  store it as one 2-digit code (11, 12, 21 …) and both adapters passed it
  whole, so ``natureOfTransactionACode`` read ``11`` and no B code was filed.
  INSTAT carries column A and column B separately; the schema types them as
  plain strings, so validation never objected.
- The description now says how the EE adapter may use an AGPL-3 module: sole
  ownership and dual licensing, not a different licence.

[19.0.1.0.1] — 2026-09-06
-------------------------

Fixed
~~~~~

- Manifest description and README still said the module "is LGPL-3 and can be
  imported by … the proprietary EE adapter alike", while the manifest declares
  **AGPL-3** — a sentence advertising precisely what the licence forbids. The
  engineering fact behind it is unchanged and is what the text says now: no
  OEEL-bound dependency, so the module is ours alone to license.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
