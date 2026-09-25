# Copyright 2022-2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import api, fields, models

from odoo.addons.currency_rate_sk_base.utils.sk_rates import (
    TB_CURRENCIES, fetch_tb_text, parse_tb,
)


class ResCurrencyRateProviderTB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("TB", "Tatra banka")],
        ondelete={"TB": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "TB":
            return super()._get_supported_currencies()  # pragma: no cover
        return list(TB_CURRENCIES)

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "TB":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        # TB publishes up to ~30 days of history.
        if date_from < datetime.date.today() - datetime.timedelta(days=30):
            date_from = datetime.date.today() - datetime.timedelta(days=30)
        return parse_tb(fetch_tb_text(), currencies, date_from, date_to)

    @api.model
    def _tb_parse(self, xml_text, currencies, date_from, date_to):
        """Thin wrapper over the shared parser (kept for the model API)."""
        return parse_tb(xml_text, currencies, date_from, date_to)
