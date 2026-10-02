# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SK Účtovná závierka — závierkové účty 701/702/710",
    "summary": "Slovak year-end closing template: costs and revenues to 710, "
               "balance-sheet accounts to 702, reopened through 701.",
    "description": """
SK Účtovná závierka — závierkové účty
=====================================

Slovak (and Czechoslovak-descended) accounting closes the year through three
**závierkové účty**, which Odoo has no concept of:

* **710 — Účet ziskov a strát**: collects trieda 5 (náklady) and trieda 6
  (výnosy). Its balance is the výsledok hospodárenia.
* **702 — Konečný účet súvahový**: collects every súvahový účet (triedy 0–4),
  and the result carried over from 710.
* **701 — Začiatočný účet súvahový**: reopens the same balances in the new year.

This module ships that as a **closing template** on the OCA
``account_fiscal_year_closing`` engine, wired to the ``l10n_sk`` chart. Creating
a closing for a year copies the template into an editable record, so the mapping
is a starting point the accountant adjusts — not something hard-coded.

What it does **not** do
-----------------------

The **transfer of the approved result to 431** (and on to 428/429) is a separate
event: it happens when the valné zhromaždenie approves the závierka, which is
not the closing itself. That posting ships as a *predkontácia* in
``l10n_sk_account_move_template`` (*Preúčtovanie schváleného zisku / straty*).

Honesty flag
------------

Closing conventions vary between účtovné jednotky — in particular whether the
result reaches 702 directly from 710 or via 431 in the closing itself. The
template implements the mainstream route (710 → 702) and is editable per
closing. Real-data validation against MRP's 2024 books already noted that the
result-to-431 convention is where implementations differ, so this mapping wants
**accountant sign-off** before a live závierka.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "account_fiscal_year_closing"],
    "data": ["data/fyc_template_data.xml"],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
