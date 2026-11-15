# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "CZ Manažerské výkazy (MIS Builder)",
    "summary": "Management P&L on the Czech chart, for Community — the "
               "counterpart to Enterprise's account_reports.",
    "description": """
CZ Manažerské výkazy
====================

Management reporting for **Community**. Enterprise ships its management
reports in ``account_reports``; Community has none.

What this ships
---------------

A **manažerská výsledovka** — a management P&L on the ``l10n_cz`` chart, built
as an OCA ``mis_builder`` template, so it is a starting point the controller
edits rather than a fixed report: KPIs, periods, comparisons, budgets and XLSX
export all come from the engine.

It reads účtové třídy 5 and 6 by account-code pattern, so it works on the
standard Czech chart with no tagging, and reports:

* tržby split into zboží / výrobky a služby / ostatní provozní výnosy
* provozní náklady split into prodané zboží, spotřeba, služby, změna stavu
  zásob vlastní činnosti a aktivace, osobní náklady, daně a poplatky, odpisy,
  ostatní
* **provozní výsledek hospodaření**
* finanční výnosy and náklady, giving the **výsledek hospodaření před
  zdaněním**
* daň z příjmů and the převod podílu společníkům, giving the **výsledek
  hospodaření po zdanění**

Revenue is negated on the way in, so every line reads as a positive figure and
the subtotals add up the way a reader expects.

One Czech difference from the Slovak twin
-----------------------------------------

Since 2016 the Czech chart books the *změna stavu zásob vlastní činnosti* and
*aktivace* in účtová skupina **58**, as an adjustment of costs, where the
Slovak chart keeps them in 61 and 62 as revenue. They are a cost line here,
and normally a negative one.

Not the statutory statements
----------------------------

This is the *management* view and is deliberately separate from the statutory
ones. The Výkaz zisku a ztráty of the účetní závěrka lives in ``l10n_cz_fs``.
Do not reconcile this against it line by line: the groupings are chosen for
readability, not for vyhláška č. 500/2002 Sb.

For a treasury forecast, install ``mis_builder_cash_flow`` — that is a
**forecast** built on due dates and manual forecast lines, which is again a
different thing from the statutory přehled o peněžních tocích.

Honesty flag
------------

The account groupings are a management choice, not a statutory mapping, and
want the same accountant sign-off as everything else here — particularly which
accounts belong in *ostatní provozní náklady* versus the operating groups.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cz", "mis_builder"],
    "data": [
        "data/mis_report_style.xml",
        "data/mis_report_pl.xml",
    ],
    "installable": True,
}
