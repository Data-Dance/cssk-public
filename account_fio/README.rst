======================
Fio banka — connection
======================

The connection every Fio feature shares: the tokens generated in Fio internet
banking (Nastavení → API), held on the bank journal itself. Fio binds one token
to one account (§2) and Odoo already has exactly one record per bank account, so
there is no separate connection object to keep in step with the journal.

Configuration
=============

#. Generate a token in Fio internet banking. It is authorised with an SMS or a
   push notification, and becomes usable **five minutes** later.
#. Open the bank journal (Accounting → Configuration → Journals) and paste the
   token into its **Fio banka** section. Record its expiry date — Fio caps a
   token at 180 days and will not issue one without an expiry.
#. Accounting → Configuration → Fio banka lists every journal that carries a
   token, with both expiry dates, so a token about to die is visible without
   opening each journal in turn.
#. Press **Test connection**. Fio's answer is compared against the journal's own
   bank account, and a token belonging to a different account is refused.

Use two tokens
==============

* a **read** token (right *Sledování účtu*) for the statement pull, and
* a **submit** token (right *Sledování účtu a zadávání platebních a inkasních
  příkazů*) for payment orders.

The read token is the one in constant use and so the one with real exposure; a
token that can only read cannot pay anyone. Each token also carries its own
30-second call budget, so splitting them doubles the throughput.

Both fields are readable by administrators only. Fio carries the token **in the
URL path**, which is exactly where credentials end up in logs, so the API client
masks it in everything it raises or logs.

Why the throttle exists
=======================

Fio allows one call per token every 30 seconds, whatever the format, for reading
or writing (§5.2). Everything goes through ``account.journal._fio_call()``, which
waits out the remainder of the interval under a PostgreSQL **advisory** lock
keyed on the journal, so a cron pull and somebody pressing *Send to Fio* cannot
answer each other's ``409``.

The lock is advisory rather than ``SELECT ... FOR UPDATE`` on the journal row on
purpose: a row lock would pin a core ``account_journal`` row for as long as the
call floor — up to 30 seconds, once an hour from the cron — and every unrelated
write to that journal would queue behind it with nothing in the UI to explain
why. This is the same mechanism core uses to serialise on a logical key.

An interactive caller is never made to wait a full interval — it is told when the
next call is possible instead. The cron waits.

Known limitations
=================

* The "last call" timestamp is written before the call. If the request fails the
  transaction rolls back and the stamp is lost, so the next attempt may hit a
  ``409`` — which arrives as an explanatory message, not as silence.
* Fio operates no test environment, so the live behaviour can only be confirmed
  against a real account.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
