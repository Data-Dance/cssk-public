=========
Changelog
=========

All notable changes to **l10n_sk_dppo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-07-04
-------------------------

Added
~~~~~

- r150 (pripočítateľná položka, book > tax) and r250 (odpočítateľná položka, tax > book) auto-fed from the asset board via the ``asset_diff`` line kind (2026-07-02).

Changed
~~~~~~~

- §15 rate bands and §46b minimum-tax bands moved to version data (``rate_bands`` / ``min_tax_bands``), so a new DPPO vintage is pure data (Wave 3, 2026-07-03).
- Line spine guarded so custom/edited versions are not clobbered on upgrade.

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

- Slovak DPPO return (**DPPOv25**, with DPPOv24 also shipped) on ``l10n_cssk_income_tax_base``: full body line set r100 … r1192 as version data; r100 (výsledok hospodárenia pred zdanením) computed from the P&L, the rest via the override UI.
- Header mapping from the company (DIČ, IČO, obchodné meno, sídlo, zdaňovacie obdobie, typ priznania).
- Official ``dppo2025.xsd`` vendored; XML export validated against it.
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
