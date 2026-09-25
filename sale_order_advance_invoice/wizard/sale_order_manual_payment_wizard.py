from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderManualPaymentWizard(models.TransientModel):
    _name = "sale.order.manual.payment.wizard"
    _description = "Register Manual Payment for Advance Invoice"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Advance Invoice",
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="sale_order_id.company_id",
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="sale_order_id.currency_id",
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="sale_order_id.partner_invoice_id.commercial_partner_id",
        readonly=True,
    )
    amount_remaining = fields.Monetary(
        string="Amount Remaining",
        currency_field="currency_id",
        compute="_compute_amount_remaining",
        readonly=True,
    )
    amount = fields.Monetary(
        string="Payment Amount",
        currency_field="currency_id",
        required=True,
    )
    payment_date = fields.Date(
        string="Payment Date",
        required=True,
        default=fields.Date.context_today,
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        required=True,
        domain="[('id', 'in', available_journal_ids)]",
    )
    available_journal_ids = fields.Many2many(
        "account.journal",
        compute="_compute_available_journal_ids",
    )
    payment_method_line_id = fields.Many2one(
        "account.payment.method.line",
        string="Payment Method",
        required=True,
        domain="[('id', 'in', available_payment_method_line_ids)]",
    )
    available_payment_method_line_ids = fields.Many2many(
        "account.payment.method.line",
        compute="_compute_available_payment_method_line_ids",
    )
    memo = fields.Char(string="Memo")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("active_model") == "sale.order" and self.env.context.get("active_id"):
            sale_order = self.env["sale.order"].browse(self.env.context["active_id"]).exists()
            if sale_order:
                remaining = max(sale_order.amount_total - sale_order.amount_paid, 0.0)
                values.setdefault("sale_order_id", sale_order.id)
                values.setdefault("amount", remaining)
                values.setdefault("memo", sale_order.name)
        return values

    @api.depends("sale_order_id", "sale_order_id.amount_total", "sale_order_id.amount_paid")
    def _compute_amount_remaining(self):
        for wizard in self:
            if wizard.sale_order_id:
                wizard.amount_remaining = max(
                    wizard.sale_order_id.amount_total - wizard.sale_order_id.amount_paid,
                    0.0,
                )
            else:
                wizard.amount_remaining = 0.0

    @api.depends("company_id")
    def _compute_available_journal_ids(self):
        Journal = self.env["account.journal"]
        for wizard in self:
            if not wizard.company_id:
                wizard.available_journal_ids = Journal
                continue
            journals = Journal.search([
                ("company_id", "=", wizard.company_id.id),
                ("type", "in", ("bank", "cash", "credit")),
            ])
            wizard.available_journal_ids = journals.filtered("inbound_payment_method_line_ids")

    @api.depends("journal_id")
    def _compute_available_payment_method_line_ids(self):
        PaymentMethodLine = self.env["account.payment.method.line"]
        for wizard in self:
            wizard.available_payment_method_line_ids = (
                wizard.journal_id._get_available_payment_method_lines("inbound")
                if wizard.journal_id
                else PaymentMethodLine
            )

    @api.onchange("available_journal_ids")
    def _onchange_available_journal_ids(self):
        for wizard in self:
            if wizard.journal_id not in wizard.available_journal_ids:
                wizard.journal_id = wizard.available_journal_ids[:1]

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        for wizard in self:
            if wizard.payment_method_line_id not in wizard.available_payment_method_line_ids:
                wizard.payment_method_line_id = wizard.available_payment_method_line_ids[:1]

    def action_create_payment(self):
        self.ensure_one()
        sale_order = self.sale_order_id
        if not sale_order.is_advance_invoice:
            raise UserError(_("This action is only available for advance invoices."))
        if not sale_order.show_manual_transfer_link:
            raise UserError(_("Manual payment can only be registered when the advance invoice still has an unpaid amount."))
        if not self.journal_id:
            raise UserError(_("Please select a journal."))
        if not self.payment_method_line_id:
            raise UserError(_("Please select a payment method."))
        if self.currency_id.compare_amounts(self.amount, 0.0) <= 0:
            raise UserError(_("The payment amount must be positive."))
        if self.currency_id.compare_amounts(self.amount, self.amount_remaining) > 0:
            raise UserError(_("The payment amount cannot exceed the unpaid amount."))

        payment_vals = {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": self.partner_id.id,
            "amount": self.amount,
            "date": self.payment_date,
            "memo": self.memo or sale_order.name,
            "journal_id": self.journal_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "payment_method_line_id": self.payment_method_line_id.id,
        }
        advance_account = self.company_id.advance_received_account_id
        if advance_account:
            payment_vals["destination_account_id"] = advance_account.id
        payment = self.env["account.payment"].create(payment_vals)
        payment.action_post()
        sale_order._link_payment_to_transaction(payment)

        # Confirm the sale order if it's still in draft state
        if sale_order.state in ("draft", "sent"):
            sale_order.action_confirm()

        return {
            "name": _("Payment"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": payment.id,
        }