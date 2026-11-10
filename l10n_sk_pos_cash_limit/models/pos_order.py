# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from odoo.addons.l10n_sk_invoice.models.account_payment import _limit_warning


class PosOrder(models.Model):
    _inherit = "pos.order"

    l10n_sk_cash_limit_warning = fields.Char(
        compute="_compute_l10n_sk_cash_limit_warning",
    )

    @api.depends("payment_ids.amount", "payment_ids.payment_method_id", "date_order")
    def _compute_l10n_sk_cash_limit_warning(self):
        """§ 4 ods. 1: one receipt is one payment; change is netted off."""
        for order in self:
            cash = sum(
                order.payment_ids.filtered("payment_method_id.is_cash_count").mapped("amount")
            )
            order.l10n_sk_cash_limit_warning = _limit_warning(
                self.env, order.company_id,
                order.currency_id or order.company_id.currency_id, cash,
                fields.Date.to_date(order.date_order), 0.0,
            )
