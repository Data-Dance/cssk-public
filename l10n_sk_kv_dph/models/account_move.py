import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

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

    # --- the supplier's numbers on a received correction (C.2) ------------
    def _l10n_sk_kv_origin_as_invoice_number(self):
        """``invoice_origin`` when it can be the supplier's invoice number.

        A vendor credit note raised from a purchase order carries the ORDER
        name there ("P00012", or several, comma-separated). That is not the
        corrected invoice, and filing it as FP would pass the export's check
        that a number is present. So an origin naming a purchase order is not
        read, and the export asks for the real number instead."""
        self.ensure_one()
        origin = (self.invoice_origin or "").strip()
        if not origin or "purchase.order" not in self.env:
            return origin
        names = [n.strip() for n in origin.split(",") if n.strip()]
        if self.env["purchase.order"].sudo().search_count(
                [("name", "in", names), ("company_id", "=", self.company_id.id)],
                limit=1):
            return ""
        return origin

    def _l10n_sk_kv_supplier_ref(self):
        """The Bill Reference, when it can be the supplier's number.

        Odoo's reversal wizard fills a credit note's reference with "Reversal
        of: BILL/2026/06/0001" — our own number of the bill, in the user's
        language. Filed as FO that is exactly what the form forbids, and it
        would pass any presence check. A reference that contains our number
        of the document it corrects is therefore not the supplier's. The
        document's OWN number is not tested: some imports name a bill by the
        supplier's number, so there the two rightly agree."""
        self.ensure_one()
        ref = (self.ref or "").strip()
        if not ref:
            return False
        # As a whole token: an imported agenda may number a bill "1", which
        # occurs inside nearly any supplier's number.
        for name in self._cssk_control_original().mapped("name"):
            if name and name != "/" and re.search(
                    r"(?<![\w/.-])%s(?![\w/.-])" % re.escape(name), ref):
                return False
        return ref

    def _l10n_sk_kv_original_supplier_number(self):
        """The SUPPLIER's number of the invoice a received correction corrects.

        The linked original's Bill Reference, else the number typed on the
        correction, else its Source Document. Never the original's internal
        name: the tax administration matches FP against the supplier's own
        statement, where our sequence does not exist."""
        self.ensure_one()
        original = self._cssk_control_original()
        return (
            (original._l10n_sk_kv_supplier_ref() if original else False)
            or self.cssk_control_original_ref
            or self._l10n_sk_kv_origin_as_invoice_number()
            or False
        )

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        # The context reaches here from any RPC caller, so the bypass is
        # honoured only for an accounting administrator (or the superuser),
        # who is who imports historical documents.
        skip = self.env.context.get("l10n_sk_kv_skip_supplier_numbers") and (
            self.env.su
            or self.env.user.has_group("account.group_account_manager"))
        # Odoo's own full cancellation (the wizard's "Modify", a reversal
        # forced by a lock date) posts the reversal in the same call: there is
        # no supplier's document behind it to number. Whether such a storno
        # belongs in C.2 at all is the export's question, and it names it.
        if not skip and not self.env.context.get("move_reverse_cancel"):
            posted._l10n_sk_kv_check_supplier_numbers()
        return posted

    def _l10n_sk_kv_check_supplier_numbers(self):
        """Refuse a received credit or debit note bound for C.2 without the
        supplier's numbers.

        C.2 files the supplier's number of the correction (FO) and of the
        invoice it corrects (FP). Discovered missing only when the statement
        is prepared, the supplier's documents may no longer be at hand, so the
        numbers are asked for when the document is posted. Checked after
        posting, through the same resolver the statement uses, so exactly the
        documents C.2 would report are held, and a credit note outside the
        statement (no Slovak VAT, an EU supplier) is not. Journal entries are
        not held here: imports post them, and the export still names any that
        lack a number. Pass ``l10n_sk_kv_skip_supplier_numbers`` in the
        context to post historical documents."""
        problems = []
        for move in self:
            if move.move_type not in ("in_refund", "in_invoice"):
                continue
            if move.company_id.account_fiscal_country_id.code != "SK":
                continue
            lines = move.line_ids.filtered(
                lambda l: l.display_type == "product" and l.tax_ids)
            if not any(l._cssk_resolve_section_code() == "C.2" for l in lines):
                continue
            doc = move.name or move.display_name
            if not "".join((move._l10n_sk_kv_supplier_ref() or "").split()):
                problems.append(_(
                    "%(doc)s: enter the supplier's number of this credit or "
                    "debit note as the Bill Reference.", doc=doc))
            original = "".join(
                (move._l10n_sk_kv_original_supplier_number() or "").split())
            if not original:
                problems.append(_(
                    "%(doc)s: enter the supplier's number of the invoice it "
                    "corrects (Other Info → Original document number), or the "
                    "Bill Reference on the linked original bill.", doc=doc))
        if problems:
            raise UserError(
                _("KV DPH section C.2 reports the supplier's own numbers, so "
                  "these documents cannot be posted without them:")
                + "\n" + "\n".join(problems))
