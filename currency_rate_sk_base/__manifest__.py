{
    "name": "SK Bank FX Rates — shared fetch/parse",
    "summary": "Shared VÚB / Tatra banka exchange-rate fetch + parse for the "
               "Slovak providers of OCA currency_rate_update.",
    "description": """
Single source of truth for the Slovak commercial-bank exchange-rate feeds:

* ``utils.sk_rates.parse_vub`` — VÚB *kurzový lístok* text feed (Devíza stred)
* ``utils.sk_rates.parse_tb`` — Tatra banka exchange-rate RSS feed
* ``fetch_vub_text`` / ``fetch_tb_text`` + the per-bank supported-currency lists

Rates are ``1 EUR = X`` foreign currency. The parse functions return
``{date: {ccy: rate_str}}``, which the OCA ``res.currency.rate.provider`` of
``currency_rate_update_sk`` consumes. There is no Enterprise
(``currency_rate_live``) provider built on it; the helpers are kept free of
models so one could be. Pure helpers imported via
``odoo.addons.currency_rate_sk_base.utils.sk_rates``.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Localizations",
    "version": "19.0.1.0.2",
    "depends": ["base"],
    "license": "AGPL-3",
}
