=========
Changelog
=========

All notable changes to **account_financial_report_interactive** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.5.1] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak and Czech catalogues: translated the strings that were still English.

[19.0.1.5.0] — 2026-11-02
-------------------------

Added
~~~~~

- Saved views: the bookmark next to the period saves the view - filters,
  extra filter, comparison - with fixed dates or a period relative to the
  day it is opened (this / last month, quarter, fiscal year); personal or
  shared, one of them the user's default. *Interactive Ledger* (OCA
  accounting reports menu) opens the default, else this year's trial
  balance; *Saved Ledger Views* lists and edits them. Shared views are read
  by everyone and edited by their owner only.

[19.0.1.4.0] — 2026-11-02
-------------------------

Added
~~~~~

- *Filter*: a filter on any field of the journal items, built in Odoo's
  domain editor (any field path, include or exclude), applied on top of the
  wizard's filters to the accounts, the partners, the items and the
  comparison; cleared with one click. Parsed as a literal domain only.

[19.0.1.3.0] — 2026-11-02
-------------------------

Added
~~~~~

- The wizard options the interactive view used to ignore:

  - *Grouped by: Partners* (general ledger): a receivable or payable account
    unfolds into partner rows (opening, debit, credit, closing), each
    unfolding into its own items with its own running balance;
  - *Activate centralization*: accounts flagged centralized show one line
    per month;
  - *Show foreign currency*: items in another currency show the amount in
    that currency;
  - *Show hierarchy* (trial balance): account-group subtotal rows before
    their accounts, honouring *Limit hierarchy levels*.

- The breadcrumb follows the period shown by the arrows.

[19.0.1.2.0] — 2026-11-02
-------------------------

Added
~~~~~

- Period arrows: step to the previous or next period of the same length (by
  whole months when the period is whole months); the fiscal year start
  follows, so profit and loss opening balances stay right across years.
- Actions on lines: open the account from its row; open the partner from a
  journal item; the OCA partner activity statement for the item's partner and
  the report's period (send / print from there; offered only when
  partner_statement is installed); copy a line to the clipboard as
  tab-separated text.

[19.0.1.1.0] — 2026-11-02
-------------------------

Added
~~~~~

- Period comparison: *Compare with* previous periods (up to 12, stepping by
  whole months when the period is whole months, by days otherwise) or the
  same period in earlier years. Each account shows its net movement per
  period and the growth against the first comparison, measured on the
  account's natural side (more revenue is positive); green where growth is
  good (income), red where it is bad (expenses). Accounts that moved only in
  a compared period are listed too.

[19.0.1.0.0] — 2026-11-02
-------------------------

Added
~~~~~

- *Interactive* button on the OCA General Ledger and Trial Balance wizards:
  account rows aggregated by the database, journal items loaded when an
  account is unfolded, 80 at a time with a running balance; entries and
  amounts drill down. Uses the wizard's own prepared filters.
