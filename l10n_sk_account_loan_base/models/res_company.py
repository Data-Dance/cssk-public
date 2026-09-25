# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# Account ROLES, engine-agnostic. Each bridge maps these onto the field names of
# whichever leasing engine is installed — the two engines name the same concepts
# differently (OCA `long_term_loan_account_id` vs Enterprise `long_term_account_id`,
# OCA `interest_expenses_account_id` vs Enterprise `expense_account_id`).
SK_LOAN_ACCOUNT_ROLES = (
    "long_term",
    "short_term",
    "interest",
    "leased_asset",
)

# Role → account xmlid on the l10n_sk chart.
SK_LOAN_ACCOUNTS = {
    "long_term": "chart_sk_474000",  # Záväzky z nájmu
    "short_term": "chart_sk_474100",  # Lízing (bežná časť)
    "interest": "chart_sk_562000",  # Úroky
    "leased_asset": "chart_sk_022000",  # Samostatné hnuteľné veci
}

# Role → the company field carrying it.
SK_LOAN_COMPANY_FIELDS = {
    role: f"l10n_sk_loan_{role}_account_id" for role in SK_LOAN_ACCOUNT_ROLES
}


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_loan_long_term_account_id = fields.Many2one(
        "account.account",
        string="Leasing — long-term liability",
        domain="[('company_ids', 'in', id)]",
        help="Dlhodobý záväzok z finančného prenájmu (474).",
    )
    l10n_sk_loan_short_term_account_id = fields.Many2one(
        "account.account",
        string="Leasing — current portion",
        domain="[('company_ids', 'in', id)]",
        help="Časť záväzku splatná do jedného roka (474100).",
    )
    l10n_sk_loan_interest_account_id = fields.Many2one(
        "account.account",
        string="Leasing — interest expense",
        domain="[('company_ids', 'in', id)]",
        help="Úrok obsiahnutý v splátke (562).",
    )
    l10n_sk_loan_leased_asset_account_id = fields.Many2one(
        "account.account",
        string="Leased asset",
        domain="[('company_ids', 'in', id)]",
        help="Účet, na ktorý sa zaradí prenajatý majetok (022 pre vozidlá).",
    )

    l10n_sk_loan_is_sk_company = fields.Boolean(
        string="Slovak chart in use (technical)",
        compute="_compute_l10n_sk_loan_is_sk_company",
        help="Technical — hides the Slovak leasing settings on other charts.",
    )

    @api.depends("chart_template")
    def _compute_l10n_sk_loan_is_sk_company(self):
        for company in self:
            company.l10n_sk_loan_is_sk_company = company.chart_template == "sk"

    def l10n_sk_loan_accounts(self):
        """{role: account.account} for this company, skipping unset roles.

        The bridges call this and rename the keys to their engine's field names,
        which is the whole point of keeping the roles here rather than in either
        bridge.
        """
        self.ensure_one()
        accounts = {}
        for role, fname in SK_LOAN_COMPANY_FIELDS.items():
            account = self[fname]
            if account:
                accounts[role] = account
        return accounts
