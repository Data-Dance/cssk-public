# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools import SQL, sql


class Eet2Transaction(models.Model):
    _inherit = "l10n.cz.eet2.transaction"

    pos_order_id = fields.Many2one(
        "pos.order", string="POS Order", ondelete="set null", copy=False,
        index="btree_not_null",
        help="The point-of-sale order this message registers.")

    # The counterpart of the payment index: a POS order holds one live sale
    # message. The Python guard (``l10n_cz_eet2_transaction_id`` on the order)
    # can be raced by a sync and a resend, or two syncs of the same order from
    # two workers; the second INSERT then fails and is logged instead of
    # evidencing the sale twice. 18.0 has no ``models.UniqueIndex``, so the
    # partial index is created in ``init()`` like the base module's own.
    _POS_UNIQUE_INDEX = (
        "l10n_cz_eet2_transaction_one_live_sale_per_pos_order",
        "(pos_order_id) WHERE pos_order_id IS NOT NULL AND storno_of_id IS NULL "
        "AND reversed_by_id IS NULL",
    )

    def init(self):
        super().init()
        name, definition = self._POS_UNIQUE_INDEX
        if not sql.index_exists(self.env.cr, name):
            self.env.cr.execute(SQL(
                "CREATE UNIQUE INDEX %s ON %s %s",
                SQL.identifier(name), SQL.identifier(self._table), SQL(definition)))

    def _create_storno(self, **kw):
        kw.setdefault("pos_order_id", self.pos_order_id.id)
        return super()._create_storno(**kw)
