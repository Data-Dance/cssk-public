# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
{
    "name": "Slovakia — INTRASTAT-SK (CE / OCA)",
    "summary": "INTRASTAT-SK INSTAT XML on the OCA intrastat_product engine "
               "(CE-clean). EE variant: l10n_sk_intrastat_ee.",
    "description": """
INTRASTAT-SK — Community / OCA adapter
======================================
Thin country layer on the OCA ``intrastat_product`` declaration engine: the
engine collects intra-EU goods movements and computes the grouped declaration
lines; this module renders them as the official Finančná správa INTRASTAT-SK
INSTAT (instat62) XML via ``l10n_cssk_intrastat_base``.

AGPL-3 because it depends on (subclasses) the AGPL OCA engine. The shared
INSTAT renderer is AGPL-3 as well; the Enterprise variant
(``l10n_sk_intrastat_ee``, on ``account_intrastat``) reuses it because Data
Dance s.r.o. is its sole owner and dual-licenses it, not because of a weaker
licence.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": [
        "intrastat_product",
        "intrastat_product_hscodes_import",
        "l10n_cssk_intrastat_base",
        "l10n_sk",
    ],
    "installable": True,
}
