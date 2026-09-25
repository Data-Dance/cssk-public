# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    # Exposed to the POS frontend (pos.config loads all its fields) so the
    # payment-validation override knows whether to do the synchronous EET send.
    l10n_cz_eet2_enabled = fields.Boolean(
        string="EET 2.0 Enabled", compute="_compute_l10n_cz_eet2_enabled")
    l10n_cz_eet2_id_pokl = fields.Char(
        string="EET 2.0 PoS ID (id_pokl)",
        help="Identifier of this point of sale sent as id_pokl (<=20 chars). "
            "Falls back to the POS name if empty.")
    l10n_cz_eet2_id_jednotky = fields.Integer(
        string="EET 2.0 Unit ID (id_jednotky)",
        help="Registrating-unit id for this POS. Falls back to the company "
            "default if empty.")

    @api.depends("company_id.l10n_cz_eet2_enabled", "company_id.l10n_cz_eet2_eic_popl")
    def _compute_l10n_cz_eet2_enabled(self):
        for config in self:
            company = config.company_id
            config.l10n_cz_eet2_enabled = bool(
                company.l10n_cz_eet2_enabled and company.l10n_cz_eet2_eic_popl)
