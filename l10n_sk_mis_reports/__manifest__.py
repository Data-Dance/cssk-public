# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SK Manažérske výkazy (MIS Builder)",
    "summary": "Management P&L on the Slovak chart, for Community — the "
               "counterpart to Enterprise's account_reports.",
    "description": """
SK Manažérske výkazy
====================

Management reporting for **Community**. Enterprise ships an executive summary and
a cash-flow report in ``account_reports``; Community has neither, which left
"management reporting (mng P&L, cash flow)" as the last open item on the
customer requirement list this collection was built against.

What this ships
---------------

A **manažérska výsledovka** — a management P&L on the ``l10n_sk`` chart, built as
an OCA ``mis_builder`` template, so it is a starting point the controller edits
rather than a fixed report: KPIs, periods, comparisons, budgets and XLSX export
all come from the engine.

It reads trieda 5 and 6 by account-code pattern, so it works on the standard
Slovak chart with no tagging, and reports:

* tržby split into tovar / vlastné výrobky a služby / ostatné výnosy
* náklady split into predaný tovar, spotreba, služby, osobné náklady, dane a
  poplatky, odpisy, ostatné
* **prevádzkový výsledok**
* finančné výnosy and náklady, giving the **výsledok pred zdanením**
* daň z príjmov, giving the **výsledok po zdanení**

Revenue is negated on the way in, so every line reads as a positive figure and
the subtotals add up the way a reader expects.

Not the statutory statements
----------------------------

This is the *management* view and is deliberately separate from the statutory
ones. The Výkaz ziskov a strát filed with the účtovná závierka lives in
``l10n_sk_fs`` (UZPODv14, XSD-validated), and the statutory Prehľad peňažných
tokov lives there too. Do not reconcile this against them line by line: the
groupings are chosen for readability, not for the Opatrenie MF SR.

For a treasury forecast, install ``mis_builder_cash_flow`` — that is a
**forecast** built on due dates and manual forecast lines, which is again a
different thing from the statutory cash-flow statement.

Honesty flag
------------

The account groupings are a management choice, not a statutory mapping, and want
the same accountant sign-off as everything else here — particularly which
accounts belong in *ostatné náklady* versus the operating groups.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "mis_builder"],
    "data": [
        "data/mis_report_style.xml",
        "data/mis_report_pl.xml",
    ],
    "installable": True,
}
