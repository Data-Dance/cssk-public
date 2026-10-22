=========
Changelog
=========

All notable changes to **account_fio** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.2.7.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **The left column's heading moves to the top of the column, and is now the
  same construct as the right one's.** 18.0.2.5.0 put "Settings" on a
  ``separator`` partway down, leaving the tokens above it unheaded — so one
  column began with a heading and the other with a run of fields, which read
  as two different kinds of thing side by side.

  ``fio_connection`` now carries ``string="Settings"`` exactly as
  ``fio_statements`` carries ``string="Bank statements"``. Same construct, so
  the columns are guaranteed to render alike rather than merely similarly, and
  each starts with its own title. The tokens sit under it, which is where they
  belong: a token is configuration.

  "What Fio reports about this account" stays a ``separator`` — it is a
  subdivision *within* the column, not a peer of the two column titles, and the
  difference in weight is now meaningful rather than accidental.

[18.0.2.6.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **Both token-expiry fields now carry help text, and it says the useful
  thing.** ``fio_token_write_expiry`` had none at all; both now explain that
  the date is recorded by hand because Fio's API never reports it, and that
  leaving it empty means the expiry warning cannot fire.

Known limitations
~~~~~~~~~~~~~~~~~

- **A token with no expiry recorded gets no warning, by decision.**
  ``_fio_cron_check_token_expiry`` skips a blank expiry (``if not expiry:
  continue``), so a token whose date nobody typed in is invisible to the very
  cron meant to stop the feed dying silently. Empty here means *unknown*, not
  *never expires* — Fio refuses to issue a token without an expiry and caps it
  at 180 days (§2), so the death date exists at the bank whether or not Odoo
  knows it.

  This is live, not theoretical: all three configured journals on a
  customer's staging build have tokens and blank expiries, because the values were
  migrated from a Studio field that carried the token and not the date. Anyone
  migrating the same way lands in the same state.

  Warning on the unknown case, and requiring the date when a token is set, were
  both considered on 2026-09-01 and **declined** — the second would refuse to
  save existing records for an unrelated edit. The help text is the mitigation.
  Recorded here so the next person to notice knows it was weighed rather than
  missed, and does not silently change the behaviour.

[18.0.2.5.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **The left column's middle block is headed "Settings"**, so it reads as a
  sibling of the right column's "Bank statements" rather than as an unlabelled
  run of fields. It covers the download format and the two last-call
  timestamps — the same grouping the pre-collapse ``fio.account`` form used.

  A ``separator`` rather than a nested ``group``: the column is already the
  second level of nesting and a third renders as an unusably narrow
  sub-column, which is why this section was flattened to begin with. The
  heading is visually the same as the group string opposite it.

[18.0.2.4.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **The Fio banka section spans the full width of the journal form.**
  ``colspan="2"`` over both columns of core's enclosing group, the same way
  sale's ``sale_total`` does. The buttons and the explanatory notes span the
  whole section; the connection fields become its left column, and
  ``account_statement_fio`` fills the right one. Half a form's width could only
  stack those two sets and push the block off the fold.

[18.0.2.3.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **Credential masking is applied at the sinks as well as at the source.**
  ``fio_upload_mixin`` passed ``str(exception)`` straight into the stored
  ``fio_response`` field, the chatter, the on-screen alert and a ``UserError``;
  ``action_fio_test_connection`` did the same in its ``FioError`` wrap. All now
  go through ``mask_token``.

  This is **hardening, not a disclosure**. Every ``FioError`` is already masked
  where the client raises it (``utils/client.py`` calls ``self._mask`` in
  ``_get``, ``_check`` and ``import_orders``), and all of these sinks catch
  ``FioError`` or narrower, so they receive text that is already clean. Traced
  before landing: the only handler catching bare ``Exception`` is the pull
  cron, and that one was already masked.

  What it buys is independence from a clause nobody is watching. The current
  guarantee holds only while every ``except`` here stays narrower than
  ``Exception``; widen one later, or have a library raise between the lock and
  the client's own ``try``, and unmasked text reaches a stored field or a
  chatter with no warning at all.

  Note what it does **not** do: the sink has no token in hand, so it masks by
  pattern (``/rest/<endpoint>/<token>``) only. Token-aware masking stays in the
  client, which is the layer that knows the value. For the upload path that is
  the right division anyway — Fio takes the submit token in the POST **body**,
  not the URL, so an upload error has no token-bearing URL to leak in the first
  place.

  A regression test covering the stored field lives in
  ``account_payment_fio_batch``, which is where the upload path can actually be
  exercised end to end.

  Ported from 19.0 (417267d), where it was written; severity re-checked here
  rather than carried across, and downgraded.
Carry-over to 19.0
~~~~~~~~~~~~~~~~~~

- **The ``fio.account`` -> ``account.journal`` collapse (18.0.2.0.0) has not
  been done on 19.0**, which still carries ``models/fio_account.py``. It takes
  the advisory lock with it (``pg_try_advisory_xact_lock(classid, objid)``
  replacing ``SELECT ... FOR UPDATE NOWAIT``), which is worth having on 19.0
  even if the collapse itself is declined there.
- **cs/sk catalogues (18.0.2.2.0) are absent on 19.0**; no module in the Fio
  family has an ``i18n/`` directory on that branch. They are reproducible with
  ``tools/i18n_export_offline.py``, which also exists only on 18.0.

[18.0.2.2.0] — 2026-09-01
-------------------------

Fixed
~~~~~

- **6 view terms were missing from the translation catalogues.** The offline
  exporter read only the first child of a view's ``arch``, and an inherited
  view normally has one top-level node per xpath — so every term after the
  first was silently absent. Among them were the alert telling an operator that
  the bank's answer to an upload was lost, and the 90-day history-unlock
  instruction: precisely the messages whose whole value is being read under
  time pressure. Fixed in ``tools/i18n_export_offline.py`` and re-exported.

[18.0.2.1.0] — 2026-08-31
-------------------------

Added
~~~~~

- **Czech and Slovak translations** (61 terms). The module had no ``i18n/``
  directory at all.

  These are English-source UI strings with no statutory wording, so per the
  repository convention they get English source plus ``cs.po`` / ``sk.po``
  rather than national-language source. Terms quoting Fio's own interface are
  left verbatim in **both** languages — the API rights ``Sledování účtu`` and
  ``Sledování účtu a zadávání platebních a inkasních příkazů``, the menu path
  ``Nastavení → API``, ``ID pohybu`` / ``ID pokynu`` — because Fio's API
  documentation and its internet banking are in Czech for Slovak accounts too,
  and translating them would name something the user cannot find on screen.

  The long safety messages got the most care, because they are the point of
  the module: the throttle refusal, the wrong-account refusal, the token-expiry
  activity, and the lost-answer wording that tells an operator to go and look
  in internet banking before sending anything.

  Exported with ``tools/i18n_export_offline.py``: ``odoo-bin i18n export``
  needs a database and there is none here. Verified by reading each catalogue
  back through Odoo's own ``PoFileReader`` — every entry resolves to a record
  reference, none is untranslated — and with ``msgfmt --check``.

[18.0.2.0.0] — 2026-08-31
-------------------------

Changed
~~~~~~~

- **``fio.account`` is gone; the tokens live on ``account.journal``.** It was a
  strict 1:1 extension table — ``journal_id`` required and unique — plus about
  thirty lines of ``account_journal.py`` whose only job was to fake delegation.
  Fio binds one token to one account (§2) and Odoo already has exactly one
  record per bank account. Every field is now on the journal under a ``fio_``
  prefix: ``fio_token_read`` / ``fio_token_write`` and their expiries,
  ``fio_download_format``, ``fio_last_read_at`` / ``fio_last_write_at``, and the
  five read-only fields recording what Fio reports.

  The chatter and the token-expiry activities come along, and are better off:
  ``account.journal`` already inherits ``mail.thread`` and
  ``mail.activity.mixin``, and the journal is where an accountant looks.

  Renamed with it: ``_call`` → ``_fio_call``, ``_token`` → ``_fio_token``,
  ``_lock`` → ``_fio_lock``, ``_stamp`` → ``_fio_stamp``, ``_wait_for_slot`` →
  ``_fio_wait_for_slot``, ``action_test_connection`` →
  ``action_fio_test_connection``, ``_cron_check_token_expiry`` →
  ``_fio_cron_check_token_expiry``. Generic names are fine on a model of one's
  own and reckless on ``account.journal``.

  **There is no migration.** The staging build is expendable and these modules
  run nowhere else; the table is simply dropped.

- **The row lock became a PostgreSQL advisory lock.** ``_fio_lock`` used
  ``SELECT ... FOR UPDATE NOWAIT`` and then slept up to 30 seconds holding the
  row to the end of the transaction. Doing that to a core ``account_journal``
  row once an hour from the cron would block every unrelated write to that
  journal, with nothing in the UI to explain the wait.
  ``pg_try_advisory_xact_lock(hashtext(...))`` keyed on the journal serialises
  the token while pinning no row at all, releases at the same moment, and needs
  no savepoint — a failed ``NOWAIT`` aborts the transaction, an advisory
  ``try`` merely returns false. It is what core uses for the same problem
  (``mail.thread``).

  The key uses the **two-argument** ``pg_try_advisory_xact_lock(classid,
  objid)`` rather than the usual ``hashtext(...)`` into the single-key space.
  ``hashtext`` is a 32-bit hash into a namespace shared with every other
  single-key user in the database, so an unrelated subsystem can collide with
  us and the symptom would be a Fio call spuriously refused as "another Fio
  operation is running". With a classid of our own and the journal id as the
  objid the key is exact, and the only thing that can contend for it is another
  Fio call on the same journal.

- The **Accounting → Configuration → Fio banka** menu is kept, now listing the
  journals that carry a Fio token, with both token expiry dates and the last
  read. One screen showing every connection is what reveals a dead token before
  a payment run does.

Removed
~~~~~~~

- ``fio.account.active``. A connection could be archived without archiving its
  journal; there is no separate record to archive any more. Clearing the token
  (and, from the next release, the journal's bank-feed source) covers the
  practical case, but this is a real capability being dropped rather than an
  oversight.
- Both ``fio.account`` ACL rows, and the module's ``ir.model.access.csv`` with
  them. The journal's own ACLs apply, and the tokens stay field-gated to
  ``base.group_system``.
- The Fio stat button in the journal's button box, which pointed at the
  connection record.

[18.0.1.2.0] — 2026-08-31
-------------------------

Fixed
~~~~~

- **A rejected token showed as "Internal server error".** ``FioError`` is a
  plain ``Exception``, so letting it escape *Test connection* stripped off the
  diagnosis — which is the entire value of that button. It is now wrapped in a
  ``UserError``, matching what the upload and pull paths already did. Found on
  a customer's staging database with a stale token, which now says "Fio rejected the token as
  unknown, expired or inactive".

[18.0.1.1.0] — 2026-08-25
-------------------------

Fixed
~~~~~

- **The interactive throttle guard was unreachable.** ``MAX_INTERACTIVE_WAIT``
  was 35 seconds against a 30-second call floor, so ``wait >
  MAX_INTERACTIVE_WAIT`` could never be true: a user pressing *Pull* or *Send
  to Fio* inside the interval was silently frozen for up to 30 seconds instead
  of being told when to come back. Lowered to 5 seconds. The ``account_fio``
  suite dropped from 63 s to 3.4 s once it stopped really sleeping — which is
  how this was found.
- **The currency check was off for most journals.** It compared
  ``self.currency_id``, which a bank journal carries only when it *differs*
  from the company currency, so a Fio account kept in a different currency than
  the journal went unnoticed on every journal in the company currency. It now
  falls back to the company currency.


[18.0.1.0.0] — 2026-08-19
-------------------------

Added
~~~~~

- ``fio.account``: one Fio connection per bank journal — read and submit tokens
  (administrator-only), the 30-second per-token throttle with a row lock, a
  *Test connection* action that refuses a token belonging to another account,
  and a daily cron that raises an activity before a token expires.
- ``fio.upload.mixin``: the payment-file upload shared by the Community and
  Enterprise bridges, including the ``unknown`` state for an upload whose
  answer was lost, and format sniffing so Fio XML, pain.001, pain.008 and ABO
  files can all be sent by the same button.
- ``res.partner.fio_payment_reason``: the ČNB platební titul default.
