# Copyright 2026 Data Dance s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models

from odoo.addons.account.models.chart_template import template

from .res_company import SK_LOAN_ACCOUNTS, SK_LOAN_COMPANY_FIELDS

# 18.0's l10n_sk chart does not ship 474100 "Lízing (bežná časť)" — it arrived
# with the 19.0 chart. Without it the current portion of a lease liability has
# nowhere to go, so the account is created here rather than mapping the current
# portion onto 474000 and losing the split the Súvaha needs.
SK_LEASE_CURRENT_PORTION = {
    "l10n_sk_lease_current_portion": {
        "name": "Lízing (bežná časť)",
        "code": "474100",
        "account_type": "liability_current",
        "reconcile": False,
    }
}


def sk_loan_company_values():
    """{company field: account xmlid} for the SK leasing accounts."""
    return {
        SK_LOAN_COMPANY_FIELDS[role]: xmlid
        for role, xmlid in SK_LOAN_ACCOUNTS.items()
    }


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.account")
    def _get_sk_lease_accounts(self):
        return SK_LEASE_CURRENT_PORTION

    @template("sk", "res.company")
    def _get_sk_res_company_loan(self):
        # Merged with l10n_sk's own res.company contribution when the SK chart
        # is loaded — wires the leasing accounts for new companies.
        return {self.env.company.id: sk_loan_company_values()}
