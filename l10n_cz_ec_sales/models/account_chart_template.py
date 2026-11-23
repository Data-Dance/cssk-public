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
    "l10n_cz_triangular_supply": "2",
}

#: The taxes this module adds to the l10n_cz chart (data/template).
TRIANGULAR_TAXES = ("l10n_cz_triangular_acquisition", "l10n_cz_triangular_supply")


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("cz", "account.tax")
    def _get_cz_ec_sales_account_tax(self):
        """The intermediary's triangular-trade taxes, and the Souhrnné hlášení
        transaction code on the intra-EU supply taxes.

        The l10n_cz chart has the return tags for rows 30 and 31 (VAT 30,
        VAT 31) but no tax that carries them, so the intermediary in a
        § 17 triangular trade had nothing to post with: the acquisition and
        the supply reached neither the return nor the EC sales list, where
        the supply is reported under code 2. Both are 0 % — the intermediary
        pays no VAT on either leg; the end customer does — and report the
        base only.

        Merged into the l10n_cz chart, so a company that gets the chart
        AFTER this module is installed has the taxes and the codes too. The
        install hook only reaches companies that already had the chart;
        without this, every company charted later computed an empty
        Souhrnné hlášení.
        """
        data = self._parse_csv("cz", "account.tax", module="l10n_cz_ec_sales")
        self._deref_account_tags("cz", data)
        for xmlid, ec_code in EC_CODES.items():
            data.setdefault(xmlid, {})["cssk_ec_summary_code"] = ec_code
        return data
