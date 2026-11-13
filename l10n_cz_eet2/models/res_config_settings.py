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
    # Domain repeated: Odoo drops a string domain on a related field.
    l10n_cz_eet2_certificate_id = fields.Many2one(
        related="company_id.l10n_cz_eet2_certificate_id", readonly=False,
        domain="[('company_id', '=', company_id)]")
    l10n_cz_eet2_max_attempts = fields.Integer(
        related="company_id.l10n_cz_eet2_max_attempts", readonly=False)
    l10n_cz_eet2_response_timeout = fields.Float(
        related="company_id.l10n_cz_eet2_response_timeout", readonly=False)
    l10n_cz_eet2_renew_days_before = fields.Integer(
        related="company_id.l10n_cz_eet2_renew_days_before", readonly=False)
