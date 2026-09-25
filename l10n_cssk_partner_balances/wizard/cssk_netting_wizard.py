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
            ],
            order="date, id",
        )

    @staticmethod
    def _allocate(lines, netting):
        """Greedily allocate ``netting`` across ``lines`` (full residual first).
        Returns [(line, amount_to_offset)] for lines that get a positive share."""
        out = []
        remaining = netting
        for line in lines:
            if remaining <= 0:
                break
            amount = min(remaining, abs(line.amount_residual))
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
        ar = lines.filtered(
            lambda l: l.company_currency_id.compare_amounts(
                l.amount_residual, 0.0
            ) > 0
        )
        ap = lines.filtered(
            lambda l: l.company_currency_id.compare_amounts(
                l.amount_residual, 0.0
            ) < 0
        )
        ar_total = sum(abs(a) for a in ar.mapped("amount_residual"))
        ap_total = sum(abs(a) for a in ap.mapped("amount_residual"))
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
                "line_ids": line_vals,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "cssk.partner.netting.agreement",
            "res_id": agreement.id,
            "view_mode": "form",
        }
