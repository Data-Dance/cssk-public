from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseAdvancePaymentWizard(models.TransientModel):
    _name = "purchase.advance.payment.wizard"
    _description = "Register Payment for Received Advance Invoice"

    order_id = fields.Many2one(
        "purchase.order",
        string="Advance Invoice",
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(related="order_id.company_id", readonly=True)
    currency_id = fields.Many2one(
        related="order_id.currency_id", readonly=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="order_id.partner_id",
        readonly=True,
    )
    amount_remaining = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_amount_remaining",
    )
    amount = fields.Monetary(
        string="Payment Amount",
        currency_field="currency_id",
        required=True,
    )
    payment_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        required=True,
        domain="[('id', 'in', available_journal_ids)]",
    )
    available_journal_ids = fields.Many2many(
        "account.journal", compute="_compute_available_journal_ids"
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
        if self.env.context.get(
            "active_model"
        ) == "purchase.order" and self.env.context.get("active_id"):
            order = (
                self.env["purchase.order"]
                .browse(self.env.context["active_id"])
                .exists()
            )
            if order:
                values.setdefault("order_id", order.id)
                values.setdefault(
                    "amount",
                    max(order.amount_total - order.amount_paid, 0.0),
                )
                values.setdefault("memo", order.name)
        return values

    @api.depends("order_id.amount_total", "order_id.amount_paid")
    def _compute_amount_remaining(self):
        for wizard in self:
            wizard.amount_remaining = max(
                wizard.order_id.amount_total - wizard.order_id.amount_paid,
                0.0,
            ) if wizard.order_id else 0.0

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
            wizard.available_journal_ids = journals.filtered(
                "outbound_payment_method_line_ids"
            )

    @api.depends("journal_id")
    def _compute_available_payment_method_line_ids(self):
        for wizard in self:
            wizard.available_payment_method_line_ids = (
                wizard.journal_id._get_available_payment_method_lines(
                    "outbound"
                )
                if wizard.journal_id
                else self.env["account.payment.method.line"]
            )

    @api.onchange("available_journal_ids")
    def _onchange_available_journal_ids(self):
        for wizard in self:
            if wizard.journal_id not in wizard.available_journal_ids:
                wizard.journal_id = wizard.available_journal_ids[:1]

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        for wizard in self:
            if (
                wizard.payment_method_line_id
                not in wizard.available_payment_method_line_ids
            ):
                wizard.payment_method_line_id = (
                    wizard.available_payment_method_line_ids[:1]
                )

    def action_create_payment(self):
        self.ensure_one()
        order = self.order_id
        if not order.is_advance_invoice:
            raise UserError(
                _("This action is only available for received advance "
                  "invoices.")
            )
        clearing = self.company_id.advance_paid_clearing_account_id
        if not clearing:
            raise UserError(
                _("Configure the paid-advances clearing account on the "
                  "company first (Received Advance Invoices settings).")
            )
        if self.currency_id.compare_amounts(self.amount, 0.0) <= 0:
            raise UserError(_("The payment amount must be positive."))
        if self.currency_id.compare_amounts(
            self.amount, self.amount_remaining
        ) > 0:
            raise UserError(
                _("The payment amount cannot exceed the unpaid amount.")
            )

        payment = self.env["account.payment"].create({
            "payment_type": "outbound",
            "partner_type": "supplier",
            "partner_id": self.partner_id.commercial_partner_id.id,
            "amount": self.amount,
            "date": self.payment_date,
            "memo": self.memo or order.name,
            "journal_id": self.journal_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "payment_method_line_id": self.payment_method_line_id.id,
            "destination_account_id": clearing.id,
        })
        payment.action_post()
        order._link_advance_payment(payment)
        return {
            "name": _("Payment"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": payment.id,
        }
