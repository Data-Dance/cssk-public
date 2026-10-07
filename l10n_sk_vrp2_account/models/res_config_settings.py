from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vrp2_fiscalize_on_payment = fields.Boolean(
        related="company_id.vrp2_fiscalize_on_payment", readonly=False
    )
