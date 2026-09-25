{
    "name": "SK Supplier Reliability — FS open-data provider",
    "summary": "Slovak provider for the CZ/SK supplier-reliability check: "
               "registered bank accounts (ds_dph_iban) and the tax-reliability "
               "index (ds_iz_ran) from the Financial Administration open data.",
    "description": """
SK Supplier Reliability provider
================================

Implements the country provider for ``l10n_cssk_payment_reliability`` against the
Slovak Financial Administration open-data API
(``iz.opendata.financnasprava.sk``):

* **Registered bank accounts** — dataset ``ds_dph_iban`` (the accounts a VAT
  payer notified to the tax authority), looked up by IČ DPH.
* **Tax reliability index** — dataset ``ds_iz_ran`` (*index daňovej
  spoľahlivosti*: vysoko spoľahlivý / spoľahlivý / menej spoľahlivý), looked up
  by IČO.

Requires an FS open-data **API key** (Settings → Accounting → "FS open-data API
key"; register at opendata.financnasprava.sk). Without a key the provider is
inert and the base reports "not checked".
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.3",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_payment_reliability", "l10n_sk"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
