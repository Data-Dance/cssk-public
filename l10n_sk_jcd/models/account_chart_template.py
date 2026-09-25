# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

from .res_company import SK_JCD_CLEARING_ACCOUNT


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "res.company")
    def _get_sk_res_company_jcd(self):
        # Merged with l10n_sk's own res.company contribution when the SK chart
        # loads — wires the import clearing account and the duty product for new
        # companies. The product xmlid carries a dot, so the loader takes it as a
        # global reference instead of company-prefixing it like a chart record.
        return {
            self.env.company.id: {
                "l10n_sk_jcd_clearing_account_id": SK_JCD_CLEARING_ACCOUNT,
                "l10n_sk_jcd_duty_product_id": "l10n_sk_jcd.product_customs_duty",
            }
        }
