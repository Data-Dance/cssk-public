===============================
SK Protokoly k majetku — base
===============================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Engine-neutral Slovak asset-protocol data and templates, shared by the Community and Enterprise asset bridges.**

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

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_asset_protocol_base``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``l10n_sk``

Authors: Data Dance s.r.o.
