from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveLinkPurchaseAdvanceWizard(models.TransientModel):
    _name = "account.move.link.purchase.advance.wizard"
    _description = "Deduct Received Advance Invoices on a Vendor Bill"

    move_id = fields.Many2one(
        "account.move",
        string="Vendor Bill",
        required=True,
        readonly=True,
    )
    advance_ids = fields.Many2many(
        "purchase.order",
        string="Advance Invoices",
        required=True,
        domain="[('id', 'in', available_advance_ids)]",
    )
    available_advance_ids = fields.Many2many(
        "purchase.order",
        compute="_compute_available_advance_ids",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get(
            "active_model"
        ) == "account.move" and self.env.context.get("active_id"):
            values.setdefault("move_id", self.env.context["active_id"])
        return values

    @api.depends("move_id")
    def _compute_available_advance_ids(self):
        Order = self.env["purchase.order"]
        for wizard in self:
            move = wizard.move_id
            if not move:
                wizard.available_advance_ids = Order
                continue
            candidates = Order.search([
                ("is_advance_invoice", "=", True),
                ("company_id", "=", move.company_id.id),
                ("state", "!=", "cancel"),
                (
                    "partner_id.commercial_partner_id",
                    "=",
                    move.partner_id.commercial_partner_id.id,
                ),
            ])
            wizard.available_advance_ids = candidates.filtered(
                lambda order: order.currency_id.compare_amounts(
                    order._advance_remaining_to_deduct(), 0.0
                )
                > 0
            )

    def action_link(self):
        self.ensure_one()
        move = self.move_id
        if move.state != "draft" or move.move_type != "in_invoice":
            raise UserError(
                _("Advances can only be deducted on a draft vendor bill.")
            )
        for advance in self.advance_ids:
            for vals in advance._prepare_advance_deduction_line_vals(move):
                move.invoice_line_ids = [(0, 0, vals)]
        return {"type": "ir.actions.act_window_close"}
