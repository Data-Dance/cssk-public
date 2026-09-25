# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, _, api, fields, models
from odoo.tools import float_round
from odoo.exceptions import UserError


class SaleAdvanceInvoiceWizard(models.TransientModel):
    _name = 'sale.advance.invoice.wizard'
    _description = "Create Advance Invoice"

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
        required=True,
    )
    advance_payment_method = fields.Selection(
        selection=[
            ('full', "Full amount"),
            ('percentage', "Percentage of total amount"),
            ('fixed', "Fixed amount"),
        ],
        string="Advance Invoice Type",
        default='full',
        required=True,
    )
    amount = fields.Float(
        string="Percentage",
        help="The percentage of the order total to invoice as advance.",
    )
    fixed_amount = fields.Monetary(
        string="Fixed Amount",
        help="The fixed amount to invoice as advance.",
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute='_compute_currency_id',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        compute='_compute_company_id',
        store=True,
    )
    has_advance_invoices = fields.Boolean(
        string='Has Advance Invoices',
        compute='_compute_has_advance_invoices',
    )
    amount_advance_invoiced = fields.Monetary(
        string='Already Invoiced',
        compute='_compute_amount_advance_invoiced',
        help='Only confirmed advance invoices are considered.',
    )
    include_items = fields.Boolean(
        string="Include the ordered items",
        help="List the ordered products on the advance invoice instead of a "
             "single generic Advance line.\n"
             "Each line then carries its own product and its own VAT rate, so "
             "an order mixing rates is requested — and later taxed on the tax "
             "document — at the right rate on every item.\n"
             "For a percentage or a fixed amount the unit prices are scaled "
             "down in the same proportion; the quantities stay as ordered.",
    )
    description = fields.Char(
        string='Advance Invoice Description',
        help='Optional description or note for this advance invoice',
    )

    #=== COMPUTE METHODS ===#

    @api.depends('sale_order_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.sale_order_id.currency_id if wizard.sale_order_id else False

    @api.depends('sale_order_id')
    def _compute_company_id(self):
        for wizard in self:
            wizard.company_id = wizard.sale_order_id.company_id if wizard.sale_order_id else False

    @api.depends('sale_order_id', 'sale_order_id.advance_invoice_ids')
    def _compute_has_advance_invoices(self):
        for wizard in self:
            if not wizard.sale_order_id:
                wizard.has_advance_invoices = False
                continue
            wizard.has_advance_invoices = bool(
                wizard.sale_order_id.advance_invoice_ids.filtered(lambda o: o.state == 'sale')
            )

    @api.depends(
        'sale_order_id',
        'sale_order_id.advance_invoice_ids.state',
        'sale_order_id.advance_invoice_ids.amount_total',
    )
    def _compute_amount_advance_invoiced(self):
        for wizard in self:
            if not wizard.sale_order_id:
                wizard.amount_advance_invoiced = 0.0
                continue
            confirmed_advances = wizard.sale_order_id.advance_invoice_ids.filtered(
                lambda o: o.state == 'sale'
            )
            wizard.amount_advance_invoiced = sum(confirmed_advances.mapped('amount_total'))

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            defaults['sale_order_id'] = self.env.context['active_id']
        return defaults

    #=== CONSTRAINT METHODS ===#

    def _check_amount_is_positive(self):
        for wizard in self:
            if wizard.advance_payment_method == 'percentage' and wizard.amount <= 0.0:
                raise UserError(_('The percentage must be positive.'))
            elif wizard.advance_payment_method == 'fixed' and wizard.fixed_amount <= 0.0:
                raise UserError(_('The fixed amount must be positive.'))

    #=== ACTION METHODS ===#

    def create_advance_invoice(self):
        self.ensure_one()
        self._check_amount_is_positive()
        order = self.sale_order_id

        # Create base advance invoice
        advance_invoice = self.env["sale.order"].create(
            {
                "partner_id": order.partner_id.id,
                "partner_invoice_id": order.partner_invoice_id.id,
                "partner_shipping_id": order.partner_shipping_id.id,
                "company_id": order.company_id.id,
                "currency_id": order.currency_id.id,
                "pricelist_id": order.pricelist_id.id,
                "is_advance_invoice": True,
                "advance_invoice_parent_order_id": order.id,
                "require_payment": True,
                "note": self.description,
            }
        )

        if self.include_items:
            self._add_itemised_lines(advance_invoice, order)
        elif self.advance_payment_method == 'full':
            self._add_full_amount_lines(advance_invoice, order)
        elif self.advance_payment_method == 'percentage':
            self._add_percentage_lines(advance_invoice, order)
        else:  # 'fixed'
            self._add_fixed_amount_lines(advance_invoice, order)

        order._add_advance_invoice_tracking_line(advance_invoice)

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": advance_invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    #=== BUSINESS METHODS ===#

    def _get_advance_ratio(self, order):
        """Proportion of the order that this advance covers, 0.0 < ratio <= 1.0.

        Both partial methods are expressed on the untaxed total, which is what
        the lump-sum lines below have always done.
        """
        if self.advance_payment_method == 'full':
            return 1.0
        if self.advance_payment_method == 'percentage':
            return self.amount / 100.0
        if not order.amount_untaxed:
            raise UserError(_(
                "A fixed amount cannot be spread over the ordered items: the "
                "order has no untaxed amount to spread it over."
            ))
        return self.fixed_amount / order.amount_untaxed

    def _itemised_line_vals(self, advance_invoice, line, ratio, suffix):
        """Mirror one order line onto the advance, keeping its product and taxes.

        The quantity is the ordered quantity - a partial advance is a smaller
        payment for the same goods, not a payment for fewer goods - so the
        proportion is taken on the unit price.
        """
        return {
            'order_id': advance_invoice.id,
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom_id.id,
            'product_uom_qty': line.product_uom_qty,
            'name': f"{line.name}{suffix}",
            'price_unit': line.price_unit * ratio,
            'discount': line.discount,
            'tax_ids': [Command.set(line.tax_ids.ids)],
            # Deliberately NOT is_downpayment: these lines are what the advance
            # order sells, not a down payment taken against it. Core forces the
            # quantity of a down-payment line to one unit, which would invoice
            # one printer where two were ordered.
            'is_downpayment': False,
        }

    def _add_itemised_lines(self, advance_invoice, order):
        ratio = self._get_advance_ratio(order)
        env = self.with_context(lang=order.partner_id.lang).env
        suffix = "" if self.advance_payment_method == 'full' else env._(
            " (advance: %(ratio)s%% of the ordered amount)",
            ratio=float_round(ratio * 100.0, precision_digits=2),
        )
        source_lines = order.order_line.filtered(
            lambda l: not l.display_type and not l.is_advance_tracking
        )
        lines = self.env['sale.order.line'].create([
            self._itemised_line_vals(advance_invoice, line, ratio, suffix)
            for line in source_lines
        ])
        if self.advance_payment_method == 'fixed':
            self._absorb_rounding_residual(advance_invoice, lines)
        return lines

    def _absorb_rounding_residual(self, advance_invoice, lines):
        """Make a fixed-amount itemised advance total exactly the amount asked.

        Scaling every unit price by the same ratio and rounding each result can
        leave the sum a cent or two off the figure the user typed.

        The correction has to go through a unit price, so a line can only
        absorb what its quantity can express: at two decimals a line of one
        unit absorbs any cent, a line of three units only multiples of three.
        Lines are therefore tried smallest quantity first, and whatever no line
        can express is left rather than made worse - a percentage advance is
        not adjusted at all, since a share of each line is exactly what was
        asked for there.
        """
        currency = advance_invoice.currency_id
        for line in lines.sorted(lambda l: abs(l.product_uom_qty)):
            residual = currency.round(self.fixed_amount - advance_invoice.amount_untaxed)
            if currency.is_zero(residual):
                return
            factor = line.product_uom_qty * (1.0 - (line.discount or 0.0) / 100.0)
            if not factor:
                continue
            before = line.price_unit
            line.price_unit += residual / factor
            new_residual = currency.round(
                self.fixed_amount - advance_invoice.amount_untaxed
            )
            if abs(new_residual) >= abs(residual):
                line.price_unit = before

    def _advance_line_vals(self, advance_invoice, name, price_unit, product_uom_qty=1.0):
        product = self.sale_order_id._get_advance_product()
        return {
            'order_id': advance_invoice.id,
            'product_id': product.id,
            'product_uom_id': product.uom_id.id,
            'product_uom_qty': product_uom_qty,
            'name': name,
            'price_unit': price_unit,
            'is_downpayment': True,
        }

    def _add_full_amount_lines(self, advance_invoice, order):
        """Copy all invoiceable order lines as Advance-product lines."""
        SaleOrderLine = self.env['sale.order.line']
        for line in order.order_line.filtered(lambda l: not l.display_type):
            SaleOrderLine.create(
                self._advance_line_vals(advance_invoice, line.name, line.price_subtotal)
            )

    def _add_percentage_lines(self, advance_invoice, order):
        """Add a single Advance-product line with percentage of order total."""
        env = self.with_context(lang=order.partner_id.lang).env
        advance_amount = order.amount_untaxed * (self.amount / 100.0)
        self.env['sale.order.line'].create(
            self._advance_line_vals(
                advance_invoice,
                env._('Advance Payment - %(percentage)s%% of Order %(order)s', percentage=self.amount, order=order.name),
                advance_amount,
            )
        )

    def _add_fixed_amount_lines(self, advance_invoice, order):
        """Add a single Advance-product line with fixed advance amount."""
        env = self.with_context(lang=order.partner_id.lang).env
        self.env['sale.order.line'].create(
            self._advance_line_vals(
                advance_invoice,
                env._('Advance Payment - %(amount)s of Order %(order)s',
                      amount=self.currency_id.format(self.fixed_amount), order=order.name),
                self.fixed_amount,
            )
        )
