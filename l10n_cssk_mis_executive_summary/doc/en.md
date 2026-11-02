---
title: CZ/SK Executive Summary
summary: A one-page MIS Builder summary for Czech and Slovak charts of accounts - cash, revenue and margins, debtor and creditor days, current ratio and return on assets.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

The figures a board asks for first, on one page, from the books: what came in
and went out of cash, what was sold and at what margin, how long customers
take to pay and how long we take, and whether the short-term debts are covered.
It is a template for [module:mis_builder](module:mis_builder), built on the
account classes the Czech and Slovak charts share.

## Using it {#usage}

*Accounting › Reporting › MIS Reports*, *New*, template **Executive Summary
(CZ/SK)**, then add the columns you want - this month, this year, the same
period last year, a comparison. The figures follow the column's dates and
filters; every figure drills down to its journal items.

## What each figure is made of {#figures}

| Figure | Accounts |
|---|---|
| Cash and bank at the start / end | 21x, 22x, 261 - opening and closing balance |
| Cash received / spent | debit / credit movement on 21x, 22x, 261 (transfers between cash and bank count on both sides) |
| Revenue | credit balance of 60x |
| Cost of goods and material sold | 501, 504 |
| Gross profit | revenue − cost of goods and material sold |
| Total income / Total expenses | class 6 / class 5 |
| Net profit | total income − total expenses |
| Gross / net margin | gross / net profit ÷ revenue |
| Trade receivables / payables | closing balance of 311 / 321 |
| Debtor days | receivables ÷ revenue × days in the period |
| Creditor days | payables ÷ purchases (classes 50 and 51) × days in the period |
| Current ratio | current assets (class 1, cash, debit balances of 31x, 33x–35x, 37x, 38x) ÷ current liabilities (credit balances of 23x, 24x, 32x–34x, 36x–38x) |
| Return on assets | net profit ÷ total assets (classes 0 and 1, debit balances of classes 2 and 3) |

Margins and ratios are not added up in a sum column; balances neither.

## Limitations {#limitations}

The figures are management indicators from account classes, not the
statutory statements: a company that posts to unusual accounts may need the
template copied and adjusted (*Duplicate* in MIS Builder). Return on assets
uses the period's profit, so for a month it is a monthly figure.
