=========
Changelog
=========

All notable changes to **account_fio** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.2.2.0] — 2026-09-02
-------------------------

Changed
~~~~~~~

- **The Fio banka section spans the full width of the journal form**, with the
  connection on the left and the statement settings ``account_statement_fio``
  adds on the right. A half-width section could only stack them and push the
  block off the fold. Both columns are titled by a ``string`` on the group
  itself rather than by a separator inside an untitled one, so they are
  guaranteed to render alike rather than merely similarly.

- **Both token-expiry fields now carry help text, and it says the useful
  thing**: Fio's API never reports an expiry, so the field can only be filled
  by hand, and an empty one is "unknown" rather than "never expires". The
  expiry cron cannot tell those apart and skips a blank one, so the warning
  does not fire and the feed stops without notice. The field is the only place
  a user finds this out.

Carried over from 18.0, where the work was done (18.0.2.3.0 - 18.0.2.7.0).

[Unreleased]
------------

[19.0.2.2.3] — 2026-09-13
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

[19.0.2.2.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak or Czech screen. The template and the catalogues now carry them,
  and the Slovak or Czech is written.

[19.0.2.2.1] — 2026-09-13
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
  accurate when written and is not any more. ``18.0-fio-api`` carries the whole
  of 19.0.1.1.0 and everything above it, and then went further: the journal
  collapse, the ``bank_statements_source`` registration and the cs/sk
  catalogues were written there first. The debt reversed direction, and this
  release is the 18.0 -> 19.0 port that settles it.

  Original note, kept for the record: everything under 19.0.1.1.0 plus the
  unreleased entries landed on ``19.0-fio-api`` only; a customer runs the 18.0
  copies vendored into its own repository, which already carried the
  19.0.1.1.0 fixes while the ``18.0-fio-api`` branch did not.

[19.0.2.1.0] — 2026-09-01
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

[19.0.2.0.0] — 2026-09-01
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

[19.0.1.2.0] — 2026-08-31
-------------------------

Fixed
~~~~~

- **A rejected token reached the user as "Internal server error".**
  ``action_test_connection`` let ``FioError`` escape unwrapped. It is a plain
  ``Exception``, not a ``UserError``, so over RPC the diagnosis — which is the
  entire value of that button — was stripped and the dialog said nothing. It
  now raises ``UserError`` the way the upload and pull paths already did.
  Found on a customer's staging database with a stale token.

[19.0.1.1.0] — 2026-08-24
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


[19.0.1.0.0] — 2026-08-19
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
