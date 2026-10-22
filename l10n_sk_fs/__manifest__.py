{
    "name": "Slovakia — Financial Statements (Súvaha / VZS)",
    "version": "18.0.1.0.4",
    "summary": "Slovak balance sheet (Súvaha) on the shared "
               "l10n_cssk_fs_base framework — account-code line mapping + "
               "comparison period + XML export.",
    "description": """
Slovakia — Financial Statements (Súvaha)
========================================

Concrete Slovak Súvaha + Výkaz ziskov a strát (druhové členenie) on top of
``l10n_cssk_fs_base``, computed CE-clean (no ``account_reports``).

**Scope:** the full statutory line structure (Opatrenie MF SR pre podnikateľov
v PÚ) — every account of the l10n_sk účtová osnova is mapped to exactly one leaf
line (partition verified in tests), so the aggregates reconcile: **SPOLU MAJETOK
= SPOLU VLASTNÉ IMANIE A ZÁVÄZKY** and VH = výnosy − náklady. The current-year
result (A.V) is computed from triedy 5/6 so the súvaha ties out before the
result is closed to účtu 431.

**Official UZPODv14 export** (``l10n.sk.uzpod``): the combined účtovná závierka
``dokument`` (Súvaha Úč POD 1 r001–r145 with Brutto/Korekcia/Netto + Výkaz
ziskov a strát Úč POD 2 r01–r61), built CE-clean from ``account.move.line`` and
**validated against the official ``data/uzpod-2014.xsd``** (FS SR). The row→
account formulas (``models/uzpod14_rows.py``) mirror the authoritative statutory
mapping. This is the fileable export; the semantic Súvaha/VZS statements above
remain for on-screen review.

**Accountant note:** the row mapping follows the official form; confirm the NACE
code and header fields on the company and validate with a SK accountant before
live filing. On EE, SK FS may instead defer to the native UZPODv14 export.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_fs_base", "l10n_sk"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/cssk_pl_split_tags.xml",
        "report/l10n_sk_fs_templates.xml",
        "report/l10n_sk_poznamky_report.xml",
        "data/cssk_fs_version_data.xml",
        "data/cssk_cashflow_version_data.xml",
        "data/cssk_equity_changes_version_data.xml",
        "views/l10n_sk_poznamky_views.xml",
    ],
    "installable": True,
}
