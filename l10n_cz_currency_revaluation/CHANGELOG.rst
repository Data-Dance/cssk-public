=========
Changelog
=========

All notable changes to **l10n_cz_currency_revaluation** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
