from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # All per company: the settings edit the current company.
    peppol_send_enabled = fields.Boolean(
        related="company_id.peppol_send_enabled", readonly=False)
    peppol_scope = fields.Selection(related="company_id.peppol_scope", readonly=False)
    peppol_auto_send = fields.Boolean(
        related="company_id.peppol_auto_send", readonly=False)
    peppol_purchase_journal_id = fields.Many2one(
        related="company_id.peppol_purchase_journal_id", readonly=False)
