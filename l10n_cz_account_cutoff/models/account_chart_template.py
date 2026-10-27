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


# No VAT on an accrual. The OCA engine defaults to accruing the tax as well
# (French practice, on a "TVA sur factures non parvenues" account), which has
# no account to go to here and makes every taxed accrual fail with "Missing
# 'Accrued Expense Tax Account'". Nor would it be right: input VAT cannot be
# deducted before the tax document is in hand (§ 73 odst. 1 písm. a) zákona
# 235/2004), and output VAT reaches the return through the document itself.
# So the accrual on 383/385 is the amount without VAT.
CZ_CUTOFF_FLAGS = {
    "accrual_taxes": False,
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("cz", "res.company")
    def _get_cz_res_company_cutoff(self):
        return {self.env.company.id: {**CZ_CUTOFF_ACCOUNTS, **CZ_CUTOFF_FLAGS}}
