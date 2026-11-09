from odoo import _, api, fields, models

#: § 69 ods. 12 písm. h) a i): reverse charge needs this base per category on
#: one invoice. Categories are not added together.
RC_INVOICE_THRESHOLD = 5000.0
RC_THRESHOLD_GOODS = ("h", "i")


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_sk_rc_threshold_warning = fields.Text(
        compute="_compute_l10n_sk_rc_threshold_warning",
    )

    @api.depends(
        "move_type", "company_id", "partner_id", "currency_id",
        "invoice_line_ids.balance", "invoice_line_ids.tax_ids",
        "invoice_line_ids.product_id",
    )
    def _compute_l10n_sk_rc_threshold_warning(self):
        for move in self:
            move.l10n_sk_rc_threshold_warning = (
                "\n".join(move._l10n_sk_rc_threshold_issues())
                if move.move_type == "out_invoice"
                and move.company_id.account_fiscal_country_id.code == "SK"
                else False
            ) or False

    def _l10n_sk_rc_threshold_issues(self):
        """Advisory only: the supply also depends on the customer's status."""
        self.ensure_one()
        issues = []
        labels = dict(
            self.env["product.template"]._fields["l10n_sk_kv_rc_goods"].selection
        )
        for goods in RC_THRESHOLD_GOODS:
            lines = self.invoice_line_ids.filtered(
                lambda l: l.product_id.l10n_sk_kv_rc_goods == goods
            )
            if not lines:
                continue
            total = abs(sum(lines.mapped("balance")))
            reverse = lines.filtered(
                lambda l: l.tax_ids.filtered("cssk_control_is_reverse_charge")
            )
            taxed = (lines - reverse).filtered(
                lambda l: any(t.amount for t in l.tax_ids)
            )
            currency = self.company_id.currency_id
            below = currency.compare_amounts(total, RC_INVOICE_THRESHOLD) < 0
            if reverse and below:
                issues.append(_(
                    "%(goods)s: the base on this invoice is %(total).2f €, under "
                    "5 000 €, so reverse charge does not apply and VAT is due.",
                    goods=labels[goods], total=total,
                ))
            elif taxed and not below and self.partner_id.vat:
                issues.append(_(
                    "%(goods)s: the base on this invoice is %(total).2f €, so "
                    "reverse charge applies if the customer is a VAT payer.",
                    goods=labels[goods], total=total,
                ))
        return issues

    l10n_sk_kv_is_simplified = fields.Boolean(
        string="Simplified invoice (KV DPH B.3)",
        help="Mark received documents that are simplified invoices / receipts "
        "(zjednodušená faktúra, bloček z e-kasy). Their input VAT is reported in "
        "KV DPH section B.3 — aggregated in B.3.1 below the 3 000 EUR period "
        "threshold, or per supplier in B.3.2 at/above it.\n"
        "NB: toggling this on an already-posted move does not auto-recompute "
        "the section tag; recompute the statement (or the line) afterwards.",
    )
