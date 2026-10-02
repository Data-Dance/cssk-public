from odoo import _, fields, models
from odoo.exceptions import UserError


class CSSKNettingWizard(models.TransientModel):
    """Create a netting agreement for a partner, auto-allocating the offset
    across the open AR/AP up to the netting amount (balanced)."""

    _name = "cssk.netting.wizard"
    _description = "Create Netting Agreement"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    partner_id = fields.Many2one(
        "res.partner", required=True, domain="[('parent_id', '=', False)]"
    )
    agreement_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True,
        default=lambda s: s.env.company.currency_id,
        help="Set off in the company's currency (every open item, at its "
        "booked amount) or in a foreign one (only items in that currency).")

    def _foreign(self):
        return self.currency_id != self.company_id.currency_id

    def _open_amount(self, line):
        return line.amount_residual_currency if self._foreign() \
            else line.amount_residual

    def _open_lines(self):
        """All open AR/AP items of the partner (both account types)."""
        self.ensure_one()
        return self.env["account.move.line"].search(
            [
                ("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ("partner_id.commercial_partner_id", "=",
                 self.partner_id.commercial_partner_id.id),
                ("account_id.account_type", "in",
                 ["asset_receivable", "liability_payable"]),
                ("reconciled", "=", False),
                ("amount_residual", "!=", 0.0),
            ] + ([("currency_id", "=", self.currency_id.id)]
                 if self._foreign() else []),
            order="date, id",
        )

    def _allocate(self, lines, netting):
        """Greedily allocate ``netting`` across ``lines`` (full residual first).
        Returns [(line, amount_to_offset)] for lines that get a positive share."""
        out = []
        remaining = netting
        for line in lines:
            if remaining <= 0:
                break
            amount = min(remaining, abs(self._open_amount(line)))
            if amount > 0:
                out.append((line, amount))
                remaining -= amount
        return out

    def action_create(self):
        self.ensure_one()
        # Sign-aware split: the side of the set-off follows the SIGN of the
        # open residual, not the account type. An open customer credit note
        # (negative residual on the receivable account) is a debt we owe the
        # partner and is offsettable on the payable side; a vendor
        # refund/debit note (positive residual on the payable account) is
        # the partner's debt to us → receivable side. This matches
        # cssk.partner.netting.agreement.line._compute_side().
        lines = self._open_lines()
        currency = self.currency_id
        ar = lines.filtered(
            lambda l: currency.compare_amounts(self._open_amount(l), 0.0) > 0
        )
        ap = lines.filtered(
            lambda l: currency.compare_amounts(self._open_amount(l), 0.0) < 0
        )
        ar_total = sum(abs(self._open_amount(l)) for l in ar)
        ap_total = sum(abs(self._open_amount(l)) for l in ap)
        netting = min(ar_total, ap_total)
        if not netting:
            raise UserError(
                _("This partner has no mutually offsettable balances "
                  "(needs both open receivables and payables).")
            )

        line_vals = []
        for line, amount in self._allocate(ar, netting):
            line_vals.append((0, 0, {"move_line_id": line.id,
                                     "amount_to_offset": amount}))
        for line, amount in self._allocate(ap, netting):
            line_vals.append((0, 0, {"move_line_id": line.id,
                                     "amount_to_offset": amount}))

        agreement = self.env["cssk.partner.netting.agreement"].create(
            {
                "company_id": self.company_id.id,
                "partner_id": self.partner_id.id,
                "agreement_date": self.agreement_date,
                "netting_currency_id": self.currency_id.id,
                "line_ids": line_vals,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "cssk.partner.netting.agreement",
            "res_id": agreement.id,
            "view_mode": "form",
        }
