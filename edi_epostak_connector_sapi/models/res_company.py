"""The ePošťák credentials a company sends and receives with.

Per environment, because sandbox keys are refused by the production host by
design, and per company, because each company may have its own ePošťák
contract (or speak through one integrator key as its own firm). Before
19.0.1.2.0 these were global ``epostak.sapi.*`` parameters, which the
migration copied to the company the inbound cron ran as.
"""

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    epostak_sandbox_client_id = fields.Char(
        string="ePošťák Sandbox Client ID", groups="base.group_system")
    epostak_sandbox_client_secret = fields.Char(
        string="ePošťák Sandbox Client Secret", groups="base.group_system")
    epostak_prod_client_id = fields.Char(
        string="ePošťák Production Client ID", groups="base.group_system")
    epostak_prod_client_secret = fields.Char(
        string="ePošťák Production Client Secret", groups="base.group_system")
