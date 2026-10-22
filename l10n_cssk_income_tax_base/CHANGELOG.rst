=========
Changelog
=========

All notable changes to **l10n_cssk_income_tax_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.2.3] — 2026-07-04
-------------------------

Changed
~~~~~~~

- DPPO export consolidated onto the shared ``cssk.statutory.submission.mixin``
  pipeline (draft gate → preflight → kontroly → render → XSD validate → attach).

[2026-07-02] — Wave 2 (P1 robustness)
-------------------------------------

Added
~~~~~

- Filed-copy retention on submit and pre-export preflight
  (``_cssk_preflight_export``) before the DPPO XML is rendered.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Changed
~~~~~~~

- Line values rounded with ``statutory_round()`` (HALF-UP).

Fixed
~~~~~

- Multi-company leakage: ``ir.rule`` ``[('company_id','in',company_ids)]`` on the
  return model.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral framework for the corporate income-tax return (DPPO),
  mirroring the VAT-return / FS frameworks; CE-clean (``account`` only).
- ``cssk.income.tax.version`` + line definitions (``account`` = P&L result,
  ``aggregate`` = tax-computation spine, ``manual`` = accountant adjustments) +
  submission types.
- ``cssk.income.tax.return`` (mail.thread) — evaluator that auto-computes the
  accounting result and the formulaic spine, preserves manual overrides and feeds
  them into dependent aggregate lines on recompute, and produces XSD-validated
  statutory XML. Country layers (``l10n_sk_dppo`` …) supply the line set, header
  mapping and schema.
- Full cs_CZ + sk_SK translations.
