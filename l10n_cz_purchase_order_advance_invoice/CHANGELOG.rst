=========
Changelog
=========

All notable changes to **l10n_cz_purchase_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
