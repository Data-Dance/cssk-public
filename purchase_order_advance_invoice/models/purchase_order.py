from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_advance_invoice = fields.Boolean(
        string="Received Advance Invoice",
        copy=False,
        help="This order registers a received advance/proforma invoice — "
        "it is never posted itself; only its payment and the "
        "supplier's tax document on that payment are.",
    )
    advance_invoice_parent_order_id = fields.Many2one(
        "purchase.order",
        string="Parent Purchase Order",
        copy=False,
        domain="[('is_advance_invoice', '=', False)]",
    )
    advance_invoice_ids = fields.One2many(
        "purchase.order",
        "advance_invoice_parent_order_id",
        string="Advance Invoices",
    )
    advance_invoice_count = fields.Integer(
        compute="_compute_advance_invoice_count",
    )
    advance_payment_ids = fields.Many2many(
        "account.payment",
        "purchase_order_advance_payment_rel",
        "order_id",
        "payment_id",
        string="Advance Payments",
        copy=False,
    )
    advance_tax_doc_ids = fields.One2many(
        "account.move",
        "advance_purchase_order_id",
        string="Advance Tax Documents",
        domain=[("move_type", "=", "in_invoice")],
    )
    amount_paid = fields.Monetary(
        string="Amount Paid",
        compute="_compute_amount_paid",
        store=True,
    )
    advance_invoice_paid_date = fields.Date(
        string="Paid Date",
        compute="_compute_amount_paid",
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
    advance_invoice_accounting_status = fields.Selection(
        selection=[
            ("nothing_to_account", "Nothing to Account"),
            ("waiting", "Waiting for Tax Document"),
            ("accounted", "Accounted"),
            ("cancel", "Cancelled"),
        ],
        string="Accounting Status",
        compute="_compute_advance_invoice_accounting_status",
        store=True,
    )
    advance_accounted_amount = fields.Monetary(
        string="Accounted Amount",
        compute="_compute_advance_accounted_amount",
    )
    advance_deducted_amount = fields.Monetary(
        string="Deducted Amount",
        compute="_compute_advance_deducted_amount",
        help="Amount already deducted on final vendor bills.",
    )
    advance_invoice_long_term = fields.Boolean(
        string="Long-term Advance",
        help="Books the net advance on the long-term account when the "
        "localization configures one.",
    )
    advance_invoice_expected_doc_date = fields.Date(
        string="Tax Document Expected By",
        compute="_compute_advance_invoice_expected_doc_date",
        store=True,
        help="Statutory deadline for the supplier to issue the tax "
        "document on the received payment.",
    )

    # ------------------------------------------------------------------
    # create / sequence
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("is_advance_invoice"):
                vals.setdefault(
                    "is_advance_invoice",
                    self.env.context.get(
                        "default_is_advance_invoice", False
                    ),
                )
            if vals.get("is_advance_invoice") and vals.get(
                "name", _("New")
            ) in (False, _("New"), "New"):
                seq_date = fields.Date.context_today(self)
                vals["name"] = (
                    self.env["ir.sequence"]
                    .with_company(vals.get("company_id"))
                    .next_by_code(
                        "purchase.order.advance", sequence_date=seq_date
                    )
                    or _("New")
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # computes
    # ------------------------------------------------------------------
    def _compute_advance_invoice_count(self):
        for order in self:
            order.advance_invoice_count = len(order.advance_invoice_ids)

    @api.depends(
        "advance_payment_ids.state",
        "advance_payment_ids.amount",
        "advance_payment_ids.date",
    )
    def _compute_amount_paid(self):
        for order in self:
            payments = order._advance_effective_payments()
            order.amount_paid = sum(payments.mapped("amount"))
            order.advance_invoice_paid_date = (
                max(payments.mapped("date")) if payments else False
            )

    def _advance_effective_payments(self):
        self.ensure_one()
        return self.advance_payment_ids.filtered(
            lambda payment: payment.state in ("in_process", "paid")
        )

    @api.depends("amount_paid", "amount_total", "state", "is_advance_invoice")
    def _compute_advance_invoice_payment_status(self):
        for order in self:
            if not order.is_advance_invoice:
                order.advance_invoice_payment_status = False
            elif order.state == "cancel":
                order.advance_invoice_payment_status = "cancelled"
            elif order.currency_id.is_zero(order.amount_paid):
                order.advance_invoice_payment_status = "none"
            elif (
                order.currency_id.compare_amounts(
                    order.amount_paid, order.amount_total
                )
                < 0
            ):
                order.advance_invoice_payment_status = "paid_partially"
            elif (
                order.currency_id.compare_amounts(
                    order.amount_paid, order.amount_total
                )
                == 0
            ):
                order.advance_invoice_payment_status = "paid_fully"
            else:
                order.advance_invoice_payment_status = "overpaid"

    @api.depends("advance_tax_doc_ids.state", "advance_tax_doc_ids.amount_total")
    def _compute_advance_accounted_amount(self):
        for order in self:
            order.advance_accounted_amount = sum(
                order.advance_tax_doc_ids.filtered(
                    lambda move: move.state == "posted"
                ).mapped("amount_total")
            )

    def _compute_advance_deducted_amount(self):
        for order in self:
            order.advance_deducted_amount = (
                order._advance_deducted_amount_now()
            )

    def _advance_deducted_amount_now(self):
        """Fresh search — the field itself has no invalidation triggers
        (the deduction lines live on other moves), so flows must use this
        method, never the possibly-stale field."""
        self.ensure_one()
        lines = self.env["account.move.line"].search([
            ("advance_deduction_order_id", "=", self.id),
            ("move_id.state", "!=", "cancel"),
            ("display_type", "=", "product"),
        ])
        return -sum(lines.mapped("price_total"))

    @api.depends(
        "is_advance_invoice",
        "state",
        "amount_paid",
        "advance_tax_doc_ids.state",
        "advance_tax_doc_ids.amount_total",
    )
    def _compute_advance_invoice_accounting_status(self):
        for order in self:
            if not order.is_advance_invoice:
                order.advance_invoice_accounting_status = False
            elif order.state == "cancel":
                order.advance_invoice_accounting_status = "cancel"
            elif order.currency_id.is_zero(order.amount_paid):
                order.advance_invoice_accounting_status = "nothing_to_account"
            elif (
                order.currency_id.compare_amounts(
                    order.advance_accounted_amount, order.amount_paid
                )
                < 0
            ):
                order.advance_invoice_accounting_status = "waiting"
            else:
                order.advance_invoice_accounting_status = "accounted"

    @api.depends("advance_invoice_paid_date")
    def _compute_advance_invoice_expected_doc_date(self):
        for order in self:
            order.advance_invoice_expected_doc_date = (
                order._advance_invoice_tax_doc_deadline(
                    order.advance_invoice_paid_date
                )
                if order.advance_invoice_paid_date
                else False
            )

    def _advance_invoice_tax_doc_deadline(self, paid_date):
        """Statutory deadline for the supplier's tax document: the earlier
        of payment + 15 days (CZ §28(5)) and the end of the payment's
        calendar month (SK §73(b) alternative) — conservative for both."""
        fifteen = paid_date + timedelta(days=15)
        next_month = (paid_date.replace(day=1) + timedelta(days=32)).replace(
            day=1
        )
        end_of_month = next_month - timedelta(days=1)
        return min(fifteen, end_of_month)

    # ------------------------------------------------------------------
    # payments
    # ------------------------------------------------------------------
    def _link_advance_payment(self, payment):
        self.ensure_one()
        if not self.is_advance_invoice:
            raise UserError(
                _("Payments can only be linked to received advance invoices.")
            )
        self.advance_payment_ids = [(4, payment.id)]
        if self.state in ("draft", "sent"):
            self.button_confirm()
        return payment

    # ------------------------------------------------------------------
    # deduction on final bills
    # ------------------------------------------------------------------
    def _advance_remaining_to_deduct(self):
        self.ensure_one()
        return self.amount_paid - self._advance_deducted_amount_now()

    def _prepare_advance_deduction_line_vals(self, move):
        """Deduction lines for this (paid) advance on the vendor bill
        ``move``: with a posted tax document, negated copies of its lines
        (net on the advances account + the same taxes → input-VAT
        reversal); without, one gross line with no taxes."""
        self.ensure_one()
        company = self.company_id
        remaining = self._advance_remaining_to_deduct()
        if self.currency_id.compare_amounts(remaining, 0.0) <= 0:
            return []
        vals_list = []
        label = _("Deduction of advance %(name)s", name=self.name)
        posted_docs = self.advance_tax_doc_ids.filtered(
            lambda doc: doc.state == "posted"
        )
        if posted_docs:
            for line in posted_docs.invoice_line_ids.filtered(
                lambda line: line.display_type == "product"
            ):
                vals_list.append({
                    "name": "%s — %s" % (label, line.name or ""),
                    "quantity": 1.0,
                    "price_unit": -line.price_subtotal,
                    "account_id": line.account_id.id,
                    "tax_ids": [(6, 0, line.tax_ids.ids)],
                    "advance_deduction_order_id": self.id,
                })
        else:
            account = (
                company.advance_paid_account_lt_id
                if self.advance_invoice_long_term
                and company.advance_paid_account_lt_id
                else company.advance_paid_account_id
            )
            if not account:
                raise UserError(
                    _("Configure the paid-advances account on the company "
                      "first (Received Advance Invoices settings).")
                )
            vals_list.append({
                "name": label,
                "quantity": 1.0,
                "price_unit": -remaining,
                "account_id": account.id,
                "tax_ids": [(5, 0, 0)],
                "advance_deduction_order_id": self.id,
            })
        return vals_list

    def action_create_invoice(self, *args, **kwargs):
        """Bills created from a parent purchase order automatically deduct
        its paid advances."""
        result = super().action_create_invoice(*args, **kwargs)
        for order in self.filtered(lambda o: not o.is_advance_invoice):
            advances = order.advance_invoice_ids.filtered(
                lambda advance: advance.state != "cancel"
                and advance.currency_id.compare_amounts(
                    advance._advance_remaining_to_deduct(), 0.0
                )
                > 0
            )
            if not advances:
                continue
            bills = order.invoice_ids.filtered(
                lambda move: move.state == "draft"
                and move.move_type == "in_invoice"
            ).sorted("id")
            if not bills:
                continue
            bill = bills[-1]
            for advance in advances:
                for vals in advance._prepare_advance_deduction_line_vals(bill):
                    bill.invoice_line_ids = [(0, 0, vals)]
        return result

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------
    def action_view_advance_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Advance Invoices"),
            "res_model": "purchase.order",
            "view_mode": "list,form",
            "domain": [("advance_invoice_parent_order_id", "=", self.id)],
            "context": {
                "default_advance_invoice_parent_order_id": self.id,
                "default_is_advance_invoice": True,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_view_advance_tax_docs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Advance Tax Documents"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("advance_purchase_order_id", "=", self.id)],
        }

    # ------------------------------------------------------------------
    # chase-the-supplier activities
    # ------------------------------------------------------------------
    @api.model
    def _cron_chase_advance_tax_documents(self):
        today = fields.Date.context_today(self)
        overdue = self.search([
            ("is_advance_invoice", "=", True),
            ("advance_invoice_accounting_status", "=", "waiting"),
            ("advance_invoice_expected_doc_date", "<", today),
        ])
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        for order in overdue:
            if order.activity_ids.filtered(
                lambda act: act.activity_type_id == activity_type
                and act.summary
                and act.summary.startswith("Advance tax document")
            ):
                continue
            order.activity_schedule(
                "mail.mail_activity_data_todo",
                date_deadline=today,
                summary=_(
                    "Advance tax document overdue — chase %(supplier)s",
                    supplier=order.partner_id.display_name,
                ),
                note=_(
                    "The supplier's tax document for the payment of "
                    "%(name)s was expected by %(date)s.",
                    name=order.name,
                    date=order.advance_invoice_expected_doc_date,
                ),
            )
