from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # The company is the "default VRP2 register" (used by invoice payments).
    # Per-till credentials live on pos.config (see pos_vrp2).

    vrp2_login = fields.Char(related="company_id.vrp2_login", readonly=False)
    vrp2_password = fields.Char(
        related="company_id.vrp2_password", readonly=False
    )

    # Read-only display
    vrp2_dkp = fields.Char(related="company_id.vrp2_dkp")
    vrp2_business_name = fields.Char(related="company_id.vrp2_business_name")
    vrp2_dic = fields.Char(related="company_id.vrp2_dic")
    vrp2_ico = fields.Char(related="company_id.vrp2_ico")
    vrp2_ic_dph = fields.Char(related="company_id.vrp2_ic_dph")
    vrp2_role = fields.Selection(related="company_id.vrp2_role")
    vrp2_last_login = fields.Datetime(related="company_id.vrp2_last_login")
    vrp2_token = fields.Char(
        related="company_id.vrp2_token", groups="base.group_system"
    )
    vrp2_status = fields.Selection(related="company_id.vrp2_status")
    vrp2_round_5c = fields.Boolean(
        related="company_id.vrp2_round_5c", readonly=False
    )

    def action_vrp2_login(self):
        return self.company_id.action_vrp2_login()

    def action_vrp2_logout(self):
        return self.company_id.action_vrp2_logout()
