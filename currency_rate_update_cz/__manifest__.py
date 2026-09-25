{
    "name": "Currency Rate Update CZ (ČNB)",
    "summary": "Czech National Bank (ČNB) daily exchange-rate provider for the "
               "OCA currency_rate_update framework.",
    "description": """
Currency Rate Update — Czech Republic (ČNB)
===========================================

Adds the **Česká národní banka** daily fixing as a
``res.currency.rate.provider`` to the OCA ``currency_rate_update`` framework.
CE-compatible — no Enterprise ``currency_rate_live`` dependency.

The ČNB publishes one daily fixing (CZK vs foreign currencies). For a CZK-base
company the stored rate is ``Amount / Rate`` (foreign per CZK), e.g.
``EMU|euro|1|EUR|24.170`` → 1/24.170, ``Japan|yen|100|JPY|13.043`` → 100/13.043.

Licensed AGPL-3 (derives from the AGPL ``currency_rate_update`` framework).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "post_init_hook": "post_init_hook",
    "data": ["data/res_currency_rate_provider_action.xml"],
    "depends": ["currency_rate_update"],
    "installable": True,
}
