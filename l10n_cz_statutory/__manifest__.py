{
    "name": "CZ Localization — Statutory Reference Data",
    "version": "19.0.1.3.0",
    "summary": "Czech statutory reference registries: finanční úřady (seeded "
               "from the official l10n_cz.tax_office codelist) and person types.",
    "description": """
CZ Localization — Statutory Reference Data
==========================================

Czech-specific seed data for the country-neutral registries defined in
``l10n_cssk_core``:

* ``cssk.tax.authority`` — the regional finanční úřady. Their **c_ufo codes** are
  seeded from the official ``l10n_cz.tax_office`` codelist (single source of
  truth), with curated Czech office names; plus the Specializovaný finanční úřad.
* ``cssk.person.type`` — Czech taxpayer types (FO / PO).

This keeps CZ-specific data out of the shared ``l10n_cssk_core`` so it never
loads on a Slovak database.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cz", "l10n_cssk_core", "partner_nace"],
    "data": [
        "data/cz_person_type_data.xml",
        "views/res_company_views.xml",
        "views/account_move_views.xml",
    ],
    "post_init_hook": "_seed_cz_tax_authorities",
    "installable": True,
}
