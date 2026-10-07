# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Porovnanie DPPO s účtovnou závierkou (SK)",
    "summary": "Tie the DPPO r100 to the VZS r56 of the účtovná závierka "
               "(UZPODv14) and flag a disagreement before filing.",
    "description": """
Porovnanie účtovnej závierky ↔ DPPO
===================================

The income-tax return starts from the accounting result: DPPO **r100**
(výsledok hospodárenia pred zdanením) is the same figure as VZS **r56** of the
účtovná závierka. This adds the *Porovnať s účtovnou závierkou* button to the
DPPO form, which finds the UZPODv14 závierka covering the period, compares the
two, and posts the result — a mismatch means the two filings disagree on the
accounting result.

Bridge module: it exists only where both optional pieces of the bundle are
installed (``l10n_sk_dppo`` for the return, ``l10n_sk_fs`` for the závierka),
and installs itself automatically when they are. The umbrella
(``l10n_sk_datadance``) must not depend on either — both are settings toggles —
which is why this glue cannot live there.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": [
        "l10n_sk_datadance",
        "l10n_sk_dppo",
        "l10n_sk_fs",
    ],
    "data": [
        "views/cssk_income_tax_views.xml",
    ],
    "auto_install": True,
    "installable": True,
}
