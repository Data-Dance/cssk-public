###################################################################################
#
#    Copyright (c) 2022 Data Dance s.r.o.
#
#    Data Dance Proprietary License v1.0
#
#    This software and associated files (the "Software") may only be used
#    (executed, modified, executed after modifications) if you have
#    purchased a valid license from Data Dance s.r.o.
#
#    The above permissions are granted for a single database per purchased
#    license. Furthermore, with a valid license it is permitted to use the
#    software on other databases as long as the usage is limited to a testing
#    or development environment.
#
#    You may develop modules based on the Software or that use the Software
#    as a library (typically by depending on it, importing it and using its
#    resources), but without copying any source code or material from the
#    Software. You may distribute those modules under the license of your
#    choice, provided that this license is compatible with the terms of the
#    Data Dance Proprietary License (For example: LGPL, MIT, or proprietary
#    licenses similar to this one).
#
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###################################################################################


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
