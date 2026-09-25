=============================================
SK Supplier Reliability — FS open-data provider
=============================================

The Slovak country provider for the shared CZ/SK supplier-reliability check
(``l10n_cssk_payment_reliability``). It queries the Slovak Financial
Administration open-data API (``iz.opendata.financnasprava.sk``) to verify a
supplier's registered bank accounts and tax-reliability index.

Features
========

* **Registered bank accounts** — dataset ``ds_dph_iban`` (the accounts a VAT
  payer notified to the tax authority), looked up by **IČ DPH**.
* **Tax reliability index** — dataset ``ds_iz_ran`` (*index daňovej
  spoľahlivosti*: vysoko spoľahlivý / spoľahlivý / menej spoľahlivý), looked up
  by **IČO**.
* Plugs into the shared reliability base, so the result appears wherever the
  base surfaces the check (partner / vendor bill).

Usage
=====

The provider needs an FS open-data **API key**. Set it in
*Settings ▸ Accounting ▸ "FS open-data API key"* (register at
``opendata.financnasprava.sk``). Without a key the provider is inert and the
base reports "not checked". With the key configured, the supplier-reliability
check on partners and vendor bills is answered from the Slovak datasets.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
