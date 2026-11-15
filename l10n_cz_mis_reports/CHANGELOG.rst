=========
Changelog
=========

All notable changes to **l10n_cz_mis_reports** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Manažerská výsledovka on the ``l10n_cz`` chart as a ``mis_builder`` template:
  21 lines from tržby down to the výsledek hospodaření po zdanění, read by
  account-code pattern so no tagging is needed. The Czech counterpart of
  ``l10n_sk_mis_reports``.
- Změna stavu zásob vlastní činnosti and aktivace (účtová skupina 58) are a
  cost line, as the Czech chart has booked them since 2016. The internal
  transfer accounts 597/697/699 are with the operating lines and 598/698 with
  the financial ones, the same sides the Výkaz zisku a ztráty puts them on.
- Tests that evaluate the report against posted entries, including one entry
  on every account of classes 5 and 6 of the chart: the result after tax must
  equal the ledger's, so an account on no line, or on two, fails.
