=========
Changelog
=========

All notable changes to **l10n_cz_purchase_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- English name of 314001 (spec ``name`` as a dict) and the post-migrate that
  renames it — 19.0.1.0.2. 18.0 has the same Czech-only name. Needs the base
  helper carried over first.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.2] — 2026-11-04
-------------------------

Fixed
~~~~~

- **314001 had only its Czech name**, stored as the English one, so an
  English-speaking user saw Czech. It is now *Advances provided – clearing
  (tax document)* in English and keeps *Poskytnuté zálohy – zúčtování (daňový
  doklad)* in Czech. The upgrade renames the account unless you renamed it.

[19.0.1.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- A company whose chart is loaded after the add-on was installed (a new
  company, or a database where chart and add-on go in in one run) is wired
  too, as on the sales side.

[19.0.1.0.0] — 2026-07-15
-------------------------

Added
~~~~~

- Initial release: statutory chart wiring (clearing 314001, net 314000,
  journal PDADV) for the received advance-invoice flow.
