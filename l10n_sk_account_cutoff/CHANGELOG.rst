=========
Changelog
=========

All notable changes to **l10n_sk_account_cutoff** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.1] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: thin chart-preset bridge between ``l10n_sk`` and the OCA cut-off / deferral engine (``account_cutoff_start_end_dates``), mapping the company's default cut-off accounts to the Slovak časové rozlíšenie accounts:

  - prepaid expense → **381** Náklady budúcich období
  - deferred revenue → **384** Výnosy budúcich období
  - accrued expense → **383** Výdaje budúcich období
  - accrued revenue → **385** Príjmy budúcich období

- New companies get the mapping when the SK chart loads; existing companies via post-init hook. AGPL-3 (depends on the AGPL OCA engine).
