# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_sk_jcd_clearing_account_id = fields.Many2one(
        related="company_id.l10n_sk_jcd_clearing_account_id", readonly=False
    )
    l10n_sk_jcd_duty_product_id = fields.Many2one(
        related="company_id.l10n_sk_jcd_duty_product_id", readonly=False
    )
    l10n_sk_jcd_default_regime = fields.Selection(
        related="company_id.l10n_sk_jcd_default_regime", readonly=False
    )
    l10n_sk_jcd_is_sk_company = fields.Boolean(
        related="company_id.l10n_sk_jcd_is_sk_company"
    )
