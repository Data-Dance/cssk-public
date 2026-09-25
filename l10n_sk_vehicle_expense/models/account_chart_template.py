# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

from .res_company import SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.tax")
    def _get_sk_vehicle_account_tax(self):
        """The § 85n 50 %-deductible vehicle taxes.

        Loaded from this module's own template CSV and merged into the SK chart,
        the same way l10n_tr_nilvera_einvoice_extended adds its withholding taxes.
        Splitting the deduction in the tax *repartition* is the only way to keep
        the DPH rows right: half the VAT reaches 343 carrying the deduction tag,
        the other half lands on a non-deductible expense account carrying none.
        """
        additional = self._parse_csv(
            "sk", "account.tax", module="l10n_sk_vehicle_expense"
        )
        self._deref_account_tags("sk", additional)
        return additional

    @template("sk", "res.company")
    def _get_sk_res_company_vehicle(self):
        return {
            self.env.company.id: {
                "l10n_sk_vehicle_nondeductible_account_id": (
                    SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT
                ),
            }
        }
