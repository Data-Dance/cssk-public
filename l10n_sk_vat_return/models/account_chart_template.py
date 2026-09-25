# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

from odoo.addons.account.models.chart_template import template

#: Received EU services — self-assessed under § 69 ods. 3, reported in
#: r09/r09a/r09b of the return and in KV oddiel B.1.
_logger = logging.getLogger(__name__)

SK_EU_SERVICE_TAXES = ("vs_eu_s_23", "vs_eu_s_19", "vs_eu_s_5")


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.tax")
    def _get_sk_vat_return_account_tax(self):
        """Received EU services, and the domestic taxes they are mapped from.

        Stock ``l10n_sk`` maps every domestic purchase tax, under the "Eu
        intra" fiscal position, to the ``vs_nad_eu_*`` taxes — the acquisition
        of GOODS from another member state, row 07/08 of the return. A service
        bought from an EU supplier is not an acquisition of goods: the place of
        supply is Slovakia and the recipient self-assesses under § 69 ods. 3,
        row 09/10. It was filed in the wrong row, and Odoo's mapping cannot
        tell the two apart, because a fiscal position maps a tax to a tax and
        never looks at the product.

        The chart already solves this on the SALE side by splitting the source:
        ``23% S`` (services) maps to ``0% EÚ S`` and ``23% T`` to ``0% EÚ T``.
        This does the same for purchases: domestic ``23% S`` / ``19% S`` /
        ``5% S`` purchase taxes with the Services scope, mapped under "Eu intra"
        to ``23% EÚ S`` / ``19% EÚ S`` / ``5% EÚ S``, which carry the
        repartition of the chart's own ``vs_rc_*`` (r09b/r10b, r09/r10,
        r09a/r10a). A service product gets the ``S`` tax as its vendor tax;
        goods keep the plain one and still map to the acquisition of goods.

        Reported by an external accountant: "Base odoo chýba nastavenie
        fiškálnej pozície na RC."
        """
        data = self._parse_csv("sk", "account.tax", module="l10n_sk_vat_return")
        self._deref_account_tags("sk", data)
        # The control statement routes self-assessment by this flag; set it
        # where the control statement is installed, and leave the field alone
        # where it is not (it belongs to l10n_cssk_kv_kh_base, which the VAT
        # return does not depend on). The KV module flags the same xmlids on
        # its own install, for the opposite installation order.
        if "cssk_control_is_reverse_charge" in self.env["account.tax"]._fields:
            for xmlid in SK_EU_SERVICE_TAXES:
                if xmlid in data:
                    data[xmlid]["cssk_control_is_reverse_charge"] = True
        return data

    def _cssk_load_sk_eu_service_taxes(self, companies):
        """Load the taxes above into companies that already have the chart.

        ``@template`` data only materialises when a chart is loaded, so an
        existing company would never get them. Reuses the chart loader for the
        same xmlids, company prefixing and tag/account dereferencing a fresh
        load produces — but ONLY for the taxes the company lacks: ``_load_data``
        rewrites an existing record and appends repartition lines to it, and a
        full ``try_loading`` duplicates nine stock ``l10n_sk`` taxes per run.
        """
        loaded = 0
        for company in companies:
            loader = self.sudo().with_company(company)
            # Parsed per company: the loader consumes the dicts it is given.
            data = loader._get_sk_vat_return_account_tax()
            missing = {
                xmlid: vals for xmlid, vals in data.items()
                if not loader.ref(xmlid, raise_if_not_found=False)
            }
            if not missing:
                continue
            # A company that deleted "Eu intra" or a VAT tax group cannot take
            # these taxes as shipped. That must cost it the taxes, not cost
            # every company the module: this runs in the install hook and the
            # upgrade, where one raise aborts the whole operation.
            try:
                with self.env.cr.savepoint():
                    loader._load_data({"account.tax": missing})
            except Exception:
                _logger.warning(
                    "EU-service taxes not loaded for %s — its chart lacks "
                    "something they refer to (fiscal position \"Eu intra\", "
                    "a VAT tax group or a tax account); create them by hand",
                    company.display_name, exc_info=True)
                continue
            loaded += len(missing)
        return loaded
