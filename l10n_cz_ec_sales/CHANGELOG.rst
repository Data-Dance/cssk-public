=========
Changelog
=========

All notable changes to **l10n_cz_ec_sales** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- The filer block (``VetaP``) comes from ``l10n_cz_statutory``, without the
  e-mail and telephone this form's XSD does not have.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Manual overrides on reported EC lines now survive a recompute (snapshot/re-apply). (Wave 3)
- Export/validation flows through the shared statutory submission pipeline of
  ``l10n_cssk_ec_summary_base`` (kontroly before render). (Wave 3)

[2026-07-02] — Wave 2 (robustness)
----------------------------------

Added
~~~~~

- Pre-export preflight checks (``_cssk_preflight_export``) before the DPHSHV XML is generated.

Changed
~~~~~~~

- Locked filed copy retained on submit (filed-history integrity).

[2026-07-01] — Wave 1 (correctness)
-----------------------------------

Changed
~~~~~~~

- Statutory rounding unified to HALF-UP (``statutory_round()``/``statutory_whole()``).
- Multi-company ``ir.rule`` (``company_id in company_ids``) added.

Fixed
~~~~~

- EPO Pisemnost/DPHSHV XML: empty attributes now emitted as ``None`` (omitted) instead of ``""``
  (XSD-invalid).

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech EC sales list (souhrnné hlášení / DPHSHV) on ``l10n_cssk_ec_summary_base``: aggregates
  intra-EU supplies per (member state, customer VAT, transaction code), with the mandatory VIES
  preflight from the base.
- Transaction codes from ``account.tax.cssk_ec_summary_code`` (0 goods, 1 triangular, 2 services …).
- EPO Pisemnost/DPHSHV XML export (VetaD / VetaP + one VetaR per reported partner line),
  validated against the official DPHSHV XSD (``data/dphshv_epo2.xsd``, ``schema.assertValid``).
- cs_CZ jsonb translations (i18n sweep).
