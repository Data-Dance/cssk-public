=========
Changelog
=========

All notable changes to **l10n_cz_vat_return** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.10.0] — 2026-09-29
--------------------------

Fixed
~~~~~

- **DPHDP3** ``VetaD`` now carries ``c_okec`` (the company's CZ-NACE 2025 code) and
  ``d_poddp`` (the filing date); EPO reports both missing as serious errors
  (checked live in test mode, 2026-09-29).

Added
~~~~~

- **ř. 33 / ř. 34 from flagged documents.** A document marked as a bad-debt
  correction leaves every ordinary row — figure and drill-down alike — and its
  tax goes to ř. 33 (creditor, positive for the § 46 reduction) or ř. 34
  (debtor, positive for the § 74b return of the deduction), on top of any
  hand-tagged ``VAT 33`` / ``VAT 34`` entry. ř. 34 was a manual line and
  becomes a tag line (migration 19.0.1.9.0; a typed value survives as an
  override).

- The filer block (``VetaP``) comes from ``l10n_cz_statutory``: typ_ds F for a
  natural person, address, oprávněná osoba, sestavil, zástupce.
- ``d_zjist`` (*Důvody zjištěny dne*) on a dodatečné return, required before
  export; ``typ_platce`` from the company's VAT status.

Fixed
~~~~~

- **"Dodatečné" exported E, which the form reads as "dodatečné/opravné".**
  The XSD's ``dapdph_forma`` is B / O / **D** dodatečné / **E**
  dodatečné/opravné; the type labelled *Dodatečné* carried E and D did not
  exist, so every dodatečné přiznání filed through this module declared itself
  a correction of a dodatečné one. D now exists and E is labelled for what it
  is (migration 19.0.1.8.0). Returns already exported are not touched.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **Intra-Community purchase-tax mapping (2026-09-27): does NOT port as-is.**
  18.0 ``l10n_cz`` has no Intra-Community fiscal position at all (only
  Domestic and Private-EU, mapping via ``tax_ids/tax_src_id``), so an EU vendor
  bill there has nothing to map through. What 18.0 needs is a position with
  ``21% G``→``21% EU G`` etc. as ``account.fiscal.position.tax`` rows; decide
  with Radovan before building it.

Fixed
~~~~~

- **An EU vendor bill kept the domestic VAT instead of self-assessing it.**
  ``l10n_cz`` ships ``21% EU G``, ``12% EU G``, ``21% EU S`` and ``12% EU S``
  with an empty ``original_tax_ids`` (the Extra-Community taxes are mapped), so
  the Intra-Community fiscal position mapped nothing: ``21% G`` stayed
  ``21% G`` and 30.00 of goods from a Slovak supplier was billed at 36.30. The
  four are now linked to ``21% G`` / ``12% G`` / ``21% S`` / ``12% S`` on
  install, on every Czech chart load and by the 19.0.1.7.0 migration. Links
  are only added, so a hand-made mapping survives; posted moves are not
  rewritten.

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
