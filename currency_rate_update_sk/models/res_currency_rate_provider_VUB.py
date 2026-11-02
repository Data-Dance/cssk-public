# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import datetime
import re
from collections import defaultdict

import requests
from odoo import fields, models


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

        # List of currencies obrained from:
        # https://www.vub.sk/ludia/kurzovy-listok.html
        return [
            "AUD",
            "BGN",
            "CAD",
            "CNY",
            "CZK",
            "DKK",
            "GBP",
            "HUF",
            "CHF",
            "JPY",
            "NOK",
            "PLN",
            "RON",
            "SEK",
            "TRY",
            "USD",
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "VUB":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        content = defaultdict(dict)
        url = "https://www.vub.sk/Downloads/VUBteclist.txt"
        response = requests.get(url).text.splitlines()
        date = datetime.datetime.strptime(
            response[1].split()[2], "%d.%m.%Y"
        ).date()
        for row in response[4:]:
            row = re.sub(r"\s+", " ", row).strip()
            if row.split()[0] in currencies:
                content[date][row.split()[0]] = str(
                    float(row.split()[3].replace(",", "."))
                )
        return content
