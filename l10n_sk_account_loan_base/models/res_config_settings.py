# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Domains repeated: Odoo drops a string domain on a related field.
    l10n_sk_loan_long_term_account_id = fields.Many2one(
        related="company_id.l10n_sk_loan_long_term_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]",
    )
    l10n_sk_loan_short_term_account_id = fields.Many2one(
        related="company_id.l10n_sk_loan_short_term_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]",
    )
    l10n_sk_loan_interest_account_id = fields.Many2one(
        related="company_id.l10n_sk_loan_interest_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]",
    )
    l10n_sk_loan_leased_asset_account_id = fields.Many2one(
        related="company_id.l10n_sk_loan_leased_asset_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]",
    )
    l10n_sk_loan_is_sk_company = fields.Boolean(
        related="company_id.l10n_sk_loan_is_sk_company"
    )
