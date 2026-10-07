=========
Changelog
=========

All notable changes to **l10n_sk_vat_return** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.1.12.0 (2026-09-21), not yet on 18.0.** EU-service purchase taxes
  and their *Eu intra* mapping (commit d380b99). Verify the 18.0 ``l10n_sk``
  chart's tax xmlids, tags and fiscal-position mapping mechanism first: the
  CSV mirrors 19.0's ``vs_tuz_*`` / ``vs_rc_*``, and 18.0 maps through
  ``account.fiscal.position.tax`` rows rather than ``original_tax_ids``.

[19.0.1.12.0] — 2026-09-21
--------------------------

Added
~~~~~

- **Services received from the EU (§ 69 ods. 3).** Stock ``l10n_sk`` maps
  every purchase tax under the *Eu intra* fiscal position to the acquisition
  of **goods** (row 07/08), so a service from an EU supplier was filed in the
  wrong row, and there was no tax for it at all. New domestic purchase taxes
  ``23% S`` / ``19% S`` / ``5% S`` (scope *Services*) map under *Eu intra* to
  ``23% EÚ S`` / ``19% EÚ S`` / ``5% EÚ S``, which self-assess in rows
  09b/10b, 09/10 and 09a/10a — the repartition of the chart's own
  ``vs_rc_*`` — and reach KV DPH B.1. Set the ``S`` tax as the vendor tax of
  service products; goods keep theirs and still map to row 07. The same split
  the chart already makes on the sale side. Loaded on install and upgrade into
  existing SK companies, only where missing. Reported by an external
  accountant.

[19.0.1.11.3] — 2026-09-13
--------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

[19.0.1.11.2] — 2026-09-13
--------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak screen. The template and the catalogues now carry them,
  and the Slovak is written.

[19.0.1.11.1] — 2026-09-13
--------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.11.0] — 2026-09-10
--------------------------

Added
~~~~~

- **``r_deduction_total`` — a rate-agnostic deduction total on every SK vzor.**
  The tlačivo has no such row: the form carries six disjoint deduction rows
  (three kinds × two rates) and r01–r38 hold nothing that sums them, which is
  why the per-rate halves are internal too. The new line is internal for the
  same reason.

  It exists because legacy systems file "odpočítaná daň celkom" as **one**
  number. Mapped onto a single per-rate half — which is what a comparison
  against an imported filing will reach for — such a figure agrees on an
  agenda whose purchases are all standard-rated and **silently drops every
  reduced-rate deduction**. Found while ruling on exactly that mapping against
  a real imported agenda.

  Excludes r29/r30, which ``r_net`` subtracts separately. Purely additive:
  ``r_net`` still reads the two halves, no computed figure moves and no filing
  changes.

  The test is the invariant rather than a direction — the total must name
  **every** half its version defines. A vintage that adds a rate, as 2025 did
  with ``r18a_total``, fails there instead of quietly under-reporting for
  years.

  A ``post-migration`` adds the line to existing databases. Measured on a
  1.10.0 copy: all five version records still lacked it after the upgrade, so
  the data-file edit alone would have reached fresh installs only. The
  migration **derives** the formula from each version's own halves rather than
  carrying a table of them — an earlier draft did carry one, which was the
  same defect the line exists to repair.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The three pre-2021 DPH vzory (19.0.1.9.0) and the § 69 ods. 3 split
  (19.0.1.10.0) are owed to 18.0.** Both are statutory, not version-specific.
  The row RENUMBERING is the part that matters: the 2021 vzor merged
  § 69 ods. 3 into r09/r10 and shifted every row from r11 down by two, so a
  2019 period filed on the 2021 grid puts daň celkom on an odpočet row and
  validates perfectly while doing it. The split needs ``line_filter`` on the
  shared line definition (l10n_cssk_vat_return_base) and the
  ``l10n_sk_dph_69_par`` marker with it.

[19.0.1.9.0] — 2026-09-09
-------------------------

Added
~~~~~

- **The three DPH vzory that precede 2021**, so a period before 2021 resolves
  to a version at all. It previously resolved to none — not a wrong figure but
  NO figure, the return refusing to compute.

  ::

      dph2012.xsd   1. 1. 2012 – 31. 12. 2017   (DPHv12)
      dph2018.xsd   1. 1. 2018 – 31. 12. 2019   (DPHv18)
      dph2020.xsd   1. 1. 2020 – 31. 12. 2020   (DPHv20)

  Probed across ``dph2009``..``dph2026``: those three plus 2021 and 2025 are
  ALL that Finančná správa publishes; every other year is a 404. The five
  vintages now tile every period from 1. 1. 2012 with no gap and no overlap.

- Two templates for them. The 2018 and 2020 vzory share one document shape —
  their schemas are byte-identical apart from a documentation string — while
  DPHv12 has a structured ``tel``/``fax`` where the later vzory have a plain
  ``telefon``/``email``, and no ``zastupca69aa``.

- ``data/SCHEMA_VERSION`` extended to pin all five, each verified
  byte-identical against the published copy.

Fixed
~~~~~

- **The row numbering.** These vzory are NOT the 2021 grid with an earlier
  date. The 2021 vzor merged § 69 ods. 3 into r09/r10 and so shifted every row
  from r11 down by two, then added the § 25a and § 53b rows and dropped the
  trojstranný obchod pair. Filing a 2019 period on the 2021 grid would put daň
  celkom on an odpočet row and the vlastná daňová povinnosť two rows off —
  while validating perfectly, because an XSD counts elements and does not read
  them. Verified row by row against the official tlačivá DPHv12, DPHv18,
  DPHv20 and DPHv21.

- **The § 69 ods. 3 split.** These vzory give § 69 ods. 3 — služba dodaná
  zahraničnou osobou — its own row pair r11/r12, apart from § 69 ods. 2 a 9 až
  12 on r09/r10. The ``l10n_sk`` chart has ONE reverse-charge purchase family
  (tags 09/10), because the current form merges the paragraphs, so no TAG can
  separate them. The rows share the tags and split on the new
  ``line_filter``, resolved per line from what the paragraph actually says:
  a § 69 ods. 3 service comes from a supplier not established in Slovakia.

  ``account.tax.l10n_sk_dph_69_par`` overrides that where a company uses a tax
  for one paragraph only — a dedicated domestic-construction prenos
  (§ 69 ods. 12) whoever the supplier is, or a § 69 ods. 2
  goods-with-installation tax whose supplier IS foreign but whose row is
  r09/r10. Nothing is preset: the shared ``vs_rc_*`` taxes carry both
  paragraphs, and marking them § 69 ods. 3 would move every domestic
  construction reverse charge onto r11/r12.

Known limitation
~~~~~~~~~~~~~~~~

- **r18 is manual in all three**, because it means different things in them
  (§ 81 deregistration in 2012/2018, § 48ca/§ 48d/§ 48e in 2020) and no
  ``l10n_sk`` tag routes to either.
- § 25a and § 53b have no row in these vzory at all — neither existed in law
  before 2021 — so a line carrying those tags in an old period reaches no row.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.3] — 2026-07-04
-------------------------

Added
~~~~~

- §53b dodatočné (supplementary) VAT-return workflow.
- 2024 DPH version data shipped alongside DPHv25 (``cssk_vat_return_2024_version_data.xml``), so prior-period returns resolve their own vintage.

Changed
~~~~~~~

- Statutory rate constants moved to version data: ``_RATE_PAIRS`` → the version record's ``rate_pairs``; settlement line codes (own-tax / excess, r32 / r33) parameterised via version fields — a new DPH vintage is now pure data (Wave 3, 2026-07-03).
- Export pipeline consolidated into the shared ``cssk.statutory.submission.mixin`` (draft gate → preflight → kontroly → render → XSD validate → attach); kontroly now run before render.

Fixed
~~~~~

- 2024 DPH periods were being validated against 2025 rates — periods now resolve the correct rate vintage from version data.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Fixed
~~~~~

- Multi-company leak: ``ir.rule [('company_id','in',company_ids)]`` added so returns no longer cross companies.

Changed
~~~~~~~

- Statutory rounding unified on ``l10n_cssk_core/tools.py::statutory_round()`` (HALF-UP ``float_round``), replacing banker's ``round()`` in the line evaluator.

[2026-06-30] — Initial baseline
-------------------------------

Added
~~~~~

- Slovak VAT return (Daňové priznanie k DPH, **DPHv25**) on ``l10n_cssk_vat_return_base``: output base/tax per category (``sk01``, ``sk03``, ``sk05``), deductible tax (``sk19``, ``sk20``), aggregates + net VAT, wired to the l10n_sk DPH tax tags — CE-clean (no ``account_reports``).
- FS SR ``DPH`` XML export (QWeb template + stand-in XSD; replace with the official schema before live filing).
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
