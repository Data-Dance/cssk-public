# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict

import requests
from odoo import fields, models


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

        # List of currencies obrained from:
        # https://www.tatrabanka.sk/en/about-bank/rss-channels/exchange-rates/
        return ["CZK", "GBP", "HUF", "PLN", "SEK", "CHF", "USD"]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "TB":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        if date_from < datetime.date.today() - datetime.timedelta(days=30):
            date_from = datetime.date.today() - datetime.timedelta(days=30)
        content = defaultdict(dict)
        url = "https://www.tatrabanka.sk/en/about-bank/rss-channels/exchange-rates/"
        response = requests.get(url)
        root = ET.fromstring(response.text)
        for row in root.find("channel").findall("item"):
            date = datetime.datetime.strptime(
                row.find("pubDate").text, "%a, %d %b %Y %H:%M:%S %z"
            ).date()
            description = row.find("description")
            for c in description.text.split("<br />")[1:]:
                currency, rate = c.split(" ")[-1], c.split(" ")[-2].replace(
                    ",", "."
                )
                if currency in currencies and date_from <= date <= date_to:
                    content[date][currency] = rate
        return content
