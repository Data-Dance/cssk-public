from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseAdvanceTaxDocWizard(models.TransientModel):
    _name = "purchase.advance.tax.doc.wizard"
    _description = "Register Received Tax Document for Advance Payment"

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
    supplier_ref = fields.Char(
        string="Supplier's Document Number",
        required=True,
        help="The evidence number exactly as the supplier wrote it — it is "
        "reported verbatim in KH B.2 / KV DPH B.2.",
    )
    invoice_date = fields.Date(
        string="Document Date",
        required=True,
        default=fields.Date.context_today,
    )
    accounting_date = fields.Date(
        string="Accounting Date",
        help="Period in which the input VAT is claimed — may differ from "
        "the tax point (e.g. the document arrived the next month, or "
        "the SK end-of-calendar-year rule). Defaults to the document "
        "date.",
    )
    taxable_supply_date = fields.Date(
        string="Taxable Supply Date",
        required=True,
        help="Tax point: the day the supplier received the payment.",
    )
    amount = fields.Monetary(
        string="Amount (Tax Included)",
        currency_field="currency_id",
        required=True,
    )

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
                    "taxable_supply_date",
                    order.advance_invoice_paid_date
                    or fields.Date.context_today(self),
                )
                values.setdefault(
                    "amount",
                    max(
                        order.amount_paid - order.advance_accounted_amount,
                        0.0,
                    ),
                )
        return values

    def action_create(self):
        self.ensure_one()
        order = self.order_id
        company = order.company_id
        if order.advance_invoice_accounting_status != "waiting":
            raise UserError(
                _("A tax document can only be registered while the advance "
                  "is waiting for one (paid amount not yet accounted).")
            )
        journal = company.advance_purchase_journal_id
        clearing = company.advance_paid_clearing_account_id
        account = (
            company.advance_paid_account_lt_id
            if order.advance_invoice_long_term
            and company.advance_paid_account_lt_id
            else company.advance_paid_account_id
        )
        if not journal or not clearing or not account:
            raise UserError(
                _("Configure the received-advances journal and accounts on "
                  "the company first (Received Advance Invoices settings).")
            )
        if self.currency_id.compare_amounts(self.amount, 0.0) <= 0:
            raise UserError(_("The amount must be positive."))
        unaccounted = order.amount_paid - order.advance_accounted_amount
        if self.currency_id.compare_amounts(self.amount, unaccounted) > 0:
            raise UserError(
                _("The amount cannot exceed the paid amount that is not "
                  "yet accounted (%(amount)s).",
                  amount=unaccounted)
            )

        # 18.0 has no account.tax._prepare_down_payment_lines (a 19.0
        # refactor). Mirror the 18.0 sale-side pattern
        # (sale_order_advance_invoice._prepare_advance_tax_doc_lines_values):
        # group the raw net amounts per (non-fixed) tax combination and scale
        # them by the paid ratio, so net + taxes reproduce the tax-included
        # amount being documented.
        AccountTax = self.env["account.tax"]
        order_lines = order.order_line.filtered(
            lambda line: not line.display_type
        )
        ratio = (
            self.amount / order.amount_total if order.amount_total else 1.0
        )
        net_by_taxes = {}
        for line in order_lines:
            base_line = line._prepare_base_line_for_taxes_computation()
            AccountTax._add_tax_details_in_base_line(base_line, company)
            taxes = line.taxes_id.flatten_taxes_hierarchy()
            taxes -= taxes.filtered(lambda tax: tax.amount_type == "fixed")
            key = tuple(sorted(taxes.ids))
            net_by_taxes[key] = (
                net_by_taxes.get(key, 0.0)
                + base_line["tax_details"]["raw_total_excluded_currency"]
            )

        description = _(
            "Payment sent for Advance Invoice %(name)s on %(paid_date)s",
            name=order.name,
            paid_date=self.taxable_supply_date,
        )
        line_commands = []
        for tax_ids, net_amount in net_by_taxes.items():
            price_unit = self.currency_id.round(net_amount * ratio)
            if self.currency_id.is_zero(price_unit):
                continue
            line_commands.append(
                (0, 0, {
                    "name": description,
                    "quantity": 1.0,
                    "price_unit": price_unit,
                    "tax_ids": [(6, 0, list(tax_ids))],
                    "account_id": account.id,
                })
            )
        move_vals = {
            "move_type": "in_invoice",
            "journal_id": journal.id,
            "company_id": company.id,
            "currency_id": self.currency_id.id,
            "partner_id": order.partner_id.commercial_partner_id.id,
            "ref": self.supplier_ref,
            "invoice_date": self.invoice_date,
            "date": self.accounting_date or self.invoice_date,
            "advance_purchase_order_id": order.id,
            "invoice_line_ids": line_commands,
        }
        # On 18.0 taxable_supply_date comes from l10n_cz / l10n_sk (or the
        # payment-symbols module), not from core account — duck-type it.
        if "taxable_supply_date" in self.env["account.move"]._fields:
            move_vals["taxable_supply_date"] = self.taxable_supply_date
        move = self.env["account.move"].create(move_vals)
        # The payable leg moves to the reconcilable clearing account so the
        # payment and this tax document net to zero there. The clearing
        # account is payable-type (core enforces payment_term ↔ payable).
        term_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        term_lines.write({"account_id": clearing.id})

        return {
            "name": _("Advance Tax Document"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": move.id,
        }
