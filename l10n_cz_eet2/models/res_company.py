# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_eet2_enabled = fields.Boolean(string="EET 2.0 Enabled")
    l10n_cz_eet2_environment = fields.Selection(
        [("playground", "Playground (non-production)"),
        ("production", "Production")],
        string="EET 2.0 Environment", default="playground")
    l10n_cz_eet2_eic_popl = fields.Char(
        string="EET 2.0 Taxpayer EIC",
        help="Registration identification number (EIC), format CZ + 8-10 digits.")
    l10n_cz_eet2_id_jednotky = fields.Integer(
        string="EET 2.0 Default Unit ID (id_jednotky)",
        help="Registrating-unit id from the MOJE daně / DIS+ portal.")
    l10n_cz_eet2_certificate_id = fields.Many2one(
        "l10n.cz.eet2.certificate", string="EET 2.0 Certificate",
        domain="[('company_id', '=', id)]")
    l10n_cz_eet2_max_attempts = fields.Integer(
        string="EET 2.0 Max Send Attempts", default=12,
        help="How many times the scheduled job retries a message (with "
            "exponential backoff) before marking it as failed.")
