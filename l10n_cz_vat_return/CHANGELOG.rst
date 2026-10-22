=========
Changelog
=========

All notable changes to **l10n_cz_vat_return** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a
Changelog. The ``19.0.x.y.z`` sections below are the 19.0 series' history,
kept verbatim: this branch reached 1.10.0 by one port rather than by those
releases, and the entries are what the port brought over.

[Unreleased]
------------

[18.0.1.10.0] — 2026-10-19
--------------------------

Changed
~~~~~~~

- **Brought the module to 19.0's 1.10.0 in one step, from 18.0.1.0.1,** with all
  ten of its migrations renumbered into this series — this branch had none, and
  sat below every version that introduced them. Adds the historical VAT rates
  (20, 19, 15, 14, 10, 9 and 5 %, generated archived by cloning each current
  rate family), the DPHDP3 work of nine releases, and the ``post_init_hook``.

Fixed
~~~~~

- **``_cz_map_intra_community_purchase_taxes`` no longer raises on install.** It
  reached for ``account.tax.original_tax_ids``, which does not exist on this
  series, and took the whole module's installation down with it
  (``AttributeError`` inside ``post_init_hook``). It is now an explicit,
  logged no-op here — see the carry-over note.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The intra-Community purchase mapping is NOT applied on 18.0, and an EU
  vendor bill therefore keeps the domestic 21 %.** This is the live bug that
  19.0's 1.7.0 fixed; on this branch it stands.

  It cannot be ported as a translation of the 19.0 code, because 19.0 solves it
  through machinery this series does not have. 19.0 reworked tax alternatives:
  ``account.tax`` gained ``original_tax_ids``, ``fiscal_position_ids``,
  ``replacing_tax_ids`` and ``is_domestic``, and core ``l10n_cz`` ships a
  ``fiscal_position_intra_community`` for them to act on. 18.0's
  ``account.tax`` has none of those four fields; a position maps taxes through
  ``account.fiscal.position.tax`` rows (``tax_src_id`` -> ``tax_dest_id``); and
  18.0 core ``l10n_cz`` has no intra-Community position at all, only
  ``fiscal_position_domestic_cz`` and ``fiscal_position_eu_private_cz`` — the
  latter being private (B2C) trade, not a B2B acquisition.

  So closing it here means CREATING a fiscal position and its mapping rows on
  the Czech chart. That is a client-visible decision about a chart, not a port,
  and it is left for one. ``tests/test_cz_intra_community_mapping.py`` is
  skipped on this series with that reason, on the same condition the model
  guards on, so it starts running again by itself once the mapping exists here.

- **18.0 core's Czech chart has no goods/service split, which is why 12 tests
  fail on this series.** 19.0's ``l10n_cz`` carries 32 taxes to 18.0's 27. The
  five it adds are the service variants — ``l10n_cz_12_domestic_service``,
  ``l10n_cz_12_receipt_domestic_service``, ``l10n_cz_21_domestic_services``,
  ``l10n_cz_21_receipt_domestic_services``, ``l10n_cz_export_services`` — and
  it renames the goods ones to match (``12%`` -> ``12% G``, ``21%`` ->
  ``21% G``).

  Everything that reads the split is affected: the deduction-tagging sweep
  examines no self-assessed purchase tax at all, the historical-rate generator
  cannot find a ``12% G`` to clone, and the intra-Community mapping above has
  no ``21% S`` to send services to.

  The remedy is the Czech twin of ``l10n_sk_tax_report_backport``, which exists
  for exactly this reason on the Slovak side (18.0 core ``l10n_sk`` ships 30
  taxes and no tags). It is a new module, not a port, and it has not been
  written.

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
