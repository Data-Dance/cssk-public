=========
Changelog
=========

All notable changes to **l10n_sk_mis_reports** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Every class 5 account reaches the result.** 507 (predané nehnuteľnosti),
  592 (odložená daň z príjmov) and 596 (prevod podielov na výsledku
  hospodárenia spoločníkom) were on no line, so *Výsledok hospodárenia po
  zdanení* differed from the ledger by whatever sat on them. 507 has its own
  cost line, 592 joins *Daň z príjmov*, 596 has its own line below it.

- **The helper line for classes 54/55 is no longer printed.** It now has a
  hidden style.

Changed
~~~~~~~

- An installed template is brought up to date on upgrade, but only where a
  line still holds what an earlier version shipped; a line you changed is
  left alone.

[19.0.1.0.0] — 2026-08-06
-------------------------

Added
~~~~~

- Manažérska výsledovka on the ``l10n_sk`` chart as a ``mis_builder`` template:
  19 KPIs from tržby down to the výsledok po zdanení, read by account-code pattern
  so no tagging is needed.
- 7 tests that evaluate the report against posted entries rather than only
  asserting the records exist — including that odpisy are not double-counted
  inside trieda 55, and that 59x income tax does not land in operating costs
  (which would make the operating result already after tax).

Gotcha
~~~~~~

A KPI name must not start with an accounting-expression prefix (``bal``, ``balp``,
``crd``, ``deb``): MIS Builder rewrites those tokens textually, so the helper KPI
``balp_54_55`` was compiled as ``(AccountingNone)_55 - odpisy`` and every
expression using it failed with ``#ERR``. Renamed ``trieda_54_55``.
