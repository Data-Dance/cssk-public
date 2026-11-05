# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

# l10n_sk tax template -> Súhrnný výkaz transaction code (KOD_PLN):
#   0 = dodanie tovaru, 1 = trojstranný obchod, 2 = dodanie služby
EC_CODES = {"vy_eu_m": "0", "vy_eu_t": "1", "vy_eu_s": "2"}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.tax")
    def _get_sk_ec_sales_account_tax(self):
        """The Súhrnný výkaz transaction code on the stock intra-EU supply taxes.

        Merged into the l10n_sk chart, so a company that gets the chart
        AFTER this module is installed has the codes too. The install hook only
        reaches companies that already had the chart; without this, every
        company charted later computed an empty Súhrnný výkaz.
        """
        return {
            xmlid: {"cssk_ec_summary_code": ec_code}
            for xmlid, ec_code in EC_CODES.items()
        }
