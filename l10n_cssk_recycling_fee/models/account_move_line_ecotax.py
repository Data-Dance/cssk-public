# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLineEcotax(models.Model):
    _inherit = "account.move.line.ecotax"

    @api.depends(
        "account_move_line_id.move_id.invoice_date",
        "account_move_line_id.move_id.date",
        "account_move_line_id.product_uom_id",
        "account_move_line_id.quantity",
        "account_move_line_id.company_id",
        # so that a reset to draft prices the line afresh
        "account_move_line_id.parent_state",
    )
    def _compute_ecotax(self):
        return super()._compute_ecotax()

    def _recycling_fee_is_frozen(self):
        """Posted, and computed at least once (``rate_currency_id`` is only
        ever set by the statutory computation, so it tells a line that has a
        stored result from one that has none yet)."""
        self.ensure_one()
        return bool(
            self.account_move_line_id.parent_state == "posted"
            and self.rate_currency_id
        )

    def _get_recycling_fee_context(self):
        """The invoice is the tax document the fee is printed on, so its own
        date picks the rate — not the order date, which may be a tariff ago."""
        self.ensure_one()
        line = self.account_move_line_id
        move = line.move_id
        date = move.invoice_date or move.date or fields.Date.context_today(self)
        pieces = line.quantity
        if line.product_uom_id and line.product_id.uom_id and (
            line.product_uom_id != line.product_id.uom_id
        ):
            pieces = line.product_uom_id._compute_quantity(
                line.quantity, line.product_id.uom_id, round=False
            )
        return date, line.company_id or move.company_id, pieces
