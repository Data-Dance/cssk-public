# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia - Asset profiles",
    "summary": "Starter accounting-depreciation profiles for a Slovak company, "
               "wired to the chart's asset and oprávky accounts.",
    "description": """
Slovak asset profiles
=====================

A fresh Slovak company gets an asset account for everything it can own and no
``account.asset.profile`` at all, so the first asset anyone creates — or
imports — has nothing to resolve against. This ships ten, one per depreciable
asset account in the Slovak chart, each wired to its own oprávky account and to
551 Odpisy.

Defaults, not statutory data
----------------------------

Slovakia keeps the two depreciations apart and so does this module:

* **Daňové odpisy** — odpisové skupiny, § 22–29 zákona 595/2003. Fixed by law,
  identical for every company, and shipped as ``account.asset.tax.class`` by
  ``l10n_sk_account_asset_tax``.
* **Účtovné odpisy** — § 28 zákona 431/2002 has the účtovná jednotka set its
  own odpisový plán from the expected useful life. That is a policy decision,
  and these profiles are a starting point for it in the same sense as the taxes
  and journals a chart already ships.

**No profile carries a default tax class.** The account does not determine the
odpisová skupina: a building is group 5 or 6 depending on what it is, a machine
1, 2 or 3. A default would be wrong often, silently, in a field that posts real
numbers — so the field is left empty, where it asks a question instead of
answering it badly.

Land and art get no profile
---------------------------

**031 Pozemky** and **032 Umelecké diela a zbierky** are deliberately absent:
nothing on them is depreciated, and a profile would assert a useful life that
neither has.

One correction to upstream
--------------------------

Core ``l10n_sk``'s own ``account.asset-sk.csv`` is wrong in 19.0 for two rows —
its asset-account column has slipped, giving the herd model account 029 and the
other-tangible model account **031, which is land**. Core's own
``account.account-sk.csv`` disagrees and is right. The pairs here follow the
oprávky accounts, which name the asset account they belong to; see the comment
in ``models/account_chart_template.py`` before changing them to match upstream.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Localizations/Account Charts",
    "version": "19.0.1.1.0",
    "license": "AGPL-3",
    "depends": ["account_asset_tax_oca", "l10n_sk"],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
}
