=========
Changelog
=========

All notable changes to **l10n_sk_dppo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
