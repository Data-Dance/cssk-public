=========
Changelog
=========

All notable changes to **l10n_cssk_fs_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.9.0] — 2026-10-05
-------------------------

Fixed
~~~~~

- **Every total, and every row without a korekcia formula, filed brutto and
  korekcia as 0.** Only leaves reading a korekcia off the ledger got the
  split, so the SK Súvaha exported r001 SPOLU MAJETOK as 0 / 0 / netto, and
  the cash rows likewise — every one of them failing netto = brutto −
  korekcia. All rows now carry both columns: a total's korekcia is its own
  formula over its children's (the rule ``l10n_cz_dppo`` already applied to
  the Czech výkazy), any other row has none, and brutto = netto + korekcia.
  Statements already exported keep their file; recompute a draft to refresh.
- **An overridden netto keeps the ledger's korekcia** and brutto follows
  from it. It used to drop both to 0 and file 0 / 0 / netto.

[19.0.1.8.0] — 2026-10-05
-------------------------

Added
~~~~~

- **Manual figures can be entered on the statement again.** The help text
  said to tick *Override*, but the foldable tree had no such control, so
  the backend override could not be reached from the UI and the two SK Úč POD
  ``manual`` rows (s113 Vydané dlhopisy, v01 Čistý obrat) were stuck at 0. A
  pencil next to any figure that is not a total opens an input; the row
  updates at once and the totals on the next *Compute*, which keeps manual
  figures.
- **The comparative column can be overridden too** (``is_prior_overridden``
  / ``prior_manual_value``). The prior column is read from the ledger, and
  in a company's first year in Odoo the prior year's ledger is not there.
- The unmapped-account warning is a dialog with a table — code, account
  name, balance as money, and a drill-down to the journal items — instead
  of an untranslated error popup. Rows live in
  ``cssk.fs.statement.unmapped`` and carry the accounts behind each code,
  which a statement account mapping can make more than one.

Changed
~~~~~~~

- The header button is *Unmapped accounts* (was *Accounts on no row*).
- ``unmapped_note`` is now derived from the rows; the migration converts
  the stored text of existing statements, which matters for those that left
  draft and can no longer be recomputed.

Fixed
~~~~~

- **Editing a manual figure sends the statement back to draft**, so it
  cannot be exported until *Compute* has brought the totals over it up to
  date (found in review by gpt-5.3-codex: an edited row beside stale totals
  was exportable).
- **Totals cannot be overridden.** A total typed over its own rows no
  longer adds them up. A constraint refuses it, and an override left on an
  aggregate by an earlier version is dropped on recompute.
- **The statement tree stopped at row 40.** An x2many loads 40 records per
  page and the widget has no pager, so a 206-row Úč POD showed only its
  first 40 rows.
- The tree widget's own labels (*Collapse all*, *Current period*, …) had no
  Slovak translation; the catalogues had also gone stale on 40+ strings.

[19.0.1.7.0] — 2026-10-03
-------------------------

Changed
~~~~~~~

- **Balance sheet and Income statement each show their own part of a
  combined document.** The Slovak Úč POD carries the súvaha and the výkaz
  ziskov a strát in one record, so since 19.0.1.5.0 both menus listed the same
  statements and opened the whole tree. Each menu now shows only its part
  (``fs_section`` in the action context); opened from anywhere else the record
  still shows every row. A row's part is decided by the top of its tree, so
  súvaha row A.VIII (current-year result), which reads the period movement,
  stays on the súvaha. A migration marks the rows of existing statements.

[19.0.1.6.0] — 2026-10-02
-------------------------

Fixed
~~~~~

- **A balance-sheet row's drill-down did not add up to the row.** It re-read
  the formula as plain code prefixes, over the period MOVEMENT even for an
  as-of row, in every journal including the year-end closing ones, and without
  the synthetic-absorb rule (022000 taking 022001). It now opens exactly the
  accounts that contributed to the figure, over the window the figure was
  read from, with the closing journals left out — so ``unreconciled`` names
  real discrepancies instead of nearly every row. Statements computed before
  keep their old drill-down until recomputed.

Changed
~~~~~~~

- Statements and the reverse-drill footprint honour the statement account
  mapping from ``l10n_cssk_core``; an account mapped for one balance side only
  is reported as feeding a row whose side depends on the balance.

[19.0.1.5.0] — 2026-10-02
-------------------------

Fixed
~~~~~

- **The Income statement menu was always empty on Slovak databases.** Úč POD
  is one document carrying the súvaha and the výkaz ziskov a strát, filed as a
  ``balance_sheet`` version, so a menu filtered by ``statement_kind`` found
  nothing and New offered no version. A version now reports
  ``covers_profit_loss`` (it is an income statement, or a balance sheet with
  movement-basis rows); the menu lists by it, New falls back to it, and such a
  statement is named *Financial statements* rather than *Balance sheet*.
- **A new statement defaulted to the previous calendar year.** It now defaults
  to the company's last completed fiscal year, so a hospodársky rok April–March
  gets April–March.

- **A brutto / korekce row drilled into half its accounts.** A row filed in
  three columns reports its NETTO, but its source-document domain named only
  the gross accounts (``account_formula``), so the drill-down omitted the
  oprávky / opravné položky and the row showed as unreconciled whenever any
  existed. The correction accounts are now part of the row's source domain.
  Surfaced by the CZ Rozvaha taking the brutto / korekce split for DPPDP9
  VetaUA; it applied to the Slovak Súvaha rows all along.

[19.0.1.4.5] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the financial statements but could not open one and hit *not
  allowed to access*. On Community, ``account.group_account_manager`` does not
  imply ``account.group_account_user`` (and on Enterprise
  ``account_accountant`` only adds ``group_account_basic``), so a model
  granted to ``group_account_user`` alone is closed to an Administrator who
  lacks "Show Full Accounting Features". The statement already granted it; its
  lines did not. ``group_account_manager`` now has the same access as
  ``group_account_user`` on ``cssk.fs.statement.line``. Takes effect on module
  update.

[19.0.1.4.4] — 2026-09-16
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

[19.0.1.4.3] — 2026-09-14
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

- The per-kind ``New`` default searched for its version with ``active_test`` on,
  so on an archived vintage it found nothing, left the required ``version_id``
  empty, and offered nothing in the dropdown either.

[19.0.1.4.2] — 2026-09-13
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

[19.0.1.4.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- ``_cssk_form_label`` was a bare Python string, so it was in no ``.pot`` at all
  — untranslatable in every language rather than merely untranslated. It is now
  a lazy translation (``_lt``), rendered in the reader's language, and the term
  is in the catalogue with its Slovak and Czech.

[19.0.1.4.0] — 2026-09-13
-------------------------

Added
~~~~~

- The statutory footprint now names the FILING each row belongs to, not just
  the form and the line code, so a reader can go and look at it. This module
  declares ``res_model`` in its footprint entries; ``l10n_cssk_core`` resolves
  it against the period. The key is optional in the contract — a contributor
  that omits it produces a row with a blank filing and nothing else changes.

[19.0.1.3.2] — 2026-09-13
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

[19.0.1.3.1] — 2026-09-13
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

[19.0.1.2.4] — 2026-09-06
-------------------------

Added
~~~~~

- ``xml_schema_optional`` on the version: "the authority publishes no XSD for
  this form", which is a fact per vintage and not per country — SK ships
  ``uzsuv``/``uzvzs`` for the Súvaha and VZS and nothing for the two prehľady,
  and CZ publishes nothing for any of the four. Without it the export refuses,
  because it cannot tell a missing file from a form that has none.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.2.3] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Financial-statement export consolidated onto the shared
  ``cssk.statutory.submission.mixin`` pipeline (draft gate → preflight → kontroly →
  render → XSD validate → attach).

Fixed
~~~~~

- Evaluator performance: balances read via ``_read_group`` helpers instead of
  per-prefix search loops (Súvaha compute ~600 queries → ~2).

[2026-07-02] — Wave 2 (P1 robustness)
-------------------------------------

Added
~~~~~

- Filed-copy retention on submit and pre-export preflight
  (``_cssk_preflight_export``).

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Changed
~~~~~~~

- Line values rounded with ``statutory_round()`` (HALF-UP).

Fixed
~~~~~

- Multi-company leakage: ``ir.rule`` ``[('company_id','in',company_ids)]`` on the
  statement model.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral framework for the Slovak **Súvaha** / **Výkaz ziskov a strát**
  and Czech **Rozvaha** / **VZZ**: a hierarchical line tree where leaf lines are
  computed from account-code balances and parent lines aggregate.
- ``cssk.fs.statement.version`` (line definitions + statement kind
  balance_sheet / profit_loss + template + schema),
  ``cssk.fs.statement.line.def`` (``accounts`` / ``aggregate`` / ``manual``), and
  ``cssk.fs.statement`` (mail.thread) computing the current **and a comparison
  (prior) period**, with per-line manual overrides preserved across recompute,
  an OWL tree field, and XSD-validated XML export.
- CE-clean: evaluator reads ``account.move.line`` balances by
  ``account.account.code`` directly — no ``account_reports`` engine. Full cs_CZ +
  sk_SK translations.
