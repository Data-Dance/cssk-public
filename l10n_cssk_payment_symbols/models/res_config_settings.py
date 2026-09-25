# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_cssk_refund_vs_policy = fields.Selection(
        related="company_id.l10n_cssk_refund_vs_policy", readonly=False
    )
    l10n_cssk_default_constant_symbol = fields.Char(
        related="company_id.l10n_cssk_default_constant_symbol", readonly=False
    )
    l10n_cssk_payment_reference_use_vs = fields.Boolean(
        related="company_id.l10n_cssk_payment_reference_use_vs", readonly=False
    )
