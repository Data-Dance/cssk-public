from odoo import fields, models


class AccountInvoiceAiTaxMap(models.Model):
    """Maps an extracted VAT rate (%) to the company's domestic input-VAT tax.

    Reverse-charge / intra-EU remapping is left to the fiscal position, so this
    only needs the domestic taxes (SK 23 / 19 / 10 / 20 ...).
    """
    _name = 'account.invoice.ai.tax.map'
    _description = "AI Invoice VAT-rate → Tax mapping"
    _order = 'company_id, rate_percent desc'

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda s: s.env.company)
    rate_percent = fields.Float(string="VAT rate (%)", required=True)
    tax_id = fields.Many2one(
        'account.tax', string="Domestic input tax", required=True,
        domain="[('type_tax_use', '=', 'purchase'), ('company_id', '=', company_id)]")

    # Odoo 19 dropped `_sql_constraints` from base in favour of the
    # `models.Constraint` class attribute.
    _rate_company_uniq = models.Constraint(
        "unique(company_id, rate_percent)",
        "A mapping for this VAT rate already exists for this company.",
    )
