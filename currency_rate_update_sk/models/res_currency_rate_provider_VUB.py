# Copyright 2022-2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from odoo.addons.currency_rate_sk_base.utils.sk_rates import (
    VUB_CURRENCIES, fetch_vub_text, parse_vub,
)


class ResCurrencyRateProviderVUB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("VUB", "VÚB banka")],
        ondelete={"VUB": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "VUB":
            return super()._get_supported_currencies()  # pragma: no cover
        return list(VUB_CURRENCIES)

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "VUB":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        return parse_vub(fetch_vub_text(), currencies)

    @api.model
    def _vub_parse(self, text, currencies):
        """Thin wrapper over the shared parser (kept for the model API)."""
        return parse_vub(text, currencies)
