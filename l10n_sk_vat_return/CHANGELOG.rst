=========
Changelog
=========

All notable changes to **l10n_sk_vat_return** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.1.0] — 2026-07-04
-------------------------

Changed
~~~~~~~

- DPH tax tags + tax bindings moved out to the new ``l10n_sk_tax_report_backport``
  module (single source of truth, full 19.0 tax parity). Dropped the inline
  ``data/sk_vat_tax_tags.xml`` and the ``account.chart.template`` tag-binding
  override; now depends on ``l10n_sk_tax_report_backport``. Tag names/codes are
  unchanged, so ``_get_tax_tags`` resolution is unaffected.

[19.0.1.0.3] — 2026-07-04
-------------------------

Added
~~~~~

- §53b dodatočné (supplementary) VAT-return workflow.
- 2024 DPH version data shipped alongside DPHv25 (``cssk_vat_return_2024_version_data.xml``), so prior-period returns resolve their own vintage.

Changed
~~~~~~~

- Statutory rate constants moved to version data: ``_RATE_PAIRS`` → the version record's ``rate_pairs``; settlement line codes (own-tax / excess, r32 / r33) parameterised via version fields — a new DPH vintage is now pure data (Wave 3, 2026-07-03).
- Export pipeline consolidated into the shared ``cssk.statutory.submission.mixin`` (draft gate → preflight → kontroly → render → XSD validate → attach); kontroly now run before render.

Fixed
~~~~~

- 2024 DPH periods were being validated against 2025 rates — periods now resolve the correct rate vintage from version data.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Fixed
~~~~~

- Multi-company leak: ``ir.rule [('company_id','in',company_ids)]`` added so returns no longer cross companies.

Changed
~~~~~~~

- Statutory rounding unified on ``l10n_cssk_core/tools.py::statutory_round()`` (HALF-UP ``float_round``), replacing banker's ``round()`` in the line evaluator.

[2026-06-30] — Initial baseline
-------------------------------

Added
~~~~~

- Slovak VAT return (Daňové priznanie k DPH, **DPHv25**) on ``l10n_cssk_vat_return_base``: output base/tax per category (``sk01``, ``sk03``, ``sk05``), deductible tax (``sk19``, ``sk20``), aggregates + net VAT, wired to the l10n_sk DPH tax tags — CE-clean (no ``account_reports``).
- FS SR ``DPH`` XML export (QWeb template + stand-in XSD; replace with the official schema before live filing).
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
