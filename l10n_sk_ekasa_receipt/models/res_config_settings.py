# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_sk_ekasa_enabled = fields.Boolean(
        related="company_id.l10n_sk_ekasa_enabled", readonly=False)
    l10n_sk_ekasa_ip_notified = fields.Boolean(
        related="company_id.l10n_sk_ekasa_ip_notified", readonly=False)
    l10n_sk_ekasa_ip_address = fields.Char(
        related="company_id.l10n_sk_ekasa_ip_address", readonly=False)
    l10n_sk_ekasa_ip_notified_on = fields.Date(
        related="company_id.l10n_sk_ekasa_ip_notified_on", readonly=False)
    l10n_sk_ekasa_hourly_budget = fields.Integer(
        related="company_id.l10n_sk_ekasa_hourly_budget", readonly=False)
    l10n_sk_ekasa_timeout = fields.Integer(
        related="company_id.l10n_sk_ekasa_timeout", readonly=False)
