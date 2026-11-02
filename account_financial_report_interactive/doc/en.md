---
title: Interactive General Ledger and Trial Balance
summary: Open the OCA general ledger and trial balance in the browser - unfold an account to load its journal items, compare periods, step through periods, and act on any line.
verified: 19.0.1.5.0
---

## What it is for {#purpose}

The *General Ledger* and *Trial Balance* of
[module:account_financial_report](module:account_financial_report) compute every
line up front and render a static page: on a large ledger it is slow to open and
long to scroll. This module adds **Interactive** to both report wizards, next to
*View*. It opens the same report as a live view in which nothing below an
account is computed until you open it.

## Opening it {#usage}

*Accounting › Reporting › General Ledger* (or *Trial Balance*), set the period
and filters as usual, then **Interactive**. Every filter of the wizard applies:
dates, posted or all entries, accounts, partners, journals, analytic accounts,
the custom domain - and anything another module adds to the wizard, such as
[module:l10n_cssk_account_financial_report](module:l10n_cssk_account_financial_report)
leaving out the year-end closing journals.

| Column | Meaning |
|---|---|
| Opening | Balance before the period. Balance-sheet accounts carry everything before it; profit and loss accounts only the current fiscal year. Earlier years' profit and loss is shown on the unaffected earnings account, so the column adds up to zero. |
| Debit / Credit | Movement in the period. Click to open the journal items. |
| Closing | Opening plus the period's movement. |

## Unfolding an account {#unfold}

Click an account to unfold it. Its journal items load **80 at a time**
(*Load more*), each with a **running balance** that starts from the opening
balance and ends on the closing one. Click an entry number to open the entry,
a partner to open the partner.

- **Grouped by: Partners** (general ledger wizard): a receivable or payable
  account unfolds into its partners first - opening, debit, credit and closing
  per partner - and each partner unfolds into its own items.
- **Activate centralization**: accounts marked *centralized* show one line per
  month instead of every item.
- **Show foreign currency**: an item in another currency shows its amount in
  that currency next to the label.
- **Show hierarchy** (trial balance wizard): account-group subtotal rows come
  before their accounts; *Limit hierarchy levels* stops at the chosen depth.

## Periods and comparison {#compare}

The arrows next to the period step to the **previous or next period** of the
same length - by whole months when the period is whole months (a quarter steps
to the next quarter), by days otherwise. The fiscal year start follows, so
profit and loss opening balances stay right across a year end.

**Compare with** adds, per account, the net movement of up to twelve earlier
periods (*Previous periods*) or of the same period in earlier years, and the
**growth** against the first of them. Growth is measured on the account's
natural side, so more revenue is a positive figure; it is green where growth is
good (income), red where it is bad (expenses) and uncoloured elsewhere.
Accounts that moved only in a compared period are listed too.

## Filtering {#filter}

**Filter** opens Odoo's domain editor on the journal items: any field, followed
through its relations (*Product › Product Category*, *Partner › Country*…), with
any operator - *is*, *is not*, *contains*, *is set*… - so a filter can include
as well as exclude. It applies on top of the wizard's filters to every figure:
accounts, partners, items and the compared periods. The button turns blue while
a filter is active; the cross next to it clears it.

## Saved views {#views}

The **bookmark** next to the period saves what you are looking at: the
filters, the extra filter and the comparison, under a name, with either

- *These dates*, or
- a period relative to the day the view is opened - this or last month,
  quarter or fiscal year - so "last month" is always last month.

A view is yours unless you **share** it (everyone sees it, only you can change
it). One of your views can be **your default**: *Accounting › Reporting ›
OCA accounting reports › Interactive Ledger* opens it directly (without a
default it opens this year's trial balance). Saved views are listed, renamed
and deleted under *Saved Ledger Views* in the same menu.

## Actions on lines {#actions}

- the arrow icon next to an account opens the account;
- the envelope on an item opens the OCA partner activity statement for its
  partner and the report's period, to send by email or print - shown only when
  [module:partner_statement](module:partner_statement) is installed;
- the clipboard copies the line as tab-separated text, ready to paste into a
  spreadsheet.

## Notes {#notes}

The view only reads: every figure comes from the journal items through the
ordinary access rights and record rules, so a user sees exactly the companies
and entries they may see. For a printable copy use *Export PDF* or
*Export XLSX* in the wizard.
