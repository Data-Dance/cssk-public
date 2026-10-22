=========
Changelog
=========

All notable changes to **l10n_sk_ec_sales** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.1.0] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Now depends on ``l10n_sk_tax_report_backport``, which backports the 19.0 SK
  tax set onto 18.0. The ``vy_eu_m`` / ``vy_eu_t`` / ``vy_eu_s`` intra-EU supply
  taxes the ``post_init_hook`` tags with their Súhrnný výkaz code now exist on
  the 18.0 chart, so EC-sales collection works as on 19.0.

[19.0.1.0.2] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Manual overrides on EC-summary lines now survive recompute (snapshot/re-apply) (Wave 3).
- Export pipeline consolidated into the shared ``cssk.statutory.submission.mixin``; kontroly now run before render.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Fixed
~~~~~

- Multi-company leak closed with an ``ir.rule [('company_id','in',company_ids)]``.

Changed
~~~~~~~

- Statutory rounding unified on ``statutory_round()`` (HALF-UP).

[2026-06-30] — Initial baseline
-------------------------------

Added
~~~~~

- Slovak Súhrnný výkaz (EC sales list) on ``l10n_cssk_ec_summary_base``: transaction codes **0** = goods (dodanie tovaru), **1** = triangulation (trojstranný obchod), **2** = services (dodanie služby), driven by ``account.tax.cssk_ec_summary_code``.
- FS SR ``SDV`` XML export (QWeb template + stand-in XSD; replace with the official schema before live filing). CE-clean (no ``account_reports``).
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
