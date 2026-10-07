# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Turn the stored unmapped-account text into rows.

``unmapped_note`` was a pre-formatted ``"code  balance"`` line per account;
it is now derived from ``cssk.fs.statement.unmapped`` rows, which carry the
account and the amount as money. A statement that has left draft cannot be
recomputed, so its report has to be carried over here or it would open empty
while ``unmapped_count`` still says otherwise.

The note held the account's own code (the statement account mapping came
later), so each row is resolved by that code within the statement's company.
A code no account carries any more keeps its row, without an account.
"""

import logging

from odoo import SUPERUSER_ID, Command, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'cssk_fs_statement'
           AND column_name = 'unmapped_note'
    """)
    if not cr.fetchone():
        return
    cr.execute("""
        SELECT id, unmapped_note FROM cssk_fs_statement
         WHERE unmapped_note IS NOT NULL AND unmapped_note != ''
    """)
    notes = cr.fetchall()
    env = api.Environment(cr, SUPERUSER_ID, {})
    converted = 0
    for statement_id, note in notes:
        stmt = env["cssk.fs.statement"].browse(statement_id)
        Account = env["account.account"].with_company(stmt.company_id)
        rows = []
        for seq, line in enumerate(note.splitlines()):
            parts = line.split()
            if len(parts) < 2:
                continue
            code = parts[0]
            try:
                balance = float(parts[1])
            except ValueError:
                continue
            accounts = Account.search([
                ("company_ids", "in", stmt.company_id.id),
                ("code", "=", code),
            ])
            rows.append(Command.create({
                "sequence": seq, "code": code, "balance": balance,
                "account_ids": [Command.set(accounts.ids)],
            }))
        if rows:
            stmt.unmapped_line_ids = rows
            converted += 1
    cr.execute("ALTER TABLE cssk_fs_statement DROP COLUMN unmapped_note")
    _logger.info(
        "l10n_cssk_fs_base 19.0.1.8.0: unmapped-account notes of %s "
        "statement(s) converted to rows", converted)
