# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK Inventarizácia — súpis a zápis",
    "summary": "Statutory Slovak inventory verification: inventúrne súpisy "
               "(§ 30 ods. 2) and the inventarizačný zápis (§ 30 ods. 3).",
    "description": """
SK Inventarizácia — súpis a zápis
=================================

**§ 29 zákona 431/2002** makes inventarizácia mandatory **as at the day the
účtovná závierka is drawn up**, and it covers **majetok, záväzky a rozdiel
majetku a záväzkov** — i.e. equity too, not just stock. Two methods:

* **fyzická inventúra** — for what can be counted or weighed (dlhodobý hmotný
  majetok, zásoby, peniaze v hotovosti);
* **dokladová inventúra** — for everything that cannot be, which is exactly what
  "inventarizácia účtov" means: receivables, payables, provisions, capital.

Both produce statutory records, and this module is those records.

Inventúrny súpis — § 30 ods. 2
------------------------------

A prescribed set of particulars, all of them fields here:

* obchodné meno alebo názov účtovnej jednotky
* **deň začatia inventúry**, **deň, ku ktorému bola inventúra vykonaná**, and
  **deň skončenia inventúry** — three distinct dates, not one
* stav majetku **s uvedením jednotiek množstva a ceny**
* miesto uloženia majetku
* meno a podpisový záznam **hmotne zodpovednej osoby**
* podpisový záznam osoby zodpovednej za **zistenie skutočného stavu**
* poznámky

Inventarizačný zápis — § 30 ods. 3
----------------------------------

The document that closes the exercise: the **výsledky porovnania** skutočného
stavu with the účtovný stav, the **posúdenie reálnosti ocenenia** (§ 26), and the
signatures. For dokladová inventúra of an account, the účtovný stav is read from
the ledger as at the deň ku ktorému, so the comparison is computed rather than
typed.

Scope note
----------

This produces and evidences the inventarizácia. It does **not** post the
inventory differences — manká a škody, opravné položky and the like are
accounting decisions that follow from the zápis, and belong to the accountant.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "report/inventarizacia_reports.xml",
        "report/inventurny_supis_template.xml",
        "report/inventarizacny_zapis_template.xml",
        "views/l10n_sk_inventarizacia_views.xml",
    ],
    "installable": True,
}
