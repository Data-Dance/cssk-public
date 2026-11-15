# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "CZ Protokoly k majetku — Community engine (OCA)",
    "summary": "Zařazovací and vyřazovací protokol as printable documents on the "
               "OCA asset register.",
    "description": """
CZ Protokoly o zařazení a vyřazení majetku
==========================================

The two documents a Czech accountant issues around a fixed asset:

* **Protokol o zařazení dlouhodobého majetku do užívání** — when the asset is
  put into use, carrying its inventární číslo, ocenění, date and the
  responsible person.
* **Protokol o vyřazení dlouhodobého majetku** — when it leaves, carrying the
  reason and the way it was disposed of.

Not a prescribed form
---------------------

Neither protokol has a prescribed form. They are **internal účetní doklady**
under **§ 11 zákona č. 563/1991 Sb., o účetnictví** (what an účetní doklad
must contain), whose further content the účetní jednotka sets in its own
*vnitřní předpis*. These templates therefore carry the § 11 particulars plus
what practice expects — and are meant to be adapted, not treated as an
official form.

They print from the OCA ``account_asset_management`` register (the Community
asset engine used by this collection), adding only the fields a protocol needs
that the register does not already hold: the inventární číslo, the location, the
responsible person and, on disposal, the reason and method.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cz_asset_protocol_base", "account_asset_management"],
    "data": [
        "report/asset_protocol_reports.xml",
        "views/account_asset_views.xml",
    ],
    "excludes": ["account_asset"],
    "auto_install": True,
    "installable": True,
}
