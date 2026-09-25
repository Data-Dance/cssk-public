# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK Protokoly k majetku — base",
    "summary": "Engine-neutral Slovak asset-protocol data and templates, shared "
               "by the Community and Enterprise asset bridges.",
    "description": """
SK Protokoly k majetku — base
=============================

The two documents every Slovak accountant issues around a fixed asset —
**protokol o zaradení do používania** and **protokol o vyradení** — with the
statutory-adjacent data they need that an asset register does not hold:
inventárne číslo, miesto umiestnenia, zodpovedná osoba, dôvod a spôsob
vyradenia.

Why a separate base
-------------------

The two editions run different, colliding asset engines. OCA
``account_asset_management`` (Community) and Odoo ``account_asset``
(Enterprise) **both declare ``account.asset``**, and the OCA one even carries
``excludes: ["account_asset"]`` — so exactly one is ever installed, and they name
the same figures differently (``purchase_value`` vs ``original_value``,
``profile_id`` vs ``model_id``, and no direct equivalent of
``value_depreciated`` on Enterprise).

So the SK data lives here as an **AbstractModel mixin**, the protocols are
**one set of QWeb templates** rendering from an engine-neutral values dict, and
each bridge maps its own engine's fields into that dict. This module depends on
``l10n_sk`` only and touches neither engine.

Not a prescribed form
---------------------

Neither protokol has a statutory vzor. They are internal účtovné doklady under
**§ 10 zákona 431/2002**, whose content the účtovná jednotka prescribes in its
own *vnútorná smernica*. These templates carry the § 10 particulars plus what
practice expects, and are meant to be adapted.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.4",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk"],
    "data": [
        "report/zaradovaci_protokol_template.xml",
        "report/vyradovaci_protokol_template.xml",
    ],
    "installable": True,
}
