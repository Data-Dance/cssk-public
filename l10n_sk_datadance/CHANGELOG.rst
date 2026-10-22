=========
Changelog
=========

All notable changes to **l10n_sk_datadance** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Two modules were renamed to English**, and the suite follows them:
  ``l10n_sk_zavierka`` is now ``l10n_sk_fiscal_year_closing`` (the settings
  toggle is now ``module_l10n_sk_fiscal_year_closing``), and
  ``l10n_sk_inventarizacia`` is now ``l10n_sk_inventory_verification``.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: one-click Slovak statutory localization meta-module. Installs the statutory core in one step — KV DPH, Súhrnný výkaz, DPH priznanie, Súvaha + VZS, DPPO, SK invoice, VIES, saldokonto + zápočet, and dohadné (accruals).
- Optional workflow pieces (FX sync, deferrals, guarantor-liability check, dual depreciation, Method A, advance invoices) selectable in Settings → Accounting → Slovak localization.
