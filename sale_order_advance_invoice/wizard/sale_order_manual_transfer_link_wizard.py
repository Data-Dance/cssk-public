from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderManualTransferLinkWizard(models.TransientModel):
    _name = "sale.order.manual.transfer.link.wizard"
    _description = "Link Manual Bank Transfer to Sale Order"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="sale_order_id.company_id",
        readonly=True,
    )
    commercial_partner_id = fields.Many2one(
        "res.partner",
        related="sale_order_id.partner_invoice_id.commercial_partner_id",
        readonly=True,
    )
    payment_id = fields.Many2one(
        "account.payment",
        string="Manual Payment",
        required=True,
        domain="""
            [
                ('company_id', '=', company_id),
                ('partner_id', 'child_of', commercial_partner_id),
                ('payment_type', '=', 'inbound'),
                ('state', 'in', ('in_process', 'paid')),
                ('payment_transaction_id', '=', False),
                ('invoice_ids', '=', False),
                ('reconciled_invoice_ids', '=', False)
            ]
        """,
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("active_model") == "sale.order" and self.env.context.get("active_id"):
            values.setdefault("sale_order_id", self.env.context["active_id"])
        return values

    def action_link_manual_transfer(self):
        self.ensure_one()
        sale_order = self.sale_order_id
        payment = self.payment_id

        if payment.partner_id.commercial_partner_id != sale_order.partner_invoice_id.commercial_partner_id:
            raise UserError(_("The selected payment does not belong to the sale order customer."))
        if payment.company_id != sale_order.company_id:
            raise UserError(_("The selected payment must belong to the same company as the sale order."))
        if payment.payment_transaction_id:
            raise UserError(_("The selected payment is already linked to a payment transaction."))
        if payment.invoice_ids or payment.reconciled_invoice_ids:
            raise UserError(_("The selected payment is already linked to an invoice."))

        if sale_order.transaction_ids.filtered(lambda tx: tx.payment_id == payment):
            raise UserError(_("This payment is already linked to the sale order."))

        tx = sale_order._link_payment_to_transaction(payment)

        # Confirm the sale order if it's still in draft state
        if sale_order.state in ("draft", "sent"):
            sale_order.action_confirm()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Manual Transfer Linked"),
                "message": _(
                    "Payment %(payment)s is now linked to %(order)s via transaction %(tx)s.",
                    payment=payment.display_name,
                    order=sale_order.name,
                    tx=tx.reference,
                ),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }