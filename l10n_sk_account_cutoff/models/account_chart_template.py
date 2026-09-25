# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.account.models.chart_template import template

# Slovak časové rozlíšenie accounts → OCA cut-off default fields.
SK_CUTOFF_ACCOUNTS = {
    "default_prepaid_expense_account_id": "chart_sk_381000",  # Náklady budúcich období
    "default_prepaid_revenue_account_id": "chart_sk_384000",  # Výnosy budúcich období
    "default_accrued_expense_account_id": "chart_sk_383000",  # Výdaje budúcich období
    "default_accrued_revenue_account_id": "chart_sk_385000",  # Príjmy budúcich období
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "res.company")
    def _get_sk_res_company_cutoff(self):
        # Merged with l10n_sk's own res.company contribution when the SK chart
        # is loaded — wires the deferral default accounts for new companies.
        return {self.env.company.id: dict(SK_CUTOFF_ACCOUNTS)}
