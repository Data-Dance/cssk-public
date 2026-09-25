from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    is_advance_invoice_flow = fields.Boolean(
        string="Advance Invoice Flow",
        compute="_compute_is_advance_invoice_flow",
    )

    @api.depends('sale_order_ids')
    def _compute_is_advance_invoice_flow(self):
        for wizard in self:
            wizard.is_advance_invoice_flow = bool(wizard.sale_order_ids.filtered('is_advance_invoice'))

    @api.onchange('sale_order_ids', 'advance_payment_method')
    def _onchange_force_delivered_for_advance(self):
        for wizard in self:
            if wizard.is_advance_invoice_flow and wizard.advance_payment_method != 'delivered':
                wizard.advance_payment_method = 'delivered'

    def create_invoices(self):
        for wizard in self:
            if wizard.is_advance_invoice_flow:
                wizard.advance_payment_method = 'delivered'
        return super().create_invoices()
