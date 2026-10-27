from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vrp2_fiscalize_on_payment = fields.Boolean(
        related="company_id.vrp2_fiscalize_on_payment", readonly=False
    )
    vrp2_cash_rounding_id = fields.Many2one(
        related="company_id.vrp2_cash_rounding_id", readonly=False
    )
