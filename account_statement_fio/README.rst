===========================
Fio banka — bank statements
===========================

Pulls transactions from Fio straight into the bank journal, on a schedule. One
code path for Community and Enterprise.

Turning it on
=============

Set the journal's **Bank Feeds** to *Fio banka API*. That single radio is what
the scheduled pull keys on, so there is no second switch to leave in the wrong
position.

``bank_statements_source`` is a Community field — core declares it with one
entry, ``undefined``, and Enterprise's ``account_online_synchronization`` merely
appends ``online_sync`` to it — so registering ``fio`` there costs nothing on
either edition and keeps this module's one-code-path premise.

It also makes Fio and Odoo's own bank feed **mutually exclusive by
construction**: the field is single-valued, and Enterprise already overrides
``write()`` so that moving the source away from ``online_sync`` detaches the
online account and flags the link. Nothing here shares a deduplication key with
that feed, so two feeds on one journal means every transaction twice; before
this, avoiding that was a runbook step rather than something the data model
enforced.

Two things come free with it: a journal fed by Fio stops being nagged to
"connect your bank" on the Accounting dashboard, which only prompts for
``undefined`` and ``online_sync``; and a Fio dashboard block becomes available
should a "last pulled" line ever be wanted.

A journal set to Fio with no read token is refused at save time — the
alternative is an hourly failure posted to its chatter that nobody reads.

The **tokens** themselves are not gated on the bank feed. A Fio token is a
credential for the account, not for the statement feed: a journal may be used
for Fio *payments* while its statements arrive some other way, and hiding the
token behind this radio would leave it unreachable.

Modes
=====

**Movements** (default) — ``/rest/periods/``. Every run re-reads the last few
days and drops what Odoo already has, so a missed cron or a restart cannot leave
a hole. Idempotent by construction.

**Official statements** — ``/rest/lastStatement/`` then ``/rest/by-id/``. Each
becomes an ``account.bank.statement`` named with the bank's own statement number
and carrying its opening and closing balance, so Odoo's balance check compares
against the document Fio issues. Use this for the accounting close.

**Since the bookmark** — ``/rest/last/``. Gapless and cheap, but the bookmark is
server-side state *on the token*: anything else reading movements with that same
token moves it, and those movements never arrive here. Off by default.

Backfill
========

*Pull a range…* chunks the range into months and tells you up front how many
calls that is — at one call per 30 seconds, a year is a six-minute operation.

Reaching further back than 90 days needs the full history unlocked for the token
in internet banking (Nastavení → API, the padlock). **That unlock lasts ten
minutes**, so the wizard refuses to start until you confirm you have just done
it, rather than letting the run fail on a ``422`` afterwards.

What lands on a statement line
==============================

======================================  ==========================================
Fio                                     Odoo
======================================  ==========================================
ID pohybu (22)                          ``unique_import_id``, ``fio_movement_id``
Datum (0)                               ``date`` — the ``+02:00`` offset is
                                        discarded; these are booking dates, and a
                                        UTC round trip moves half of them a day
Objem (1)                               ``amount``
Protiúčet + Kód banky (2, 3)            ``account_number``, then partner matching
Název protiúčtu (10)                    ``partner_name``
KS / VS / SS (4, 5, 6)                  the symbol fields, plus ``VS:`` tokens in
                                        the label
Zpráva pro příjemce → Komentář →        ``payment_ref`` (first non-empty)
Uživatelská identifikace → Typ
Typ (8)                                 ``transaction_type``
Reference plátce (27)                   ``ref``
ID pokynu (17)                          ``fio_instruction_id``
======================================  ==========================================

``ID pokynu`` is deliberately **not** used for duplicate detection: a transfer
and its fee share one, and so do a payment and its later reversal. Deduplicating
on it would silently drop storno movements and leave the balance wrong.

Known limitations
=================

* **Switching from GPC files to the API does not deduplicate across the two.**
  ``account_statement_import_gpc`` derives its import key from the GPC record,
  this module from Fio's movement id, and the two cannot be compared. Switch at a
  date boundary: import the last GPC statement, then start the pull the next day.
* A Fio account is single-currency, so a movement should always be in the
  journal's currency. If one is not, it is imported as delivered and a warning is
  logged rather than guessing at ``foreign_currency_id`` — the original text is
  kept in ``raw_data``. This case needs confirming against a live account.
* On Enterprise this brings in two OCA LGPL base modules
  (``account_statement_base``, ``account_statement_import_base``) for the import
  key and the partner-matching hooks.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
