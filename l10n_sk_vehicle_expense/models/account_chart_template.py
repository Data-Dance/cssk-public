# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

from odoo.addons.account.models.chart_template import template

from .res_company import SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT

_logger = logging.getLogger(__name__)


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

    def _l10n_sk_vehicle_load_taxes(self, companies):
        """Create the vehicle taxes a company with the chart lacks.

        ``@template`` data only materialises when a chart is loaded, so a
        company whose chart predates a tax never gets it. The chart loader is
        reused for the same xmlids, company prefixing and tag/account
        dereferencing a fresh load produces, but ONLY for the taxes the company
        lacks: ``_load_data`` rewrites an existing record and appends
        repartition lines to it. A company whose chart lacks an account or tax
        group the taxes need is skipped with a warning rather than aborting the
        upgrade for every company. Returns the number of taxes created.
        """
        loaded = 0
        for company in companies:
            loader = self.sudo().with_company(company)
            data = loader._get_sk_vehicle_account_tax()
            missing = {
                xmlid: vals for xmlid, vals in data.items()
                if not loader.ref(xmlid, raise_if_not_found=False)
            }
            if not missing:
                continue
            try:
                with self.env.cr.savepoint():
                    loader._load_data({"account.tax": missing})
            except Exception:
                _logger.warning(
                    "Vehicle taxes not created for %s: its chart lacks an "
                    "account or tax group they refer to; create them by hand",
                    company.display_name, exc_info=True)
                continue
            loader._load_translations(companies=company)
            loaded += len(missing)
        return loaded

    @template("sk", "res.company")
    def _get_sk_res_company_vehicle(self):
        return {
            self.env.company.id: {
                "l10n_sk_vehicle_nondeductible_account_id": (
                    SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT
                ),
            }
        }
