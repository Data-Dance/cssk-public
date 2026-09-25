# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SK Účtovné vzory — predkontácie interných dokladov",
    "summary": "Slovak posting templates for INTERNAL accounting documents on the "
               "l10n_sk chart. Not a document-level predkontácia: invoices, bank "
               "and cash keep deriving their accounts from Odoo's own rules.",
    "description": """
SK Účtovné vzory — predkontácie interných dokladov
==================================================

**Scope first, because the word is ambiguous.** In POHODA, ABRA Gen, Money S3
and Omega a *predkontácia* is an attribute **of a document**: you pick it on the
faktúra / bankový výpis / pokladničný doklad and the program derives the MD/D
entry when the document is posted. **This module is not that.** The OCA engine it
builds on (``account_move_template``) has no link to any document at all — it is
a wizard that *composes a new manual journal entry* from a named MD/D pattern.

So what this module ships is the *interný doklad* slice of the concept: named
patterns for entries that have no source document to derive anything from. The
accountant picks one, types a single amount, and gets a balanced draft entry.

For invoices, bank and cash, Odoo derives the accounts itself — from the
product / product category, the partner's receivable-payable accounts, the
fiscal position, the tax repartition lines, the journal defaults and the bank
reconciliation models. Nothing here changes that, and a customer's existing
predkontácia list does **not** map one-to-one onto these records; most of it
maps onto those Odoo objects instead.

Starter set
-----------
* **Prevod peňazí cez účet 261** (peniaze na ceste), both legs, both directions:
  výber z pokladnice, príjem na bankový účet, vklad do pokladnice, výber z
  bankového účtu.
* **Preúčtovanie výsledku hospodárenia** po schválení: zisk 431 → 428,
  strata 429 ← 431.

New companies get the templates when the SK chart loads (via the chart
template); SK companies that already had the chart get them on install
(post-init hook). Templates are ordinary editable records — the set is a
**starting point, not a prescription**.

Scope note
----------
The starter set is deliberately minimal and mechanically indisputable. A real
deployment's predkontácie follow that company's own *vnútorná smernica*, so the
intended workflow is to extend this set per customer — ideally by mining the
predkontácie out of their previous accounting system rather than inventing them.
When you do that, expect most of the source list to land on product categories,
fiscal positions and partner accounts, not here.

The account mapping wants the same **accountant sign-off** as the other
statutory mappings in this collection.

Licensed **AGPL-3** because it depends on the AGPL OCA template engine.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "account_move_template"],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
