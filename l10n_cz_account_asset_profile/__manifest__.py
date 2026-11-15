# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic - Asset profiles",
    "summary": "Starter accounting-depreciation profiles for a Czech company, "
               "wired to the chart's asset and oprávky accounts.",
    "description": """
Czech asset profiles
====================

A fresh Czech company gets an asset account for everything it can own and no
``account.asset.profile`` at all, so the first asset anyone creates — or
imports — has nothing to resolve against. This ships ten, one per depreciable
asset account in the Czech chart, each wired to its own oprávky account and to
551 Odpisy dlouhodobého nehmotného a hmotného majetku.

Defaults, not statutory data
----------------------------

Czech law keeps the two depreciations apart and so does this module:

* **Daňové odpisy** — odpisové skupiny, § 26–33 zákona č. 586/1992 Sb. Fixed
  by law, identical for every company, and shipped as
  ``account.asset.tax.class`` by ``l10n_cz_account_asset_tax``.
* **Účetní odpisy** — § 28 odst. 6 zákona č. 563/1991 Sb. has the účetní
  jednotka draw up its own odpisový plán and depreciate the asset in the
  course of its use. That is a policy decision, and these profiles are a
  starting point for it in the same sense as the taxes and journals a chart
  already ships.

**No profile carries a default tax class.** The account does not determine the
odpisová skupina: a stavba is group 4, 5 or 6 depending on what it is, a
movable thing 1, 2 or 3. A default would be wrong often, silently, in a field
that posts real numbers — so the field is left empty, where it asks a question
instead of answering it badly.

What gets no profile
--------------------

**031 Pozemky**, **032 Umělecká díla a sbírky**, **016 Povolenky na emise**
and **017 Preferenční limity** are deliberately absent: § 56 odst. 11
vyhlášky č. 500/2002 Sb. lists them as not depreciated, and a profile would
assert a useful life that none has. **027 Oceňovací rozdíl k nabytému
majetku** is depreciated, but only arises on the acquisition of an obchodní
závod and posts to 557; create its profile by hand when it is needed.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Localizations/Account Charts",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_asset_tax_oca", "l10n_cz"],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
}
