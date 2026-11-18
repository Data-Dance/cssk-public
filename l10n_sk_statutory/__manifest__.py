{
    "name": "SK Localization — Statutory Reference Data",
    "version": "18.0.1.1.1",
    "summary": "Slovak statutory reference registries: daňové úrady and person "
               "types.",
    "description": """
SK Localization — Statutory Reference Data
==========================================

Slovak-specific seed data for the country-neutral registries defined in
``l10n_cssk_core``:

* ``cssk.tax.authority`` — the eight regional daňové úrady plus the Daňový úrad
  pre vybrané daňové subjekty. Unlike CZ (c_ufo numbers), the SK statutory XSDs
  (``dph2025.xsd``, ``svdph20.xsd``) declare ``danovyUrad`` as a free-text
  ``xsd:string`` with no codelist; ``submission_code`` carries the seat of the
  office ("Bratislava"), which is how the tax office's form lists them.
* ``cssk.person.type`` — Slovak taxpayer types (FO / PO).

There is no official ``l10n_sk`` tax-office model to seed from, so this list is
curated.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_sk", "l10n_cssk_core"],
    "data": [
        "data/sk_tax_authority_data.xml",
        "data/sk_person_type_data.xml",
    ],
    "installable": True,
}
