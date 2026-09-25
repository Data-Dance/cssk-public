from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    advance_invoice_auto_match_statement = fields.Boolean(
        string="Auto-match Bank Statements to Advance Invoices",
        help="A scheduled action (and the Enterprise bank reconciliation, "
        "when installed) matches unreconciled incoming transactions to "
        "open advance invoices by their number / variable symbol and "
        "registers the payment automatically.",
    )
    advance_invoice_auto_tax_doc = fields.Selection(
        [
            ("none", "Leave for manual creation"),
            ("draft", "Create as draft"),
            ("post", "Create and post"),
        ],
        string="Tax Document on Matched Payment",
        default="none",
        required=True,
        help="What happens with the payment tax document when a bank "
        "transaction pays an advance invoice. Posting immediately "
        "also nets the advance clearing account automatically.",
    )
