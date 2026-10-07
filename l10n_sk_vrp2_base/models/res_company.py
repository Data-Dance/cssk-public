from odoo import models


class ResCompany(models.Model):
    # The company carries VRP2 credentials/session via the mixin and acts as
    # the "company default register" used by invoice-payment fiscalization.
    _name = "res.company"
    _inherit = ["res.company", "vrp2.credentials.mixin"]
