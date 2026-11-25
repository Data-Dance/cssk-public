{
    "name": "CZ Účetní závěrka — závěrkové účty 701/702/710",
    "version": "19.0.2.0.0",
    "summary": "Czech year-end closing template: costs and revenues to 710, "
               "balance-sheet accounts to 702, reopened through 701 with the "
               "result on 431.",
    "description": """
CZ Účetní závěrka — závěrkové účty
===================================

Czech double-entry bookkeeping closes the year through the **závěrkové účty**
of class 7, which Odoo has no concept of (ČÚS 002):

* **710 — Účet zisků a ztrát**: collects třída 5 (náklady) and třída 6
  (výnosy). Its balance is the výsledek hospodaření.
* **702 — Konečný účet rozvažný**: collects every rozvahový účet (třídy 0–4)
  and the result carried over from 710.
* **701 — Počáteční účet rozvažný**: reopens the same balances in the new
  year, with the result on **431**.

The module does two things:

1. ``l10n_cz`` ships 701000 / 702000 / 710000 as ``off_balance``, and Odoo
   refuses to mix an off-balance account with any other in one entry, which
   is exactly what a closing entry does. They are retyped to ``equity``.
2. It ships a **closing template** on the OCA ``account_fiscal_year_closing``
   engine for the ``l10n_cz`` chart, and a list of what to look at before the
   year is closed.

The distribution of the approved result from 431 is a separate entry, posted
when the competent body decides; it is not part of the closing.

The mirror of ``l10n_sk_fiscal_year_closing``.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cz", "account_fiscal_year_closing"],
    "data": [
        "data/fyc_template_data.xml",
        "views/account_fiscalyear_closing_views.xml",
        "views/account_move_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
