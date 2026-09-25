from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    advance_purchase_journal_id = fields.Many2one(
        related="company_id.advance_purchase_journal_id", readonly=False
    )
    advance_paid_clearing_account_id = fields.Many2one(
        related="company_id.advance_paid_clearing_account_id", readonly=False
    )
    advance_paid_account_id = fields.Many2one(
        related="company_id.advance_paid_account_id", readonly=False
    )
    advance_paid_account_lt_id = fields.Many2one(
        related="company_id.advance_paid_account_lt_id", readonly=False
    )
