=========
Changelog
=========

All notable changes to **l10n_cz_vat_return** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.14.0] — 2026-10-29
--------------------------

Added
~~~~~

- **ř. 47 — hodnota pořízeného majetku.** ``l10n_cz`` declares
  ``VAT 47 Base`` and ``VAT 47 Total`` in its tax report and ships no tax
  carrying either, so *hodnota pořízeného majetku vymezeného v § 4 odst. 4
  písm. d) a e)* filed 0.00 on every return this module has produced.
  Checked against a Czech agenda's own filed returns for 11 periods between
  2021-09 and 2025-11, the row carried millions of crowns of base in a single
  month on every one of them — so the shipped chart could not produce a
  correct return for any taxpayer that buys fixed assets.

  The missing fact is per-document and binary — is this purchase a long-term
  asset? — and Odoo has nowhere to put it, so it goes where the return
  already reads from: the tax. Every purchase tax whose acquisition is
  deductible on ř. 40–44 now has a *Majetek* twin (``21% G Majetek``,
  ``21% EU G Majetek``, …; 16 of them on the shipped chart), identical to its
  source in rate, repartition, accounts and deduction tags, and additionally
  carrying the ř. 47 tags: ``VAT 47 Base`` on the base repartition and
  ``VAT 47 Total`` on the **positive** tax leg, so ``od_maj``'s unsigned
  formula is unchanged. Picking a twin reports the acquisition on ř. 47 as
  well as on ř. 40–44, with no other change to the return.

  The twins follow the historical-rate generator, so each exists at every
  Czech rate since 2004 (56 archived clones) and a history import can report
  a 15 % asset purchase on ř. 47. ř. 9 (new means of transport), ř. 42 (daň
  zaplacená celnímu orgánu, shipped at 0 %) and ř. 32 (osvobozené dovozy)
  deliberately get no twin — see ``CZ_ASSET_SOURCE_TAGS``.

[19.0.1.13.0] — 2026-10-29
--------------------------

Fixed
~~~~~

- **The Extra-Community position could not tell goods from services.**
  ``l10n_cz`` points BOTH extra-Community service taxes at the domestic
  **goods** tax, so one 1 000 CZK line carrying ``21% G`` was mapped onto
  three taxes — ``21% EX G``, ``21% EX S`` and ``0% EX G.Custom`` — and the
  same purchase was declared on ř. 7, ř. 12 and ř. 42 while ř. 43 deducted
  420.00 against a real 210.00. The bill still totalled 1 000.00, because
  each self-assessment cancels itself, so nothing on the document disagreed.
  In the other direction ``21% S`` mapped to nothing at all, so a service
  bought from outside the EU kept the Czech 21 % the supplier never charged
  and was never self-assessed. ``0% EX G.Custom``'s own auto-mapping is
  reported but deliberately left alone.

[19.0.1.12.0] — 2026-10-27
--------------------------

Fixed
~~~~~

- **Whole crowns by the rule, not by banker's rounding.** Tax rows (daň na
  výstupu, odpočet, ř. 62 – 66) are rounded up to the next crown, as § 146
  odst. 1 daňového řádu says ("Daň se zaokrouhluje na celé koruny
  nahoru"); bases and values to the nearest crown, half away from zero; the
  ř. 52 / 53 coefficients up to a whole percent (§ 76 odst. 3 ZDPH). The
  export used ``'%.0f'``, which rounds a half to the even crown: 1 002.50
  of base was filed as 1 002.
- **A dodatečné přiznání files the differences.** Every row now states the
  difference from the return it amends ("V dodatečném přiznání se uvádí
  pouze rozdíly od údajů, ze kterých byla stanovena poslední známá daň",
  pokyny 25 5412), and ř. 66 the difference from the last known tax. It
  filed the full values of the period, so ř. 66 claimed the whole period's
  tax again. The rows on screen keep the full values. A dodatečné/opravné
  (E) raised from a dodatečné differs from what that dodatečné amended.

- **The settlement of a dodatečné přiznání is ř. 66.** *To pay* read ř. 64 /
  65, which a dodatečné leaves empty, so it showed nothing to pay; it now
  shows the difference against the poslední známá daň.

Changed
~~~~~~~

- A dodatečné (D) or dodatečné/opravné (E) return must be created with
  *Amended / corrective* on the filed return: without the return it amends
  there is nothing to state differences from, and the export says so.

[19.0.1.11.0] — 2026-10-27
--------------------------

Fixed
~~~~~

- **ř. 46 and ř. 62 – 66 are computed.** They were manual lines, so a return
  filed vlastní daň, nadměrný odpočet and the totals as 0 unless every one
  was overridden by hand. They now follow the EPO structure's own
  definitions (ř. 62 = 1 … 13 − 61, ř. 63 = 46 + 52 + 53 + 60, ř. 64 / 65
  the positive difference, ř. 66 the difference on a dodatečné přiznání
  only), summed from the rows as filed so the totals foot. An override on
  any of them is kept. The § 108 odst. 4 písm. g) and h) tax, which has no
  row of its own, still has to be added to ř. 62 by override.
- **One discovery date.** The return had two (the shared one, asked for on
  an amendment, and the Czech *Důvody zjištěny dne* the XML read); they are
  now the same field, and existing values of the Czech one are kept.
- The settlement (*To pay / (refund)* and the excess carry-forward) now
  works for Czech returns: the version names ř. 64 and ř. 65.
- Content checks: ř. 64 and ř. 65 must not be negative and are never both
  filled.
- The bundled ``dphdp3_epo2.xsd`` is refreshed to the published structure
  03.01.04 (documentation changes only), ``verzePis`` states that version,
  and both are pinned in ``data/SCHEMA_VERSION`` with a test.

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
