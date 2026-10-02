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
# Every fixing of one calendar year: ?year=YYYY.
_CNB_YEAR_URL = (
    "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/"
    "central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/year.txt"
)


class ResCurrencyRateProviderCNB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("CNB", "Česká národní banka")],
        ondelete={"CNB": "set default"},
    )
    cnb_rate_mode = fields.Selection(
        [("daily", "Daily rate (denní kurz)"),
         ("monthly", "Fixed monthly rate (pevný kurz)")],
        string="ČNB rate", default="daily",
        help="Daily: every ČNB fixing is stored and a document takes the rate "
        "of its day. Fixed monthly: one rate per month, dated the 1st, which "
        "Odoo then applies to the whole month (§ 24 odst. 6 ZoÚ; for VAT "
        "§ 38 ZDPH). The actual daily fixings are still kept, apart, for the "
        "balance-sheet revaluation, which must use the rate of that day.\n\n"
        "Switching to monthly does not delete daily rates already stored; "
        "remove those for the months that should use the fixed rate.")
    cnb_monthly_reference = fields.Selection(
        [("first_day", "Rate valid on the 1st of the month"),
         ("previous_month_end", "Last fixing of the previous month")],
        string="Fixed rate taken from", default="first_day",
        help="Which ČNB fixing a month's fixed rate is. They differ only when "
        "the 1st is itself a fixing day.")

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
        if self.cnb_rate_mode == "monthly":
            return self._cnb_obtain_monthly(
                currencies, date_from or date_to, date_to)
        if date_from and date_to and date_from < date_to:
            return self._cnb_obtain_range(currencies, date_from, date_to)
        return self._cnb_obtain_day(currencies, date_to)

    def _cnb_obtain_monthly(self, currencies, date_from, date_to):
        """One rate per month touched by the range, dated the 1st.

        Reads every fixing from shortly before the first month (the
        reference fixing of a month can fall in the one before), keeps them
        all as actual rates for the revaluation, and returns for each month
        the fixing valid on its reference day — the last fixing on or before
        it, which is how ČNB defines the rate of a day without its own.
        """
        first = date_from.replace(day=1)
        fixings = self._cnb_obtain_range(
            currencies, first - datetime.timedelta(days=14), date_to)
        self._cnb_store_actual(fixings)
        days = sorted(fixings)
        content = {}
        month = first
        while month <= date_to:
            reference = (month if self.cnb_monthly_reference == "first_day"
                         else month - datetime.timedelta(days=1))
            valid = [d for d in days if d <= reference]
            if valid:
                content[month] = dict(fixings[valid[-1]])
            month = (month + datetime.timedelta(days=32)).replace(day=1)
        return content

    def _cnb_store_actual(self, fixings):
        """Keep the actual daily fixings apart from the fixed monthly rate."""
        Actual = self.env["cssk.currency.rate.actual"].sudo()
        company = self.company_id
        codes = {c for rates in fixings.values() for c in rates}
        currencies = {
            c.name: c for c in self.env["res.currency"].with_context(
                active_test=False).search([("name", "in", list(codes))])}
        existing = {
            (a.name, a.currency_id.id): a for a in Actual.search([
                ("company_id", "=", company.id),
                ("name", "in", list(fixings)),
            ])}
        to_create = []
        for day, rates in fixings.items():
            for code, value in rates.items():
                currency = currencies.get(code)
                if not currency:
                    continue
                known = existing.get((day, currency.id))
                if known:
                    known.rate = float(value)
                else:
                    to_create.append({
                        "name": day, "currency_id": currency.id,
                        "company_id": company.id, "rate": float(value)})
        if to_create:
            Actual.create(to_create)

    def _cnb_obtain_day(self, currencies, day):
        params = {}
        if day:
            params["date"] = day.strftime("%d.%m.%Y")
        resp = requests.get(
            _CNB_URL, params=params, headers={"User-Agent": _UA}, timeout=30
        )
        resp.raise_for_status()
        return self._cnb_parse(resp.text, currencies)

    def _cnb_obtain_range(self, currencies, date_from, date_to):
        """Every fixing from ``date_from`` to ``date_to``, one request a year.

        The daily feed answers for ONE day, and this provider used to send it
        only ``date_to``: *Update rates* over January–June stored 30 June and
        nothing else, so a back-dated document took whatever earlier rate
        happened to exist. § 38 ZDPH wants the rate valid on the day the tax
        point arises, and a history import is exactly the job that needs it.

        A range starting on a weekend or holiday has no fixing of its own; the
        rate valid then is the last one before it, so that is fetched too —
        dated with its own day, which is how Odoo resolves the gap.
        """
        content = defaultdict(dict)
        for year in range(date_from.year, date_to.year + 1):
            resp = requests.get(
                _CNB_YEAR_URL, params={"year": year},
                headers={"User-Agent": _UA}, timeout=60,
            )
            resp.raise_for_status()
            for day, rates in self._cnb_parse_year(resp.text, currencies).items():
                if date_from <= day <= date_to:
                    content[day].update(rates)
        if date_from not in content:
            for day, rates in self._cnb_obtain_day(currencies, date_from).items():
                if day <= date_from:
                    content[day].update(rates)
        return content

    @api.model
    def _cnb_parse_year(self, text, currencies):
        """Parse the ČNB yearly file into provider content.

        Layout::

            Date|1 AUD|1 BGN|...|100 HUF|...|1 USD
            02.01.2025|15.145|12.872|...|6.097|...|24.398

        The header repeats wherever the currency set changed during the year
        — 2022 has a second one after the rouble was dropped — so each
        ``Date`` line restarts the column list rather than the first one
        being trusted for the whole file.
        """
        content = defaultdict(dict)
        columns = None
        for line in text.splitlines():
            parts = [part.strip() for part in line.split("|")]
            if not parts or not parts[0]:
                continue
            if parts[0] == "Date":
                columns = parts[1:]
                continue
            if columns is None:
                continue
            try:
                day = datetime.datetime.strptime(parts[0], "%d.%m.%Y").date()
            except ValueError:
                continue
            for head, value in zip(columns, parts[1:]):
                amount, _sep, code = head.partition(" ")
                if code not in currencies or not value:
                    continue
                try:
                    amount = float(amount)
                    rate = float(value.replace(",", "."))
                except ValueError:
                    continue
                if rate:
                    content[day][code] = str(amount / rate)
        return content

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
        if len(lines) < 2:
            # An empty or truncated answer is no fixing, not a crash.
            return defaultdict(dict)
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
