=========
Changelog
=========

All notable changes to **l10n_sk_dppo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- Print Table K whole-euro amounts in its continuous rectangles rather than
  imposing an artificial four-digit cell limit. Preserve the original cent
  cells, normal font size and strict checks against actual field width.

- Select the published form by its applicable legal filing deadline, including
  a recorded effective extension. Fiscal-period overlap alone cannot authorize
  the obsolete2025 wire. The paper adapter shares this applicability check;
  minimum-tax amounts remain keyed on the period start. A late actual filing
  date does not change the form's legal deadline.

Added
~~~~~

- Ordinary double-entry Tables F/L from the existing posted ledger or
  explicitly reviewed imported source figures. Entered signed revenue
  adjustments feed native row 560, validate their linked return rows and
  print every item, with continuation copies where needed. Row 1110 now
  defaults to the published advance-tax calculation; reviewed historic
  section 35/35a relief has an explicit evidenced blank-field treatment.

- Entered Table D original losses, native prior-return references, reviewed
  following-period ordinals, deduction caps and remaining/expired balances.
  Apply the reviewed total to native row 410, recompute and validate atomically;
  changed facts also block an inconsistent native tax provision. Print all
  eight columns and the total on the original pages, plus entered special
  records. Eligibility remains an accountant fact, not a second tax ledger.
- Share company-scoped input normalization across I/D. Entire multi-return
  batches are checked first and lock one sorted parent set in a savepoint,
  preventing the former opposite-order batch deadlock and partial mutation.

- Native entered Table I transactions and loans, the below-threshold
  declaration and official PDF mapping. Signed effects remain disclosure
  facts and never write the tax spine or GL. Original printed rows continue
  on marked additional pattern pages up to the statutory 99 rows per section.
  Company-scoped child access, native amendment copy and terminal-state
  protection apply to the entered facts.

- Unsigned native download on the pinned 21-page MF/014309/2026-721 PDF,
  with body and Tables A/B, entered identity/declarations, reviewed minimum
  tax, supplementary discovery date, source hashes and preserved original
  pages. Saved financial inputs are validated before printing. Other nonzero
  annex claims explicitly require their matching entered annex adapter.
  Equal snapshots reuse attachments; historical PDF bytes remain available.

- Published MF/014309/2026-721 form registry and calculation, separate from
  historical2025: sports306, shifted vehicle/CFC rows, manual17k adjustment310,
  subtotal315, special tax1072 and the period-sensitive11,520 minimum band.
  Effective accountant overrides feed subsequent rows and the native tax
  provision. The published paper form is not confused with a published XML
  schema: XML export remains explicitly unavailable pending its official
  electronic adapter. Official source/archive hashes are recorded in
  ``data/FORM_PUBLICATION.json``.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.1.5.0 (2026-11-09), not yet on 18.0:** tabuľky A and B as return
  lines, r130/r150/r250 derived from them, the table export check, the
  two-digit row fix and its migration. Needs ``l10n_cssk_income_tax_base``
  19.0.1.6.0 (dependency-ordered aggregates) first.

[19.0.1.5.0] — 2026-11-09
-------------------------

Added
~~~~~

- **Tabuľky A and B are return lines.** Every vzor carries them as lines of
  their own, coded by table: ``a01`` … ``a17`` (``a15`` on 2013 and 2014) and
  ``b01`` … ``b06`` (``b04`` on 2013 and 2014). The úhrn rows are computed:
  A17 = A1 + … + A16, B6 = max(0, B2 − B3 − B4 + B5) (DPPOv25 eForm,
  ``vypocet_r06tabb``). The XML files the tables; a row nobody touched is
  filed empty.
- With ``account_asset_tax`` installed, Table B comes from the tax
  depreciation register: B1 accounting depreciation, B2 tax depreciation
  before B4 and without B5, B4 the § 22 ods. 9 suspended charge, B5 the
  § 22 ods. 12 part in the year of sale, tangible assets only. B3 (§ 19
  ods. 3 písm. a)) is entered by hand. Every table line can be overridden.
- Export check: an overridden r130, r150, r250, A17 or B6 that disagrees with
  its table blocks the export, as the eForm refuses it. It applies only when
  the table carries a value, so a return that types r150 on the main row and
  leaves the tables empty files as before.

Changed
~~~~~~~

- **r130 = A17, r150 = max(0, B1 − B6), r250 = max(0, B6 − B1)** (2013 and
  2014: r150 = max(0, B2 − B1), r250 the reverse; their tabuľka B has the
  účtovné odpisy on r. 2). Before, r130 was typed and r150/r250 came straight
  from the register. With r. 3 at 0 the figures are the same; an existing
  override on any of the three rows is kept.
- The migration switches the three rows on existing databases (the version
  data is ``noupdate``) and removes the generic two-digit rows.

Fixed
~~~~~

- **A two-digit row no longer files into every table.** The 2013–2022 vzory
  had one line per code ``r01`` … ``r31``, and the template read it in row N
  of every table and section (13 to 24 places). A figure typed into one row
  appeared in all of them, and an untouched one filed ``0.00`` in all of
  them. Those lines are gone; the other tables are filed empty. An override
  left on one of them is logged by the migration, because it cannot be
  assigned to one table.

[19.0.1.4.9] — 2026-11-09
-------------------------

Added
~~~~~

- Export warns when the loss deduction r410 is above 50 % of the tax base (§ 30 ods. 1), for periods from 2020 and income above 100 000 €.

[19.0.1.4.8] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.4.7] — 2026-10-27
-------------------------

Fixed
~~~~~

- The seat's *ulica* / *číslo* are read by the shared helper of
  ``l10n_cssk_core``, the same as on every other Finančná správa form. A
  street that is only a number (``č. p. 123``) now files an empty *ulica* and
  the number as *číslo*, instead of the whole text as *ulica*.

[19.0.1.4.6] — 2026-10-27
-------------------------

Fixed
~~~~~

- **r200 on the 2015 and 2017 editions now includes r120 and r160.** Both rows
  sit in the block of pripočítateľné položky that r200 totals (DPPOv15 and
  DPPOv17 poučenie, riadky 110 až 180) — r120 for pokuty and úroky z
  omeškania under § 17 ods. 19 as in force to 2014, r160 for § 17 ods. 17
  kurzové rozdiely — and were left out, understating the tax base.

- **The XML no longer names the company as the § 50 recipient.** The
  generated templates filled every IČO, name and address in the schema with
  the company's own, so the § 50 prijímateľ, the oprávnená osoba's trvalý
  pobyt and a stála prevádzkareň carried the filer's data. Only the header
  (sídlo) does now; the rest is left for you.

- **Header from the company record.** The DIČ is the Slovak DIČ, or the
  IČ DPH without its "SK"; the house number is taken from the end of
  *Street* instead of from *Street2*; the SK NACE code comes from the
  company's NACE code and the právna forma from the trade register module
  when they are installed; the date of the declaration is the export day.

[19.0.1.4.5] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Daňová licencia in the lower band when the VAT registration category is
  blank.** With ``l10n_sk_vat_registration`` installed but neither the
  registration date nor the category filled in, the company was treated as
  not a VAT payer, so the licencia came out at 480 € instead of 960 €. A blank
  category now falls back to the *Tax ID*, as without that module.

[19.0.1.4.4] — 2026-10-27
-------------------------

Fixed
~~~~~

- **No daňová licencia on the 2018 and 2019 editions after § 52zk.** r810
  carried a licencia of 480 € / 960 € / 2 880 € on every return filed on the
  2018 or 2019 vzor, overstating the tax. § 52zk applies the licencia for the
  last time to a period ending on 31 December 2017, or to a hospodársky rok
  ending in 2018; for every later period r810 is now 0 and r1050 is the tax
  alone. A hospodársky rok ending in 2018 still gets its licencia.
- **A 2026 period explains why it cannot be created.** Finančná správa SR has
  not published the DPPO vzor for 2026 (checked 27. 10. 2026), and none is
  invented here; instead of an empty *Version* list the return now warns
  that no form version covers the period.

[19.0.1.4.3] — 2026-09-13
-------------------------

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

[19.0.1.4.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak screen. The template and the catalogues now carry them,
  and the Slovak is written.

[19.0.1.4.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.4.0] — 2026-09-10
-------------------------

Fixed
~~~~~

- **The kladný rozdiel was filed on the wrong row for 2017–2019.** The spine
  wrote ``r820 = r810`` on every vintage. That is right for the minimálna daň
  vzory and wrong for the daňová licencia ones, because the form **reused the
  row number**: verified against the pinned FS SR schemas, 2017/2018/2019
  define r800/r810/r820 and **no r830**, while 2013–2015 and 2024+ define r830
  as well. Finančná správa's own usmernenie (20. 12. 2018) prints the
  licencia vzor's worked example — r800 600, r810 960, **r820 360** — i.e.
  ``r810 − r800``, not ``r810``.

  The spine now routes on whether the vzor defines r830. 2013–2015 keep their
  existing behaviour: they do define r830, their block is four rows, and
  there is no source here for how it differs.

Added
~~~~~

- **§ 46b daňová licencia bands on 2014–2019.** ``min_tax_bands`` was
  populated only on 2024, so r810 computed 0,00 for every licencia year.
  480 € / 960 € / 2 880 €, verified against the usmernenie quoting § 46b
  ods. 2 verbatim.

- **Bands may carry a condition.** 480 and 960 sit at the *same* turnover
  bound and are separated by whether the taxpayer was a platiteľ DPH on the
  last day of the period — which a table keyed on turnover alone cannot say.
  A band is now ``[upper, amount]`` or ``[upper, amount, condition]``;
  unknown conditions never match, so a band nobody can evaluate is skipped
  rather than silently applied. Backward compatible: the 2024/2025 tables
  carry no conditions and are untouched.

  Platiteľ status is read from ``l10n_sk_vat_registration`` when installed
  (it records the registration *and* its effective date, which is what the
  statute asks about) and otherwise falls back to whether the company carries
  a VAT number — an approximation that errs downwards, into the 480 band.

Known limitations
~~~~~~~~~~~~~~~~~

- **The licencia vzory have no r560**, so there is no turnover row on the form
  to key the band on — that row arrived with the 2020 vzor for the § 15
  reduced-rate test. The band falls back to **class 6 revenue**, which is
  literally r560's own ``account_formula`` on the later form. That is a
  reading rather than a citation, and it is documented at the call site.
  Override r810 where the taxpayer's ročný obrat differs.

- **§ 46b ods. 3** (half the licencia where disabled employees are ≥ 20 % of
  the average headcount) and **ods. 7** (exemption) remain accountant
  overrides; the module models neither.

[19.0.1.3.0] — 2026-09-10
-------------------------

Added
~~~~~

- **``_cssk_derived_codes()`` for the SK tax spine.** The nineteen rows
  ``_compute_tax_spine`` writes — r200, r300, r301, r310, r400, r500, r510,
  r550, r600, r700, r800, r810, r820, r830, r900, r1050, r1080, r1100, r1101 —
  intersected with what each vzor actually defines, because r830 exists only
  on 2013–2015 and 2024+, and r810/r820 vanish across 2020–2022 with the
  daňová licencia.

  The set is declared once as ``_SPINE_ROWS`` and **``put()`` raises on a code
  that is not in it**, so the declaration cannot fall behind the spine. A
  raise rather than an assert: ``python -O`` strips asserts, and a guard that
  disappears under a flag is not a guard.

  This exists so a consumer does not copy the set. Until now it lived only
  inside ``_compute_tax_spine``, and the only way for a legacy-import bridge
  to have it was to duplicate it — which is the same defect
  ``l10n_sk_vat_return`` 19.0.1.11.0 had to repair in its own migration.

  A test asserts that the derived rows are all ``kind='manual'``: the fact that
  makes the hook necessary. If ``kind`` ever learns to express "derived", that
  test fails and the hook can be retired instead of lingering as a second way
  to ask one question.

[19.0.1.2.1] — 2026-09-10
-------------------------

Fixed
~~~~~

- **Two 1.2.0 labels in the 800/900 block were wrong.** r820 was labelled
  "Daňová licencia na úhradu" and r900 "Suma na účely určenia výšky
  preddavkov" on the licencia-era vzory. Both were extrapolated from the
  DPPOv24/v25 computation spine onto vzory it does not describe. Finančná
  správa SR's own *Usmernenie k započítaniu daňovej licencie v súlade s § 46b
  ods. 5 a § 52zk* (20. 12. 2018) prints those captions::

      r. 800 – Daň po úľavách a po zápočte dane
      r. 810 – Daňová licencia
      r. 820 – Kladný rozdiel medzi daňovou licenciou a daňou určený na zápočet
      r. 900 – Daňová licencia na úhradu

  **The form reused those row numbers between the two eras** — r820 is the
  kladný rozdiel under the licencia and r900 is the amount payable, where the
  minimálna daň vzory put the rozdiel on r830 and use r900 for the preddavky
  base. So an extrapolation that is safe everywhere else on this form is not
  safe here.

  r800/r810/r820/r830/r900 are now labelled **only where a source covers that
  vzor** — 2017–2019 from the usmernenie, 2024–2025 from the spine's DPPOv25
  citations — and are bare on 2013–2015 and 2020–2022. Net effect: 142
  labelled line definitions rather than 1.2.0's 155, three of which were
  wrong.

  1.2.0's migration cannot repair this: it only fills a name still equal to
  its code, by design, and a wrong label is not a bare one. All eleven vintage
  data files are ``noupdate="1"``, so a reload does not reach them either.
  A ``post-migration`` therefore **forces** the 800/900 block to match the data
  files, bare included, and touches nothing outside that block.

  The test changed with it: "labelled on one vzor, labelled on all" now holds
  only for rows outside the reused block, and a new test refuses an era's
  wording on the other era's vzor.

[19.0.1.2.0] — 2026-09-10
-------------------------

Added
~~~~~

- **Labels on the load-bearing DPPO rows.** Every one of the 941 line
  definitions across the eleven vzory carried ``name`` equal to ``code``, so a
  mapping onto a DPPO row could be checked *structurally* and never
  *semantically* — a row that could not be corroborated from a second source
  was unreviewable by anyone, including us.

  17 codes now carry the statutory row name (155 line definitions in all):
  r100, r200, r300, r301, r310, r400, r550, r560, r810, r820, r830, r900,
  r1040, r1050, r1080, r1100, r1101.

  **§ 46b is named for its era** — *daňová licencia* on the 2013–2019 vzory,
  *minimálna daň* from 2024. Same paragraph, different levy, and r810/r820/r830
  exist in exactly those years while being absent from 2020, 2021 and 2022:
  the abolition visible in the form itself.

  Every label is **sourced, not inferred** — from the computation spine and its
  comments in ``models/cssk_income_tax.py`` (which cite the DPPOv24/v25 eForm
  routines and the DPPOv25 poučenie by row), from ``provision_line_code``'s
  help, and from this changelog for r100. The remaining rows stay unlabelled on
  purpose: there is no source for their names here, and an invented statutory
  row name reads as authoritative, which is worse than a blank.

  The test is the invariant — a label on one vzor is a label on all of them, so
  a new vintage generated from its XSD (which arrives with ``name`` equal to
  ``code`` on every row) fails rather than quietly losing what the others have.

  A ``post-migration`` carries the labels to existing databases, reading them
  out of the data files rather than repeating them. Needed: the 2025 file is
  ``noupdate="1"``, and on the validation DB the data reload covered 121 of the
  155 — the migration supplied the other 34.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The nine pre-2024 DPPO vzory (19.0.1.1.0) are owed to 18.0**, together
  with the switch of 2025 to ``dppo2025_v2.xsd``. The generators
  (``tools/gen_dppo_template.py``, ``tools/gen_dppo_version.py``) read only the
  official XSDs, so the same nine templates and version records regenerate on
  18.0 unchanged; ``values_int`` in the render context goes with them
  (l10n_cssk_income_tax_base). Carry the empty ``rate_bands`` for 2015-2019
  and the reason with it — do not fill them on 18.0 either.

[19.0.1.1.0] — 2026-09-09
-------------------------

Added
~~~~~

- **The nine DPPO vzory before 2024**, so a period earlier than 2024 resolves
  to a version at all. It previously resolved to none — not a wrong figure but
  NO figure — which matters most for a dodatočné priznanie, the case where an
  old period comes back.

  ::

      dppo2013.xsd   2013        dppo2019.xsd   2019
      dppo2014.xsd   2014        dppo2020.xsd   2020
      dppo2015.xsd   2015-2016   dppo2021.xsd   2021
      dppo2017.xsd   2017        dppo2022.xsd   2022-2023
      dppo2018.xsd   2018

  **2016 and 2023 have no vzor of their own** and are filed on the preceding
  one — confirmed by the 2015 and 2022 poučenia, each of which ships separate
  instructions for both years in one package. The eleven records now tile
  every year from 2013 with no gap and no overlap.

- Templates and version records are GENERATED from each vzor's own schema
  (``tools/gen_dppo_template.py``, ``tools/gen_dppo_version.py``). Element
  order, nesting, the row set and each field's type come from the XSD, and an
  export test validates the result against the same file. The row NUMBERING is
  stable across DPPO vintages — r100, r400 and r500 say the same thing in the
  2013 and 2022 poučenia — so the four computed rows carry forward unchanged
  and the rest are manual, as they are on the current form.

- ``values_int`` in the render context. Not every row is money: the older
  vzory carry counts and years typed as an integer union, and ``"0.00"`` is
  not a valid value of one.

Changed
~~~~~~~

- **2025 now files against ``dppo2025_v2.xsd``.** FS SR published a revision
  under a NEW NAME beside an unchanged ``dppo2025.xsd``: v2 adds a repeatable
  ``dalsiaTransakcia`` and is otherwise the same file. A digest check on the
  pinned name could never have found it, so the refresh procedure now probes
  for a ``_v2`` suffix too. Being a superset, v2 accepts every document the
  original did. A migration moves an existing database.

Rate bands
~~~~~~~~~~

- **The § 15 písm. b) rate is now on every vintage that has a rate row**:
  22 % for 2015-2016, 21 % from 1. 1. 2017 and unchanged through 2019, after
  which the 15 % reduced band arrives on 1. 1. 2020. 2013 and 2014 need none —
  those vzory have no rate row at all.

  For 2020 onwards the figure comes from the vzor's OWN poučenie, which states
  it at riadok 550. For 2015-2019 the vzor does not state it, and that is
  deliberate on FS SR's part: r550 "Sadzba dane (v %)" is an ENTRY field and
  the poučenie says only "sadzba dane podľa § 15 písm. b) prvého bodu zákona",
  because a hospodársky rok can straddle a rate change and no single rate is
  right for a vzor — only for a period. Those four figures are therefore
  sourced separately and the source is named in
  ``tools/gen_dppo_version.py``; it was cross-checked on 2020, the year where
  it overlaps the official poučenie, and agrees word for word.

  A trade publication is not the law. These are good enough to compute and
  compare with; have an accountant confirm the rate for the year before a
  period from it is FILED.

Superseded limitation
~~~~~~~~~~~~~~~~~~~~~

- **``rate_bands`` was deliberately empty for 2015-2019.** Those poučenia say
  only "sadzba dane podľa § 15 písm. b)" — the rate was flat and the taxpayer
  entered it — so nothing written down states it. The module already refuses
  to compute a tax spine without bands, naming the version and saying what to
  fill, and that is the right answer: a rate recited from memory computes
  somebody's tax silently and wrongly. Fill it from § 15 for the year before
  computing such a period. 2013 and 2014 need nothing: those vzory have no
  rate row at all. 2020-2022 are filled from their own poučenia, which state
  the bands at riadok 550.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
