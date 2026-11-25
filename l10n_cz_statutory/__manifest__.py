{
    "name": "CZ Localization — Statutory Reference Data",
    "version": "19.0.1.3.4",
    "summary": "Czech statutory reference registries: finanční úřady (seeded "
               "from the official l10n_cz.tax_office codelist).",
    "description": """
CZ Localization — Statutory Reference Data
==========================================

Czech-specific seed data for the country-neutral registries defined in
``l10n_cssk_core``:

* ``cssk.tax.authority`` — the regional finanční úřady. Their **c_ufo codes** are
  seeded from the official ``l10n_cz.tax_office`` codelist (single source of
  truth), with curated Czech office names; plus the Specializovaný finanční úřad.

This keeps the Czech tax offices out of the shared ``l10n_cssk_core`` so they
never load on a Slovak database. The Czech person types (FO / PO) were here
until 19.0.1.3.4 and are core data now: a Slovak database has Czech customers,
and they need a type too.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cz", "l10n_cssk_core", "partner_nace"],
    "data": [
        "views/res_company_views.xml",
        "views/account_move_views.xml",
    ],
    "post_init_hook": "_seed_cz_tax_authorities",
    "installable": True,
}
