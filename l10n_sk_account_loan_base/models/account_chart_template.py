# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

from .res_company import SK_LOAN_ACCOUNTS, SK_LOAN_COMPANY_FIELDS


def sk_loan_company_values():
    """{company field: account xmlid} for the SK leasing accounts."""
    return {
        SK_LOAN_COMPANY_FIELDS[role]: xmlid
        for role, xmlid in SK_LOAN_ACCOUNTS.items()
    }


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "res.company")
    def _get_sk_res_company_loan(self):
        # Merged with l10n_sk's own res.company contribution when the SK chart
        # is loaded — wires the leasing accounts for new companies.
        return {self.env.company.id: sk_loan_company_values()}
