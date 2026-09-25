from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_extract_provider_id = fields.Many2one(
        related='company_id.ai_extract_provider_id', readonly=False)
    ai_extract_model_id = fields.Many2one(
        related='company_id.ai_extract_model_id', readonly=False)
    ai_extract_journal_id = fields.Many2one(
        related='company_id.ai_extract_journal_id', readonly=False)
    ai_extract_expense_account_id = fields.Many2one(
        related='company_id.ai_extract_expense_account_id', readonly=False)
    ai_extract_confidence_threshold = fields.Float(
        related='company_id.ai_extract_confidence_threshold', readonly=False)
    ai_extract_auto_create_partner = fields.Boolean(
        related='company_id.ai_extract_auto_create_partner', readonly=False)
    ai_extract_auto_create_bank = fields.Boolean(
        related='company_id.ai_extract_auto_create_bank', readonly=False)
    ai_extract_auto_extract = fields.Boolean(
        related='company_id.ai_extract_auto_extract', readonly=False)
    ai_extract_reverse_charge_rate = fields.Float(
        related='company_id.ai_extract_reverse_charge_rate', readonly=False)
    ai_extract_flag_period_mismatch = fields.Boolean(
        related='company_id.ai_extract_flag_period_mismatch', readonly=False)
    ai_extract_tax_map_ids = fields.One2many(
        related='company_id.ai_extract_tax_map_ids', readonly=False)
