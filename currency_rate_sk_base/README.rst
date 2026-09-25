=====================================
SK Bank FX Rates — shared fetch/parse
=====================================

Single source of truth for the Slovak commercial-bank exchange-rate feeds. It
provides the shared **VÚB** *kurzový lístok* and **Tatra banka** RSS fetch and
parse helpers on which both the Community (OCA ``currency_rate_update``) and
Enterprise (``currency_rate_live``) Slovak rate providers build, so neither
edition has to duplicate any feed logic.

Rates are expressed as ``1 EUR = X`` foreign currency. The parse functions
return ``{date: {ccy: rate_str}}`` — the format the OCA
``res.currency.rate.provider`` (CE) consumes directly, and which is trivially
adapted to Enterprise ``currency_rate_live``'s ``{ccy: (rate, date)}`` (EE).

This module defines **no models** — it is a library of pure helpers imported via
``odoo.addons.currency_rate_sk_base.utils.sk_rates``.

Features
========

* ``fetch_vub_text`` / ``parse_vub`` — VÚB *kurzový lístok* text feed, using the
  **Devíza stred** (middle) rate for accounting valuation.
* ``fetch_tb_text`` / ``parse_tb`` — Tatra banka exchange-rate RSS feed, parsed
  over a date range.
* Per-bank supported-currency lists (``VUB_CURRENCIES`` / ``TB_CURRENCIES``).
* Browser-like User-Agent so the bank endpoints (Tatra banka sits behind
  Cloudflare) do not reject the request.

Usage
=====

This is a base library; it is not used directly. Install the edition-specific
Slovak rate provider that depends on it (OCA ``currency_rate_update`` bridge on
Community, ``currency_rate_live`` bridge on Enterprise) and configure the rate
update there. To use the helpers from your own code::

    from odoo.addons.currency_rate_sk_base.utils import sk_rates
    text = sk_rates.fetch_vub_text()
    rates = sk_rates.parse_vub(text, sk_rates.VUB_CURRENCIES)

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
