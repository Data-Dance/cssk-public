# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_cz_eet2_enabled = fields.Boolean(
        related="company_id.l10n_cz_eet2_enabled", readonly=False)
    l10n_cz_eet2_environment = fields.Selection(
        related="company_id.l10n_cz_eet2_environment", readonly=False)
    l10n_cz_eet2_eic_popl = fields.Char(
        related="company_id.l10n_cz_eet2_eic_popl", readonly=False)
    l10n_cz_eet2_id_jednotky = fields.Integer(
        related="company_id.l10n_cz_eet2_id_jednotky", readonly=False)
    l10n_cz_eet2_certificate_id = fields.Many2one(
        related="company_id.l10n_cz_eet2_certificate_id", readonly=False)
    l10n_cz_eet2_max_attempts = fields.Integer(
        related="company_id.l10n_cz_eet2_max_attempts", readonly=False)
