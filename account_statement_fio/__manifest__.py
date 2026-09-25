# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Fio banka — bank statements",
    "summary": "Pull movements and official statements from the Fio banka API "
               "into bank journals. Community and Enterprise alike.",
    "description": """
Fio banka — bank statements
===========================

Pulls transactions straight from Fio into the bank journal, on a schedule.
One code path for Community and Enterprise: it builds on core ``account`` and
on the OCA ``account_statement_import_base`` (LGPL) for the duplicate key and
the partner-matching hooks, and needs neither Enterprise's bank feeds nor the
AGPL online-import framework.

Three pull modes
----------------

**Movements** (default) — ``/rest/periods/``. Re-reads the last few days on
every run and drops what it already has, so a missed cron, a restart or an
operator mistake cannot leave a hole.

**Official statements** — ``/rest/lastStatement/`` then ``/rest/by-id/``.
Produces a real ``account.bank.statement`` named with the bank's own statement
number and carrying its opening and closing balance, so the books reconcile
against the document Fio issues. This is the mode to use for the accounting
close.

**Since the bookmark** — ``/rest/last/``. Efficient and gapless, but the
bookmark is server-side state *on the token*: a second consumer of the same
token silently eats movements this one will never see. Off by default.

Backfill
--------

The pull wizard chunks a date range and refuses to reach past 90 days until you
confirm the history has been unlocked in internet banking — that unlock lasts
ten minutes (§3.1), so it has to be done immediately before the run, not
whenever somebody gets round to it.

Payment symbols
---------------

VS/KS/SS are written to ``variable_symbol`` / ``constant_symbol`` /
``specific_symbol`` when a module providing them is installed
(``l10n_cssk_payment_symbols``), and are always kept as ``VS:``-style tokens in
the label, so matching works either way — the same arrangement as
``account_statement_import_gpc``.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.2.3.3",
    "license": "AGPL-3",
    "depends": ["account_fio", "account_fio_base", "account_statement_import_base"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "wizard/fio_statement_pull_views.xml",
        "views/account_journal_views.xml",
        "views/account_bank_statement_line_views.xml",
    ],
    "installable": True,
}
