# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_l10n_sk_fuel_split(self):
        self.ensure_one()
        if self.move_type not in ("in_invoice", "in_refund"):
            raise UserError(_("Fuel splitting applies to vendor bills."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Split fuel (§ 19 ods. 2 písm. l)"),
            "res_model": "l10n.sk.fuel.split",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }
