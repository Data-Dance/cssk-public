# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ Inventarizace — inventurní soupis a inventarizační zápis",
    "summary": "Czech inventory verification: inventurní soupisy with the "
               "particulars of § 30 odst. 7 zákona č. 563/1991 Sb. and an "
               "internal closing record of the inventarizace.",
    "description": """
CZ Inventarizace — inventurní soupis a inventarizační zápis
===========================================================

**§ 29 zákona č. 563/1991 Sb., o účetnictví** has every accounting entity
establish the actual state of **veškerý majetek a závazky** and verify that it
matches the books — as a **periodická inventarizace** to the moment the účetní
závěrka is drawn up, or, for the assets § 29 odst. 2 names, as a **průběžná
inventarizace** during the period. Two methods (§ 30 odst. 1):

* **fyzická inventura** — for assets whose existence can be established
  visually;
* **dokladová inventura** — for liabilities and for assets whose existence
  cannot be, which covers receivables, payables, provisions and equity
  accounts.

Inventurní soupis — § 30 odst. 7
--------------------------------

A průkazný účetní záznam with prescribed particulars, all of them fields here:

* the actual states, so that the assets and liabilities can be identified
* podpisový záznam **osoby odpovědné za zjištění skutečností** and of the
  **osoby odpovědné za provedení inventury**
* **způsob zjišťování** skutečných stavů
* the **ocenění** as at the rozvahový den (periodická) or the day the inventura
  ended (průběžná)
* **okamžik, ke kterému se sestavuje účetní závěrka**
* **rozhodný den**, where the entity set one (§ 30 odst. 4)
* **okamžik zahájení a okamžik ukončení inventury**

Inventarizační zápis — an internal record
-----------------------------------------

Unlike the Slovak act, the Czech one prescribes **no closing document** for
businesses. The entity must still be able to prove the inventarizace for five
years (§ 29 odst. 3), so the module prints an internal record: the comparison
of the actual state with the books per soupis, the assessment of valuation
(§ 25 odst. 3) and the signatures. For a dokladová inventura of an account,
the stav v účetnictví is read from the ledger, so the comparison is computed
rather than typed.

Inventarizační rozdíly — § 30 odst. 10 a 11
-------------------------------------------

Manka, schodky and přebytky are settled per soupis (above the norm, within
the norm, claim against the liable person) and booked as **draft** journal
entries dated the day of valuation of each soupis — the period being
verified, as § 30 odst. 11 requires. Accounts are proposed from ČÚS 007 and
vyhláška č. 500/2002 Sb. Reopening the inventarizace deletes the draft or
reverses the posted entry on the same day; a locked period refuses all of it
rather than letting Odoo move the entry into the next period.

Scope note
----------

Opravné položky and other adjustments of valuation (§ 25 odst. 3) stay with
the accountant. So do the asset register, quantities in Odoo Inventory and
VAT.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cz", "l10n_cssk_inventory_verification_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/inventory_rules.xml",
        "data/ir_sequence.xml",
        "report/inventarizace_reports.xml",
        "report/inventurni_soupis_template.xml",
        "report/inventarizacni_zapis_template.xml",
        "views/l10n_cz_inventarizace_views.xml",
    ],
    "installable": True,
}
