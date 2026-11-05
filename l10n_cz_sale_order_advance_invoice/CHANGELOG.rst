=========
Changelog
=========

All notable changes to **l10n_cz_sale_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- TDADV journal and 324001 named in cs/sk/en, post-migrate — 19.0.1.1.2.
- English name of 324001 (spec ``name`` as a dict) and the post-migrate that
  renames it — 19.0.1.1.1. 18.0 has the same Czech-only name. Needs the base
  helper carried over first.

[19.0.1.1.2] — 2026-11-04
-------------------------

Fixed
~~~~~

- **The TDADV journal had only its Czech name**, stored as the English one.
  It is now *Daňové doklady k přijatým platbám* / *Faktúry k prijatým
  platbám* / *Tax Documents for Received Advance Payments*, and 324001 has a
  Slovak name too. The upgrade renames both unless you renamed them.

[19.0.1.1.1] — 2026-11-04
-------------------------

Fixed
~~~~~

- **324001 had only its Czech name**, stored as the English one, so an
  English-speaking user saw Czech. It is now *Advances received – clearing
  (tax document)* in English and keeps *Přijaté zálohy – zúčtování (daňový
  doklad)* in Czech. The upgrade renames the account unless you renamed it.

[19.0.1.1.0] — 2026-09-30
-------------------------

Fixed
~~~~~

- **Companies whose Czech chart was loaded after this module was installed were
  never wired** with the advance accounts and journal. That includes a fresh
  database where both go in in one run, because the install hook ran before
  the chart existed. The spec is now applied whenever the ``cz`` chart is
  loaded, and the migration wires the companies left out. Only empty settings
  are filled.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0]
------------

- Initial Czech localization of ``sale_order_advance_invoice``: post_init hook
  wiring the advance-invoice journal and accounts to the Czech chart
  (324001 clearing [created], 324000 short-term, 475000 long-term).
