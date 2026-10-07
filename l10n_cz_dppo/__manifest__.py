{
    "name": "CZ Corporate Income Tax Return (DPPDP9)",
    "summary": "Czech corporate income-tax return on the income-tax framework: "
               "ř.10 from the P&L, manual adjustments, the II. oddíl tax spine, "
               "and EPO Pisemnost/DPPDP9 XML validated against the official XSD.",
    "description": """
CZ Corporate Income Tax Return (DPPDP9)
=======================================

The Czech country layer for the income-tax framework
(``l10n_cssk_income_tax_base``). ``ř.10`` (výsledek hospodaření před zdaněním) is
computed from the P&L; the adjustments are entered by the accountant; the spine
(základ daně → daň 21 % → daň po slevách) is arithmetic.

**Scope:** the II. oddíl tax-calculation spine (ř.10 → ř.340) mapped to the
official EPO ``VetaO/@kc_ii*`` attributes; the export validates against the
bundled official DPPDP9 XSD (``data/dppdp9_epo2.xsd``). ř.10 is computed from the
P&L (class 6 − class 5, excluding income-tax accounts 591–599); the
připočitatelné/odčitatelné adjustments, loss/§34 deductions and slevy are manual
(accountant-entered) and aggregate into the spine.

**Účetní závěrka:** the Rozvaha and the Výkaz zisku a ztráty (druhové
členění) are filed inside the return as VetaUA / VetaUD / VetaUB, zkrácený
rozsah per vyhláška 500/2002 Sb., read from the ``l10n_cz_fs`` statements
linked to the return — the one account → row mapping, not a second one. Every
row of the zkrácený rozsah is mapped or declared not applicable
(``models/dppdp9_vykazy.py``).

**Out of scope:** the appendix tables (odpisy příl. 1B, §23e výpůjční náklady
příl. 3, zápočet daně ze zahraničí, investiční fondy), the plný rozsah of the
výkazy, and the přehledy / příloha účetní závěrky (E-přílohy). The XSD makes every line but the VetaD header optional, so a
spine-only return validates. Confirm the VetaD header codes (typ_dapdpp /
typ_zo / typ_popldpp) and the full adjustment set with a CZ accountant before
live filing.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.3.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_income_tax_base", "l10n_cz", "l10n_cz_statutory",
                "l10n_cz_fs"],
    "data": [
        "report/dppo_report.xml",
        "data/cz_dppo_version_data.xml",
        "views/cssk_income_tax_views.xml",
    ],
    "installable": True,
}
