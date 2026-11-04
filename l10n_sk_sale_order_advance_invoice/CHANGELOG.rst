=========
Changelog
=========

All notable changes to **l10n_sk_sale_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- English name of 324001 (spec ``name`` as a dict) and the post-migrate that
  renames it — 19.0.1.1.1. 18.0 has the same Slovak-only name. Needs the base
  helper carried over first.

[19.0.1.1.1] — 2026-11-04
-------------------------

Fixed
~~~~~

- **324001 had only its Slovak name**, stored as the English one, so an
  English-speaking user saw Slovak. It is now *Advances received – clearing
  (tax document)* in English and keeps *Prijaté preddavky – zúčtovanie (daňový
  doklad)* in Slovak. The upgrade renames the account unless you renamed it.

[19.0.1.1.0] — 2026-09-30
-------------------------

Fixed
~~~~~

- **Companies whose Slovak chart was loaded after this module was installed
  were never wired** with the advance accounts and journal. That includes a
  fresh database where both go in in one run, because the install hook ran
  before the chart existed. The spec is now applied whenever the ``sk`` chart
  is loaded, and the migration wires the companies left out. Only empty
  settings are filled.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0]
------------

- Initial Slovak localization of ``sale_order_advance_invoice``: post_init hook
  wiring the advance-invoice journal and accounts to the Slovak chart
  (324001 clearing [created], 324000 short-term, 475000 long-term).
