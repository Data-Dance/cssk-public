=====================================
SK Bank FX Rates — shared fetch/parse
=====================================

Single source of truth for the Slovak commercial-bank exchange-rate feeds. It
provides the shared **VÚB** *kurzový lístok* and **Tatra banka** RSS fetch and
parse helpers on which the Slovak providers of OCA ``currency_rate_update``
(``currency_rate_update_sk``) build. There is no Enterprise
(``currency_rate_live``) provider built on them; on Enterprise, install the
OCA module as well.

Rates are expressed as ``1 EUR = X`` foreign currency. The parse functions
return ``{date: {ccy: rate_str}}`` — the format the OCA
``res.currency.rate.provider`` consumes directly.

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

This is a base library; it is not used directly. Install
``currency_rate_update_sk``, which depends on it, and configure the rate update
there. To use the helpers from your own code::

    from odoo.addons.currency_rate_sk_base.utils import sk_rates
    text = sk_rates.fetch_vub_text()
    rates = sk_rates.parse_vub(text, sk_rates.VUB_CURRENCIES)

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
