=========
Changelog
=========

All notable changes to **l10n_cssk_vat_return_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.10.5] — 2026-09-17
--------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the VAT return list but could not open a return and hit *not
  allowed to access*. On Community, ``account.group_account_manager`` does not
  imply ``account.group_account_user`` (and on Enterprise
  ``account_accountant`` only adds ``group_account_basic``), so a model
  granted to ``group_account_user`` alone is closed to an Administrator who
  lacks "Show Full Accounting Features". The return itself already granted it;
  its lines did not. ``group_account_manager`` now has the same access as
  ``group_account_user`` on ``cssk.vat.return.line``. Takes effect on module
  update.

[19.0.1.10.4] — 2026-09-16
--------------------------

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

[19.0.1.10.3] — 2026-09-14
--------------------------

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

- Three tests pin what the whole approach rests on: that only the VERSION
  carries ``active`` (a line definition or statement type gaining one would
  make archiving cascade and break recomputation), that a plain search really
  does hide an archived vintage, and that an archived version still yields its
  line definitions through the stored Many2one.

[19.0.1.10.2] — 2026-09-13
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

[19.0.1.10.1] — 2026-09-13
--------------------------

Fixed
~~~~~

- ``_cssk_form_label`` was a bare Python string, so it was in no ``.pot`` at all
  — untranslatable in every language rather than merely untranslated. It is now
  a lazy translation (``_lt``), rendered in the reader's language, and the term
  is in the catalogue with its Slovak and Czech.

[19.0.1.10.0] — 2026-09-13
--------------------------

Added
~~~~~

- The statutory footprint now names the FILING each row belongs to, not just
  the form and the line code, so a reader can go and look at it. This module
  declares ``res_model`` in its footprint entries; ``l10n_cssk_core`` resolves
  it against the period. The key is optional in the contract — a contributor
  that omits it produces a row with a blank filing and nothing else changes.

[19.0.1.9.5] — 2026-09-13
-------------------------

Added
~~~~~

- A test for the tuple-valued rows a row-based form compares, on the three
  helpers that had only ever been handed floats.

[19.0.1.9.4] — 2026-09-13
-------------------------

Changed
~~~~~~~

- Tests follow the comparison out of the chatter: the two that asserted the
  posted HTML rendered and escaped correctly are replaced by one asserting the
  comparison posts **nothing**, since a ``message_post`` added back on that
  path would look harmless in review. Added: agreeing rows are recorded in
  state ``agrees`` and stay out of the worklist; an answered row that starts
  agreeing keeps its answer.

[19.0.1.9.3] — 2026-09-13
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

[19.0.1.9.2] — 2026-09-13
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

[19.0.1.9.1] — 2026-09-13
-------------------------

Added
~~~~~

- Two tests for the chatter body of the filed-vs-computed comparison: that it
  renders as HTML rather than escaped text, and that a row code carrying
  markup is escaped rather than rendered. The second is the one a bare
  ``Markup("".join(...))`` would fail — see ``l10n_cssk_core`` 19.0.1.9.1.

[19.0.1.9.0] — 2026-09-12
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

[19.0.1.8.2] — 2026-09-10
-------------------------

Fixed
~~~~~

- **The superseded-tax marker was read in one language, and it is written in
  one language.** ``account.tax.name`` is ``translate=True``, and core's rename
  in ``chart_template.py`` is a plain assignment — so the marker lands in
  whichever language the chart load ran under and nowhere else. On a database
  built with ``sk_SK`` the two records read::

      {"en_US": "[old] 23% BAD DEBT", "sk_SK": "23 % POH"}
      {"en_US": "23% BAD DEBT",       "sk_SK": "23 % POH"}

  Identical in Slovak. ``tax.name`` resolves in the environment's language, so
  the skip added in 1.8.0 was **blind on exactly the databases this module
  exists for** — it worked in English and silently did nothing in Slovak.

  The marker is now looked for in **every stored translation**, not the active
  one.

[19.0.1.8.1] — 2026-09-10
-------------------------

Fixed
~~~~~

- **The superseded-tax marker is numbered, and 1.8.0 matched only the first
  form.** Core builds it in ``account/models/chart_template.py`` as
  ``f"[old{n if n > 1 else ''}] {name}"`` — so a second rename gives
  ``[old1]``, a third ``[old2]``, and core's own matcher is
  ``^(?:\[old\d*\] |)``. 1.8.0 tested ``startswith("[old]")``, which sees the
  first rename and lets every later one through as a source. A host that has
  been through two rate changes would have kept generating duplicates.

  Now mirrors core's pattern.

[19.0.1.8.0] — 2026-09-10
-------------------------

Fixed
~~~~~

- **A tax the chart had already superseded was used as a source, producing a
  duplicate.** Odoo renames a tax it replaces to ``[old] <name>`` and leaves it
  in place, so a host that has been through a rate change carries both
  ``23% BAD DEBT`` and ``[old] 23% BAD DEBT`` at the same amount. Neither is
  one of ours, so both passed the "never clone a clone" filter and the
  generator made a historical twin of **each**::

      20% BAD DEBT            <- from "23% BAD DEBT"          correct
      20% [old] 23% BAD DEBT  <- from "[old] 23% BAD DEBT"    duplicate

  Same concept, same rate, same ``type_tax_use``, two records — and the second
  named for two rates. Six of them on the reporting host.

  A superseded tax is history already; a historical twin of it is not a period
  anyone filed under. The generator now skips such sources.

  **This is also why the 1.7.0 name repair was a no-op on that host**, which is
  worth recording because the prediction that it would fix them was wrong and
  testable. The leading token of ``[old] 23% BAD DEBT`` is not a rate, so 1.7.0's
  token rule correctly declines to substitute and the collision branch prefixes
  exactly as the buggy generator did — the fixed generator and the old one
  *agree* on this input. Nothing to rewrite. The defect was in which taxes were
  chosen as sources, not in how they were named.

  A ``post-migration`` removes twins generated from a superseded source, but
  only ones nothing references: a tax named on a posted move line is left in
  place and logged by name and id, so no figure moves silently.

[19.0.1.7.0] — 2026-09-10
-------------------------

Fixed
~~~~~

- **Historical VAT taxes were named with two rates on charts that write
  ``23 %`` with a space.** ``_cssk_historic_tax_name`` tested
  ``name.startswith("%g%%" % source_rate)`` — that is ``"23%"`` — so a chart
  naming the same tax ``"23 % EÚ"`` failed the test and fell through to the
  collision-avoiding branch. Result: ``"20% 23 % EÚ"``, two rates in one name,
  saying neither.

  Reported from a client instance where **every** pre-2025 tax read that way,
  while a host whose chart writes ``"23%"`` was clean — which is why it went
  unnoticed here. It is not cosmetic: a cross-host mapping recipe of "match on
  name + type_tax_use + amount", derived on the clean host, matched **nothing**
  on the mangled one.

  The leading rate is now matched as a token, tolerating ``23%``, ``23 %``,
  ``12,5 %`` and ``12.5%``, and **the chart's own spacing is carried into the
  replacement** — ``"23 % EÚ"`` → ``"20 % EÚ"``, ``"23% RC"`` → ``"20% RC"``.
  Substitution happens only when the leading token *is* the source rate, so a
  name leading with some other rate is never silently renamed onto a rate it
  never had.

  A ``post-migration`` repairs existing names, and only ones this module
  generated the old way: it recomputes what the buggy generator would have
  produced and replaces the name only where the stored one matches it exactly.
  A tax renamed by hand does not match and is left alone.

[19.0.1.5.1] — 2026-09-06
-------------------------

Fixed
~~~~~

- **The drill-down and the figure selected different periods.**
  ``_tag_source_domain`` filtered move lines by ``date`` while the value was
  computed over ``_cssk_period_move_ids`` — output by tax point, input by
  deduction date. A document whose supply and booking straddle a period
  boundary (routine in SK, and on CZ imports) was therefore inside the figure
  and absent from the list it drills into, so ``source_reconciles`` went false
  and the return painted red while being correctly computed. The domain now
  carries the same move ids the figure was built from, resolved once per return
  rather than once per line.
- **A per-term ``-`` was read as part of the tag name.** The domain spelled the
  per-term sign as ``.replace("+", "|")``, which turns ``-24|+24_PR`` into the
  right tags by accident and ``+24|-24_PR`` into a lookup of the literal string
  ``-24_PR``, matching nothing. Both sides now read the grammar through one
  parser, ``_iter_tag_terms``, so they cannot drift again. No shipped formula
  writes the second form today; ``_eval_tags`` commits the grammar that allows
  it.
- Licence header on ``views/account_tax_views.xml`` said ``Other proprietary``
  and ``AGPL-3.0 or later`` in one sentence — sole outlier in a module this
  repository relicensed to AGPL-3, and the clause a header linter reads first.

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

- ``account.tax._cssk_rate_window()`` and ``_cssk_in_force_on(date)`` — the
  period a rate was in force. A historical clone states its own window; a
  current rate's start is derived from the clone that preceded it (SK 23 %
  begins the day its 20 % clone ends). A current rate no clone points at stays
  unbounded, because nothing in the data says when it began — SK 5 % was added
  in 2023 rather than replacing a predecessor, and may carry
  ``cssk_historic_valid_from`` by hand.

[19.0.1.3.1] — 2026-08-14
--------------------------

Changed
~~~~~~~

- Period selection follows the corrected two-sided basis (output by tax point,
  input by accounting date). Measured against one company's filed return, the
  input side moved from 84,731 understated to within a boundary document.

[19.0.1.3.0] — 2026-08-14
-------------------------

Fixed
~~~~~

- The return selected its period by **accounting date** instead of by the tax
  point. A CZ/SK VAT period is defined by the date of supply; the two coincide
  in everyday CZ use only because ``l10n_cz`` forces ``date =
  taxable_supply_date`` on draft moves. ``l10n_sk`` does not, and imported
  accounting history does not either, so documents fell in the wrong period.
  Period selection now delegates to ``_cssk_period_move_ids()``.

[19.0.1.2.3] — 2026-07-04
-------------------------

Changed
~~~~~~~

- VAT-return export now runs through the shared
  ``cssk.statutory.submission.mixin`` pipeline (draft gate → preflight → kontroly →
  render → XSD validate → attach); kontrolné pravidlá run before render.

[2026-07-02] — Wave 2 (P1 robustness)
-------------------------------------

Added
~~~~~

- Filed-copy retention: submitting the return freezes the exported XML; recompute
  and re-export are blocked on a submitted return.
- Pre-export preflight (``_cssk_preflight_export``) covering the required header /
  company data before the DPH XML is produced.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Changed
~~~~~~~

- Line values rounded with ``statutory_round()`` / ``statutory_whole()`` (HALF-UP),
  replacing ad-hoc rounding.

Fixed
~~~~~

- Multi-company leakage: ``ir.rule`` ``[('company_id','in',company_ids)]`` so returns
  no longer cross companies.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral framework for the Slovak **daňové priznanie k DPH** (DPHv25)
  and Czech **DPHDP3**: a fixed set of numbered riadky, each a signed sum of
  move-line balances carrying given tax tags, plus aggregate lines over other
  lines.
- ``cssk.vat.return.version`` (versioned line definitions + template + schema),
  ``cssk.vat.return.line.def`` (``tags`` / ``aggregate`` / ``manual``), ``cssk.vat.return``
  (mail.thread; draft → preview → exported → submitted) with the own tax-tag
  evaluator and ``action_export_xml``, and ``cssk.vat.return.line``.
- CE-clean: own evaluator over ``account.account.tag._get_tax_tags``, no dependency
  on the EE ``account_reports`` engine. Country layers ship the line set, XML
  template and XSD.
- Full cs_CZ + sk_SK translations.
