{
    "name": "SK Bank FX Rates — shared fetch/parse",
    "summary": "Shared VÚB / Tatra banka exchange-rate fetch + parse. The CE "
               "(OCA currency_rate_update) and EE (currency_rate_live) SK "
               "providers both build on this.",
    "description": """
Single source of truth for the Slovak commercial-bank exchange-rate feeds:

* ``utils.sk_rates.parse_vub`` — VÚB *kurzový lístok* text feed (Devíza stred)
* ``utils.sk_rates.parse_tb`` — Tatra banka exchange-rate RSS feed
* ``fetch_vub_text`` / ``fetch_tb_text`` + the per-bank supported-currency lists

Rates are ``1 EUR = X`` foreign currency. The parse functions return
``{date: {ccy: rate_str}}`` so the edition-specific providers — OCA
``res.currency.rate.provider`` (CE) and Enterprise ``currency_rate_live`` (EE) —
reuse them without duplicating any feed logic. No models; pure helpers imported
via ``odoo.addons.currency_rate_sk_base.utils.sk_rates``.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Localizations",
    "version": "19.0.1.0.1",
    "depends": ["base"],
    "license": "AGPL-3",
}
