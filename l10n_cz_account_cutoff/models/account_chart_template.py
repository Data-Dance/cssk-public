# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.account.models.chart_template import template

CZ_CUTOFF_ACCOUNTS = {
    "default_prepaid_expense_account_id": "chart_cz_381000",  # Náklady příštích období
    "default_prepaid_revenue_account_id": "chart_cz_384000",  # Výnosy příštích období
    "default_accrued_expense_account_id": "chart_cz_383000",  # Výdaje příštích období
    "default_accrued_revenue_account_id": "chart_cz_385000",  # Příjmy příštích období
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("cz", "res.company")
    def _get_cz_res_company_cutoff(self):
        return {self.env.company.id: dict(CZ_CUTOFF_ACCOUNTS)}
