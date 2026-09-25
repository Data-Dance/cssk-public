=========
Changelog
=========

All notable changes to **l10n_cz_account_cutoff** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-07-04
-------------------------

Added
~~~~~

- Thin bridge between the Czech chart (``l10n_cz``) and the OCA cut-off/deferral engine
  (``account_cutoff_start_end_dates``): a post-init hook pre-fills the company's default cut-off
  accounts with the Czech časové rozlišení accounts — prepaid expense → **381**, deferred
  revenue → **384**, accrued expense → **383**, accrued revenue → **385** — so it works out of
  the box. Licensed AGPL-3 (depends on the AGPL OCA engine).
