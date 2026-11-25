=========
Changelog
=========

All notable changes to **l10n_cz_inventory_verification** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.2.0] — 2026-11-24
-------------------------

Added
~~~~~

- **Inventarizační rozdíly are booked.** A new tab settles the difference of
  each soupis — manko or schodek, loss within the norm, přebytek, and the
  claim against the liable person — and creates draft journal entries dated
  the day of valuation of each soupis (§ 30 odst. 11), so a průběžná
  inventarizace gets one entry per day. Accounts are proposed from ČÚS 007
  and vyhláška č. 500/2002 Sb.: a cash schodek 569 / 211, stock
  549 / 501 / 504 / 648, zásoby vlastní činnosti through 58x, a přebytek of a
  depreciated asset against the oprávky, of a non-depreciated one against
  413. Both accounts stay editable.
- A soupis whose difference is settled elsewhere is marked as not booked here,
  with a reason; the entry is refused until every difference is either
  explained in full or so marked.
- Reopening the inventarizace, or *Cancel the booking of differences*, deletes a
  draft entry and reverses a posted one on the same day.
- The inventarizační zápis prints the settlement: kind, debit and credit account, amount and
  the journal entry.
- *Account* can be filled on a fyzická inventura too; the proposal starts from
  it.

Changed
~~~~~~~

- Depends on the new ``l10n_cssk_inventory_verification_base``, which holds
  the booking logic shared with the Slovak module.
- **Multi-company record rules.** An inventory verification, its count
  sheets and its differences are visible only in the companies the user is
  working in; until now they had no rule and showed across companies.
- **A locked period refuses the booking.** Odoo moves an entry dated in a
  locked period to the first open day when it is posted; for an inventory
  difference that is another accounting period. Creating, posting and
  reversing these entries stop with a message instead.

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Czech inventarizace under § 29 and § 30 zákona č. 563/1991 Sb.:
  ``l10n.cz.inventarizace`` (periodická or průběžná, with the rozvahový den),
  its inventurní soupisy carrying the particulars of § 30 odst. 7 (both
  responsible persons, způsob zjišťování, rozhodný den, okamžik zahájení a
  ukončení inventury, ocenění) and their items. A dokladová inventura reads
  the account's ledger balance as at the day of valuation. Closing is refused
  while a soupis lacks a prescribed particular, and an inventura outside the
  § 30 odst. 6 window raises a warning. Prints the inventurní soupis and an
  internal inventarizační zápis.
