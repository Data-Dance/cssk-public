# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLineEcotax(models.Model):
    _inherit = "sale.order.line.ecotax"

    @api.depends(
        "sale_order_line_id.order_id.date_order",
        "sale_order_line_id.product_uom_id",
        "sale_order_line_id.product_uom_qty",
        "sale_order_line_id.company_id",
    )
    def _compute_ecotax(self):
        return super()._compute_ecotax()

    def _get_recycling_fee_context(self):
        """An order is priced at its order date. The invoice re-prices at its
        own date, because the invoice is the tax document the law is about."""
        self.ensure_one()
        line = self.sale_order_line_id
        order = line.order_id
        date = (
            fields.Date.to_date(order.date_order)
            if order.date_order
            else fields.Date.context_today(self)
        )
        pieces = line.product_uom_qty
        if line.product_uom_id and line.product_id.uom_id and (
            line.product_uom_id != line.product_id.uom_id
        ):
            pieces = line.product_uom_id._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id, round=False
            )
        return date, line.company_id or order.company_id, pieces
