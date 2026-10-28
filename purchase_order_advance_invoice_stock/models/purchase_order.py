# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _create_picking(self):
        """Never receive goods on a received advance invoice.

        An advance carries the real products (the supplier's proforma lists
        them), and paying it confirms it, so ``purchase_stock`` would open a
        receipt for goods the parent purchase order already expects: two
        receipts for one delivery, and stock counted twice if both are
        validated. Receiving belongs to the parent order.
        """
        return super(
            PurchaseOrder, self.filtered(lambda o: not o.is_advance_invoice)
        )._create_picking()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _create_or_update_picking(self):
        # Adding a line or raising a quantity on a confirmed order goes this
        # way rather than through _create_picking.
        return super(
            PurchaseOrderLine,
            self.filtered(lambda line: not line.order_id.is_advance_invoice),
        )._create_or_update_picking()
