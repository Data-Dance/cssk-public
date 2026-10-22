=========
Changelog
=========

All notable changes to **l10n_sk_payment_reliability** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: Slovak country provider for ``l10n_cssk_payment_reliability`` against the FS open-data API (``iz.opendata.financnasprava.sk``).
- **Registered bank accounts** — dataset ``ds_dph_iban`` (accounts a VAT payer notified to the tax authority), looked up by IČ DPH.
- **Tax reliability index** — dataset ``ds_iz_ran`` (index daňovej spoľahlivosti: vysoko spoľahlivý / spoľahlivý / menej spoľahlivý), looked up by IČO.
- Requires an FS open-data API key (Settings → Accounting); the provider is inert and reports "not checked" without one.
