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

Carried over
~~~~~~~~~~~~

- **ř. 47 for periods already booked is derivable, and deliberately not
  derived.** ``account_asset_management`` sets ``asset_id`` on a vendor
  bill's own line at post time, so where that module is in use the asset
  acquisitions are a recorded fact and ř. 47 could be computed for history.
  The 1.12.0 migration's first note claimed otherwise and has been
  corrected. Doing it needs a reviewable wizard rather than an unattended
  upgrade — the asset module is optional, the link is absent for assets
  entered by hand or imported from a legacy register, ``tax_tag_ids`` is
  lock-date protected, and re-tagging a filed period adds reporting to a
  return that was already filed.

[18.0.1.12.0] — 2026-10-29
--------------------------

Added
~~~~~

- **ř. 47 — hodnota pořízeného majetku**, ported from 19.0.1.14.0.
  ``l10n_cz`` declares ``+VAT 47 Base`` and ``+VAT 47 Total`` in its tax
  report and ships no tax carrying either, so *hodnota pořízeného majetku
  vymezeného v § 4 odst. 4 písm. d) a e)* filed 0.00 on every return this
  module has produced.

  Every purchase tax whose acquisition is deductible on ř. 40–44 now has a
  *Majetek* twin, identical to its source in rate, repartition, accounts and
  deduction tags, and additionally carrying the ř. 47 tags: ``VAT 47 Base``
  on the base repartition and ``VAT 47 Total`` on the **positive** tax leg,
  so ``od_maj``'s unsigned formula is unchanged. The twins follow the
  historical-rate generator, so each exists at every Czech rate since 2004.

  Three differences from the 19.0 original, all of them this series':

  * **14 twins, not 16.** 18.0 ships the domestic rates as plain ``21%`` and
    ``12%`` where 19.0 splits them into ``21% G``/``21% S``/``12% G``/
    ``12% S``, so the domestic twins are ``21% Majetek`` and
    ``12% Majetek``. Anything mapping legacy tax positions onto them has to
    read the name off this series rather than assume 19.0's.
  * **The tags are signed, per document side.** ``+VAT 47 Base`` /
    ``+VAT 47 Total`` on the invoice repartition and the ``-`` pair on the
    refund one, resolved through ``_cz_deduction_tag``. Our own reader would
    not notice if that were wrong — ``_get_tax_tags`` matches both variants
    and the figures net either way — but Odoo's own tax report multiplies by
    ``tax_negate``, so an unsigned tag on a refund leg inverts ř. 47 there.
  * **No fiscal-position rewiring, because there is nothing to rewire.**
    19.0 carries the replacement on the tax (``original_tax_ids``), where a
    copy inherits it and the Intra-Community position would map one domestic
    line onto both the plain EU tax and its twin. 18.0 has no such field and
    this module does not build the intra-Community mapping on this series, so
    an EU asset purchase has to be entered with ``21% EU G Majetek``
    directly.

  ř. 9 (new means of transport), ř. 42 (daň zaplacená celnímu orgánu,
  shipped at 0 %) and ř. 32 (osvobozené dovozy) deliberately get no twin —
  see ``CZ_ASSET_SOURCE_TAGS``.

  Not ported: 19.0.1.13.0's extra-Community goods/services mapping repair and
  l10n_cssk_vat_return_base 19.0.1.12.0's vintage re-pointing. Both act on
  ``account.tax.original_tax_ids`` / ``replacing_tax_ids``, which do not
  exist on 18.0 — the defects they fix cannot arise here.


[18.0.1.11.0] — 2026-10-28
--------------------------

Fixed
~~~~~

- **ř43/ř44 were still empty on this series, and ř3–13's tax read negative.**
  The deduction hook looked its tags up by their 19.0 names (``VAT 3 Base``)
  while Odoo 18 signs them (``+VAT 3 Base``), so it matched no tax at all and
  tagged nothing; and the ``-VAT 3 Tax`` the 18.0 chart puts on the −100 leg
  is a negating tag on a credit, which Odoo's engine reads as positive and the
  return engine, summing raw balances, as negative. Measured on the first Czech
  agenda compared on this series: ř3 tax −207 298.56 against 207 299 filed,
  ř43 0.00 against 987 136. The hook now reads signed names, creates its
  ř43/ř44 tags signed like the chart's own, and moves the declaration to the
  +100 leg as ``+VAT 3 Tax`` — the shape 19.0's chart ships and the one both
  engines read the same way. A migration re-runs it on existing companies.
- **A period straddling that upgrade would have declared nothing.** Relocating
  the tag on the chart and leaving the posted lines alone is worse than the
  defect it replaces: ``_get_tax_tags`` matches both signed variants of a
  name, so an old line's ``-VAT 3 Tax`` on the output credit leg still sums
  raw as −210 beside a new line's ``+VAT 3 Tax`` on the input debit leg at
  +210, and the two CANCEL. Measured on a throwaway database, one bill posted
  either side of the upgrade: ř3 base 2 000 with ř3 tax 0.00, where 420 was
  due — a plausible base row over an empty tax row. The migration now
  reconciles the posted lines with the repartition's current tags as well,
  through SQL on the tag relation so that a tax lock date cannot abort the
  upgrade or, worse, leave it half done. It logs a warning naming the entries
  and the date range, because those periods recompute differently afterwards;
  nothing filed from Odoo can have depended on the old tags, which produced a
  negative ř3 that no return could carry.

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
