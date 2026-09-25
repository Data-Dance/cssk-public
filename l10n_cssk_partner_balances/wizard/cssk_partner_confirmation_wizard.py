from odoo import fields, models


class CSSKPartnerConfirmationWizard(models.TransientModel):
    """Issue balance confirmations for many partners at once."""

    _name = "cssk.partner.confirmation.wizard"
    _description = "Generate Partner Balance Confirmations"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    as_of_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    confirmation_type = fields.Selection(
        [
            ("receivable", "Receivables only"),
            ("payable", "Payables only"),
            ("both", "Receivables and payables"),
        ],
        default="both",
        required=True,
    )
    partner_ids = fields.Many2many(
        "res.partner",
        help="Leave empty to issue for every partner with an open balance.",
    )

    def _account_types(self):
        return {
            "receivable": ["asset_receivable"],
            "payable": ["liability_payable"],
            "both": ["asset_receivable", "liability_payable"],
        }[self.confirmation_type]

    def action_generate(self):
        self.ensure_one()
        partners = self.partner_ids.mapped("commercial_partner_id")
        if not partners:
            # Same as-of-date open-items logic as the confirmation snapshot:
            # items paid AFTER the as-of date still count as open on it.
            lines = self.env["account.move.line"].search(
                self.env["cssk.partner.confirmation"]._open_items_domain(
                    self.company_id, self._account_types(), self.as_of_date
                )
            )
            partners = lines.mapped("partner_id.commercial_partner_id")

        created = self.env["cssk.partner.confirmation"]
        for partner in partners:
            conf = self.env["cssk.partner.confirmation"].create(
                {
                    "company_id": self.company_id.id,
                    "partner_id": partner.id,
                    "as_of_date": self.as_of_date,
                    "confirmation_type": self.confirmation_type,
                }
            )
            conf.action_compute_lines()
            created |= conf

        return {
            "type": "ir.actions.act_window",
            "name": "Balance Confirmations",
            "res_model": "cssk.partner.confirmation",
            "view_mode": "list,form",
            "domain": [("id", "in", created.ids)],
        }
