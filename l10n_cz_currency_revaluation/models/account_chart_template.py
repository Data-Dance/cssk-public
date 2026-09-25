# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.account.models.chart_template import template

# Czech kurzové rozdiely accounts -> OCA account_multicurrency_revaluation
# fields. 563 = exchange losses, 663 = exchange gains.
CZ_REVAL_ACCOUNTS = {
    "revaluation_loss_account_id": "chart_cz_563000",
    "revaluation_gain_account_id": "chart_cz_663000",
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("cz", "res.company")
    def _get_cz_res_company_reval(self):
        return {self.env.company.id: dict(CZ_REVAL_ACCOUNTS)}
