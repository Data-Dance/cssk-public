=========
Changelog
=========

All notable changes to **l10n_cz_payment_reliability** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.2] — 2026-07-04
-------------------------

Changed
~~~~~~~

- External SOAP call hardened: request timeout and error surfacing on the ADIS web service
  (unreachable service / malformed response no longer silently fail). (Wave 2)
- Adopted ``normalize_vat()`` from ``l10n_cssk_core`` for DIČ handling. (Wave 3)

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech provider for ``l10n_cssk_payment_reliability`` against the MFČR ADIS SOAP web service
  (``/dpr/axis2/``, ``rozhraniCRPDPH`` / ``getStatusNespolehlivyPlatce``; no API key required).
- Tax reliability — nespolehlivý plátce: ANO → unreliable, NE → reliable, NENALEZEN → unknown.
- Registered bank accounts (zveřejněné účty): ``standardníÚčet`` (předčíslí/číslo/kódBanky)
  converted to IBAN to match the bill's bank account; ``nestandardníÚčet`` taken as-is.
- cs_CZ jsonb translations (i18n sweep).
