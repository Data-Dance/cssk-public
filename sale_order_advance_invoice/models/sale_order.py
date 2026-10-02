import calendar
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools.misc import format_date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_advance_invoice_send_template(self):
        self.ensure_one()
        return self.env.ref(
            "sale_order_advance_invoice.email_template_edi_advance_invoice",
            raise_if_not_found=False,
        )

    def _get_advance_invoice_confirmation_template(self):
        self.ensure_one()
        return self.env.ref(
            "sale_order_advance_invoice.mail_template_advance_invoice_confirmation",
            raise_if_not_found=False,
        )

    def _get_advance_invoice_payment_template(self):
        self.ensure_one()
        return self.env.ref(
            "sale_order_advance_invoice.mail_template_advance_invoice_payment_executed",
            raise_if_not_found=False,
        )

    def _find_mail_template(self):
        self.ensure_one()
        if self.is_advance_invoice:
            return self._get_advance_invoice_send_template()
        return super()._find_mail_template()

    def _get_confirmation_template(self):
        self.ensure_one()
        if self.is_advance_invoice:
            return self._get_advance_invoice_confirmation_template()
        return super()._get_confirmation_template()

    def _send_payment_succeeded_for_order_mail(self):
        default_template = self.env.ref(
            "sale.mail_template_sale_payment_executed",
            raise_if_not_found=False,
        )
        for order in self:
            mail_template = (
                order._get_advance_invoice_payment_template()
                if order.is_advance_invoice
                else default_template
            )
            order._send_order_notification_mail(mail_template)

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        if self.is_advance_invoice:
            journal = self.company_id.advance_invoice_journal_id
            if journal:
                values["journal_id"] = journal.id
        return values

    def _get_copiable_order_lines(self):
        """Exclude advance-invoice tracking section/lines from duplicated quotations/orders."""
        lines = super()._get_copiable_order_lines()
        if self.is_advance_invoice:
            return lines
        return lines.filtered(
            lambda l: not l.is_advance_tracking
            and not l.advance_source_order_id
        )


    is_advance_invoice = fields.Boolean(string="Advance Invoice")
    advance_invoice_long_term = fields.Boolean(
        string="Long-term Advance",
        copy=False,
        help="Settle this advance against the long-term received-advance account "
        "(e.g. 475) instead of the short-term one (e.g. 324). Used when the "
        "advance will be settled after more than one year.",
    )
    advance_invoice_parent_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        ondelete="restrict",
    )
    advance_invoice_ids = fields.One2many(
        "sale.order",
        "advance_invoice_parent_order_id",
        string="Advance Invoices",
    )
    advance_invoice_count = fields.Integer(
        compute="_compute_advance_invoice_count",
    )
    advance_invoice_accounting_status = fields.Selection(
        selection=[
            ("nothing_to_account", "Nothing to Account"),
            ("waiting", "Waiting"),
            ("accounted", "Accounted"),
            ("cancel", "Cancelled"),
        ],
        string="Accounting Status",
        compute="_compute_accounting_status",
        store=True,
    )
    advance_invoice_paid_date = fields.Date(
        string="Paid Date",
        compute="_compute_advance_invoice_paid_date",
        store=True,
    )
    advance_invoice_payment_status = fields.Selection(
        selection=[
            ("none", "Not Paid"),
            ("paid_partially", "Partially Paid"),
            ("paid_fully", "Fully Paid"),
            ("overpaid", "Overpaid"),
            ("cancelled", "Cancelled"),
        ],
        string="Payment Status",
        compute="_compute_advance_invoice_payment_status",
        store=True,
    )
    advance_invoice_date_due = fields.Date(
        string="Due Date",
        compute="_compute_advance_invoice_date_due",
        store=True,
        readonly=False,
        copy=False,
    )
    advance_invoice_accounting_date_due = fields.Date(
        string="Accounting Date Due",
        compute="_compute_advance_invoice_accounting_date_due",
        store=True,
    )
    advance_invoice_partner_bank_id = fields.Many2one(
        "res.partner.bank",
        string="Bank Account",
        compute="_compute_advance_invoice_partner_bank_id",
        store=True,
        readonly=False,
    )
    advance_invoice_qr_code_method = fields.Selection(
        string="Payment QR-code",
        copy=False,
        selection=lambda self: self.env["res.partner.bank"].get_available_qr_methods_in_sequence(),
        compute="_compute_advance_invoice_qr_code_method",
        store=True,
        readonly=False,
        help="Type of QR-code to be generated for the payment of this advance invoice when printing it. "
             "If left blank, the first available and usable method will be used.",
    )
    advance_invoice_display_qr_code = fields.Boolean(
        string="Display QR-code",
        compute="_compute_advance_invoice_display_qr_code",
    )
    show_manual_transfer_link = fields.Boolean(
        compute="_compute_show_manual_transfer_link",
    )

    def _create_advance_invoice_section_line_if_needed(self):
        self.ensure_one()
        if any(
            line.display_type == 'line_section' and line.is_advance_tracking
            for line in self.order_line
        ):
            return

        env = self.with_context(lang=self.partner_id.lang).env
        sequence = max(self.order_line.mapped('sequence') or [10]) + 1
        self.env['sale.order.line'].with_context(sale_no_log_for_new_lines=True).create({
            'order_id': self.id,
            'display_type': 'line_section',
            'name': env._("Advance Invoices"),
            'sequence': sequence,
            'is_advance_tracking': True,
        })

    def _add_advance_invoice_tracking_line(self, advance_invoice):
        self.ensure_one()
        if self.is_advance_invoice:
            return

        existing = self.order_line.filtered(
            lambda line: line.advance_source_order_id.id == advance_invoice.id
        )
        if existing:
            self._sync_advance_tracking_line_from_advance(advance_invoice)
            return

        self._create_advance_invoice_section_line_if_needed()
        sequence = max(self.order_line.mapped('sequence') or [10]) + 1
        advance_product = self._get_advance_product()
        self.env['sale.order.line'].with_context(sale_no_log_for_new_lines=True).create({
            'order_id': self.id,
            'product_id': advance_product.id,
            'product_uom_id': advance_product.uom_id.id,
            'product_uom_qty': 0.0,
            'price_unit': self._get_advance_tracking_line_price_unit(advance_invoice),
            'name': self._get_advance_tracking_line_description(advance_invoice),
            'sequence': sequence,
            'is_advance_tracking': True,
            'advance_source_order_id': advance_invoice.id,
        })

    def _get_advance_tracking_line_price_unit(self, advance_invoice):
        return advance_invoice.amount_untaxed

    def _get_advance_tracking_line_quantity(self, advance_invoice):
        return 0.0

    def _get_advance_tracking_line_description(self, advance_invoice):
        env = self.with_context(lang=self.partner_id.lang).env
        tracking_state = self._get_advance_tracking_state(advance_invoice)
        if tracking_state == 'draft':
            description = env._(
                "Advance Invoice %(name)s: %(date)s (Draft)",
                name=advance_invoice.name,
                date=format_date(env, advance_invoice.create_date.date()) if advance_invoice.create_date else '',
            )
        elif tracking_state == 'cancel':
            description = env._("Advance Invoice %(name)s (Cancelled)", name=advance_invoice.name)
        else:
            description = env._("Advance Invoice %(name)s", name=advance_invoice.name)

        if advance_invoice.advance_invoice_paid_date:
            paid_date = format_date(env, advance_invoice.advance_invoice_paid_date)
            description = env._("%(description)s - paid on %(date)s", description=description, date=paid_date)

        posted_invoices = advance_invoice.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted'
        )
        if posted_invoices:
            invoice_names = ', '.join(posted_invoices.mapped('name'))
            description = env._("%(description)s, Tax Document %(name)s", description=description, name=invoice_names)

        return description

    def _get_advance_tracking_state(self, advance_invoice):
        invoices = advance_invoice.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice')
        if invoices:
            if all(inv.state == 'draft' for inv in invoices):
                return 'draft'
            if all(inv.state == 'cancel' for inv in invoices):
                return 'cancel'
            return ''

        if advance_invoice.state == 'draft':
            return 'draft'
        if advance_invoice.state == 'cancel':
            return 'cancel'
        return ''

    def _sync_advance_tracking_line_from_advance(self, advance_invoice):
        self.ensure_one()
        tracking_lines = self.order_line.filtered(
            lambda l: l.is_advance_tracking and l.advance_source_order_id.id == advance_invoice.id
        )
        if not tracking_lines:
            return

        tracking_lines.write({
            'name': self._get_advance_tracking_line_description(advance_invoice),
            'product_uom_qty': 0.0,
            'price_unit': self._get_advance_tracking_line_price_unit(advance_invoice),
        })
        tracking_lines._compute_qty_to_invoice()
        tracking_lines._compute_invoice_status()

    def _cleanup_advance_tracking_section_if_empty(self):
        self.ensure_one()
        has_tracking_lines = bool(
            self.order_line.filtered(
                lambda l: l.is_advance_tracking and not l.display_type
            )
        )
        if has_tracking_lines:
            return

        empty_sections = self.order_line.filtered(
            lambda l: l.is_advance_tracking and l.display_type == 'line_section'
        )
        if empty_sections:
            empty_sections.with_context(sale_no_log_for_new_lines=True).unlink()

    def _get_fallback_provider(self):
        self.ensure_one()
        provider = self.env["payment.provider"].search([
            ("code", "=", "none"),
            ("company_id", "=", self.company_id.id),
        ], limit=1)
        if provider:
            return provider
        return self.env["payment.provider"].search([
            ("company_id", "=", self.company_id.id),
        ], limit=1)

    def _get_payment_method_for_provider(self, provider):
        payment_method = provider.with_context(active_test=False).payment_method_ids[:1]
        if payment_method:
            return payment_method

        payment_method = self.env["payment.method"].with_context(active_test=False).search([
            ("code", "=", "bank_transfer"),
        ], limit=1)
        if payment_method:
            return payment_method

        return self.env["payment.method"].with_context(active_test=False).search([], limit=1)

    def _create_transaction_from_payment(self, payment):
        self.ensure_one()
        provider = payment.payment_method_line_id.payment_provider_id or self._get_fallback_provider()
        if not provider:
            raise UserError(_("No payment provider was found to create the transaction link."))

        payment_method = self._get_payment_method_for_provider(provider)
        if not payment_method:
            raise UserError(_("No payment method was found to create the transaction link."))

        reference_prefix = payment.memo or payment.name or self.name
        reference = self.env["payment.transaction"].sudo()._compute_reference(
            provider.code,
            prefix=reference_prefix,
            sale_order_ids=[Command.set([self.id])],
        )

        tx_values = {
            "provider_id": provider.id,
            "payment_method_id": payment_method.id,
            "reference": reference,
            "amount": abs(payment.amount),
            "currency_id": payment.currency_id.id,
            "partner_id": payment.partner_id.id,
            "operation": "offline",
            "state": "done",
            "is_post_processed": True,
            "payment_id": payment.id,
            "sale_order_ids": [Command.set([self.id])],
        }
        if "invoice_ids" in self.env["payment.transaction"]._fields:
            invoices = self.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice" and inv.state != "cancel"
            )
            if invoices:
                tx_values["invoice_ids"] = [Command.set(invoices.ids)]

        return self.env["payment.transaction"].sudo().create(tx_values)

    def _link_payment_to_transaction(self, payment):
        self.ensure_one()
        tx = payment.payment_transaction_id
        if tx:
            tx_values = {"sale_order_ids": [Command.link(self.id)]}
            if "invoice_ids" in tx._fields:
                invoices = self.invoice_ids.filtered(
                    lambda inv: inv.move_type == "out_invoice" and inv.state != "cancel"
                )
                if invoices:
                    tx_values["invoice_ids"] = [Command.set(invoices.ids)]
            tx.sudo().write(tx_values)
            return tx
        return self._create_transaction_from_payment(payment)

    def _get_advance_product(self):
        product_tmpl = self.env.ref(
            'sale_order_advance_invoice.product_advance_invoice',
            raise_if_not_found=False,
        )
        if not product_tmpl:
            ProductTemplate = self.env['product.template'].sudo()
            product_tmpl = ProductTemplate.search([
                ('name', '=', 'Advance'),
                ('type', '=', 'service'),
            ], limit=1)
            if not product_tmpl:
                vals = {
                    'name': 'Advance',
                    'type': 'service',
                    'sale_ok': True,
                    'purchase_ok': False,
                }
                if 'publish_date' in ProductTemplate._fields:
                    vals['publish_date'] = fields.Datetime.now()
                # website_sale adds a required, NOT NULL base_unit_count whose
                # default is not applied on a bare template create (no variant
                # yet): set it explicitly when the field is present.
                if 'base_unit_count' in ProductTemplate._fields:
                    vals['base_unit_count'] = 0
                product_tmpl = ProductTemplate.create(vals)

            self.env['ir.model.data'].sudo().search([
                ('module', '=', 'sale_order_advance_invoice'),
                ('name', '=', 'product_advance_invoice'),
            ], limit=1) or self.env['ir.model.data'].sudo().create({
                'module': 'sale_order_advance_invoice',
                'name': 'product_advance_invoice',
                'model': 'product.template',
                'res_id': product_tmpl.id,
                'noupdate': True,
            })

        return product_tmpl.product_variant_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Apply action context defaults for advance invoice creation if not explicitly provided
            vals.setdefault('is_advance_invoice', self.env.context.get('default_is_advance_invoice', False))
            
            if vals.get("is_advance_invoice"):
                vals.setdefault("require_payment", True)
            if vals.get("is_advance_invoice") and vals.get("name", _("New")) == _("New"):
                seq_date = (
                    fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(vals["date_order"])
                    )
                    if "date_order" in vals
                    else None
                )
                vals["name"] = self.env["ir.sequence"].with_company(
                    vals.get("company_id")
                ).next_by_code("sale.order.advance", sequence_date=seq_date) or _("New")
        return super().create(vals_list)

    @api.depends("advance_invoice_ids")
    def _compute_advance_invoice_count(self):
        for order in self:
            order.advance_invoice_count = len(order.advance_invoice_ids)

    @api.depends("is_advance_invoice", "state", "amount_total", "amount_paid", "currency_id")
    def _compute_show_manual_transfer_link(self):
        for order in self:
            order.show_manual_transfer_link = (
                order.is_advance_invoice
                and order.state not in ("draft", "cancel")
                and order.currency_id.compare_amounts(order.amount_total, order.amount_paid) > 0
            )

    @api.depends(
        "is_advance_invoice",
        "amount_total",
        "transaction_ids.state",
        "transaction_ids.amount",
        "transaction_ids.last_state_change",
    )
    def _compute_advance_invoice_paid_date(self):
        for order in self:
            if not order.is_advance_invoice:
                order.advance_invoice_paid_date = False
                continue
            done = order.transaction_ids.filtered(lambda t: t.state == "done").sorted(
                "last_state_change", reverse=True
            )
            done_amount = sum(done.mapped("amount"))
            order.advance_invoice_paid_date = (
                done[0].last_state_change.date()
                if done and done[0].last_state_change and not order.currency_id.is_zero(done_amount)
                else False
            )
            parent = order.advance_invoice_parent_order_id
            if parent:
                parent._sync_advance_tracking_line_from_advance(order)

    @api.depends(
        "is_advance_invoice",
        "state",
        "amount_total",
        "transaction_ids.state",
        "transaction_ids.amount",
    )
    def _compute_advance_invoice_payment_status(self):
        for order in self:
            if not order.is_advance_invoice:
                order.advance_invoice_payment_status = False
                continue
            if order.state == "cancel":
                order.advance_invoice_payment_status = "cancelled"
                continue
            paid = order.amount_paid
            total = order.amount_total
            if order.currency_id.is_zero(paid):
                order.advance_invoice_payment_status = "none"
            elif order.currency_id.compare_amounts(paid, total) < 0:
                order.advance_invoice_payment_status = "paid_partially"
            elif order.currency_id.compare_amounts(paid, total) == 0:
                order.advance_invoice_payment_status = "paid_fully"
            else:
                order.advance_invoice_payment_status = "overpaid"

    @api.depends(
        "is_advance_invoice", "date_order", "payment_term_id",
        "amount_total", "amount_untaxed", "amount_tax", "currency_id", "company_id",
    )
    def _compute_advance_invoice_date_due(self):
        today = fields.Date.context_today(self)
        for order in self:
            if not order.is_advance_invoice:
                order.advance_invoice_date_due = False
                continue
            date_ref = order.date_order.date() if order.date_order else today
            if not order.payment_term_id:
                order.advance_invoice_date_due = date_ref
                continue
            terms = order.payment_term_id._compute_terms(
                date_ref=date_ref,
                currency=order.currency_id,
                company=order.company_id,
                tax_amount=order.amount_tax,
                tax_amount_currency=order.amount_tax,
                sign=1,
                untaxed_amount=order.amount_untaxed,
                untaxed_amount_currency=order.amount_untaxed,
            )
            due_dates = [line["date"] for line in terms.get("line_ids", []) if line.get("date")]
            order.advance_invoice_date_due = max(due_dates) if due_dates else date_ref

    @api.depends("advance_invoice_paid_date", "state")
    def _compute_advance_invoice_accounting_date_due(self):
        for order in self:
            paid = order.advance_invoice_paid_date
            if not paid or order.state != "sale":
                order.advance_invoice_accounting_date_due = False
                continue
            order.advance_invoice_accounting_date_due = order._advance_invoice_tax_doc_deadline(paid)

    def _get_saleorder_report_filename(self):
        """Filename of the sale-order PDF (wired into
        ``sale.action_report_saleorder``'s ``print_report_name``): an advance
        invoice must not be called an "Order" — translated in the rendering
        language, so a Slovak advance prints as "Zálohová faktúra - ADV…"."""
        self.ensure_one()
        if self.is_advance_invoice:
            return "%s - %s" % (self.env._("Advance Invoice"), self.name)
        if self.state in ("draft", "sent"):
            return "%s - %s" % (self.env._("Quotation"), self.name)
        return "%s - %s" % (self.env._("Order"), self.name)

    def _advance_invoice_tax_doc_deadline(self, paid_date):
        """Statutory deadline to issue the tax document on a received advance.

        Default (shared by the Czech and Slovak rules): the earlier of 15 days
        after the payment was received and the end of that calendar month.
        Localizations may override this for country-specific deadlines.
        """
        self.ensure_one()
        last_day = calendar.monthrange(paid_date.year, paid_date.month)[1]
        end_of_month = paid_date.replace(day=last_day)
        return min(paid_date + timedelta(days=15), end_of_month)

    def _get_advance_invoice_net_account(self):
        """Net (ex-VAT) received-advance liability account for this advance.

        Routes to the long-term account when the advance is flagged long-term and
        a long-term account is configured, otherwise the short-term account.
        """
        self.ensure_one()
        company = self.company_id
        if self.advance_invoice_long_term and company.advance_tax_doc_account_lt_id:
            return company.advance_tax_doc_account_lt_id
        return company.advance_tax_doc_account_id

    @api.depends(
        "is_advance_invoice",
        "state",
        "invoice_ids.state",
        "invoice_ids.amount_total",
        "advance_invoice_parent_order_id.order_line.invoice_lines.move_id.state",
        "advance_invoice_accounting_date_due",
        "advance_invoice_payment_status",
    )
    def _compute_accounting_status(self):
        for order in self:
            if not order.is_advance_invoice:
                order.advance_invoice_accounting_status = False
                continue
            if order.state in ("draft", "sent"):
                order.advance_invoice_accounting_status = "nothing_to_account"
            elif order.state == "cancel":
                order.advance_invoice_accounting_status = "cancel"
            else:
                payment_status = order.advance_invoice_payment_status
                if payment_status == "none":
                    order.advance_invoice_accounting_status = "nothing_to_account"
                else:
                    already_invoiced = sum(
                        inv.amount_total
                        for inv in order.invoice_ids
                        if inv.move_type == 'out_invoice' and inv.state == 'posted'
                    )
                    amount_unaccounted = order.currency_id.round(order.amount_paid - already_invoiced)
                    own_accounted = order.currency_id.compare_amounts(amount_unaccounted, 0.0) <= 0

                    parent = order.advance_invoice_parent_order_id
                    tracking_accounted = bool(parent and parent.order_line.filtered(
                        lambda l: l.is_advance_tracking and l.advance_source_order_id.id == order.id
                    ).invoice_lines.filtered(
                        lambda l: l.move_id.state == "posted"
                    ))

                    if own_accounted or tracking_accounted:
                        order.advance_invoice_accounting_status = "accounted"
                    else:
                        order.advance_invoice_accounting_status = "waiting"

    @api.depends("is_advance_invoice", "currency_id", "company_id")
    def _compute_advance_invoice_partner_bank_id(self):
        for order in self:
            if not order.is_advance_invoice:
                order.advance_invoice_partner_bank_id = False
                continue
            company_partner = order.company_id.partner_id.commercial_partner_id
            banks = company_partner.bank_ids.filtered(
                lambda b: not b.company_id or b.company_id == order.company_id
            ).sorted(
                key=lambda b: (0 if (b.currency_id == order.currency_id or not b.currency_id) else 1)
            )
            order.advance_invoice_partner_bank_id = banks[:1]

    @api.depends("is_advance_invoice", "advance_invoice_partner_bank_id", "partner_id", "currency_id")
    def _compute_advance_invoice_qr_code_method(self):
        for order in self:
            if not order.is_advance_invoice or not order.advance_invoice_partner_bank_id:
                order.advance_invoice_qr_code_method = False
                continue
            selected = False
            for candidate_method, _name in self.env["res.partner.bank"].get_available_qr_methods_in_sequence():
                error_msg = order.advance_invoice_partner_bank_id._get_error_messages_for_qr(
                    candidate_method, order.partner_id, order.currency_id
                )
                if not error_msg:
                    selected = candidate_method
                    break
            order.advance_invoice_qr_code_method = selected

    @api.onchange("advance_invoice_qr_code_method")
    def _onchange_advance_invoice_qr_code_method(self):
        if not self.advance_invoice_qr_code_method or not self.advance_invoice_partner_bank_id:
            return
        error_msg = self.advance_invoice_partner_bank_id._get_error_messages_for_qr(
            self.advance_invoice_qr_code_method, self.partner_id, self.currency_id
        )
        if error_msg:
            raise UserError(error_msg)

    @api.depends("is_advance_invoice", "company_id")
    def _compute_advance_invoice_display_qr_code(self):
        for order in self:
            order.advance_invoice_display_qr_code = (
                order.is_advance_invoice and bool(order.company_id.qr_code)
            )

    def _generate_advance_invoice_qr_code(self, silent_errors=False):
        self.ensure_one()
        if not self.advance_invoice_display_qr_code or not self.advance_invoice_partner_bank_id:
            return None
        qr_method = self.advance_invoice_qr_code_method
        if not qr_method:
            return None
        error_msg = self.advance_invoice_partner_bank_id._get_error_messages_for_qr(
            qr_method, self.partner_id, self.currency_id
        )
        if error_msg:
            if silent_errors:
                return None
            raise UserError(error_msg)
        return self.advance_invoice_partner_bank_id.build_qr_code_base64(
            self.amount_total, self.name, self.name,
            self.currency_id, self.partner_id, qr_method, silent_errors=silent_errors,
        )

    def _get_order_lines_to_report(self):
        if not self.is_advance_invoice:
            return super()._get_order_lines_to_report()
        # For advance invoices the main product lines are is_downpayment=True,
        # which the core method hides unless they have posted invoices linked.
        # Show all lines except internal advance-tracking section/lines.
        return self.order_line.filtered(lambda l: not l.is_advance_tracking)

    def _get_invoiceable_lines(self, final=False):
        lines = super()._get_invoiceable_lines(final=final)

        if self.is_advance_invoice:
            return lines

        # Split result into regular lines and advance tracking lines.
        tracking_lines = lines.filtered(lambda l: l.is_advance_tracking and not l.display_type)
        if not tracking_lines:
            return lines

        regular_lines = lines.filtered(lambda l: not l.is_advance_tracking)
        if not regular_lines:
            # Tracking deductions are ready but no product/service lines qualify
            # under their invoice policy yet (e.g. delivery policy, nothing shipped).
            # Return empty so Odoo raises "nothing to invoice" — advances cannot
            # be deducted without a corresponding product line on the same invoice.
            return self.env['sale.order.line']

        # Regular invoiceable lines exist: append the tracking section header
        # (if present) and tracking deduction lines after them.
        tracking_section = self.order_line.filtered(
            lambda l: l.display_type == 'line_section' and l.is_advance_tracking
        )
        return regular_lines | tracking_section | tracking_lines

    def _create_invoices(self, grouped=False, final=False, date=None):
        if final:
            for order in self.filtered(lambda so: not so.is_advance_invoice):
                for advance in order.advance_invoice_ids:
                    order._sync_advance_tracking_line_from_advance(advance)

        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)
        if not final:
            return invoices

        # Keep parent order tracking line labels in sync for advance orders
        # after invoice creation/cancellation flows.
        for advance in self.filtered('is_advance_invoice'):
            parent = advance.advance_invoice_parent_order_id
            if parent:
                parent._sync_advance_tracking_line_from_advance(advance)

        return invoices

    def _has_posted_advance_tax_document(self):
        """Whether this advance has already accounted VAT on a tax document."""
        self.ensure_one()
        return bool(self.invoice_ids.filtered(
            lambda move: move.move_type == 'out_invoice' and move.state == 'posted'
        ))

    def _advance_tax_document_rate(self, currency):
        """The rate, per company-currency unit, the advance's VAT was declared at.

        Taken from its posted tax documents in ``currency`` as a whole, so an
        advance paid in instalments on different days deducts at the rate its
        documents averaged. 0.0 when there is none: an advance without a tax
        document declared no VAT to give back.
        """
        self.ensure_one()
        docs = self.invoice_ids.filtered(
            lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
            and m.currency_id == currency
        )
        value = sum(docs.mapped('amount_untaxed_signed'))
        if self.company_id.currency_id.is_zero(value):
            return 0.0
        return sum(docs.mapped('amount_untaxed')) / value

    def _advance_deduction_tax_groups(self, advance):
        """The advance's net amount broken down by the taxes it charged.

        Returns ``[(taxes, net), ...]``, in the order the advance lists them. A
        lump-sum advance has a single group and is unaffected; an itemised one
        at two VAT rates has two, which is the point: the deduction has to give
        back exactly the VAT the tax document took.
        """
        groups = {}
        lines = advance.order_line.filtered(
            lambda line: not line.display_type and not line.is_advance_tracking
        )
        for line in lines:
            key = tuple(sorted(line.tax_ids.ids))
            groups.setdefault(key, [line.tax_ids, 0.0])[1] += line.price_subtotal
        return [(taxes, net) for taxes, net in groups.values()]

    def _split_advance_deduction_lines(self, invoice_vals_list):
        """Fan a deduction line out into one line per rate the advance charged.

        The deduction is prepared from a single tracking line on the order, so
        it can carry only one tax - which is right until an advance charges
        more than one. Then a single line reverses the wrong amount of VAT and
        the difference is billed to a customer who has already paid it.
        """
        Line = self.env['sale.order.line']
        for vals in invoice_vals_list:
            commands = vals.get('invoice_line_ids') or []
            new_commands = []
            for cmd in commands:
                new_commands.extend(self._split_one_advance_deduction(Line, cmd))
            if len(new_commands) != len(commands):
                vals['invoice_line_ids'] = new_commands

    @api.model
    def _command_record_ids(self, commands):
        """The ids an x2many command list refers to, whichever form it takes."""
        ids = []
        for command in commands or []:
            code = command[0]
            if code in (Command.LINK.value, Command.UPDATE.value):
                ids.append(command[1])
            elif code == Command.SET.value:
                ids.extend(command[2] or [])
        return ids

    def _split_one_advance_deduction(self, Line, cmd):
        if cmd[0] != 0:
            return [cmd]
        line = Line.browse(self._command_record_ids(cmd[2].get('sale_line_ids'))).exists()
        advance = line.advance_source_order_id
        if len(line) != 1 or not line.is_advance_tracking or not advance:
            return [cmd]
        # Only the deduction of an advance that raised a tax document carries
        # VAT to give back. Without one the deduction is the gross amount with
        # no taxes at all, and there is nothing to split.
        if not advance._has_posted_advance_tax_document():
            return [cmd]

        groups = self._advance_deduction_tax_groups(advance)
        if len(groups) < 2:
            return [cmd]
        # Only the command carrying the advance's whole net is the one to
        # split. Anything else is a share of it that has been split already,
        # and splitting a share again would deduct the advance twice over.
        if advance.currency_id.compare_amounts(
            cmd[2].get('price_unit', 0.0), advance.amount_untaxed
        ):
            return [cmd]

        split = []
        for taxes, net in groups:
            group_vals = dict(cmd[2])
            group_vals['price_unit'] = net
            group_vals['tax_ids'] = [Command.set(taxes.ids)]
            group_vals['name'] = "%s (%s)" % (
                cmd[2].get('name', ''), ", ".join(taxes.mapped('name')),
            )
            split.append(Command.create(group_vals))
        return split

    def _create_account_invoices(self, invoice_vals_list, final):
        if final:
            # Once for the whole batch, not once per order: the split is keyed
            # on each command's own sale line, and running it twice over the
            # same list would split lines it had already split.
            self._split_advance_deduction_lines(invoice_vals_list)
        if self.filtered('is_advance_invoice'):
            # Core forces quantity=-1.0 on is_downpayment lines (to deduct them from a
            # final invoice of the parent order). For the advance invoice's own invoice
            # these lines ARE the primary charges, so restore to positive quantity.
            for vals in invoice_vals_list:
                for cmd in vals.get('invoice_line_ids', []):
                    if cmd[0] == 0 and cmd[2].get('is_downpayment') and cmd[2].get('quantity', 0) < 0:
                        cmd[2]['quantity'] = abs(cmd[2]['quantity'])
        return super()._create_account_invoices(invoice_vals_list, final)

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            for advance in self.filtered('is_advance_invoice'):
                parent = advance.advance_invoice_parent_order_id
                if parent:
                    parent._sync_advance_tracking_line_from_advance(advance)
        return res

    def unlink(self):
        advances = self.filtered('is_advance_invoice')
        if advances:
            parents = advances.mapped('advance_invoice_parent_order_id')
            tracking_lines = parents.mapped('order_line').filtered(
                lambda l: l.is_advance_tracking and l.advance_source_order_id.id in advances.ids
            )
            if tracking_lines:
                tracking_lines.with_context(sale_no_log_for_new_lines=True).unlink()
            for parent in parents:
                parent._cleanup_advance_tracking_section_if_empty()
        return super().unlink()

    def action_create_advance_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Advance Invoice"),
            "res_model": "sale.advance.invoice.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id},
        }

    def action_register_manual_payment(self):
        self.ensure_one()
        if not self.is_advance_invoice:
            raise UserError(_("This action is only available for advance invoices."))
        if not self.show_manual_transfer_link:
            raise UserError(_("Manual payment can only be registered when the advance invoice still has an unpaid amount."))

        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale_order_advance_invoice.action_sale_order_manual_payment_wizard"
        )
        action_context = dict(self.env.context)
        action_context.update({
            "active_model": "sale.order",
            "active_id": self.id,
        })
        action["context"] = action_context
        return action

    def action_view_advance_invoices(self):
        self.ensure_one()
        advances = self.advance_invoice_ids
        if len(advances) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": "Advance Invoice",
                "res_model": "sale.order",
                "res_id": advances.id,
                "view_mode": "form",
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "name": "Advance Invoices",
            "res_model": "sale.order",
            "domain": [("advance_invoice_parent_order_id", "=", self.id)],
            "context": {
                "default_is_advance_invoice": True,
                "default_require_payment": True,
                "default_advance_invoice_parent_order_id": self.id,
            },
            "view_mode": "list,form",
            "target": "current",
        }

    def action_view_parent_order(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.advance_invoice_parent_order_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_create_invoice_direct_for_advance(self):
        self.ensure_one()
        if not self.is_advance_invoice:
            raise UserError(_("This action is only available for advance invoices."))
        if self.advance_invoice_accounting_status != "waiting":
            raise UserError(_("Invoice can only be created when accounting status is Waiting."))

        already_invoiced = sum(
            inv.amount_total
            for inv in self.invoice_ids
            if inv.move_type == 'out_invoice' and inv.state == 'posted'
        )
        amount_to_invoice = self.currency_id.round(self.amount_paid - already_invoiced)
        if self.currency_id.compare_amounts(amount_to_invoice, 0.0) <= 0:
            raise UserError(_("No unpaid amount remains to be invoiced."))

        AccountTax = self.env['account.tax']
        order_lines = self.order_line.filtered(lambda l: not l.display_type and not l.is_advance_tracking)
        base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id)
        down_payment_base_lines = AccountTax._prepare_down_payment_lines(
            base_lines=base_lines,
            company=self.company_id,
            amount_type='fixed',
            amount=amount_to_invoice,
            computation_key=f'advance_tax_doc,{self.id},{len(self.invoice_ids)}',
        )

        self._create_down_payment_section_line_if_needed()
        so_lines = self._create_down_payment_lines_from_base_lines(down_payment_base_lines)

        wizard = self.env['sale.advance.payment.inv'].create({
            'sale_order_ids': [Command.set([self.id])],
            'advance_payment_method': 'fixed',
            'fixed_amount': amount_to_invoice,
        })
        accounts = [
            wizard._get_down_payment_account(base_line['product_id'])
            for base_line in down_payment_base_lines
        ]
        invoice_vals = wizard.with_context(accounts=accounts)._prepare_down_payment_invoice_values(
            order=self, so_lines=so_lines
        )
        if self.advance_invoice_paid_date:
            invoice_vals['taxable_supply_date'] = self.advance_invoice_paid_date

        company = self.company_id
        net_account = self._get_advance_invoice_net_account()
        if net_account:
            for cmd in invoice_vals.get('invoice_line_ids', []):
                if cmd[0] == 0 and cmd[2].get('display_type', 'product') == 'product':
                    cmd[2]['account_id'] = net_account.id

        invoice = self.env['account.move'].with_context(
            allow_advance_invoice_journal_mismatch=True,
        ).create(invoice_vals)

        # Override the receivable line to use the advance clearing account so the
        # advance payment and this tax document are posted on the same account and
        # can be reconciled together.
        if company.advance_received_account_id:
            rec_lines = invoice.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable'
            )
            if rec_lines:
                rec_lines.write({
                    'account_id': company.advance_received_account_id.id,
                    'date_maturity': False,
                })

        paid_date = format_date(self.env, self.advance_invoice_paid_date) if self.advance_invoice_paid_date else ""
        description = _(
            "Payment received for Advance Invoice %(name)s on %(paid_date)s",
            name=self.name,
            paid_date=paid_date,
        )
        invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product").write({"name": description})

        return self.action_view_invoice(invoices=invoice)
