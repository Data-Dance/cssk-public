=========
Changelog
=========

All notable changes to **l10n_cz_eet2_pos_loyalty** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Follows ``l10n_cz_eet2_pos`` in building ``celk_trzba`` from the contact
  payment lines: the total is the contact money plus the redeemed wallet
  amount, a top-up still goes to ``urceno_cerp_zuct``. No behaviour change for
  cash-paid orders; an order paid partly through a remote method now reports
  only its contact part.

Port from 19.0
~~~~~~~~~~~~~~

- Carried over from 19.0.1.0.0 and 19.0.1.0.1 on 2026-10-31 without code
  changes: 18.0's ``pos_loyalty`` has the same ``is_reward_line`` /
  ``reward_id`` / ``rule_ids.product_ids`` surface.

[18.0.1.0.0] — 2026-10-31
-------------------------

Added
~~~~~

- Gift-card / eWallet top-ups go out as ``urceno_cerp_zuct`` and redemptions as
  ``cerp_zuct``, with the redeemed amount added back to ``celk_trzba`` (§ 4
  odst. 2 and § 17 odst. 2 ZoET; FS Q&A 585 / 584; item methodology ch. 13–14).
- An order settled entirely by a gift card or eWallet is recorded even though
  it has no payment line.
