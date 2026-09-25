=========
Changelog
=========

All notable changes to **l10n_cz_vat_return** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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

- Export/validation now flows through the shared statutory submission pipeline of
  ``l10n_cssk_vat_return_base`` (kontroly run before render; XML rendered → validated →
  attached in one path). (Wave 3)

[2026-07-02] — Wave 2 (robustness)
----------------------------------

Added
~~~~~

- Pre-export preflight checks (``_cssk_preflight_export``) run before the DPHDP3 XML is generated.

Changed
~~~~~~~

- Locked filed copy retained on submit (filed-history integrity).

[2026-07-01] — Wave 1 (correctness)
-----------------------------------

Changed
~~~~~~~

- Statutory rounding unified to HALF-UP (``l10n_cssk_core`` ``statutory_round()``/``statutory_whole()``),
  replacing banker's ``round()`` / truncation.
- Multi-company ``ir.rule`` (``company_id in company_ids``) added so returns no longer leak across companies.

Fixed
~~~~~

- EPO Pisemnost/DPHDP3 XML: empty attributes now emitted as ``None`` (omitted) instead of ``""``
  (which was XSD-invalid).

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech VAT return (přiznání k DPH / DPHDP3) on the shared VAT-return framework
  (``l10n_cssk_vat_return_base``), CE-clean — computes from the core l10n_cz tax tags
  (no Enterprise ``account_reports``).
- 48 tag-based base/tax lines (obrat23/dan23/…) auto-computed from move-line tags.
- EPO Pisemnost/DPHDP3 XML export (VetaD / VetaP / Veta1–Veta6), mirroring the Odoo EE structure.
- cs_CZ jsonb translations (i18n sweep).
