=========
Changelog
=========

All notable changes to **l10n_cssk_kv_kh_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.2.2.0] — 2026-09-28
-------------------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- *Original document number* and the drill-down audit columns
  (19.0.2.2.0, 2026-09-28).

Added
~~~~~

- **Original document number** (``cssk_control_original_ref``) on credit
  notes and on entries marked as a correction, for a credit note created by
  hand because it could not be raised from the invoice — it has no link to
  follow. Shown on *Other Info* for Czech and Slovak companies when there is
  no linked original. ``_cssk_control_original()`` returns the linked
  original: a reversal's ``reversed_entry_id`` or a debit note's
  ``debit_origin_id``.
- **Base, rate, VAT and VAT deducted** in the drill-down behind every control
  statement row (the *Documents* button). VAT and VAT deducted differ exactly
  where a deduction is partial by its tax repartition — fuel at 50 %, one leg
  on the VAT account and one onto the expense — which is what an accountant
  checks a B.3.1 total against. Display only; nothing filed changes.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.2.1.5 (2026-09-21), not yet on 18.0.** ``_cssk_taxes`` exigibility
  filter, ``account.move._cssk_vat_document`` and
  ``_cssk_recompute_cash_basis_section_codes`` (commit 02eda35). Needed by the
  SK and CZ resolvers of the same change.

[19.0.2.1.5] — 2026-09-21
-------------------------

Fixed
~~~~~

- **Taxes "Based on Payment" are reported when due.** ``_cssk_taxes`` drops a
  tax that is not yet exigible — the same rule as Odoo's
  ``_get_tax_exigible_domain`` — so an unpaid cash-basis document no longer
  receives a section. ``account.move._cssk_vat_document`` answers for a
  cash-basis entry with the document it settles (direction, partner, VAT),
  and ``_cssk_recompute_cash_basis_section_codes`` lets a country module's
  migration re-resolve just those lines.

[19.0.2.1.4] — 2026-09-16
-------------------------

Fixed
~~~~~

- Version bump only. 775995c changed the module's behaviour without moving its
  version, and downstream deployments track versions, so a module that changed
  behaviour under an unchanged version is its own defect.

  ⚠️ IT DOES NOT CARRY THE FIX, and the first version of this entry said it did.
  A field's ``context`` is never persisted: it is not among the parameters
  ``_reflect_field_params`` writes to ``ir.model.fields``
  (``odoo/addons/base/models/ir_model.py`` — field_description, help, ttype,
  relation, index, store, related, readonly, required, translate and the rest;
  no ``context``), and ``ir.model.fields`` has no such column. It is a plain
  Python attribute read off the class every time the registry is built.

  So **a pull and a restart** delivered 775995c to every database on that code,
  upgraded or not, with no ``-u`` and no version change. Boxes on the previous
  version were never at risk once the code was there. Said explicitly because
  the opposite reading costs somebody an ``-u`` across every database to fix
  something a restart had already fixed.

[19.0.2.1.3] — 2026-09-14
-------------------------

Fixed
~~~~~

- **Archiving a superseded vzor would have made old periods unenterable.** The
  ``version_id`` dropdown filtered archived records out, so a historical filing
  could not be created or re-pointed once its vintage was tidied away. The
  field now carries ``context={'active_test': False}``. The domain already
  scopes by period — a 2026 filing never sees the 2014 vzor regardless — so
  archiving stays a presentation decision rather than one that removes
  capability.

  ⚠️ As first written this did NOT work: the context was given as a STRING,
  ``context="{'active_test': False}"``. That is view-XML syntax; a field's
  ``context`` is a dict (``odoo/orm/fields_relational.py:38``,
  ``context: ContextType = {}``), and the string was passed through raw and
  ignored, so archived vintages stayed invisible in the dropdown. Corrected in
  775995c. This entry described the broken form as if it worked — the text
  above is repaired rather than left standing.

[19.0.2.1.2] — 2026-09-13
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

[19.0.2.1.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- ``_cssk_form_label`` was a bare Python string, so it was in no ``.pot`` at all
  — untranslatable in every language rather than merely untranslated. It is now
  a lazy translation (``_lt``), rendered in the reader's language, and the term
  is in the catalogue with its Slovak and Czech.

[19.0.2.1.0] — 2026-09-13
-------------------------

Added
~~~~~

- The statutory footprint now names the FILING each row belongs to, not just
  the form and the line code, so a reader can go and look at it. This module
  declares ``res_model`` in its footprint entries; ``l10n_cssk_core`` resolves
  it against the period. The key is optional in the contract — a contributor
  that omits it produces a row with a blank filing and nothing else changes.

[19.0.2.0.3] — 2026-09-13
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

[19.0.2.0.2] — 2026-09-13
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

[19.0.2.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The 19.0.2.0.0 collapse ran in the wrong module and did
  nothing.** It lived in this module's post-migration, but the
  surviving records are declared by a COUNTRY module's data file,
  and a country module depends on this one and so loads after it.
  The pairing query was correct and matched nothing, because the
  rows it looked for did not exist yet. Measured on a 134-filing
  agenda: 15 type records where there had been 12, every filing
  still on an orphan, upgrade exit code 0.

  The collapse now runs from each country module's PRE-migration
  — ``l10n_sk_kv_dph`` and ``l10n_cz_kh`` — where the rows it
  needs already exist. It picks a survivor from them, moves the
  other rows' filings onto it and gives it the xmlid the data
  file is about to declare, so the load UPDATES it instead of
  inserting a fourth copy.

- **Each country migration now asserts its own outcome** and
  raises if it is not met: no code declared twice for the
  country, no filing on a type without an xmlid. The reason the
  broken version reached a commit is that a no-op and a success
  are indistinguishable unless something is counted afterwards.

- ``_cssk_collapse_to_one_per_code`` prefers a row that already
  holds the target xmlid over the oldest row, which makes it
  idempotent and safe on a database that took the broken version.

- **The collapse crashed on its second code**, and the first four tests for it
  could not have caught that: every one used a single code, so none reached a
  second loop iteration. The helper held one recordset across the loop and
  deleted rows from it, then filtered it again — ``MissingError`` on whichever
  code sorted second, every time. It now groups to plain ids before anything is
  deleted and re-browses per code; a recordset held across a delete is stale by
  definition, ids are not. A fifth test collapses three codes at once, which is
  the shape the real migration runs.

[19.0.2.0.0] — 2026-09-12
-------------------------

Changed
~~~~~~~

- **Submission types are scoped by COUNTRY, not by form version.**
  ``cssk.control.statement.type`` loses ``version_id`` and gains
  ``country_id``; ``cssk.control.statement.version.statement_type_ids`` is
  gone, and the statement's domain is now ``[('country_id', '=', country_id)]``.

  The axis was wrong and the data said so: the Slovak three — riadny /
  opravný / dodatočný, R / O / D — were declared identically on all four
  vzory, 2014 through 2025. Twelve records expressing three facts, none of
  which changed in eleven years. Czechia declares a different set (B / O / E),
  which is what shows the discriminator is the form family.

  The user-visible cost, and how it was found: grouping a filing list by "Typ
  výkazu" yields one group per type RECORD, so every label repeated once per
  vzor in use — Riadny three times and Dodatočný three times on a 134-filing
  agenda. Correct data reading as a duplication bug, and one row worse with
  every new vzor.

  It is a simplification rather than a rewrite: the statement only ever
  *domained* its type on the version and never derived the version through it,
  and ``_is_dodatocne`` plus all four report templates read ``fa_xml_value``
  rather than the record's identity.

- The "Submission Types" page on the version form is replaced by a list of
  their own under CZ/SK Localization. Editing them from one version would
  have been editing every version's.

Notes
~~~~~

- **The two countries were declared in different shapes, and the migration
  turns on it.** The Slovak twelve were ``(0, 0, {...})`` payloads on a
  one2many, so they carry **no xmlid**; the Czech three always were standalone
  records that do. Presence of an ``ir_model_data`` row is therefore what
  separates "superseded" from "surviving".
- Nothing is deleted unless a survivor with the same country and code exists to
  take its filings. A type somebody added by hand has no xmlid either, and is
  left in place and logged rather than removed — deleting a record whose
  filings have nowhere to go would take the filings with it.
- ``country_id`` is filled in **pre**-migration, before the schema update adds
  its NOT NULL. Odoo adds that constraint only if no existing row violates it
  and silently declines otherwise, which would have left the column nullable
  for good.
- If a future vzor ever does add a type or change an XML value, that is the
  moment to version them — not before.
- **A ``UNIQUE (country_id, code)`` constraint was considered and deliberately
  NOT added**, though it is the obvious structural guard and was raised in
  review. It cannot be applied in this version: Odoo runs the schema update
  BEFORE any post-migration, so the constraint would be created while the
  twelve duplicate rows still exist and the upgrade would fail. Splitting it
  across two version bumps does not help — the schema is synced once per
  upgrade run, whatever the intervening migration steps. The invariant is
  held by a test (``test_no_country_declares_the_same_code_twice``) until a
  release in which every install is known to be collapsed, which is when the
  constraint becomes addable.

[19.0.1.8.0] — 2026-09-12
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

[19.0.1.7.1] — 2026-09-06
-------------------------

Fixed
~~~~~

- **``KV_NO_TAX`` never saw a summary section.** ``check_kontroly`` skipped any
  row without a ``tax_rate`` field, which is every aggregated section (SK
  B.3.1, CZ A.5/B.3). A below-threshold aggregate could therefore be filed with
  ``total_tax_base > 0`` and ``total_tax_amount == 0`` — the undescribable
  taxable supply the check exists to block, in a schema-valid document that
  reported green. Summary rows are now checked on their totals; the message
  names the section, since an aggregate has no document to name.

Changed
~~~~~~~

- Test fixture extracted to a mixin. ``TestSubmissionOpensOnSubmit`` inherited
  ``TestKvOverrideSurvival`` to reuse its ``setUpClass``, which re-collected the
  parent's two tests under the child's name and — worse — inherited its
  ``SkipTest``, so three submission tests that need no concrete section were
  silently skipped on every non-SK install.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.7.0] — 2026-08-20
-------------------------

Fixed
~~~~~

- A line carrying the return tags without the tax reported **zero tax in every
  historical period**, in every company. Resolving a tag to a tax ignored the
  date, so introducing the 23 % rate in 2025 gave each standard-rate tag a
  second candidate and the resulting disagreement refused to compute — for a
  2016 supply as much as a 2025 one, and retroactively. Candidates are now
  filtered to the rates in force on the document's tax point. The filter may
  only remove ambiguity: where it matches nothing the unfiltered set is kept,
  so no line that used to compute stops computing.

Added
~~~~~

- ``account.move.line.cssk_control_rate_declared`` — the VAT rate the source
  document states, for a tags-only line. Some statutory lines never named a
  rate: the CZ/SK reverse-charge band was one line for every rate until the
  vzor of 1. 7. 2025, so its tag cannot say which applied and no date can
  separate rates that were in force at once. Where the producer knows, it says
  so. Covered by a fixture taken from a real document rather than invented
  (a 2025 credit note on tag 24, five candidate rates, base -31 353.00 at
  23 %), because corrections are the ordinary case in that section and a
  negative base must not be a special one. It **selects** among the taxes the
  tag already reaches and never
  computes: a rate matching none of them is refused, not applied. Nor does it
  override the calendar — a declared rate that was not in force when the
  document was taxed is a contradiction, not a tie broken, and refuses. A line
  carrying a real tax ignores it.

[19.0.1.3.0] — 2026-08-14
-------------------------

Fixed
~~~~~

- Section rows selected their period by accounting date rather than by tax
  point, so a control statement could disagree with the VAT return it
  reconciles against. Both detail and summary row selection now delegate to
  ``_cssk_period_move_ids()``.

[19.0.1.2.3] — 2026-07-04
-------------------------

Added
~~~~~

- Manual section overrides now survive ``action_compute_lines``: section
  assignments are snapshotted and re-applied on recompute so accountant edits are
  not clobbered.

Changed
~~~~~~~

- Statement export consolidated onto the shared ``cssk.statutory.submission.mixin``
  pipeline (draft gate → preflight → kontroly → render → XSD validate → attach).
- Partner VAT canonicalised through the shared ``normalize_vat()`` helper from
  ``l10n_cssk_core``.

[2026-07-02] — Wave 2 (P1 robustness)
-------------------------------------

Added
~~~~~

- Filed-copy retention on submit and pre-export preflight
  (``_cssk_preflight_export``) before the KV/KH XML is rendered.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Changed
~~~~~~~

- Statement values rounded with ``statutory_round()`` (HALF-UP).

Fixed
~~~~~

- Multi-company leakage: ``ir.rule`` ``[('company_id','in',company_ids)]`` on the
  statement model.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral framework for the Slovak **Kontrolný výkaz DPH** and Czech
  **Kontrolní hlášení**; country layers plug in their concrete section sets,
  thresholds and schemas.
- ``cssk.control.statement.version`` (versioned template + section registry +
  submission types + threshold) and ``cssk.control.statement`` (mail.thread;
  draft → preview → exported → submitted) with ``action_compute_lines`` and
  ``action_export_xml`` (QWeb render + ``lxml`` XSD validation).
- Three row mixins (detail / summary / reconciliation) for concrete section
  models; ``account.move.line.cssk_control_section_code`` computed by a
  country-overridable resolver (reverse-charge first) with multi-VAT override;
  ``account.tax`` and ``account.journal`` default-section fields.
- CE-clean (Odoo core only — no ``account_reports``). Full cs_CZ + sk_SK
  translations.
