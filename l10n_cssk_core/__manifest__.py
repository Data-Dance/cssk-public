{
    "name": "CZ/SK Localization — Shared Core",
    "version": "19.0.1.14.0",
    "summary": "Country-neutral foundation for the Czech & Slovak statutory "
               "localization: tax-authority registry, person types, shared "
               "company/partner fields, settings and security.",
    "description": """
CZ/SK Localization — Shared Core
================================

The country-neutral substrate every other ``l10n_cssk_*`` / ``l10n_sk_*``
/ ``l10n_cz_*`` module builds on. It deliberately depends on **Odoo core
only** (``account`` + ``mail``) — no ``account_reports`` and no OCA report
engine — so it is installable on both Community and Enterprise, and on 18.0 and
19.0.

Provides:

* ``cssk.tax.authority`` — registry of tax offices (daňový úrad / finanční
  úřad) with the code used in statutory XML submissions.
* ``cssk.person.type`` — person/entity-type catalogue (FO / PO …).
* ``res.company`` / ``res.partner`` extensions wiring those registries.
* Settings + security scaffolding.
* Documented hook points for the customer's own components (PAY by Square,
  ARES/FinStat lookup) — see ``static/description``.

This module ships **no statutory logic itself**; it is the shared base for
``l10n_cssk_kv_kh_base`` (control statement), ``l10n_cssk_ec_summary_base``
(EC sales list), ``l10n_cssk_fs_base`` (financial statements) and the
country layers.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/cssk_tax_authority_rules.xml",
        "views/cssk_tax_authority_views.xml",
        "views/cssk_person_type_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/account_move_views.xml",
        "views/cssk_statutory_footprint_views.xml",
        "views/cssk_filing_comparison_views.xml",
        "views/cssk_filing_discrepancy_views.xml",
        "views/res_config_settings_views.xml",
        "views/cssk_core_menus.xml",
    ],
    "installable": True,
}
