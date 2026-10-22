=========
Changelog
=========

All notable changes to **l10n_cssk_ec_summary_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.2.3] — 2026-07-04
-------------------------

Added
~~~~~

- Manual line overrides now survive ``action_compute_lines``: edited EC lines are
  snapshotted and re-applied on recompute.

Changed
~~~~~~~

- Export consolidated onto the shared ``cssk.statutory.submission.mixin`` pipeline
  (draft gate → preflight → kontroly → render → XSD validate → attach).

[2026-07-02] — Wave 2 (P1 robustness)
-------------------------------------

Added
~~~~~

- Filed-copy retention on submit and pre-export preflight hardening around the
  mandatory VIES gate.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Changed
~~~~~~~

- Reported amounts rounded with ``statutory_round()`` (HALF-UP).

Fixed
~~~~~

- Multi-company leakage: ``ir.rule`` ``[('company_id','in',company_ids)]`` on the
  statement model.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral framework for the Slovak **Súhrnný výkaz** and Czech
  **Souhrnné hlášení** (EC sales list): one aggregated line per (member-state,
  customer VAT, transaction code), so a single line model serves both.
- ``cssk.ec.summary.statement.version`` (versioned template + schema + types),
  ``cssk.ec.summary.statement`` (mail.thread; draft → preview → exported →
  submitted) with ``action_compute_lines`` and ``action_export_xml``,
  ``cssk.ec.summary.statement.line``, and ``account.tax.cssk_ec_summary_code``
  marking intra-EU supply taxes + their transaction code.
- **Mandatory VIES preflight** before export (hard block, not a soft warning).
- CE-clean (Odoo core only — no ``account_reports``). Full cs_CZ + sk_SK
  translations.
