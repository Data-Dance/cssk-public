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

        # Deduct what the advance actually settled, not its face value: the
        # net its posted tax documents declared, at their own taxes, so the
        # VAT they charged is given back exactly; plus, gross and without VAT,
        # whatever was received on it that no tax document covers yet (the
        # final invoice then charges the VAT on that part itself). A partly
        # paid advance is therefore deducted only for the part paid.
        # Several parts - documents at several rates, or a documented and an
        # undocumented part - are fanned out by _split_advance_deduction_lines.
        components = advance._advance_deduction_components()
        res['extra_tax_data'] = False
        if not components:
            res.update({'price_unit': 0.0, 'tax_ids': [Command.clear()]})
            return res
        first = components[0]
        res.update({
            'price_unit': first['amount'],
            'tax_ids': [Command.set(first['taxes'].ids)],
        })
        if first['account']:
            res['account_id'] = first['account'].id
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
