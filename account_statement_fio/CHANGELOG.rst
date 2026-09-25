=========
Changelog
=========

All notable changes to **account_statement_fio** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.2.3.3] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the Fio statement pull on a bank journal and hit *not allowed to
  access*. On Community, ``account.group_account_manager`` does not imply
  ``account.group_account_user`` (and on Enterprise ``account_accountant``
  only adds ``group_account_basic``), so a model granted to
  ``group_account_user`` alone is closed to an Administrator who lacks "Show
  Full Accounting Features". The journal it is bound to is open to an
  Administrator. ``group_account_manager`` now has the same access as
  ``group_account_user`` on the pull wizard. Takes effect on module update.

[19.0.2.3.0] — 2026-09-02
-------------------------

Changed
~~~~~~~

- **The bank-statement settings are the right-hand column of the Fio banka
  section**, and switching the bank feed away from Fio hides them as one
  block. Gating field by field left the column half present — some rows gone,
  the heading and the stragglers still there — which reads as a rendering
  fault rather than as a setting that no longer applies. The tokens in the left
  column stay ungated on purpose: a Fio token is a credential for the account,
  not for the statement feed, and a journal may be used for Fio payments while
  its statements arrive some other way.

Carried over from 18.0 (18.0.2.3.0).

[Unreleased]
------------

[19.0.2.3.2] — 2026-09-13
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

[19.0.2.3.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The model's own name was never exported.** ``_description`` is what
  labels a record's type in breadcrumbs and the technical model list, and
  ``tools/i18n_export_offline.py`` emitted no ``model:ir.model,name:`` line
  at all — the entries already in the catalogues had come from an older
  DATABASE export. So every model added since had no entry and its name
  could not be translated. The exporter now emits it, and the missing
  entries are merged and filled.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

Changed
~~~~~~~

- **``mask_token`` is applied at the sinks as well as at the raise site.**
  Defence in depth on a credential, **not** the repair of a live disclosure —
  an earlier draft of this entry claimed it was one and that was wrong.

  ``FioClient`` already masks every exception it constructs from something that
  saw a URL (``_check``, ``_get``, ``import_orders`` all pass through
  ``self._mask``), and each of the six sinks catches ``FioError`` or narrower,
  so they receive text the client has already cleaned. The single handler that
  catches bare ``Exception`` is the scheduled pull — which is precisely the one
  that already had ``mask_token``.

  What the change buys is that the guarantee stops depending on every sink's
  ``except`` clause staying narrow, which nothing enforces. Widen one to
  ``Exception``, or have any library raise between ``_fio_lock()`` and the
  client's own ``try``, and the protection disappears silently. Masking at both
  ends removes that dependency. Covered on:
  ``action_fio_test_connection``; the payment upload's three sinks
  (``fio_response`` is **stored**, and the chatter is readable by every
  follower); the upload's ``FioError`` re-raise; and ``_fio_explain``'s
  fallback, the only branch that returns the bank's own words.

  Correcting a second claim from that draft: the token is in the URL **path**
  for the seven read endpoints (``periods``, ``by-id``, ``last``,
  ``lastStatement``, ``set-last-id``, ``set-last-date``, ``merchant``), but
  ``import_orders`` posts it in the request **body** and its URL contains no
  token at all. So the *submit* token — the one that can move money — is the
  one credential that never reaches a URL, and the upload sink is the least
  exposed rather than the most.

  The local ``FioOrderError`` paths in the two payment bridges are deliberately
  left unmasked: they come from building and validating the file, never from
  the HTTP client, so they cannot carry a URL.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **DISCHARGED 2026-09-01 — do not port this again.** The note below was
  accurate when written and is not any more. ``18.0-fio-api`` now carries the
  whole of 19.0.1.1.0 (as ``[18.0.1.1.0]``, identical text) and everything
  above it: ``d60cf46`` landed the five fixes that had been stranded in a
  working tree, ``ec70ec8`` the ``fa-bolt`` icon and the ``FioError`` wrap.
  The 18.0 branch is now *ahead* of this one, not behind — the journal
  collapse, the ``bank_statements_source`` registration and the cs/sk
  catalogues exist only there. The live debt runs 18.0 -> 19.0, and is
  recorded in the 18.0 CHANGELOGs under "Carry-over to 19.0".

  Original note, kept for the record: everything under 19.0.1.1.0 plus the
  unreleased entries landed on ``19.0-fio-api`` only; DURWEN runs the 18.0
  copies vendored into ``DURWEN_CZ/addons``, which already carried the
  19.0.1.1.0 fixes while the ``18.0-fio-api`` branch did not.

[19.0.2.2.0] — 2026-09-01
-------------------------

Added
~~~~~

- **Czech and Slovak translations** (56 terms). The module had no ``i18n/``
  directory at all.

  These are English-source UI strings with no statutory wording, so per the
  repository convention they get English source plus ``cs.po`` / ``sk.po``
  rather than national-language source. Terms quoting Fio's own interface are
  left verbatim in **both** languages — the API rights ``Sledování účtu`` and
  ``Sledování účtu a zadávání platebních a inkasních příkazů``, the menu path
  ``Nastavení → API``, ``ID pohybu`` / ``ID pokynu`` — because Fio's API
  documentation and its internet banking are in Czech for Slovak accounts too,
  and translating them would name something the user cannot find on screen.

  Includes the 90-day history-unlock instruction, which has to be followed
  inside ten minutes and is therefore the one message a reader must not have to
  puzzle over.

  Exported with ``tools/i18n_export_offline.py``: ``odoo-bin i18n export``
  needs a database and there is none here. Verified by reading each catalogue
  back through Odoo's own ``PoFileReader`` — every entry resolves to a record
  reference, none is untranslated — and with ``msgfmt --check``.

[19.0.2.1.0] — 2026-09-01
-------------------------

Added
~~~~~

- **``fio`` is registered as a bank-statement source.** The journal's *Bank
  Feeds* radio now offers *Fio banka API*, and the scheduled pull keys on it.

  ``bank_statements_source`` is **Community**: core's base returns a single
  ``undefined`` entry, and Enterprise's ``account_online_synchronization`` only
  appends ``online_sync``. So this works on both editions and needs no
  Enterprise-only bridge, which keeps the module's one-code-path premise.

  The extension point is name-mangled — ``__get_bank_statements_available_sources``
  compiles every reference to ``_<ClassName>__get_...`` — so the override lives
  in a class literally named ``AccountJournal`` and calls
  ``super(AccountJournal, self)`` by name rather than a bare ``super()``, the
  way core's own Enterprise override does. Written any other way it would not
  override anything and the base sources would silently disappear. There is a
  test asserting that ``undefined`` survives alongside ``fio``, because that is
  the half a mangling mistake breaks.

  The real gain is that Fio and Odoo's Enterprise bank feed become mutually
  exclusive **by construction** rather than by runbook: the field is
  single-valued, and Enterprise already overrides ``write()`` to detach
  ``account_online_account_id`` when the source moves away from ``online_sync``.
  Nothing here shares a dedup key with that feed, so a journal on both imports
  every transaction twice — which is exactly what a live pull did on a staging
  build carrying both, duplicating 15 lines.

- A journal whose feed is Fio but which has no read token is refused at save
  time (``_check_fio_source_has_a_token``), rather than failing in the cron
  every hour into a chatter nobody reads. It constrains ``fio_token_read``
  itself, under ``sudo()`` — not the stored ``fio_has_token_read`` compute. A
  constraint triggering on derived state depends on when the recompute is
  flushed relative to the validation, and a write that sets the token and the
  source in one go is exactly where that ordering would decide whether the
  constraint sees the truth. The ``sudo()`` is what lets an accountant who may
  set the bank feed, but may not read the token, get this refusal rather than
  an access error.

Changed
~~~~~~~

- The pull settings are gated on the source, the way core gates a source's own
  settings (``account_bank_statement_import_qif``). The **tokens are
  deliberately not**: a Fio token is a credential for the account rather than
  for the statement feed, and a journal may be used for Fio payments while its
  statements arrive some other way — hiding the token block behind the bank-feed
  radio would leave that journal no way to reach its submit token. Such a
  journal now says so in place of the pull settings.

Fixed
~~~~~

- **The scheduled pull's failure message is masked before it reaches the
  chatter.** That handler catches ``Exception``, not just ``FioError``, so it
  can be handed a message the API client never sanitised — and Fio carries the
  token **in the URL path**, which is precisely what a stray ``requests``
  message quotes. Every follower of the journal can read that chatter. Now run
  through ``mask_token``, with a regression test.

Removed
~~~~~~~

- ``fio_pull_enabled``. It duplicated the new radio, and two switches that can
  disagree guarantee a support question about why a journal set to Fio is not
  pulling. ``l10n_be_codaclean`` keys its cron on the source alone for the same
  reason. To pause a journal, move its bank feed off Fio.

[19.0.2.0.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **Follows ``account_fio``'s collapse of ``fio.account`` into
  ``account.journal``.** The pull settings are now journal fields:
  ``fio_pull_enabled``, ``fio_pull_mode``, ``fio_overlap_days``,
  ``fio_create_statements``, ``fio_last_pull_at``, ``fio_last_movement_id``,
  ``fio_last_statement_year`` and ``fio_last_statement_number``.
  ``_cron_pull_statements`` is ``_fio_cron_pull_statements``, and the
  ``fio.statement.pull`` wizard takes a ``journal_id`` instead of a
  ``fio_account_id`` (its contextual action is bound to ``account.journal``).

- **The pull cron now also requires a read token.** Every journal carries the
  Fio fields, so ``fio_pull_enabled`` alone — which defaults to ``True`` —
  would have matched every journal in the database and raised "No Fio read
  token" on each. The search is ``fio_pull_enabled AND fio_has_token_read``.
  This is the sharp edge of moving fields onto a core model, and it is covered
  by a test.

[19.0.1.1.1] — 2026-09-01
-------------------------

Fixed
~~~~~

- **The scheduled pull discarded everything it imported.** Diagnosed on the
  18.0 twin of this code against a real Fio account: the interactive *Pull now*
  imported 15 statement lines while the cron, minutes later on the same
  accounts, imported zero — and reported no failure, because as far as it was
  concerned there had not been one.

  ``Savepoint.close()`` is declared ``close(self, *, rollback=True)``
  (``odoo/sql_db.py``). The success path called ``savepoint.close()`` bare,
  which reads exactly like "release this savepoint" and in fact **rolls it
  back**. Every line the pull had just created was discarded at the moment the
  pull succeeded. (The rows really were written first: statement-line ids
  jumped 5168 → 5172 with 5169–5171 unused, because a PostgreSQL sequence does
  not roll back.)

  What made it invisible was the second half. ``cr.savepoint(flush=False)``
  returns the plain ``Savepoint``, whose ``rollback()`` does **not**
  ``cr.clear()``. The record's own ``write()`` calls were still unflushed in
  the ORM cache when the rollback ran, so they *survived* it and were written
  afterwards — leaving ``last_read_at``, ``last_pull_at`` and the correct
  ``last_movement_id`` on an account with no lines. Worse, a genuinely failed
  pull therefore advanced the bookmark past movements it had thrown away, so
  the next run skipped them for good.

  Now used as a **context manager** with the default ``flush=True``:
  ``__exit__`` passes ``rollback=exc_type is not None``, which is the intent,
  and ``_FlushingSavepoint`` flushes on release and clears the cache on
  rollback. Four regression tests; the persistence ones assert with ``search``
  rather than the returned recordset, since a rolled-back ``INSERT`` still
  returns a perfectly good recordset — which is why every existing cron test
  passed against the bug.

- **The scheduled pull's failure message is masked before it reaches the
  chatter.** That handler catches ``Exception``, not just ``FioError``, so it
  can be handed a message the API client never sanitised — and Fio carries the
  token **in the URL path**, which is precisely what a stray ``requests``
  message quotes. Every follower of the account can read that chatter. Now run
  through ``mask_token``, with a regression test.

- **``last_pull_at`` now means what it says.** It was written inside
  ``_fio_import_lines``, which returns early when there is nothing new, so an
  account that had simply been quiet showed a last pull weeks in the past —
  indistinguishable from a feed that had stopped, which is the one question the
  field exists to answer. It is stamped once per completed pull in
  ``fio_pull()``; ``last_movement_id`` stays where it was, since it really is
  about what was imported.

[19.0.1.1.0] — 2026-08-24
-------------------------

Fixed
~~~~~

- **A failing account in the pull cron discarded every account already pulled
  in the same run.** ``_cron_pull_statements`` rolled back the whole
  transaction, so one bank failing late silently undid the successful imports
  before it. It now rolls back to a per-account ``SAVEPOINT``. A bare rollback
  is also forbidden inside a test, which is how it surfaced.


[19.0.1.0.0] — 2026-08-19
-------------------------

Added
~~~~~

- Three pull modes on ``fio.account``: re-readable date range (default),
  official numbered statements with the bank's own balances, and the
  server-side bookmark.
- Hourly cron, per-account, that isolates a failing bank from the rest.
- Pull wizard with range chunking and a refusal to reach past 90 days until the
  operator confirms the history is unlocked in internet banking.
- ``fio_movement_id`` / ``fio_instruction_id`` on statement lines; duplicate
  detection through ``unique_import_id``.
- VS/KS/SS written to the symbol fields when a module supplies them, and always
  kept as ``VS:``-style tokens in the label.
