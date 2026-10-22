# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SK Predkontácie (účtovné vzory)",
    "summary": "Slovak posting templates (predkontácie) for the OCA journal-entry "
               "template engine, wired to the l10n_sk chart.",
    "description": """
SK Predkontácie (účtovné vzory)
===============================

Thin country layer between the Slovak chart (``l10n_sk``) and the OCA
journal-entry template engine (``account_move_template``). It ships a small
starter set of Slovak *predkontácie* — named MD/D patterns that an accountant
picks from a wizard, enters one amount, and posts — resolved against the Slovak
chart of accounts:

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

The account mapping wants the same **accountant sign-off** as the other
statutory mappings in this collection.

Licensed **AGPL-3** because it depends on the AGPL OCA template engine.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "account_move_template"],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
