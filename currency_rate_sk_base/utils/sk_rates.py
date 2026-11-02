# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Shared fetch + parse for the Slovak commercial-bank FX feeds.

Rates are expressed as ``1 EUR = X`` foreign currency. ``parse_vub`` /
``parse_tb`` return ``{datetime.date: {ccy: rate_str}}`` — the format consumed
by the OCA ``res.currency.rate.provider`` (CE) directly, and trivially adapted
to Enterprise ``currency_rate_live``'s ``{ccy: (rate, date)}`` (EE).
"""
import datetime
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

import requests

# Browser-like UA — both bank endpoints reject the default python-requests UA
# (tatrabanka.sk additionally sits behind Cloudflare).
_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

VUB_URL = "https://www.vub.sk/Downloads/VUBteclist.txt"
TB_URL = "https://www.tatrabanka.sk/en/about-bank/rss-channels/exchange-rates/"

# Currencies published on each bank's kurzový lístok.
VUB_CURRENCIES = [
    "AUD", "BGN", "CAD", "CNY", "CZK", "DKK", "GBP", "HUF", "CHF",
    "JPY", "NOK", "PLN", "RON", "SEK", "TRY", "USD",
]
TB_CURRENCIES = ["CZK", "GBP", "HUF", "PLN", "SEK", "CHF", "USD"]


# ---------------------------------------------------------------------------
# VÚB banka — kurzový lístok text feed
# ---------------------------------------------------------------------------
def fetch_vub_text():
    response = requests.get(VUB_URL, headers={"User-Agent": _UA}, timeout=30)
    response.raise_for_status()
    return response.text


def parse_vub(text, currencies):
    """Parse the VÚB *kurzový lístok* text feed.

    Layout (whitespace-separated, header on lines 0-3, data from line 4)::

        Kurzový listok VÚB, a.s.
        platný od 11.06.2026 07:30
        <blank>
        Mena  Devíza nákup  Devíza stred  Devíza predaj  Valuta ...
        AUD   1,6780        1,6451        1,6122         1,7117 ...

    Uses **Devíza stred** (column index 2) — the middle rate for accounting
    valuation. Returns ``{date: {ccy: rate_str}}``.
    """
    lines = text.splitlines()
    date = datetime.datetime.strptime(lines[1].split()[2], "%d.%m.%Y").date()
    content = defaultdict(dict)
    for row in lines[4:]:
        row = re.sub(r"\s+", " ", row).strip()
        if not row:
            continue
        cols = row.split()
        if cols[0] in currencies:
            content[date][cols[0]] = str(float(cols[2].replace(",", ".")))
    return content


# ---------------------------------------------------------------------------
# Tatra banka — exchange-rate RSS feed
# ---------------------------------------------------------------------------
def fetch_tb_text():
    response = requests.get(TB_URL, headers={"User-Agent": _UA}, timeout=30)
    response.raise_for_status()
    return response.text


def parse_tb(xml_text, currencies, date_from, date_to):
    """Parse the Tatra banka exchange-rate RSS feed.

    Each ``<item>`` carries a ``<pubDate>`` and a ``<description>`` whose text
    is ``<br />``-separated ``"<rate> <CURRENCY>"`` pairs after a lead segment.
    Rate is ``1 EUR = X`` foreign currency. Returns ``{date: {ccy: rate_str}}``.
    """
    content = defaultdict(dict)
    root = ET.fromstring(xml_text)
    for row in root.find("channel").findall("item"):
        date = datetime.datetime.strptime(
            row.find("pubDate").text, "%a, %d %b %Y %H:%M:%S %z"
        ).date()
        if not (date_from <= date <= date_to):
            continue
        description = row.find("description")
        for chunk in description.text.split("<br />")[1:]:
            parts = chunk.split(" ")
            currency, rate = parts[-1], parts[-2].replace(",", ".")
            if currency in currencies:
                content[date][currency] = rate
    return content
