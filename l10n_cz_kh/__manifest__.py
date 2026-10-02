{
    "name": "CZ Control Statement (Kontrolní hlášení / DPHKH1)",
    "summary": "Czech VAT control statement on the shared KV/KH framework: "
               "per-document A1–B3 sections with the 10 000 CZK split + the "
               "EPO Pisemnost/DPHKH1 XML export.",
    "description": """
CZ Control Statement (Kontrolní hlášení / DPHKH1)
=================================================

The Czech country layer for the shared control-statement framework
(``l10n_cssk_kv_kh_base``). A line-level resolver classifies posted move lines
into the KH sections; the per-document **10 000 CZK** threshold splits the
detail sections (A4/B2, over) from the aggregates (A5/B3, up to). Reverse-charge
supplies/acquisitions go to A1/B1 and EU acquisitions to A2.

Exports the EPO **Pisemnost / DPHKH1** XML (VetaD/VetaP, the per-document
VetaA1/A2/A4/B1/B2 rows, the VetaA5/B3 aggregates, and the VetaC control totals
computed from the sections).

**Scope note (v1):** the resolver decision tree (esp. the §92a reverse-charge
commodity list and §44 bad-debt corrections) needs CZ-accountant validation. The
official EPO DPHKH1 XSD (``data/dphkh1_epo2.xsd``) is wired onto the version
record and the export is validated against it (``schema.assertValid``).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.8.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_kv_kh_base", "l10n_cz", "l10n_cz_statutory"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "report/l10n_cz_kh_templates.xml",
        "data/cz_kh_version_data.xml",
        "views/cz_kh_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
