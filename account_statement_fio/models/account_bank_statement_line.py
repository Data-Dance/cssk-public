# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    fio_movement_id = fields.Char(
        string="Fio Movement ID",
        readonly=True,
        copy=False,
        index="btree_not_null",
        help="Fio's ID pohybu — unique per movement, and the key this "
             "integration deduplicates on.",
    )
    fio_instruction_id = fields.Char(
        string="Fio Instruction ID",
        readonly=True,
        copy=False,
        help="Fio's ID pokynu. NOT unique: a transfer and its fee share one, "
             "and so do a payment and its later reversal — which is why it is "
             "never used for duplicate detection. It is also a different "
             "number from the batch id returned when a payment order is "
             "uploaded, so it cannot link a statement line back to a payment "
             "order either.",
    )
