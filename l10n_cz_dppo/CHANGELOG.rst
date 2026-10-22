=========
Changelog
=========

All notable changes to **l10n_cz_dppo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

TODO
~~~~

- CZ asset ř.50/150 wiring is still pending. The asset book-vs-tax difference is not yet fed
  into the DPPDP9 spine (připočitatelné ř.50 / odčitatelné ř.150); the SK counterpart
  (``l10n_sk_dppo``) is wired via the ``asset_diff`` line kind, CZ is not.

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Statutory rounding unified to HALF-UP (``statutory_round()``/``statutory_whole()``). (Wave 1)
- Multi-company ``ir.rule`` (``company_id in company_ids``) added. (Wave 1)

Fixed
~~~~~

- Removed ``typ_ds="P"`` from the DPPDP9 VetaP element — that attribute belongs to the DPH forms,
  not the income-tax return. (Wave 1)
- EPO Pisemnost/DPPDP9 XML: empty attributes now emitted as ``None`` (omitted) instead of ``""``
  (XSD-invalid). (Wave 1)

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech corporate income-tax return (DPPDP9) on ``l10n_cssk_income_tax_base``: II. oddíl tax
  spine (ř.10 → ř.340) mapped to the EPO ``VetaO/@kc_ii*`` attributes.
- ř.10 (výsledek hospodaření před zdaněním) computed from the P&L (class 6 − class 5, excluding
  income-tax accounts 591–599); připočitatelné/odčitatelné adjustments, §34 deductions and slevy
  are accountant-entered and aggregate into the spine.
- EPO Pisemnost/DPPDP9 XML export validated against the bundled official XSD
  (``data/dppdp9_epo2.xsd``).
- cs_CZ jsonb translations (i18n sweep).
