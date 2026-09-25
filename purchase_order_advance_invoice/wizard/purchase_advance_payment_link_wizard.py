from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseAdvancePaymentLinkWizard(models.TransientModel):
    _name = "purchase.advance.payment.link.wizard"
    _description = "Link Existing Payment to Received Advance Invoice"

    order_id = fields.Many2one(
        "purchase.order",
        string="Advance Invoice",
        required=True,
        readonly=True,
    )
    payment_id = fields.Many2one(
        "account.payment",
        string="Payment",
        required=True,
        domain="[('id', 'in', available_payment_ids)]",
        help="Outbound payment already booked against the paid-advances "
        "clearing account.",
    )
    available_payment_ids = fields.Many2many(
        "account.payment", compute="_compute_available_payment_ids"
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get(
            "active_model"
        ) == "purchase.order" and self.env.context.get("active_id"):
            values.setdefault(
                "order_id", self.env.context["active_id"]
            )
        return values

    @api.depends("order_id")
    def _compute_available_payment_ids(self):
        Payment = self.env["account.payment"]
        for wizard in self:
            order = wizard.order_id
            if not order:
                wizard.available_payment_ids = Payment
                continue
            linked = self.env["purchase.order"].search([
                ("is_advance_invoice", "=", True),
            ]).advance_payment_ids
            wizard.available_payment_ids = Payment.search([
                ("payment_type", "=", "outbound"),
                ("partner_type", "=", "supplier"),
                ("state", "in", ("in_process", "paid")),
                ("company_id", "=", order.company_id.id),
                (
                    "partner_id",
                    "=",
                    order.partner_id.commercial_partner_id.id,
                ),
                ("id", "not in", linked.ids),
            ])

    def action_link(self):
        self.ensure_one()
        if not self.payment_id:
            raise UserError(_("Select a payment to link."))
        self.order_id._link_advance_payment(self.payment_id)
        return {"type": "ir.actions.act_window_close"}
