# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Fio banka — connection",
    "summary": "Fio banka API tokens per bank journal, with the mandatory "
               "30-second throttle and token-expiry watch.",
    "description": """
Fio banka — connection
======================

The connection every Fio feature shares: the API tokens generated in Fio
internet banking (Nastavení → API), held on the bank journal itself.

Why the tokens live on the journal
----------------------------------

Fio binds one token to one account (§2), and Odoo already has exactly one
record per bank account — the journal. A separate model would be a strict 1:1
extension table of it, and the journal is where an accountant looks; it also
already carries the chatter and the activities this module posts to.

Fio's 30-second call floor is a property of the **token**, not of the feature
using it (§5.2). Statement pulling and payment submission would otherwise trip
over each other and answer ``409``. Every call goes through
``account.journal._fio_call()``, which takes a PostgreSQL advisory lock keyed
on the journal and waits out the remainder of the interval — an advisory lock
rather than ``SELECT ... FOR UPDATE`` precisely because pinning a core journal
row for up to 30 seconds, once an hour, would block unrelated writes for
reasons nothing in the UI could explain.

Two tokens, on purpose
----------------------

* **Read token** — right "Sledování účtu". Used by the hourly statement pull,
  so it is the one with real exposure. If it leaks, it reads.
* **Submit token** — right "Sledování účtu a zadávání platebních a inkasních
  příkazů". Used only when somebody presses *Send to Fio*.

They are separate fields because a token that can only read cannot pay anyone,
and because each token carries its own 30-second budget.

Both are readable by administrators only (``base.group_system``): Fio carries
the token in the URL path, which is exactly where credentials get logged.

Token expiry
------------

Fio refuses to issue a token without an expiry, and caps it at 180 days (§2).
A daily cron raises an activity two weeks before either token dies, because the
alternative is finding out when the bank feed has been silently stale for a
week.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.2.2.3",
    "license": "AGPL-3",
    "depends": ["account", "account_fio_base"],
    "data": [
        "data/ir_cron.xml",
        "views/account_journal_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
