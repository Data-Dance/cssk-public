# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SK Protokoly k majetku — Community engine (OCA)",
    "summary": "Zaraďovací and vyraďovací protokol as printable documents on the "
               "OCA asset register.",
    "description": """
SK Protokoly o zaradení a vyradení majetku
==========================================

The two documents every Slovak accountant issues around a fixed asset:

* **Protokol o zaradení dlhodobého majetku do používania** — when the asset is
  put into use, carrying its inventárne číslo, obstarávacia cena, date and the
  responsible person.
* **Protokol o vyradení dlhodobého majetku** — when it leaves, carrying the
  reason and the way it was disposed of.

Not a prescribed form
---------------------

Neither protokol has a statutory vzor. They are **internal účtovné doklady**
under **§ 10 zákona 431/2002** (obsahové náležitosti účtovného dokladu), whose
content the účtovná jednotka prescribes in its own *vnútorná smernica*. These
templates therefore carry the § 10 particulars plus what practice expects — and
are meant to be adapted, not treated as an official form.

They print from the OCA ``account_asset_management`` register (the Community
asset engine used by this collection), adding only the fields a protocol needs
that the register does not already hold: the inventárne číslo, the location, the
responsible person and, on disposal, the reason and method.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.2.0.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk_asset_protocol_base", "account_asset_management"],
    "data": [
        "report/asset_protocol_reports.xml",
        "views/account_asset_views.xml",
    ],
    "excludes": ["account_asset"],
    "auto_install": True,
    "installable": True,
}
