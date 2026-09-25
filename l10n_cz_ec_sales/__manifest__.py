{
    "name": "CZ EC Sales List (Souhrnné hlášení)",
    "summary": "Czech EC sales list / souhrnné hlášení (DPHSHV) on the shared "
               "EC-summary framework + the EPO Pisemnost/DPHSHV XML export.",
    "description": """
CZ EC Sales List (Souhrnné hlášení / DPHSHV)
============================================

The Czech country layer for the shared EC-summary framework
(``l10n_cssk_ec_summary_base``). Aggregates intra-EU supplies per
(member state, customer VAT, transaction code) — with the mandatory VIES
preflight from the base — and exports the EPO **Pisemnost / DPHSHV** XML
(VetaD / VetaP + one VetaR per reported partner line).

Transaction codes come from ``account.tax.cssk_ec_summary_code`` (0 = goods,
1 = triangular, 2 = services …). The official EPO DPHSHV XSD
(``data/dphshv_epo2.xsd``) is wired onto the version record and the export is
validated against it (``schema.assertValid``) before it is attached.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_ec_summary_base", "l10n_cz", "l10n_cz_statutory"],
    "data": [
        "report/l10n_cz_ec_sales_templates.xml",
        "data/cz_ec_summary_version_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
