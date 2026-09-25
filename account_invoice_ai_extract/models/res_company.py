from odoo import fields, models
from odoo.tools import float_compare


class ResCompany(models.Model):
    _inherit = 'res.company'

    ai_extract_provider_id = fields.Many2one(
        'muk_ai.provider', string="AI Invoice Provider")
    ai_extract_model_id = fields.Many2one(
        'muk_ai.model', string="AI Invoice Model",
        help="Model used to read invoice PDFs. Leave empty to use the provider's "
             "default model. A small model (e.g. Haiku) is usually enough for clean "
             "digital invoices; escalate to a larger model for scanned documents.")
    ai_extract_journal_id = fields.Many2one(
        'account.journal', string="AI Invoice Journal",
        domain="[('type', '=', 'purchase')]")
    ai_extract_expense_account_id = fields.Many2one(
        'account.account', string="AI Default Expense Account")
    ai_extract_confidence_threshold = fields.Float(
        string="AI Confidence Threshold", default=0.7,
        help="Extractions below this confidence are parked for review instead of "
             "creating a draft bill.")
    ai_extract_auto_create_partner = fields.Boolean(
        string="AI Auto-create Supplier", default=False,
        help="If no supplier matches the extracted VAT, create a draft partner "
             "instead of parking the extraction for review.")
    ai_extract_auto_create_bank = fields.Boolean(
        string="AI Auto-create Bank Account", default=True,
        help="Attach the supplier's extracted IBAN as a bank account on the partner "
             "(when not already present). Disable if bank accounts must be validated "
             "and entered manually.")
    ai_extract_auto_extract = fields.Boolean(
        string="AI Auto-extract on Email", default=True,
        help="Automatically queue an AI extraction when a PDF arrives on a draft "
             "vendor bill (e.g. via the vendor-bills email alias).")
    ai_extract_reverse_charge_rate = fields.Float(
        string="AI Reverse-charge Rate", default=23.0,
        help="VAT rate the buyer self-assesses on reverse-charge purchases. EU "
             "supplier invoices show 0%% VAT; on a reverse-charge fiscal position "
             "their lines are taxed at this standard rate, which the fiscal "
             "position then remaps to the reverse-charge tax.")
    ai_extract_flag_period_mismatch = fields.Boolean(
        string="AI Flag Unusual Tax Point", default=False,
        help="Post a review warning when the taxable supply date (tax point) falls "
             "outside the expected window around the bill date: after the bill date, or "
             "earlier than the month before it. A supply date in the bill's month or the "
             "previous month (e.g. a last-month invoice issued early this month) is normal "
             "and is not flagged.")
    ai_extract_tax_map_ids = fields.One2many(
        'account.invoice.ai.tax.map', 'company_id', string="AI VAT-rate mapping")

    def _ai_extract_tax_for_rate(self, rate):
        """Return the configured domestic input tax for a VAT rate, or empty."""
        self.ensure_one()
        if rate is None:
            return self.env['account.tax']
        rounding = 0.01
        for mapping in self.ai_extract_tax_map_ids:
            if float_compare(mapping.rate_percent, rate, precision_rounding=rounding) == 0:
                return mapping.tax_id
        return self.env['account.tax']
