from odoo import fields, models


class AccountInvoiceAiExtractionRun(models.Model):
    _name = 'account.invoice.ai.extraction.run'
    _description = "AI Invoice Extraction Run"
    _order = 'run_date desc, id desc'

    extraction_id = fields.Many2one(
        'account.invoice.ai.extraction', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='extraction_id.company_id', store=True)
    run_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    provider_id = fields.Many2one('muk_ai.provider', readonly=True)
    model_id = fields.Many2one('muk_ai.model', readonly=True)
    input_tokens = fields.Integer(readonly=True)
    output_tokens = fields.Integer(readonly=True)
    cost = fields.Float(string="Cost (USD)", readonly=True, digits=(12, 5), aggregator='sum')
    confidence = fields.Float(readonly=True)
