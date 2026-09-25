=========
Changelog
=========

All notable changes to **l10n_sk_mis_reports** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
