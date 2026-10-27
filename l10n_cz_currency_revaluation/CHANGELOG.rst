=========
Changelog
=========

All notable changes to **l10n_cz_currency_revaluation** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- The revaluation at the rate of the balance-sheet day is § 24c odst. 1
  písm. b) zákona o účetnictví, not "§ 24 odst. 6" (which does not exist).
  The user guide no longer says that Enterprise revalues a fixed-rate company
  at the fixed rate: ``l10n_cz_currency_revaluation_ee`` now reads the ČNB
  rate of the day as well.

[19.0.1.1.0] — 2026-09-28
-------------------------

Changed
~~~~~~~

- The revaluation runs with ``cssk_actual_rates``: a company on a fixed
  monthly rate (``currency_rate_update_cz``) is revalued at ČNB's actual rate
  of the revaluation date. Inert for a company on daily rates.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Thin bridge between the Czech chart (``l10n_cz``) and the OCA multicurrency-revaluation engine
  (``account_multicurrency_revaluation``): a post-init hook pre-fills the revaluation accounts with
  the Czech kurzové rozdíly accounts — **563** and **663**. Licensed AGPL-3 (depends on the AGPL
  OCA engine).
