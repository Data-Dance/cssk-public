---
title: CZ/SK Cash Journal (peňažný denník / peněžní deník)
summary: A cash-basis book derived from ordinary Odoo accounting — every payment becomes a dated, numbered row filed under a category, for sole traders on tax records or Slovak single-entry accounting.
verified: 19.0.1.6.3
---

## What it is for {#purpose}

A Czech or Slovak sole trader who does not keep double-entry accounts still
has to record income and expenses **when they are paid**, broken down the way
the income-tax return needs them: the Slovak **peňažný denník**, the Czech
**peněžní deník**. Odoo itself keeps only double-entry books.

This module does not replace them. You keep invoicing, paying, importing bank
statements and filing VAT in Odoo exactly as before; the cash journal is a
**separate, stored book generated from the posted entries**:

- an invoice on its own writes nothing — the **payment** writes the row;
- the payment is traced back through its reconciliation to the invoice or bill
  it paid, so the row carries the **category** of what was actually sold or
  bought (goods, services, wages…), not just "bank";
- the VAT part of each payment sits in its own column, apart from the amount
  that reaches the income-tax base;
- rows are numbered in date order within each year and stay as they are until
  you regenerate them.

This is the shared engine. The national category catalogue, the printed book
in the national layout and the figures for the tax return come from the
country module:

- [module:l10n_sk_cash_journal](module:l10n_sk_cash_journal) — Slovakia;
- [module:l10n_cz_cash_journal](module:l10n_cz_cash_journal) — Czech Republic.

Install the one for your country; it brings this module with it.

## Legal background {#legal}

Neither country prescribes software; what the law asks for is the content of
the records.

- **Slovakia — daňová evidencia.** A taxpayer claiming actual expenses may keep
  records of income and tax expenses *„v časovom slede v členení potrebnom na
  zistenie základu dane“*, plus property, stock, receivables and liabilities —
  [§ 6 ods. 11 of the Income Tax Act](law:sk/2003/595#paragraf-6.odsek-11).
  A taxpayer on flat-rate expenses keeps only the income and the stock and
  receivables records —
  [§ 6 ods. 10](law:sk/2003/595#paragraf-6.odsek-10).
- **Slovakia — jednoduché účtovníctvo** (single-entry accounting). Its books
  are the peňažný denník, the books of receivables and payables and auxiliary
  books; the peňažný denník holds the cash and bank balances, income and
  expenses in the breakdown needed for the tax base, and *priebežné položky*
  (money in transit) —
  [§ 15 ods. 1 and 2 of the Accounting Act](law:sk/2002/431#paragraf-15.odsek-1).
  Its columns are set by the Ministry of Finance measure
  [MF/27076/2007-74](law:sk/2007/628), § 4.
- **Czech Republic — daňová evidence.** Records of income and expenses
  *„v členění potřebném pro zjištění základu daně“* and of property and debts —
  [§ 7b of the Income Taxes Act](law:cz/1992/586). The term *peněžní deník*
  belongs to single-entry accounting under
  [§ 13b of the Accounting Act](law:cz/1991/563), which
  [§ 1f of the same act](law:cz/1991/563) opens only to certain non-profit
  bodies — not to a sole trader.

## Setting it up {#setup}

### Settings

*Accounting → Configuration → Settings*, block **Cash Journal (peňažný
denník)**:

| Setting | What it does |
|---|---|
| Bookkeeping Regime | Double-entry (default), tax records, single-entry accounting (Slovak companies only — refused for a Czech company), or flat-rate expenses. The cash journal can be generated in every regime; the setting decides only which balance table the Slovak tax-return figures show. |
| Partial Payment Allocation | How a part payment is split between the tax base and the VAT: **pro rata** (default, Odoo's own convention), **VAT first**, or **base first**. Choose one in your internal directive and keep it for the whole year; a full payment gives the same result under all three. |
| Map the Chart | The button *Map chart to cash journal categories* fills the category on every account the country mapping knows. It never overwrites a category already set and can be run again after you add accounts. |
| Cash Journal Starts | The first date the book covers. Earlier payments are ignored — use it when you start mid-year. |

### Categories on accounts

Where a row's category comes from is decided **per account**. Open an account
(*Accounting → Configuration → Chart of Accounts*) and its **Cash Journal**
tab:

- **Cash Journal Category** — the category for payments touching this account.
- **Cash Journal Category (Money In)** — only for accounts where money moves
  both ways and each direction is a different column: a loan account receives
  the loan and pays instalments, the VAT account pays VAT over and receives a
  refund. Leave it empty when one category covers both.

The country module maps its national chart automatically — when it is
installed, and again whenever a chart is loaded — but only fills empty fields.
Receivable and payable accounts and advance accounts are deliberately left
unmapped; see [how payments become rows](#rows).

A single invoice or bill line can override the account: show the optional
column *Cash Journal Category* in *Accounting → Accounting → Journal Items*
and set it on the line, for example for a bill that is partly goods and partly
services.

### The categories themselves

*Accounting → Accounting → Cash Journal → Categories* (accounting managers
only) lists the catalogue shipped by the country module. Each category has a
**type** — Income, Expense or Transit (priebežná položka) — and two flags:

- **Affects the tax base** — cleared for an owner's withdrawal, a loan, the VAT
  remittance, income tax paid;
- **Non-cash** — for entries that move no money but belong in the book,
  typically depreciation (see [below](#non-cash)).

**Tax Return Code** names the row of the personal income-tax return the
category feeds (SK DPFO typ B tabuľka 1, CZ Příloha č. 1); the country module
sets it, and the [tax-return figures](#tax-return) group by it.

A transit category can be neither taxable nor non-cash; the form refuses it.
You may add your own categories; a code must be unique per country.

## Generating the book {#usage}

*Accounting → Accounting → Cash Journal → Generate*: choose the period and
click **Generate**.

- The rows of the period are deleted and built again from the **posted**
  entries, so running it twice gives the same book.
- **Rows marked *Manual*** and rows **on or before the accounting lock date**
  are kept. A period entirely closed by the lock date cannot be regenerated.
- The whole year is renumbered `2026/00001`, `2026/00002`, … in date order.

Nothing happens automatically: a payment posted today appears in the book the
next time you generate it. The result opens in *Cash Journal*, filtered to
**This Year**.

## How payments become rows {#rows}

A row is written for every movement of money on a bank or cash journal's
account, on Odoo's outstanding receipts/payments accounts, on the bank suspense
and the internal transfer accounts — in any journal, so a correction posted in
*Miscellaneous Operations* that moves money counts too. The same money is
counted **once**: a payment that has already been matched to a bank statement
line appears through the statement line, not twice.

From the money the engine follows the reconciliation to what was paid:

- **An invoice or bill.** The payment is split across the document's lines and
  VAT rates, so a bill for goods and services gives two rows. A part payment is
  split by the *Partial Payment Allocation* setting.
- **A direct entry** — a bank charge, a transfer to the tax office — takes the
  category of the account on the other side.
- **A refund** (a credit note, a refund from a supplier) is a **storno**: it
  reduces its own column instead of appearing in the opposite one. 1 000 sold
  and 200 refunded is income 800, not income 1 000 and an expense 200.
- **A transfer between your own bank and till** is a transit row (*priebežná
  položka*), neither income nor expense.
- **A payment on a receivable or payable with no document behind it** — usually
  an advance — is filed under the account's category if it has one, otherwise
  flagged for review. Its column depends on what the advance is for, which only
  you know. An advance invoice that posts to the account of the final supply
  carries that account's category.

Each row has the amount that reaches the tax base (net of VAT for a VAT payer)
and the **VAT** separately; for a non-payer there is no VAT part.

### Non-cash rows {#non-cash}

Depreciation is an expense that never touches the bank, while paying for the
asset itself is not an expense. Every posted line on an account whose category
is flagged **Non-cash** becomes a row with no money column, outside the bank
and cash journals. It counts towards the tax base, not towards the money
totals. A reversed or credited depreciation entry is a **storno**: it reduces
the depreciation column instead of adding to it.

## Rows that need review {#review}

The engine never guesses. When it cannot decide, the row is still written, with
an amount, but highlighted and marked **Needs review** with the reason:

| Reason | What to do |
|---|---|
| No cash journal category on account … | Set the category on the account (or on the document line) and regenerate. |
| Money came in / went out through …, which is categorised as … | The account moves both ways: set *Cash Journal Category (Money In)* on it. |
| Payment on … is not matched to a document — an advance? | Map the account, or reconcile the payment with its invoice, and regenerate. |
| Money in transit through … with no transit category | Map that account to a transit category. |
| The reconciliation chain is longer than 5 hops | Trace and correct the reconciliation by hand. |

*Accounting → Accounting → Cash Journal → Needs Review* lists them all. Fix the
cause — the account, the line, the reconciliation — and **regenerate**, rather
than editing the row: an edited generated row is replaced at the next
regeneration.

You can add a row by hand in the *Cash Journal* list. Tick **Manual** on it,
otherwise the next regeneration deletes it.

## Printing {#print}

*Accounting → Accounting → Cash Journal → Print*: choose the period and the
output.

- **PDF** — the book in the national layout, from the country module. Without
  one the button says so; print the spreadsheet instead.
- **Spreadsheet** — an XLSX workbook with every row of the period (number,
  date, document, partner, category, type, money, in, out, VAT, storno, tax
  base, non-cash, review) and a sheet of **totals per category**. The Slovak
  module adds a first sheet with the statutory grid.

## Figures for the tax return {#tax-return}

The country modules turn the book into the figures the personal income-tax
return asks for: income and expenses from the book, and the balances at the
start and end of the year from the general ledger. See
[the Slovak DPFO typ B figures](module:l10n_sk_cash_journal#dpfo) and
[the Czech Příloha č. 1 figures](module:l10n_cz_cash_journal#priloha).

## Limitations {#limitations}

- **The book is only as good as the mapping.** Every unmapped account produces
  rows for review; check *Needs Review* before every printout.
- **Generation is manual.** The book does not follow new payments by itself.
- **Editing a generated row does not last.** Regeneration replaces it. Marking
  it *Manual* keeps your row, but regeneration still writes a fresh row for the
  same payment beside it — so correct the account or the document line instead.
- **Rows added by hand get a number only at the next regeneration.**
- **Categories on accounts are not per company.** Companies sharing a chart
  share its mapping; the per-line override is the way out.
- **Only the cash journal.** The books of receivables and payables and the
  property records that single-entry accounting and tax records also require
  are not produced here; the year-end balances come from the general ledger.
- The tax-return figures are a working aid to check and copy into the return,
  not a filing.
