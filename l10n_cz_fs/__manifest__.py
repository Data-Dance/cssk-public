{
    "name": "CZ Financial Statements (Rozvaha / Výsledovka)",
    "summary": "Czech balance sheet (Rozvaha), P&L (Výkaz zisku a ztráty), cash "
               "flow and changes in equity on the shared FS framework — "
               "account-code line mappings + XML.",
    "description": """
CZ Financial Statements (Rozvaha / Výsledovka)
==============================================

The Czech country layer for the shared financial-statement framework
(``l10n_cssk_fs_base``). CE-clean — line values are summed from
``account.move.line`` by account-code prefix (balance sheet = cumulative as-of
date, P&L = period movement).

**Scope:** the full statutory line structure per vyhláška 500/2002 Sb. —
Rozvaha (plný-rozsah groups + key numbered lines) and Výkaz zisku a ztráty
v druhovém členění. Every account of the l10n_cz směrná osnova is mapped to
exactly one leaf line (partition verified in tests), so the aggregates
reconcile: **AKTIVA = PASIVA** and výsledek hospodaření = výnosy − náklady. The
current-year result (A.V) is computed from class 5/6 so the balance sheet ties
out even before the result is closed to účet 431.

The **Přehled o peněžních tocích** (cash flow, nepřímá metoda) and **Přehled o
změnách vlastního kapitálu** (changes in equity) are the příloha components,
built as a complete account partition into provozní/investiční/finanční činnost
(resp. equity components) so they reconcile by construction — A + B + C = Δcash
and počátek + Σ změny = konec (G = 0, asserted in tests). They are filed as PDF /
within the commercial-register submission; there is no standalone EPO XSD for
them, so the XML export is a structured stand-in.

**Accountant note:** the dlouhodobé/krátkodobé receivable & payable splits and
the opravné-položka allocations follow the standard chart convention — confirm
with a CZ accountant for entities using non-standard account assignments. The
statements feed the DPPDP9 appendices / commercial-register filing; there is no
single standalone EPO XSD for the full závěrka.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_fs_base", "l10n_cz"],
    "data": [
        "report/l10n_cz_fs_templates.xml",
        "data/cz_fs_version_data.xml",
        "data/cz_cashflow_version_data.xml",
        "data/cz_equity_changes_version_data.xml",
    ],
    "installable": True,
}
