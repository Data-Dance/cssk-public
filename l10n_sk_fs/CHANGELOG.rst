=========
Changelog
=========

All notable changes to **l10n_sk_fs** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.7.0] — 2026-10-05
-------------------------

Changed
~~~~~~~

- **One UZPODv14 generator.** The Úč POD statement's export and the
  ``l10n.sk.uzpod`` builder used to produce the same document independently.
  They agreed on the netto figures and on little else: the statement's export
  hardcoded SK NACE 00.00.0, malá / riadna and no poznámky and ran none of the
  kontrolné pravidlá, while the builder ignored the accountant's overrides.
  ``l10n.sk.uzpod`` now renders through the Úč POD statement of its period
  (creating and computing one when there is none), so what is filed is what
  was reviewed; its header choices (size class, druh, poznámky) are passed
  over the statement's own.

Added
~~~~~

- The statement carries the UZPODv14 header choices itself: *Veľkostná
  trieda*, *Druh závierky*, *Poznámky priložené*. The header takes SK NACE
  from the partner and the trade register from the company, and
  ``datZostavenia`` is the export day as ``dd.mm.yyyy``, the format the other
  Finančná správa forms of this repository use.
- The statement's **Export XML** runs the UZPODv14 kontrolné pravidlá
  (bilančná rovnosť, netto = brutto − korekcia, medzisúčty; unmapped accounts
  as a warning) and refuses a document that fails them.
- Amounts are filed in whole euros, each cell rounded on its own.

[19.0.1.6.0] — 2026-10-05
-------------------------

Fixed
~~~~~

- **v01 (Čistý obrat) showed 0 on screen while the filed XML read it off
  the ledger.** It was transcribed as a ``manual`` row, and
  ``tools/gen_uzpod_v14_version.py`` skipped every non-``accounts`` row, so
  it never got the reference formula (``-601,-602,-604,-606,-607``) — the
  same defect 19.0.1.5.0 fixed by hand for s113. The generator now promotes
  a manual row whose filed counterpart reads the ledger; a migration writes
  v01 on existing databases (the data file is ``noupdate``), leaving it
  alone if somebody has since given it a formula. A new test refuses a
  manual row that the filed export computes.

[19.0.1.5.0] — 2026-10-03
-------------------------

Fixed
~~~~~

These change filed figures. Each one moves a balance that was missing from,
doubled on, or misplaced in the Súvaha onto the row the tlačivo (UZPODv14,
MF SR č. 18009/2014) names for it.

- **34 balance-sheet accounts of the l10n_sk chart reached no row**, among them
  325000 Iné záväzky, 461000 bank loans, 471000/471200, 473000/473100 issued
  bonds, 474000 leasing, 372000, 377000, 371000/375000, 354000/358000, 351000,
  313000, 111000, 055000, 068000 and the synthetic allowances 091000, 092000,
  095000 and 096000. All now map to rows.
- **16 codes the chart does not have** were replaced with the ones it does
  (091120 → 091200 and so on, 0391120 → 391120, 391314 → 391341, 322300/322500
  → 322100/322200, 361300 → 361200, 471300 → 471200, 475400 → 475300), or
  dropped (078000, 323100, 336200).
- **Doubled balances:** 221100 (blocked accounts > 1 year) was on r030 and r073;
  475000 on r111 and r126; 316100 on r107 and r127.
- **Two-sided accounts are gated in the filed export.** 316, 336, 373, 398 and
  481 go to the asset side when the balance is a debit and to the liability side
  when it is a credit, as the on-screen statement already did. Before this, a
  deferred tax asset was filed on r052 and, negated, on r117.
- **Korekcia sign:** 391336 (r062) and 391700 (r051) raised the netto by the
  allowance instead of reducing it.
- **Totals are roll-ups of their rows** (``_SUM`` in ``uzpod14_rows.py``) and no
  longer carry account lists of their own. Those lists had drifted: 098000 and
  481000 were missing from the totals, and 255100/473100 appeared only in them.
- r113 Vydané dlhopisy is computed (473 minus own bonds 255100) on screen as
  well, instead of being a manual row.

Needs an accountant's confirmation: 066000, 091000, 092000, 095000, 096000,
461000 and 473000 are synthetic accounts the chart does not split by row, so
each one was assigned to the most general matching row. Also 391600 (r058
korekcia), 391730 (r050 korekcia) and 395000/431000 (not reported).

[19.0.1.4.0] — 2026-09-29
-------------------------

Fixed
~~~~~

- **Úč POD** ``skNace`` read ``l10n_sk_nace_code``, a field nothing defined, so every
  statement was filed with SK NACE 00.00.0. It now reads the company's NACE code
  (``partner_nace``).
- The statement template no longer fails without ``l10n_sk_base``
  (``l10n_sk_dic``).

[19.0.1.3.5] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the notes (poznámky) but not their depreciation lines and hit
  *not allowed to access*. On Community, ``account.group_account_manager``
  does not imply ``account.group_account_user`` (and on Enterprise
  ``account_accountant`` only adds ``group_account_basic``), so a model
  granted to ``group_account_user`` alone is closed to an Administrator who
  lacks "Show Full Accounting Features". The notes already granted it; the
  lines did not. ``group_account_manager`` now has the same access as
  ``group_account_user`` on ``l10n.sk.poznamky.odpis.line``. Takes effect on
  module update.

[19.0.1.3.4] — 2026-09-15
-------------------------

Fixed
~~~~~

- **An upgrade from 19.0.1.0.0 that could not finish.** The 19.0.1.2.0
  caption migration compared ``name`` with text, but on a database coming
  from 19.0.1.0.0 that column is still ``jsonb`` when the migration runs:
  ``name`` was translatable then, and Odoo 19 keeps a field that the
  database records as translated patched as translated for the whole load.
  The upgrade stopped with
  ``operator does not exist: jsonb = text`` and left every module after
  ``l10n_cssk_fs_base`` un-upgraded. The migration now reads and writes the
  ``en_US`` value when the column is ``jsonb``.

[19.0.1.3.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The mixin's field labels reached the mixin and nothing else.** Odoo keeps
  one ``ir.model.fields`` row per CONCRETE model, so the translation of
  ``legacy`` — addressed to ``cssk.statutory.submission.mixin`` — landed there
  and on none of the six models that inherit it. A live instance showed a
  Slovak statusbar and an English ``Historical filing`` ribbon on the same
  record.
- ``--source`` could not see this: the string WAS in the template, addressed to
  one row out of seven. All seven mixin fields are now referenced per concrete
  model, with the Slovak and Czech already written for the mixin.

[19.0.1.3.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **"Historical filing" was untranslatable, and it is the most visible label on
  a migrated filing.** It arrived with the ``legacy`` state and the templates
  were never regenerated, so the string existed in the source, in no ``.pot``
  and in no ``.po`` anywhere — 217 materialised filings on a live instance
  showed an English status on an otherwise fully Slovak form.
- It was not alone. Regenerating and diffing found **209 terms** across the
  statutory modules that exist in source and had never entered a template. A
  string missing from the TEMPLATE is invisible to coverage, to distinctness
  and to a fuzzy count alike, because all three compare a catalogue against its
  template — which is why the modules read as healthy.
- Merged additively rather than by regeneration: the committed templates carry
  terms a source-only export cannot see (menu and action names, view arch from
  data records), and replacing them destroyed 186 translations once already.
- Slovak and Czech filled for the new terms. ``Historical filing`` is
  **Historické podanie** / **Historické podání** — ``podanie`` is the statutory
  word for a filing made to the authority, and the sibling states already read
  Podané / Podáno.

[19.0.1.3.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.3.0] — 2026-09-12
-------------------------

Added
~~~~~

- ``("legacy", "Historical filing")`` on ``state``, and the list badge
  distinguishes it. Set automatically with the ``legacy`` flag — see
  ``l10n_cssk_core`` 19.0.1.9.0 for the reasoning and for why ``submitted``
  was the wrong value to reuse.

Fixed
~~~~~

- Buttons gated on ``state`` were written when ``legacy`` records sat in
  ``draft``, so the new value would have made some of them appear on a
  historical filing — Export XML, and the reconciliation / mapping indicators
  that count against a computation never run for one. Their conditions now
  name ``legacy`` alongside ``draft``.
- A post-migration moves existing historical filings onto the new state. Raw
  SQL, and not out of laziness: a write carrying ``state`` on a record that is
  already ``legacy`` is refused by ``_cssk_check_not_legacy``, which is exactly
  the guarantee the state exists to give, so the migration goes under it rather
  than around it.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The UZPODv14 rework (19.0.1.1.0) and the corrected row captions
  (19.0.1.2.0) are owed to 18.0.** The one that matters is the mapping: the
  on-screen statement was a second transcription of the form and disagreed
  with the filed XML on 47 of 114 súvaha leaf rows, hidden because A.VIII was
  a plug. 18.0 still carries that. Port the generator, the corrected captions,
  the two-sided account gating and the unmapped-account diagnostic
  (l10n_cssk_fs_base) together — the gating and the diagnostic are what stop
  the same class of error coming back.

[19.0.1.2.0] — 2026-09-09
-------------------------

Fixed
~~~~~

- **The row captions.** They were transcribed from a plain ``pdftotext`` dump
  of the tlačivo, where a two-line caption bleeds into the row below it:
  "Poskytnuté" sat on r009 and r010 read "7. preddavky na dlhodobý nehmotný
  majetok". About a third of the form was shifted like that, and a shifted
  caption is worse than a missing one — it names the row above's accounts
  while reading perfectly ordinarily.

  They are now read off the form's OWN column layout (označenie / text / číslo
  riadku), which is what ties a caption printed above a row number to that
  row. ``tools/parse_uzpod14_labels.py`` produces
  ``data/uzpod14_row_labels.tsv``; the generator writes them into the version
  record and a test asserts all 206 still match.

  Figures are untouched. A migration corrects the captions on an existing
  database — the data file cannot, because re-creating a ``noupdate="1"``
  record's one2many payload only happens on a CREATE.

[19.0.1.1.0] — 2026-09-09
-------------------------

Changed
~~~~~~~

- **One UZPODv14 mapping, not two.** The on-screen Súvaha/VZS statement was a
  second, hand-transcribed mapping of the same form the filed XML already had
  in ``models/uzpod14_rows.py``, and the two disagreed on 47 of 114 súvaha
  leaf rows — rows r043/r044/r045 each claimed the whole of 311-315, tripling
  trade receivables. The statement's leaf rows are now generated from the
  filed mapping by ``tools/gen_uzpod_v14_version.py``, and
  ``tests/test_uzpod_one_mapping.py`` keeps them there.
- **A.VIII is no longer a plug.** It was ``SPOLU MAJETOK`` minus the other
  passive rows, so it silently absorbed every mapping error on that side and
  the sheet balanced regardless — which is why the 47 divergent rows went
  unnoticed. It now reads the movement of triedy 5/6, so it equals VZS r61
  even on a ledger whose prior year is not yet closed to účet 431.
- **The Súvaha and the VZS are one document again.** They were filed as two,
  with roots ``UZSUV``/``UZVZS`` against two schemas we wrote ourselves; FS SR
  publishes neither root nor schema, and ``uzpod-2014.xsd`` was sitting in the
  module unreferenced. One version record now covers both blocks, reading the
  cumulative balance for the súvaha and the period movement for the výkaz, and
  validates against the official schema. The two invented XSDs are deleted and
  the stand-in version records are retired on upgrade.

Added
~~~~~

- ``data/SCHEMA_VERSION`` pinning ``uzpod-2014.xsd`` by size and digest, with
  the refresh procedure and a test that no bundled schema sits unpinned.
- **Accounts that reach no row are now reported** on the statement
  (``unmapped_count`` / "Accounts on no row"). With the rows naming specific
  chart codes, a company whose chart puts a balance somewhere the mapping does
  not name would otherwise lose that money from the form silently — the sheet
  still foots and still balances.
- Two-sided accounts (341-347, 316100, 373100, 481000) are gated on the sign
  of each account's own balance, so a deferred tax liability no longer shows
  as a liability AND a negative asset of the same size.

Fixed
~~~~~

- The residual-token mechanism read an ``X`` in a TAG name (``666&X_1``) as an
  account-code residual, which switched on a rule under which a six-digit
  token ending in 000 excludes its own account — ``013000`` matched nothing.

[19.0.1.0.5] — 2026-09-06
-------------------------

Fixed
~~~~~

- The two prehľady (peňažných tokov, zmien vlastného imania) could not be
  exported: Finančná správa publishes ``uzsuv``/``uzvzs`` for the Súvaha and
  the VZS and nothing for these, and the core mixin had been tightened to
  refuse an export it could not validate. Both versions now declare
  ``xml_schema_optional``, with a migration — they live in ``noupdate="1"``
  data. The Súvaha and VZS keep validating against their schemas.

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

- Poznámky (Úč PODV 3-01) generated as **PDF v1**: new ``l10n.sk.poznamky`` model + QWeb report, with depreciation figures auto-populated. No structured Poznámky XSD exists, so the PDF is the definitive artefact.
- Cash-flow and statement-of-changes-in-equity datasets alongside Súvaha + VZS.

Changed
~~~~~~~

- Evaluator performance (Wave 3): Súvaha compute uses ``_read_group`` balance helpers (~600 queries → 2); form-load reconcile reduced from N-per-line to ≤3 queries.
- Export pipeline consolidated into the shared ``cssk.statutory.submission.mixin``.

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

- Slovak Súvaha + Výkaz ziskov a strát (druhové členenie) on ``l10n_cssk_fs_base``, computed CE-clean (no ``account_reports``): full statutory line partition, so SPOLU MAJETOK = SPOLU VLASTNÉ IMANIE A ZÁVÄZKY and VH = výnosy − náklady; current-year result (A.V) computed from triedy 5/6.
- Official **UZPODv14** export (``l10n.sk.uzpod``): combined Súvaha Úč POD 1 (r001–r145, Brutto/Korekcia/Netto) + Výkaz ziskov a strát Úč POD 2 (r01–r61), validated against ``data/uzpod-2014.xsd``.
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
