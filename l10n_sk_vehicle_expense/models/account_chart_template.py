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
        """Create the vehicle taxes in companies that already have the chart.

        ``@template`` data only materialises when a chart is loaded, so a
        company whose chart predates this module would never get them. The
        chart loader is reused for the same xmlids, company prefixing and
        tag/account dereferencing a fresh load produces, but ONLY for the taxes
        the company lacks: ``_load_data`` rewrites an existing record and
        appends repartition lines to it, and a full ``try_loading`` duplicates
        nine stock ``l10n_sk`` taxes per run.

        Returns the number of taxes created.
        """
        loaded = 0
        for company in companies:
            loader = self.sudo().with_company(company)
            # Parsed per company: the loader consumes the dicts it is given.
            data = loader._get_sk_vehicle_account_tax()
            missing = {
                xmlid: vals for xmlid, vals in data.items()
                if not loader.ref(xmlid, raise_if_not_found=False)
            }
            if not missing:
                continue
            # A company that deleted 343110, 343120, 548000 or a VAT tax group cannot
            # take the taxes as shipped. That must cost it the taxes, not cost
            # every company the module: this runs in the install hook, where
            # one raise aborts the whole installation.
            try:
                with self.env.cr.savepoint():
                    loader._load_data({"account.tax": missing})
            except Exception:
                _logger.warning(
                    "Vehicle taxes not created for %s: its chart lacks an "
                    "account or tax group they refer to (343110, 343120, 548000, the "
                    "23 %% or 19 %% VAT group); create them by hand",
                    company.display_name, exc_info=True)
                continue
            loaded += len(missing)
        return loaded

    def _l10n_sk_vehicle_fix_19_account(self, companies):
        """Move vs_auto_19's deducted half from 343120 to 343110.

        Up to 19.0.1.0.3 the 19 % vehicle tax shipped with 343120, the 23 %
        input-VAT account. Only repartition lines still on the shipped 343120
        are moved; returns how many were.
        """
        moved = 0
        for company in companies:
            loader = self.sudo().with_company(company)
            tax = loader.ref("vs_auto_19", raise_if_not_found=False)
            wrong = loader.ref("chart_sk_343120", raise_if_not_found=False)
            right = loader.ref("chart_sk_343110", raise_if_not_found=False)
            if not (tax and wrong and right):
                continue
            lines = tax.repartition_line_ids.filtered(
                lambda line: line.account_id == wrong
            )
            if lines:
                lines.account_id = right
                moved += len(lines)
                _logger.info(
                    "vs_auto_19 of %s: %s line(s) moved to 343110",
                    company.display_name, len(lines))
        return moved

    @template("sk", "res.company")
    def _get_sk_res_company_vehicle(self):
        return {
            self.env.company.id: {
                "l10n_sk_vehicle_nondeductible_account_id": (
                    SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT
                ),
            }
        }
