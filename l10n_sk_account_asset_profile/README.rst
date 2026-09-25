==========================
Slovakia - Asset profiles
==========================

Ten starter ``account.asset.profile`` records for a Slovak company, one per
depreciable asset account in the chart, each wired to its own oprávky account
and to 551 Odpisy.

Why this exists
===============

A fresh Slovak company gets an asset account for everything it can own and no
asset profile at all, so the first asset anyone creates — or imports — has
nothing to resolve against. An import then invents its own profiles, which is
why a restore onto a different company cannot reproduce them.

Defaults, not statutory data
============================

Slovakia keeps two depreciations apart and so does this module:

* **Daňové odpisy** — odpisové skupiny, § 22-29 zákona 595/2003. Fixed by law
  and identical for every company; shipped as ``account.asset.tax.class`` by
  ``l10n_sk_account_asset_tax``.
* **Účtovné odpisy** — § 28 zákona 431/2002 has the účtovná jednotka set its
  own odpisový plán from the expected useful life. A policy decision, and these
  are a starting point for it in the same sense as the taxes and journals a
  chart already ships.

No profile carries a tax class
==============================

The account does not determine the odpisová skupina: a building is group 5 or 6
depending on what it is, a machine 1, 2 or 3. A default would be wrong often,
silently, in a field that posts real numbers — so it is left empty, where it
asks a question rather than answering it badly.

``account_asset_tax_oca`` puts ``tax_class_id`` on the profile and assets
inherit it, so once a profile is given its group, every asset made from it
carries the group too.

Land and art get no profile
===========================

**031 Pozemky** and **032 Umelecké diela a zbierky** are deliberately absent.
Nothing on them is depreciated, and a profile would assert a useful life that
neither has.

Known upstream defect
=====================

Core ``l10n_sk``'s ``data/template/account.asset-sk.csv`` is wrong in 19.0. Its
asset-account column has slipped by a row for the last two entries, giving
``sk_asset_basic_herd_and_draft_animals`` account 029000 (Ostatný dlhodobý
hmotný majetok) and ``sk_asset_other_tangible_fixes_assets`` account 031000 —
which is **Pozemky**, land, and is not depreciated at all.

Core contradicts itself: ``account.account-sk.csv`` links 026000 to the herd
model and 029000 to the other-tangible one, which is right. The pairs in this
module follow the oprávky accounts, each of which names the asset account it
belongs to. Do not "fix" them to match upstream — ``test_each_profile_pairs_with_its_own_opravky_account`` exists to catch that.

Master (Odoo 20) replaces the model with ``account.depreciation.model``, which
carries no accounts, so the defect is 19.0-shaped and worth reporting there.
