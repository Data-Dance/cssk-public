============================================
Interactive General Ledger and Trial Balance
============================================

|badge1|

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

The OCA *General Ledger* and *Trial Balance* compute every line up front and
render static HTML, which on a large ledger is slow to open and long to scroll.
This module adds an **Interactive** button to both wizards that opens the same
report as a browser view:

* one row per account with opening balance, debit, credit and closing balance,
  aggregated in the database;
* click an account to **unfold** it: its journal items for the period are
  loaded only then, **80 at a time** (*Load more*), each with a running
  balance that continues from the opening balance;
* click a journal entry to open it, or a debit / credit figure to open the
  account's journal items in a list;
* step to the previous or next period with the arrows, or **compare** with
  previous periods or the same period in earlier years (net movement and
  growth per account);
* from a journal item open its partner, open the OCA partner activity
  statement for the period (when partner_statement is installed), or
  copy the line.

Opening balances follow the account type: balance sheet accounts carry
everything before the period, profit and loss accounts only the current fiscal
year; earlier years' profit and loss is shown on the unaffected earnings
account, so the opening and closing columns balance.

The view uses the filters the wizard prepares for its own report (dates,
posted / all entries, accounts, partners, journals, analytic accounts and the
custom domain), so a module adjusting those - for instance one leaving out the
year-end closing journals - adjusts this view too. Every read goes through the
ORM, so access rights and record rules apply.

**Filter** opens Odoo's domain editor on the journal items: any field, any
operator, on top of the wizard's filters. The bookmark next to the period
**saves the view** - filters, comparison, and fixed dates or a relative period
such as *this month* - personal or shared; *Interactive Ledger* in the OCA
accounting reports menu opens your default view.

The wizard's options apply here too: *Grouped by: Partners* unfolds a
receivable or payable account into partners first, *Activate centralization*
shows centralized accounts one line per month, *Show foreign currency* adds
the amount in the item's currency, and the trial balance's *Show hierarchy*
inserts account-group subtotals (down to *Hierarchy Levels to display* when
limited).

Credits
=======

Author: Data Dance s.r.o.
