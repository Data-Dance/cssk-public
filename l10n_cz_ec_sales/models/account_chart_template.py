# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

# l10n_cz tax template -> Souhrnné hlášení kód plnění (k_pln):
#   0 = dodání zboží do JČS, 1 = přemístění obch. majetku,
#   2 = třístranný obchod (prostřední osoba), 3 = poskytnutí služby
EC_CODES = {
    "l10n_cz_supply_goods_eu": "0",
    "l10n_cz_supply_service_eu": "3",
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("cz", "account.tax")
    def _get_cz_ec_sales_account_tax(self):
        """The Souhrnné hlášení transaction code on the stock intra-EU supply taxes.

        Merged into the l10n_cz chart, so a company that gets the chart
        AFTER this module is installed has the codes too. The install hook only
        reaches companies that already had the chart; without this, every
        company charted later computed an empty Souhrnné hlášení.
        """
        return {
            xmlid: {"cssk_ec_summary_code": ec_code}
            for xmlid, ec_code in EC_CODES.items()
        }
