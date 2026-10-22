# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from collections import defaultdict

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
# English daily fixing; accepts ?date=DD.MM.YYYY for a specific day.
_CNB_URL = (
    "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/"
    "central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/daily.txt"
)


class ResCurrencyRateProviderCNB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("CNB", "Česká národní banka")],
        ondelete={"CNB": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "CNB":
            return super()._get_supported_currencies()  # pragma: no cover
        return [
            "AUD", "BRL", "BGN", "CAD", "CNY", "DKK", "EUR", "HKD", "HUF",
            "CHF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW", "MXN", "MYR",
            "NOK", "NZD", "PHP", "PLN", "RON", "SEK", "SGD", "THB", "TRY",
            "USD", "GBP", "ZAR", "XDR",
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "CNB":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        params = {}
        if date_to:
            params["date"] = date_to.strftime("%d.%m.%Y")
        resp = requests.get(
            _CNB_URL, params=params, headers={"User-Agent": _UA}, timeout=30
        )
        resp.raise_for_status()
        return self._cnb_parse(resp.text, currencies)

    @api.model
    def _cnb_parse(self, text, currencies):
        """Parse the ČNB daily fixing into provider content.

        Layout::

            12 Jun 2026 #112
            Country|Currency|Amount|Code|Rate
            EMU|euro|1|EUR|24.170
            Japan|yen|100|JPY|13.043

        Rate is ``Amount`` foreign = ``Rate`` CZK, so for a CZK-base company the
        stored rate (foreign per CZK) is ``Amount / Rate``.
        """
        lines = [line for line in text.splitlines() if line.strip()]
        date = datetime.datetime.strptime(
            lines[0].split("#")[0].strip(), "%d %b %Y"
        ).date()
        content = defaultdict(dict)
        for row in lines[2:]:  # line 1 is the column header
            parts = row.split("|")
            if len(parts) < 5:
                continue
            try:
                amount = float(parts[2].replace(",", "."))
                rate = float(parts[4].replace(",", "."))
            except ValueError:
                continue
            code = parts[3].strip()
            if code in currencies and rate:
                content[date][code] = str(amount / rate)
        return content
