from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    advance_invoice_journal_id = fields.Many2one(
        related="company_id.advance_invoice_journal_id",
        readonly=False,
        domain="[('company_id', '=', company_id), ('type', 'in', ('sale', 'general'))]",
    )
    advance_received_account_id = fields.Many2one(
        related="company_id.advance_received_account_id",
        readonly=False,
        domain="[('reconcile', '=', True)]",
    )
    advance_tax_doc_account_id = fields.Many2one(
        related="company_id.advance_tax_doc_account_id",
        readonly=False,
    )
    advance_tax_doc_account_lt_id = fields.Many2one(
        related="company_id.advance_tax_doc_account_lt_id",
        readonly=False,
    )
