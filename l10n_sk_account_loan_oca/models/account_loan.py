# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models

# Slovak account role (from l10n_sk_account_loan_base) → OCA engine field.
OCA_LOAN_ACCOUNT_FIELDS = {
    "long_term": "long_term_loan_account_id",
    "short_term": "short_term_loan_account_id",
    "interest": "interest_expenses_account_id",
    # Contributed by `account_leasing`, which this module depends on.
    "leased_asset": "leased_asset_account_id",
}


class AccountLoan(models.Model):
    _inherit = ["account.loan", "l10n.sk.lease.mixin"]
    _name = "account.loan"

    @api.depends("periods", "method_period")
    def _compute_l10n_sk_lease_months(self):
        # OCA models the term as `periods` instalments of `method_period` months.
        for loan in self:
            loan.l10n_sk_lease_months = (loan.periods or 0) * (loan.method_period or 0)

    def _l10n_sk_loan_account_defaults(self, company):
        """{OCA field: account id} for a Slovak company, empty for any other."""
        if not company or company.chart_template != "sk":
            return {}
        return {
            OCA_LOAN_ACCOUNT_FIELDS[role]: account.id
            for role, account in company.l10n_sk_loan_accounts().items()
            if role in OCA_LOAN_ACCOUNT_FIELDS
        }

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        company = self.env["res.company"].browse(
            values.get("company_id")
        ) or self.env.company
        for fname, account_id in self._l10n_sk_loan_account_defaults(company).items():
            if fname in fields_list and not values.get(fname):
                values[fname] = account_id
        return values

    @api.onchange("company_id")
    def _onchange_company(self):
        # The engine clears the three liability/interest accounts when the
        # company changes (they are company-specific). Refill them from the new
        # company's Slovak defaults instead of leaving the user with blanks.
        res = super()._onchange_company()
        for fname, account_id in self._l10n_sk_loan_account_defaults(
            self.company_id
        ).items():
            if not self[fname]:
                self[fname] = account_id
        return res
