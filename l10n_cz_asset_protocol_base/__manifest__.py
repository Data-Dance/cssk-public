# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ Protokoly k majetku — base",
    "summary": "Engine-neutral Czech asset-protocol data and templates, shared "
               "by the Community and Enterprise asset bridges.",
    "description": """
CZ Protokoly k majetku — base
=============================

The two documents a Czech accountant issues around a fixed asset —
**protokol o zařazení dlouhodobého majetku do užívání** and **protokol o
vyřazení dlouhodobého majetku** — with the data they need that an asset
register does not hold: inventární číslo, místo umístění, odpovědná osoba,
důvod a způsob vyřazení.

Why a separate base
-------------------

The two editions run different, colliding asset engines. OCA
``account_asset_management`` (Community) and Odoo ``account_asset``
(Enterprise) **both declare ``account.asset``**, and the OCA one even carries
``excludes: ["account_asset"]`` — so exactly one is ever installed, and they name
the same figures differently (``purchase_value`` vs ``original_value``,
``profile_id`` vs ``model_id``, and no direct equivalent of
``value_depreciated`` on Enterprise).

So the CZ data lives here as an **AbstractModel mixin**, the protocols are
**one set of QWeb templates** rendering from an engine-neutral values dict, and
each bridge maps its own engine's fields into that dict. This module depends on
``l10n_cz`` only and touches neither engine.

Not a prescribed form
---------------------

Neither protokol has a prescribed form. They are internal účetní doklady under
**§ 11 zákona č. 563/1991 Sb., o účetnictví**, whose further content the účetní
jednotka sets in its own *vnitřní předpis*. These templates carry the § 11
particulars plus what practice expects, and are meant to be adapted.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cz"],
    "data": [
        "report/zarazovaci_protokol_template.xml",
        "report/vyrazovaci_protokol_template.xml",
    ],
    "installable": True,
}
