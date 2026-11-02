from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # POS-only, company-level VAT mapping (VRP2 VAT rate -> Odoo sales tax).
    # Per-till credentials, login and catalog sync now live on pos.config; the
    # VAT list is cached when a till logs in. Invoice-payment credentials (the
    # "company default register") are configured in the Accounting settings.

    # Domains repeated: Odoo drops a string domain on a related field.
    _SALE_TAX = "[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]"
    vrp2_tax_0 = fields.Many2one(
        related="company_id.vrp2_tax_0", readonly=False, domain=_SALE_TAX
    )
    vrp2_tax_5 = fields.Many2one(
        related="company_id.vrp2_tax_5", readonly=False, domain=_SALE_TAX
    )
    vrp2_tax_10 = fields.Many2one(
        related="company_id.vrp2_tax_10", readonly=False, domain=_SALE_TAX
    )
    vrp2_tax_19 = fields.Many2one(
        related="company_id.vrp2_tax_19", readonly=False, domain=_SALE_TAX
    )
    vrp2_tax_20 = fields.Many2one(
        related="company_id.vrp2_tax_20", readonly=False, domain=_SALE_TAX
    )
    vrp2_tax_23 = fields.Many2one(
        related="company_id.vrp2_tax_23", readonly=False, domain=_SALE_TAX
    )
