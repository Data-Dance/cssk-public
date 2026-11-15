=========
Changelog
=========

All notable changes to **l10n_cz_account_asset_profile** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Ten starter ``account.asset.profile`` records for a company on the
  ``l10n_cz`` chart, one per depreciable asset account (012, 013, 014, 015,
  019, 021, 022, 025, 026, 029), each paired with its own oprávky account and
  posting účetní odpisy to 551. The Czech counterpart of
  ``l10n_sk_account_asset_profile``.
- Straight-line, monthly, pro rata from the start date. The useful lives are
  defaults for the odpisový plán (§ 28 odst. 6 zákona č. 563/1991 Sb.), not
  statutory values, and no profile presets an odpisová skupina.
- No profile for what § 56 odst. 11 vyhlášky č. 500/2002 Sb. does not
  depreciate: pozemky (031), umělecká díla a sbírky (032), povolenky na emise
  (016), preferenční limity (017).
- Loaded with the chart, and on install for companies that already have it;
  a profile the company has is never recreated or overwritten.
