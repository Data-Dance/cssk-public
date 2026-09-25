=========
Changelog
=========

All notable changes to **l10n_cssk_core** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.13.1] — 2026-09-17
--------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the statutory footprint smart button on invoices and hit *not
  allowed to access*. On Community, ``account.group_account_manager`` does not
  imply ``account.group_account_user`` (and on Enterprise
  ``account_accountant`` only adds ``group_account_basic``), so a model
  granted to ``group_account_user`` alone is closed to an Administrator who
  lacks "Show Full Accounting Features". The filings it links to already
  granted it. ``group_account_manager`` now has the same access as
  ``group_account_user`` on the footprint wizard and its lines. The smart
  button is also now shown only to users who can read the filings, so an
  Invoicing-only user no longer sees a button that failed when clicked. Takes
  effect on module update.

[19.0.1.13.0] — 2026-09-17
--------------------------

Removed
~~~~~~~

- **The dependency on ``l10n_cssk_payment_symbols``.** It existed only
  because the VS/KS/SS fields lived in core until 19.0.1.3.0; nothing in
  core uses them. Installing core no longer installs the symbols module. A
  module that uses the symbols must declare ``l10n_cssk_payment_symbols``
  itself, as ``l10n_cz_invoice`` and ``l10n_sk_invoice`` do since
  19.0.1.0.2 / 19.0.1.0.3. Databases that already have the symbols module
  keep it.
- A database still on a core older than 19.0.1.3.0 has the symbol fields
  registered under core, so without the dependency this upgrade would drop
  their columns. A post-migration installs ``l10n_cssk_payment_symbols`` in
  the same run, which keeps them. If that module is not on the addons path
  while the columns hold data, the upgrade stops with an error instead.

[19.0.1.12.0] — 2026-09-15
--------------------------

Added
~~~~~

- **Taxable supply date in the invoice and bill lists.** 19.0 core shows
  ``taxable_supply_date`` (DUZP / dátum zdaniteľného plnenia) on the invoice
  form only, although it decides the VAT period in both countries. It is now
  an optional column, shown by default, in every customer invoice, credit
  note, vendor bill and refund list. The cell is blank where ``l10n_cz`` /
  ``l10n_sk`` do not enable the field. The search views gain a date filter
  and a *Group By* on it.

[19.0.1.11.4] — 2026-09-13
--------------------------

Fixed
~~~~~

- **A warning that fired on every database and said something untrue.** The
  check added in 19.0.1.11.3 — "rows on model(s) the registry does not know" —
  ran in core's own post-migration, where only core and its DEPENDENCIES are
  loaded. ``cssk.vat.return`` lives in ``l10n_cssk_vat_return_base``, which
  depends on core and therefore loads later, so from there the registry has
  never heard of it. It reported three perfectly installed models as unknown,
  on both tables, on every upgrade.

  Same family as the migrate-arity bug earlier in this work: correct code
  placed where it cannot observe the thing it asks about. Moved to an ``end``
  script, which runs at ``load_modules`` STEP 3.5 after every module in the
  graph is loaded — the earliest point at which the question can be asked
  honestly.

- **The stale ``recomputed`` basis label is cleared rather than left to a
  re-run.** 19.0.1.11.3 stopped WRITING it; the old English text stayed in the
  column until somebody re-ran that comparison, so a database nobody re-runs
  kept showing it for ever. That is the same stored-snapshot trap the form
  label was, so leaving it would have reintroduced in one column what had just
  been removed from another. Only the ``recomputed`` basis is touched; the
  others name specific records, are Slovak in source, and carry what the
  selection cannot.

Verified on a live customer-path upgrade: a database restored at 19.0.1.10.5
and taken straight to 19.0.1.11.3 ran 19.0.1.11.0's backfill against the FINAL
schema (7 comparisons, 77 rows, 0 orphaned) and dropped ``form_label`` without
touching it — which is what the removal of that column from 11.0's INSERT was
for.

[19.0.1.11.3] — 2026-09-13
--------------------------

Changed
~~~~~~~

- **The form's label is rendered per reader instead of stored per runner.**
  ``form_label`` held the name as text, written in the language of whoever ran
  the comparison — so a comparison run in English read English to everybody
  afterwards, and the only repair was to re-run it. Seven filings had to be
  re-run by hand on the demo box to turn one screen Slovak. On a migrated
  agenda that is hundreds, and any run by a cron or an English-locale colleague
  puts it back.

  The key was already in the next column. ``res_model`` is now a Selection
  whose labels come from each model's ``_cssk_form_label`` (an ``_lt``, so
  ``env._`` resolves it against that model's own module catalogue) and are
  rendered at read time. That keeps the field GROUPABLE, which a plain computed
  label would not have — the "Form" group-by needs a stored column, and losing
  it was the whole objection to computing the label.

  The selection is built from the registry, not a literal list, so a country
  module adding a submission model appears without editing core.

  ``form_label`` is dropped from both models and its column removed in
  ``19.0.1.11.3``. Nothing is backfilled because nothing is lost: it was
  derived from ``res_model`` on every write.

- The ``recomputed`` basis no longer stores a ``basis_label``. It restated the
  ``basis`` selection — which the screen already shows translated — in English,
  and being stored it was the other half of the same problem. The labels on the
  other bases name specific records ("DPH priznanie FA/2017/06", "účtovníctvo —
  účet 343") and are Slovak in source, so they carry something the selection
  cannot and stay.

- ``19.0.1.11.0``'s migration no longer names ``form_label``. A database
  upgrading from 19.0.1.10.5 straight to this version gets the new schema
  before that script runs, so the old INSERT would have failed on a column that
  no longer exists.

Reviewed by GPT-5.3-Codex. Two of its points were already covered — the drop is
guarded by an ``information_schema`` check so it IS idempotent, and the new
tests assert inclusion rather than a global selection list. It hedged on the
migration ordering, so that was verified in the source rather than argued:
``loading.py`` runs ``migrate_module(pre)`` → ``registry.init_models()`` →
``migrate_module(post)``, ONCE per module upgrade rather than once per version,
so every post-migration sees the final schema. Taken from it: a stored
``res_model`` whose module is uninstalled renders as the raw model name, which
is legitimate but invisible — the migration now logs those rather than leaving
a screen quietly showing ``cssk.vat.return`` where a name used to be.


[19.0.1.11.2] — 2026-09-13
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

[19.0.1.11.1] — 2026-09-13
--------------------------

Fixed
~~~~~

- **The comparison screen was entirely English, and the form label could not be
  Slovak in any language.** Two separate causes behind one symptom.

  ``cssk.filing.comparison`` shipped between i18n passes, so it had **zero**
  entries in the template — not a missing translation but a model that had never
  been exported: field labels, both selections, the form's headings and its
  prose. 48 terms are now in the catalogue and written in Slovak and Czech.

  ``_cssk_form_label`` was a bare Python string on six models — ``"VAT return"``,
  ``"control statement"`` and the rest — so it was in no ``.pot`` at all and was
  untranslatable rather than merely untranslated. It is now ``_lt`` (lazy, which
  is what lets a module-level constant be translated) and rendered with
  ``self.env._(...)`` at every use site, which also makes the five error messages
  that interpolate it translatable for the first time.

- Documented what remains, because it is not a bug but it does surprise: both
  ``form_label`` and ``basis_label`` are STORED, written in the language of
  whoever ran the comparison rather than rendered for the reader. Re-running the
  comparison rewrites them, so one run in Slovak makes them Slovak from then on.
  Making them per-reader means storing a key and rendering on read, which costs
  the ``group_form`` filter its groupable column; not done unasked.

[19.0.1.11.0] — 2026-09-13
--------------------------

Added
~~~~~

- **``cssk.filing.comparison`` — the rows grouped into the unit a reader
  actually reads.** ``cssk.filing.discrepancy`` is row-grained, and one Slovak
  DPH priznanie produced 608 of them. The list could not even be grouped by the
  filing they belonged to, because the filing is ``(res_model, res_id)`` — a
  PAIR — and Odoo cannot group by a pair. So the one grouping worth having was
  the one the screen could not express.

  The unit is the row's own uniqueness key minus the row:
  ``(res_model, res_id, basis)``. ``basis`` belongs in it because the same
  filing is compared against a recomputation of itself AND against účet 343,
  and those are two comparisons sharing a filing, not one comparison.

  The consolidated state is **computed and stored, never settable**: a summary
  somebody could type drifts from its rows the first time a row moves, and a
  drifted summary is worse than none because it is read and believed. It splits
  on the same two axes the row does — ``clean`` / ``open`` / ``in_progress`` /
  ``resolved`` — with the counts beside it.

  ``expected`` and ``info`` rows are deliberately NOT findings: the row model
  already states they are "findings of neither agreement nor error", so a
  comparison whose only non-agreeing rows are structural reads ``clean``.
  Counting them would flag every correct KV as needing review, which is the
  precise failure this screen exists to avoid.

  The one thing that is NOT derived is the **sign-off** — that a person looked
  at the whole comparison and accepted it. Nothing about the rows implies it,
  so it gets its own field, and the form says so where a green badge could
  otherwise be mistaken for somebody's approval.

- **The statutory footprint now names the filing**, so a row can be opened
  rather than only read. ``res_model`` (and optionally ``res_id``) joins the
  footprint contract as an OPTIONAL key: a contributor that omits it produces
  a row with a blank filing and nothing else changes, which is what keeps this
  from being a breaking change across six modules that have drifted before.

  The resolver **asks the filing** rather than deciding for it. Which period
  reports a document is not a date comparison — the basis differs between the
  output and the input side, a deduction may be exercised periods after the
  supply, and ``cssk_vat_deduction_date`` overrides the tax point on both.
  ``_cssk_period_move_ids`` is the one implementation of that rule; restating
  it here would have made this a second reader of it, which is exactly what
  cost this codebase a VAT-return footprint that reported no DPH row at all.
  The date window in ``_cssk_footprint_filings`` is a pre-filter deciding which
  filings are worth ASKING, and nothing more.

  A blank filing column is the honest normal case, not a failure: the footprint
  matches line DEFINITIONS precisely so a document can be asked what it feeds
  before any return for its period exists. The dialog says so.

Robustness (from a GPT-5.3-Codex review of the new code)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **``_cssk_comparison`` was a search-then-create race.** It is reached from a
  button a user can double-click and from a cron that can overlap a user; both
  transactions missed, both created, and the UNIQUE constraint killed one with
  an IntegrityError that aborted the whole comparison — losing the run, not
  merely duplicating a record. Now creates inside a savepoint (without which
  the failed INSERT poisons the cursor and even the re-read fails) and falls
  through to the update path on conflict.

- **The migration now refuses a NULL key instead of producing a puzzle.** All
  three key columns are ``required=True``, but this repo has already found
  eleven modules whose constraints Odoo never created and four required fields
  sitting on NULL rows — so "required" is not evidence. GROUP BY treats NULLs
  as one group while the linking join compares them with ``=``, which is false
  for NULL: such a row got a comparison created for it and then failed to link
  to it, surfacing as an orphan count with no hint of the cause. It is now
  detected up front and named, and rows disagreeing within a group are logged
  rather than silently coalesced by ``MIN()``.

- **The footprint's candidate window was anchored on the wrong date and was
  ten times wider than it needed to be.** Asking a filing whether it reports a
  document costs two or three searches over ``account.move`` and materialises
  every move id in the period, so the number of candidates is the cost. The
  window was ±62/+400 days around the tax point alone — generous precisely
  because the tax point is the wrong anchor for a late-claimed deduction. It
  now spans the three dates the period rule can actually key on (tax point,
  accounting date, ``cssk_vat_deduction_date``) with one period of slack, and
  refuses above 40 candidates rather than grinding — leaving the link blank
  rather than answering it from part of the set.

Not changed, and why: Copilot flagged ``tracking=True`` on a ``mail.thread``
model written by a machine process. The tracked fields are ``signed_off_uid``
and ``signed_off_date``, which only a person sets; everything the comparison
run writes — the counts, the state, ``last_run_date`` — is untracked, so no
message is generated per run.

Changed
~~~~~~~

- ``cssk.filing.discrepancy`` gains a required ``comparison_id``. The ten
  descriptive fields it duplicates from the parent are left in place rather
  than converted to ``related`` — every domain, search view and the
  ``_row_uniq`` constraint reads them directly, and converting them buys
  nothing on screen. Recorded as known duplication, not as an oversight.

- The "Filed vs computed" menu now opens the COMPARISON list, with the rows
  beneath it as "Rows to review". Opening on several hundred rows answers
  "what is wrong" while hiding "how much landed", and a migration is judged by
  the second.

Fixed before the version ever landed (found by a live upgrade)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **The migration was written ``migrate(env, version)`` and took the whole
  upgrade down.** Odoo checks the parameter NAMES, not the arity
  (``odoo/modules/migration.py`` accepts only ``cr``/``_cr`` + ``version``/
  ``_version``) and hands the function a CURSOR. The failure is total and
  happens before anything runs: the schema update had already tried to apply
  this version's NOT NULL, found the nulls the migration was meant to fill, and
  rolled the transaction back whole — module left at 19.0.1.10.5, the new table
  absent, nothing partial. 74 other migrations in this repo take
  ``(cr, version)``; this one was the only offender. ``post_init_hook`` is the
  hook that takes ``env`` in 19, which is where the confusion came from.

  The version number is deliberately NOT bumped: 19.0.1.11.0 never completed
  anywhere, so the migration directory must keep matching the version that will
  actually be applied.

- Documented, after a live run made the mistake worth writing down: only the
  ``ledger`` basis can produce ``expected`` / ``info`` rows. The mixin's own
  comparator (``basis='recomputed'``, the "Compare with computed" button) emits
  exactly ``ok``, ``only_filed``, ``only_computed``, ``differs`` and
  ``unmapped`` — there is no branch that yields the other two, which come from
  ``l10n_sk_datadance``'s ``_RECON_KIND``. So a ``recomputed`` comparison with
  ``finding_count == open_count`` and no structural rows is correct rather than
  a collapse that failed to fire. Twelve migrated PREMIER filings showed that
  exact uniformity and it read as a bug; it was the wrong basis to expect them
  on.

- Two pre-existing tests in ``TestHistoricTaxNaming`` created an
  ``account.tax`` with no ``tax_group_id``. That field is required with a
  precomputed default resolved through the company's chart, and the class is a
  plain ``TransactionCase`` with no chart loaded — so on a database where
  nothing else had left a group behind, the INSERT died with NotNullViolation.
  They passed wherever some other module happened to have created one. Not
  caused by this change; fixed here because it was blocking the run.

[19.0.1.10.5] — 2026-09-13
--------------------------

Fixed
~~~~~

- **The model's own name was never exported.** ``_description`` is what
  labels a record's type in breadcrumbs and the technical model list, and
  ``tools/i18n_export_offline.py`` emitted no ``model:ir.model,name:`` line
  at all — the entries already in the catalogues had come from an older
  DATABASE export. So every model added since had no entry and its name
  could not be translated. The exporter now emits it, and the missing
  entries are merged and filled.

[19.0.1.10.4] — 2026-09-13
--------------------------

Added
~~~~~

- Slovak and Czech for the two labels renamed in ``fcf4277``: ``Row name``
  (the column Radovan asked for by name) and ``Compared against (detail)``.
  The old ``Name`` could never have rendered Slovak whatever the catalogue
  said — it is core's own generic msgid, deliberately left untranslated
  because what a bare "Name" names varies by context.

[19.0.1.10.3] — 2026-09-13
--------------------------

Fixed
~~~~~

- Two field labels that came up **English in the middle of an otherwise Slovak
  screen**, caught by rendering the view in ``sk_SK`` rather than by reading the
  catalogue. ``row_label`` was ``Name`` — already in the templates from core's
  own generic use and sitting there untranslated, because what a bare "Name"
  names varies by context. It is ``Row name`` now: a label specific enough to
  translate is a label specific enough to export.

- ``basis_label`` was ``Right-hand side``, which said nothing about being the
  same axis as ``basis`` (``Compared against``). The two read as unrelated
  fields side by side. Now ``Compared against (detail)``.

[19.0.1.10.2] — 2026-09-13
--------------------------

Added
~~~~~

- Slovak and Czech for the filed-vs-computed comparison screen —
  the kind and state values, the ``basis`` discriminator and its
  label, the search filters and the three explanatory alerts on the
  form. The screen is what a migrated filing is read through, and
  the accountant reading it works in Slovak.

[19.0.1.10.1] — 2026-09-13
--------------------------

Fixed
~~~~~

- **A ROW-BASED form could not be compared at all**: ``TypeError: bad operand
  type for abs(): 'tuple'``. A coded form compares floats, but a control
  statement and an EC sales list compare a tuple per row — (base, tax, rate,
  deduction, …) — and ``_cssk_drop_empty_rows`` and
  ``_cssk_pair_classifications`` both asked ``abs()`` of it. Comparing a KV
  with a ledger behind it died outright; found by running it against KV/KH
  2017-03 on a live agenda, not by reading.

- Emptiness now reads the **whole** tuple. Testing only the leading figure
  would drop a row whose base is zero and whose daň is not — on a KV that is a
  § 69 reverse charge, which is exactly the row worth seeing.

[19.0.1.10.0] — 2026-09-13
--------------------------

Changed
~~~~~~~

- **The comparison is a screen, not a chatter post.**
  ``action_cssk_compare_to_computed`` no longer posts a copy of its result to
  the record. It is re-run whenever anything changes, and posting it does not
  make a timestamped audit trail — it makes a thread nobody can read, and it
  buries the record it claims to be. The rows are the record: queryable,
  answerable, and carrying what the accountant said about each one. The action
  now always opens them.

- **The rows that AGREE are recorded too**, which is what turns the screen from
  a defect list into a comparison. A migration is judged by how much of it
  landed, and a screen carrying only the failures cannot answer that: on the
  agenda this was built for, 583 of 608 rows agree and there was no way to see
  it. Agreeing rows are created in state ``agrees``, so the worklist filter
  (state ``open`` / ``asked``) never fills with them — present when somebody
  opens the comparison, absent when somebody is working through findings.

Added
~~~~~

- ``cssk.filing.discrepancy.basis`` / ``basis_label`` — **what the right-hand
  column IS**, and it is not decoration. The mixin's comparator recomputes the
  filing from the ledger; the Slovak reconciliations put the same filing beside
  the ledger itself (účet 343) or beside a different filing for the same period
  (KV ↔ priznanie, VZS ↔ DPPO). Three different questions on one screen: a
  reader who cannot tell which one was asked reads correct figures as wrong.
  ``basis`` joins the uniqueness key for the same reason — two comparisons of
  one filing legitimately carry the same row code with different figures.

- ``cssk.filing.discrepancy.row_label`` — the row in words, where the source of
  the comparison has one. A coded form identifies its rows by code alone; a
  reconciliation says "Daň na výstupe (priznanie r17 ↔ účet 343 výstup)".

- ``kind`` gains ``ok``, ``expected`` and ``info``, and ``state`` gains
  ``agrees``. ``expected`` and ``info`` are findings of neither agreement nor
  error — the KV is a proper subset of the priznanie, and the VAT base
  legitimately diverges from účtová trieda 60. Painting either as a difference
  sends an accountant chasing a number that is doing what it should.

- ``_cssk_upsert_comparison_rows`` on the mixin: one entry point for any
  comparator to persist its rows, upserting on (filing, basis, row) and never
  overwriting an answer somebody has given.

- The list view is coloured **by kind**, not by state — green agrees, red
  differs, grey is structural. The first question a reader of a comparison asks
  is whether the row agrees; what somebody has decided about it is a second
  question and stays on the state badge.

[19.0.1.9.5] — 2026-09-13
-------------------------

Fixed
~~~~~

- **"(vocabulary not mapped)" fired on a filing whose every mapped row agreed
  to the cent.** ``_cssk_collapse_unmapped`` is handed only the non-ok rows, so
  the sole evidence it would accept that the two sides share a vocabulary was a
  row that DIFFERS — and a row that matches perfectly, the strongest proof
  available, had been filtered out one line earlier.

  Seen on a live migration: a DPH 2018-02 return with 19 rows agreeing exactly,
  0 differing and 23 rows we compute that the filing does not carry. The
  accountant was told the vocabulary was not mapped at all. On that agenda most
  periods have that shape, so the better the import, the more confidently the
  screen misreported it.

  The count of agreeing rows is now passed in and counts as overlap.

[19.0.1.9.4] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The reconcile toast told the user to read the record, and left the record
  unchanged on screen.** ``message_post`` wrote the comparison to the chatter,
  the action returned a bare ``display_notification``, and a notification does
  not reload the form — so the chatter still showed its pre-click state and the
  entry the toast referred to was not visible. A user who trusted the toast
  would conclude the warnings had never been written.
- The notification now carries
  ``"next": {"type": "ir.actions.client", "tag": "reload"}``, and the warning
  and danger variants are sticky: a toast that says "pozri záznam" must not
  dismiss itself before the record it points at has rendered.

[19.0.1.9.3] — 2026-09-13
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

[19.0.1.9.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Gave the technical computed field an explicit ``string=``. Without one Odoo
  derives a label from the field name and exports it — "L10N Sk Jcd Is Sk
  Company" and the like — which is not English in any useful sense and cannot
  be translated into anything better. The field is a view modifier behind
  ``invisible="1"``, so no user reads it; the point is that it stops putting a
  mangled msgid in the catalogue.

[19.0.1.9.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The chatter posted its own HTML as visible text.** ``message_post``
  ESCAPES a plain ``str`` and renders only a ``markupsafe.Markup`` —
  ``mail_thread.py`` says so on the parameter (``str|Markup body: … str
  content will be escaped``) and applies it at ``'body': escape(body)``. So a
  summary built by joining ``"<li>…"`` fragments arrived in the chatter as
  literal markup. Nothing failed: the post succeeded and the log was clean,
  which is why it survived to a user.

- Built as ``Markup(template) % args`` rather than by wrapping the finished
  string, and the difference is not cosmetic. ``%`` on a ``Markup`` escapes
  what it substitutes; wrapping the join renders it. The interpolated values
  here are not ours — a row code carries an invoice reference or a
  counterparty VAT, a warning detail carries a partner name — so the
  shorter fix would have turned an escaping bug into an injection one.

- Two sites: the filed-vs-computed summary and the "Marked **submitted**"
  note.

[19.0.1.9.0] — 2026-09-12
-------------------------

Added
~~~~~

- **A ``legacy`` state, and it is now inseparable from the ``legacy`` flag.**
  ``create`` and ``write`` on ``cssk.statutory.submission.mixin`` set
  ``state = 'legacy'`` whenever the flag is set, so no caller can produce the
  one combination that means nothing: a completed, years-old filing sitting in
  ``draft``. That combination was not hypothetical — the importer sets the flag
  and never touches the state, so the default won on every materialised
  record: 134 control statements, 81 VAT returns and 2 DPPO on one agenda, all
  reading "Draft" in a list. A ribbon on the form does not reach a list view.

  Joined in the localization rather than fixed in the importer on purpose: the
  importer lives in another repository, and a rule split across two
  repositories is a rule that drifts.

  The state is terminal and **off** the workflow rather than at the end of it.
  Nothing transitions into or out of it; the only thing that may be done to a
  historical filing is to compare it with what this system computes for the
  same period.

Notes
~~~~~

- **It deliberately does not reuse ``submitted``**, though that is what these
  filings are. ``unlink`` refuses a submitted record and points at
  ``action_reset_to_draft``, which changes ``state`` and is therefore refused
  in turn by ``_cssk_check_not_legacy`` — so every materialised filing would
  have been permanently undeletable, against an importer whose whole method is
  reload-and-remeasure. Same shape as the ``ondelete="restrict"`` incident that
  already cost manual row deletion under time pressure on two agendas. There is
  a regression test for deletion specifically.
- **"Frozen" means it cannot be advanced, recomputed, exported or submitted —
  not that it cannot be removed.** A re-import deletes and re-materialises, and
  that must keep working.
- An amendment is unaffected: ``action_create_amendment`` sets
  ``state: draft`` explicitly and ``copy=False`` keeps the flag off the copy,
  so a dodatočné raised against a historical period is an ordinary submittable
  return, in state as well as in flag.
- **Normalisation runs both ways, and a constraint backs it.** Either value
  arriving alone implies the other, so the pair stays whole whichever end a
  caller touches. Two holes the normalisation alone did not close, both found
  in second-opinion review: ``write({"legacy": False})`` names no state and
  would clear the flag while leaving the record in ``legacy``; and
  ``default_legacy`` in the context is applied by ``create`` itself, after the
  override has read its vals, so no override can see it.
  ``_cssk_check_legacy_state_agree`` is therefore the guarantee and
  create/write only the convenience.

[19.0.1.8.0] — 2026-09-07
-------------------------

Added
~~~~~

- ``normalize_company_name``, ``name_search_token`` and
  ``company_name_similarity`` — the canonical home for the company-name
  matching that ``dd_ai_invoice`` had been carrying privately. Legal forms are
  **canonicalised, never stripped**: in CZ/SK the form is part of the identity,
  so "Alfa s.r.o." and "Alfa a.s." are two companies and reducing both to
  "alfa" would post one supplier's bill against the other.
- The similarity ratio is plain ``difflib.SequenceMatcher`` over the
  normalised strings, deliberately — it is the ratio that was **calibrated
  against the live register**. On 45 real Slovak companies, 44 scored exactly
  1.000 (including every case where the raw strings differed by case, spacing
  or a comma) and one scored 0.716. A cleverer ratio would move those numbers
  and invalidate the thresholds derived from them.

Fixed
~~~~~

- ``normalize_registry`` **padded short numbers into validity**: ``1`` became
  ``00000001``, which satisfies the check digit. The floor in ``is_valid_ico``
  could not catch it because by then there were eight digits. Both functions
  now refuse the same short values — otherwise one launders junk past the
  other. Found while building the register-verification module, not by the
  original tests, which passed only because the constraint happened to fire
  before canonicalisation ran.

[19.0.1.7.0] — 2026-09-07
-------------------------

Added
~~~~~

- **The company registry is now validated as an IČO on CZ/SK partners.**
  ``company_registry`` is core's field and core validates nothing in it. On the
  Data Dance production base that left **12 of 96** CZ/SK values unusable:
  ``Test``, ``12345``, ``-``, ``JUSTICE.CZ``, ``cepatay111`` — and three cases
  of the company *name* pasted into the number field, two of which reached
  **posted invoices**, where a company name in place of the IČO is a defect in
  a statutory document rather than untidy data. ``is_valid_ico`` applies the
  mod-11 check both countries share; measured against that base it rejects all
  12 and accepts all 84 genuine companies.
- ``normalize_registry`` canonicalises storage (``00 585 441`` → ``00585441``,
  ``614556`` → ``00614556``), keeping the leading zeros a Czech IČO is printed
  with. It rewrites **only values that are already valid**, so it can never
  turn a typo into a different-looking typo, and it returns anything it does
  not recognise unchanged so the error can quote what was typed.
  This is also what makes core's own ``same_company_registry_partner_id``
  duplicate warning work: core compares the two strings exactly, so without a
  canonical stored form ``00 585 441`` and ``00585441`` never see each other.
- ``registry_key`` is the separate COMPARISON form — digits only, padding
  dropped — for matching ``00682811`` against ``682811``. Using the storage
  form to match misses half the matches; using the match form to store puts an
  unpadded IČO on a statutory document. They are deliberately two functions.

Notes
~~~~~

- **The check digit alone does not bound the length**, and this was caught in
  review rather than by the measurement. One number in eleven satisfies the
  mod-11 arithmetic, so zero-padding an arbitrary short number makes it
  "valid": ``1``, ``19``, ``27`` … — **10 000** values of five digits or fewer
  would have been accepted, which is precisely the junk a signup form
  collects. ``ICO_MIN_DIGITS = 6`` rejects all 10 000 and breaks no real
  number: every genuine IČO is written with at least six digits, the oldest
  carrying leading zeros (``00614556`` printed as ``614556``).
- **The check is scoped by** ``country_code``, **not** ``_deduce_country_code``.
  The latter also reads the VAT prefix, so a foreign company VAT-registered in
  Czechia — a ``CZ…`` VAT number over a German ``HRB 6089`` company registry —
  would be deduced as CZ and have its legitimate home-register number
  rejected. Core scopes this field's own uniqueness by country too.
  The mod-11 scheme is Czechoslovak; an unscoped check rejects Hetzner's
  ``HRB 6089``, a US EIN ``93-1564675``, an 11-digit Latvian registry and a
  Papua New Guinean ``1-120979442`` — all legitimate, all present on that
  same base.
- Because the registry is a **commercial field**, a bad value on a parent is
  synced onto every child and the constraint fires for those too. The error
  names the ``commercial_partner_id`` that owns the number rather than
  whichever contact happened to be written first, which would otherwise send
  the user to a record that has nothing to fix.
- A partner with no registry, or no country yet, is not checked. Signup
  captures an e-mail long before a country, and a private customer has no IČO
  at all; failing either would make checkout impossible.
- The ``19.0.1.7.0`` migration **reports and does not rewrite**. A wrong
  registry cannot be repaired by guessing — the correct value for each real
  case came from looking the company up in ARES — and writing something
  plausible over it would replace a visible error with an invisible one on
  records that reach invoices. Existing rows keep working until edited; the
  log names the ones to fix.

[19.0.1.6.1] — 2026-09-06
-------------------------

Fixed
~~~~~

- **The no-schema raise refused forms that have no schema to load.** Tightening
  ``_validate_against_schema`` to stop an unvalidated export was right — a KV
  DPH once exported unvalidated and looked as though it had passed — but it
  made every financial-statement export impossible where the authority
  publishes no XSD. Measured on a pristine tree: **8 errors** across
  ``l10n_cz_fs``, ``l10n_sk_fs`` and ``l10n_cssk_fs_base``. A version may now
  declare the absence via ``xml_schema_optional``; export then skips
  validation and says so in the log. Anything that has not declared it still
  raises, so the narrowing cannot widen into "never validate".
- ``cssk_vat_deduction_date`` was hidden on customer documents, though its own
  help documents the § 42 / late-entry **output** case and
  ``_cssk_period_move_ids`` deliberately prefers it over the tax point for the
  tax-point move types. The field that overrides a document's period was
  settable only by server action or import.
- ``tests/__init__.py`` still carried the proprietary banner — the one file the
  relicense sweep missed in this module.

Removed
~~~~~~~

- **``l10n_cssk_dic`` moved to the new ``l10n_sk_base``.** It lived here on the
  premise that both CZ and SK need a separate DIČ field. Slovakia does — DIČ,
  IČO and IČ DPH are three different identifiers, and a subject can hold a DIČ
  without being a VAT payer. Czech does not: there *DIČ* **is** the VAT number
  (``CZ`` + IČO), so ``vat`` already holds it, and ``l10n_cz_invoice`` was
  printing the same number twice from two fields.
  Existing values are carried over automatically when ``l10n_sk_base`` is
  installed; the old column is left untouched.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.5.0] — 2026-08-20
--------------------------

Added
~~~~~

- ``account.move._cssk_rate_date()`` — the date whose VAT rates governed a
  document: its tax point where it records one, its accounting date otherwise.
  Deliberately not the period date, and it ignores ``cssk_vat_deduction_date``:
  the period a deduction is claimed in may fall after a rate change, while the
  rate was fixed when the supply took place.

[19.0.1.4.2] — 2026-08-14
--------------------------

Added
~~~~~

- ``account.move.cssk_vat_deduction_date`` — the period in which the input-VAT
  deduction is exercised, where that differs from the accounting date (CZ § 73
  and the SK equivalent allow it to be later than the supply). Empty means "the
  accounting date", which is the ordinary case.

Changed
~~~~~~~

- ``_cssk_period_move_ids()`` selects the input side on the deduction date where
  a document records one, falling back to the accounting date.

[19.0.1.4.1] — 2026-08-14
--------------------------

Changed
~~~~~~~

- ``_cssk_period_move_ids()`` now applies a **different basis per direction**:
  output by the tax point, input by the accounting date (the period the
  deduction is claimed in, per CZ § 73 and the SK equivalent). Using the tax
  point on both sides understates the deduction whenever a document is supplied
  in one period and received in the next.

[19.0.1.4.0] — 2026-08-14
-------------------------

Added
~~~~~

- ``_cssk_period_move_ids()`` on the statutory submission mixin: shared period
  selection for VAT-derived filings, by **tax point** (DUZP / deň dodania) with
  the accounting date as fallback where no tax point is recorded.

[19.0.1.3.0] — 2026-07-14
-------------------------

Changed
~~~~~~~

- The CZ/SK payment-symbol fields (``l10n_cssk_variable_symbol`` /
  ``_constant_`` / ``_specific_``) moved to the new dedicated
  ``l10n_cssk_payment_symbols`` module, which is now a dependency. Columns
  and field names are unchanged — existing data is preserved; the new home
  adds validation, a credit-note VS policy and statement-line symbols.

[19.0.1.2.3] — 2026-07-04
-------------------------

Added
~~~~~

- ``normalize_vat()`` helper in ``tools.py`` (strip separators, optional country
  prefix) — the single VAT-canonicalisation used by the control statement and
  ADIS reliability lookups downstream.
- ``_read_group``-based balance helpers on ``cssk.statutory.submission.mixin``
  (``_cssk_balances_by_account_code``, ``_cssk_account_balance_map``) so evaluators
  in the statement bases can fetch account balances in a couple of queries
  instead of per-prefix search loops.

Changed
~~~~~~~

- Export orchestration consolidated into ``cssk.statutory.submission.mixin``:
  ``action_export_xml`` is the one pipeline (ensure-not-submitted → draft gate →
  ``_cssk_preflight_export`` → kontroly → render → ``lxml`` XSD validate → attach),
  with per-base hooks. Every ``l10n_cssk_*`` statement now shares it.

[2026-07-02] — Wave 2 (P1 robustness)
-------------------------------------

Added
~~~~~

- Filed-history retention on the submission mixin: ``action_submit`` freezes the
  exported XML as an immutable filed copy; ``_ensure_not_submitted`` guards
  recompute/export against a submitted record.
- ``action_create_amendment`` — dodatočné / opravné podanie workflow off a filed
  statement.
- ``_cssk_preflight_export`` hook (blocking pre-export checks) called before render.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Added
~~~~~

- ``statutory_round()`` / ``statutory_whole()`` in ``tools.py`` — HALF-UP rounding via
  ``float_round``, replacing banker's ``round()`` and truncating ``int(x+0.5)``; the
  canonical rounding adopted across VAT / KV / DPPO / FS.

Fixed
~~~~~

- Multi-company leakage: ``ir.rule`` ``[('company_id','in',company_ids)]`` pattern
  established for the statement models built on this base.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral substrate for the whole CZ/SK statutory cluster, depending on
  Odoo core only (``account`` + ``mail``) — no ``account_reports``, no OCA — so it is
  CE- and EE-clean.
- ``cssk.tax.authority`` (daňový úrad / finanční úřad registry with the code used
  in statutory XML) and ``cssk.person.type`` (FO / PO catalogue), wired onto
  ``res.company`` / ``res.partner``.
- ``account.move`` / ``account.move.line`` statutory extensions and the statutory
  footprint views; settings + security scaffolding.
- ``cssk.statutory.submission.mixin`` — shared draft → preview → exported →
  submitted lifecycle for all statement bases.
- Full cs_CZ + sk_SK translations (Odoo 19 jsonb).
