=========
Changelog
=========

All notable changes to **l10n_cz_eet2_pos_loyalty** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Follows ``l10n_cz_eet2_pos`` in building ``celk_trzba`` from the contact
  payment lines: the total is the contact money plus the redeemed wallet
  amount, a top-up still goes to ``urceno_cerp_zuct``. No behaviour change for
  cash-paid orders; an order paid partly through a remote method now reports
  only its contact part.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The whole module.** 18.0 carries ``l10n_cz_eet2_pos`` and ``pos_loyalty``
  with the same model surface (``is_reward_line``, ``reward_id``,
  ``trigger_product_ids``); port together with ``l10n_cz_eet2`` 19.0.1.1.0.
  DISCHARGED 2026-10-31 by ea53193a on branch 18.0 (origin/18.0 ea53193a) — do not port this again.

[19.0.1.0.2] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak catalogue: translated the strings that were still English.

[19.0.1.0.0] — 2026-10-29
-------------------------

Added
~~~~~

- Gift-card / eWallet top-ups go out as ``urceno_cerp_zuct`` and redemptions as
  ``cerp_zuct``, with the redeemed amount added back to ``celk_trzba`` (§ 4
  odst. 2 and § 17 odst. 2 ZoET; FS Q&A 585 / 584; item methodology ch. 13–14).
- An order settled entirely by a gift card or eWallet is recorded even though
  it has no payment line.
