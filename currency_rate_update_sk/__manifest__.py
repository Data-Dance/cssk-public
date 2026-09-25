{
    "name": "Currency Rate Update SK (NBS/ECB + Slovak banks)",
    "summary": "Slovak FX-rate providers for OCA currency_rate_update: ECB "
               "reference rate (NBS statutory) with previous-day fill, plus "
               "VÚB and Tatra banka commercial rate lists.",
    "description": """
Currency Rate Update — Slovakia
===============================

Adds Slovak exchange-rate **providers** to the OCA ``currency_rate_update``
framework (``res.currency.rate.provider`` subclasses). CE-compatible — no
Enterprise ``currency_rate_live`` dependency.

Providers
---------

* **ECB** (ships in the OCA base) — the *referenčný výmenný kurz* the National
  Bank of Slovakia republishes from the European Central Bank. This is the rate
  used for statutory foreign-currency valuation in SK accounting.
* **VÚB banka** — the bank's daily *kurzový lístok* (Devíza stred / middle rate).
* **Tatra banka** — the bank's published exchange-rate RSS feed.

Previous-day fill
-----------------

Central banks and commercial banks do not publish on weekends and holidays.
With **Fill non-publishing days** enabled (default), after each sync the last
published rate is carried forward to every calendar day in the synced window, so
every day has an explicit ``res.currency.rate`` and a posting never lands on a
day with no rate.

The VÚB and Tatra banka providers publish *commercial* rates and are intended
for reconciling actual bank conversions; for statutory valuation use **ECB**.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["currency_rate_update", "currency_rate_sk_base"],
    "post_init_hook": "post_init_hook",
    "data": [
        "data/res_currency_rate_provider_action.xml",
        "views/res_currency_rate_provider.xml",
    ],
    "installable": True,
    "auto_install": False,
}
