# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CSSKReceipt(models.Model):
    _inherit = "cssk.receipt"

    l10n_sk_ekasa_okp = fields.Char(
        string="OKP", copy=False,
        help="Overovací kód podnikateľa, as returned by the service. Stored "
             "upper-cased: the service emits it in either case.")
    l10n_sk_ekasa_is_paragon = fields.Boolean(
        string="Paragón", copy=False,
        help="A substitute receipt written out while the till was out of "
             "service.")
    l10n_sk_ekasa_call_ids = fields.One2many(
        "sk.ekasa.call", "receipt_id", string="Verification calls")
    l10n_sk_ekasa_call_count = fields.Integer(
        compute="_compute_l10n_sk_ekasa_call_count")

    def _compute_l10n_sk_ekasa_call_count(self):
        grouped = {}
        if self.ids:
            for group in self.env["sk.ekasa.call"]._read_group(
                    [("receipt_id", "in", self.ids)],
                    groupby=["receipt_id"], aggregates=["__count"]):
                grouped[group[0].id] = group[1]
        for receipt in self:
            receipt.l10n_sk_ekasa_call_count = grouped.get(receipt.id, 0)

    def action_l10n_sk_ekasa_open_calls(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Verification calls"),
            "res_model": "sk.ekasa.call",
            "view_mode": "list,form",
            "domain": [("receipt_id", "=", self.id)],
        }
