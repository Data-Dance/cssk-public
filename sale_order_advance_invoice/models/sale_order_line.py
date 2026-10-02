from odoo import api, fields, models
from odoo.fields import Command
from odoo.tools.misc import format_date


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_downpayment_description(self):
        if not self.order_id.is_advance_invoice:
            return super()._get_downpayment_description()

        env = self.order_id.with_context(lang=self.order_id.partner_id.lang).env

        if self.display_type:
            return env._("Tax Documents")

        dp_state = self._get_downpayment_state()
        if dp_state == 'draft':
            return env._(
                "Tax Document: %(date)s (Draft)",
                date=format_date(env, self.create_date.date()),
            )
        if dp_state == 'cancel':
            return env._("Tax Document (Cancelled)")

        invoice = self._get_invoice_lines().filtered(
            lambda aml: aml.quantity >= 0
        ).move_id.filtered(lambda move: move.move_type == 'out_invoice')
        if len(invoice) == 1 and invoice.payment_reference and invoice.invoice_date:
            return env._(
                "Tax Document (ref: %(reference)s on %(date)s)",
                reference=invoice.payment_reference,
                date=format_date(env, invoice.invoice_date),
            )
        return env._("Tax Document")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_advance_tracking'):
                vals['discount'] = 0.0
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if vals.get('is_advance_tracking') or ('discount' in vals and any(self.mapped('is_advance_tracking'))):
            vals['discount'] = 0.0
        return super().write(vals)

    is_advance_tracking = fields.Boolean(
        string="Advance Tracking Line",
        default=False,
        copy=False,
    )
    advance_source_order_id = fields.Many2one(
        "sale.order",
        string="Advance Source Order",
        ondelete="set null",
        copy=False,
    )
    advance_tracking_amount = fields.Monetary(
        string="Advance Amount",
        compute="_compute_advance_tracking_amount",
        currency_field="currency_id",
    )

    @api.depends('is_advance_tracking', 'price_unit')
    def _compute_advance_tracking_amount(self):
        for line in self:
            line.advance_tracking_amount = line.price_unit if line.is_advance_tracking else 0.0

    @api.depends(
        'state',
        'display_type',
        'qty_invoiced',
        'advance_source_order_id.advance_invoice_paid_date',
        'advance_source_order_id.state',
    )
    def _compute_qty_to_invoice(self):
        super()._compute_qty_to_invoice()
        for line in self.filtered('is_advance_tracking'):
            if line.state != 'sale' or line.display_type:
                line.qty_to_invoice = 0.0
            elif not line.advance_source_order_id or line.advance_source_order_id.state == 'cancel':
                line.qty_to_invoice = 0.0
            elif line.advance_source_order_id.advance_invoice_paid_date and line.qty_invoiced >= 0:
                line.qty_to_invoice = -1.0
            else:
                line.qty_to_invoice = 0.0

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        self.ensure_one()

        advance = self.advance_source_order_id
        if not self.is_advance_tracking or not advance:
            return res

        company = self.order_id.company_id
        net_account = advance._get_advance_invoice_net_account()

        # Determine whether the advance already has a posted tax document.
        # The accounting treatment of the settlement deduction differs:
        #   • With tax document    → debit the net received-advance account and
        #                            keep taxes so Odoo generates the VAT reversal.
        #   • Without tax document → debit the gross advance amount (no VAT split).
        has_posted_tax_doc = advance._has_posted_advance_tax_document()

        if has_posted_tax_doc and net_account:
            # Reverse the tax-document entry: Dr net received-advance account +
            # automatic VAT reversal generated from the kept taxes.
            res.update({
                'account_id': net_account.id,
                'price_unit': advance.amount_untaxed,
                'extra_tax_data': False,
            })
            # Give back the VAT at the taxes the tax document charged, not at
            # the advance product's defaults: a 21 % advance deducted at 15 %
            # bills the customer the difference again. Advances at several
            # rates are split per rate later (_split_advance_deduction_lines).
            groups = self.order_id._advance_deduction_tax_groups(advance)
            if len(groups) == 1:
                res['tax_ids'] = [Command.set(groups[0][0].ids)]
        elif company.advance_received_account_id:
            # No posted tax document: deduct the gross advance amount using the
            # product's default income account (from super()).  The clearing
            # account balance from the payment must be cleared via a separate
            # journal entry after the settlement invoice is posted.
            res.update({
                'price_unit': advance.amount_total,
                'tax_ids': [Command.clear()],
                'extra_tax_data': False,
            })
        else:
            # Fallback (no advance accounts configured): gross amount, no taxes.
            res.update({
                'price_unit': advance.amount_total,
                'tax_ids': [Command.clear()],
                'extra_tax_data': False,
            })

        return res

    def _action_launch_stock_rule(self, *, previous_product_uom_qty=False):
        """Never procure from an advance invoice.

        An itemised advance carries the real products, so with ``sale_stock``
        installed confirming it would run the stock rules a second time and the
        customer would end up with two delivery orders reserving the same goods
        twice. Fulfilment belongs to the parent order, which is the only
        document that tracks delivered quantities.
        """
        lines = self.filtered(lambda line: not line.order_id.is_advance_invoice)
        if not lines:
            return True
        return super(SaleOrderLine, lines)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty
        )
