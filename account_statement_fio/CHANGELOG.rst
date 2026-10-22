=========
Changelog
=========

All notable changes to **account_statement_fio** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.2.3.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **The bank-statement settings are the right-hand column of the Fio banka
  section**, beside the connection rather than stacked under it.

Fixed
~~~~~

- **Switching the bank feed away from Fio now hides those settings as one
  block.** Each field carried its own ``bank_statements_source`` condition, so
  changing the radio emptied the rows but left the surrounding structure — a
  section half there, which reads as a rendering fault rather than as settings
  that no longer apply. The condition now sits once, on the group.

  The note explaining the absence moves out of that group to the full-width
  area, since a message about why the column is gone cannot live inside it.
  The **tokens stay ungated**: a Fio token is a credential for the account, not
  for the statement feed, and a journal may be used for Fio payments while its
  statements arrive some other way.

[18.0.2.2.3] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **``_fio_explain``'s fallback masks the exception text.** The two branches
  above it name specific errors; the fallback exists to pass through whatever
  they do not, which makes it precisely the path an unfamiliar exception type
  would arrive on. It is reachable only from the pull wizard's
  ``except FioError``, so nothing unmasked reaches it today — see the note in
  ``account_fio`` 18.0.2.3.0 for why that is not a reason to leave it.

Carry-over to 19.0
~~~~~~~~~~~~~~~~~~

- **``fio`` is not registered as a ``bank_statements_source`` on 19.0**
  (18.0.2.1.0). That is the change making Fio and Odoo's Enterprise bank feed
  mutually exclusive by construction; without it a 19.0 journal can carry both
  and import every transaction twice, which is what a live pull did before it.
  The name-mangled ``__get_bank_statements_available_sources`` override and its
  "class name is load-bearing" comment port unchanged.
- The collapse onto ``account.journal`` and the cs/sk catalogues are likewise
  19.0 debt; see ``account_fio``.
- The savepoint fix (18.0.2.2.1) is **already ported** — it is on branch
  ``19.0-fio-savepoint-fix`` (1701f3b) awaiting a fast-forward onto
  ``19.0-fio-api``, together with the ``mask_token`` fix and the
  ``last_pull_at`` semantics.

[18.0.2.2.2] — 2026-09-01
-------------------------

Fixed
~~~~~

- **3 view terms were missing from the translation catalogues.** The offline
  exporter read only the first child of a view's ``arch``, and an inherited
  view normally has one top-level node per xpath — so every term after the
  first was silently absent. Among them were the alert telling an operator that
  the bank's answer to an upload was lost, and the 90-day history-unlock
  instruction: precisely the messages whose whole value is being read under
  time pressure. Fixed in ``tools/i18n_export_offline.py`` and re-exported.

[18.0.2.2.1] — 2026-08-31
-------------------------

Fixed
~~~~~

- **The scheduled pull imported nothing, and said it had succeeded.** Found by
  a live run on staging: the interactive *Pull now* imported 15 lines from the
  same journals, minutes apart, while the cron imported zero — and posted no
  failure, because as far as it was concerned there had not been one.

  ``Savepoint.close()`` is declared ``close(self, *, rollback=True)``. The
  success path called ``savepoint.close()`` bare, which reads exactly like
  "release this savepoint" and in fact **rolls it back**. Every statement line
  the pull had just created was discarded at the moment the pull succeeded.
  (The rows really were written first: statement-line ids on staging jumped
  5168 → 5172 with 5169–5171 unused, because a PostgreSQL sequence does not
  roll back.)

  What made it invisible was the second half. ``cr.savepoint(flush=False)``
  returns the plain ``Savepoint``, whose ``rollback()`` does **not**
  ``cr.clear()``. The journal's own ``write()`` calls were still unflushed in
  the ORM cache when the rollback ran, so they *survived* it and were written
  afterwards — leaving ``fio_last_read_at``, ``fio_last_pull_at`` and the
  correct ``fio_last_movement_id`` on a journal with no lines. A run that was
  successful in every field an operator would check, and empty in the only one
  that mattered. Worse, it also meant a genuinely failed pull advanced the
  bookmark past movements it had thrown away, so the next run skipped them.

  The savepoint is now used as a **context manager** with the default
  ``flush=True``: ``__exit__`` passes ``rollback=exc_type is not None``, which
  is the intent, and ``_FlushingSavepoint`` flushes on release and clears the
  cache on rollback. Two regression tests, both of which fail against the old
  code: one asserts via ``search`` that the lines are still in the database
  after the cron, and one asserts that a pull failing after it wrote its
  bookmark does not keep it.

  The bug came in with the recovered ``_cron_pull_statements`` savepoint and
  was never exercised: every cron test asserted on call counts and the returned
  recordset, and none asked whether anything had persisted.

- **``fio_last_pull_at`` now means what it says.** It was written inside
  ``_fio_import_lines``, which returns early when there is nothing new, so an
  account that had simply been quiet showed a last pull weeks in the past —
  indistinguishable from a feed that had stopped, which is the one question the
  field exists to answer. It is stamped once per completed pull in
  ``fio_pull()``; ``fio_last_movement_id`` stays where it was, since it really
  is about what was imported.

[18.0.2.2.0] — 2026-08-31
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

[18.0.2.1.0] — 2026-08-31
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

[18.0.2.0.0] — 2026-08-31
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

[18.0.1.1.0] — 2026-08-25
-------------------------

Fixed
~~~~~

- **A failing account in the pull cron discarded every account already pulled
  in the same run.** ``_cron_pull_statements`` rolled back the whole
  transaction, so one bank failing late silently undid the successful imports
  before it. It now rolls back to a per-account ``SAVEPOINT``. A bare rollback
  is also forbidden inside a test, which is how it surfaced.


[18.0.1.0.0] — 2026-08-19
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
