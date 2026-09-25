from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    advance_invoice_auto_match_statement = fields.Boolean(
        related="company_id.advance_invoice_auto_match_statement",
        readonly=False,
    )
    advance_invoice_auto_tax_doc = fields.Selection(
        related="company_id.advance_invoice_auto_tax_doc",
        readonly=False,
    )
