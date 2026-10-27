---
title: Open Advances Saldo (XLSX)
summary: A spreadsheet of issued and received advance invoices with what was paid, covered by tax documents, deducted and is still open.
verified: 19.0.1.0.2
---

## What it is for {#purpose}

Advance invoices are not posted, so no ledger report lists them. This
workbook does. It shows every advance issued with
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) and
received with
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice),
with how much has been paid on each, how much tax documents cover and how
much the final invoices have already deducted. Use it to check, at a month or
year end, which advances are still open, which still lack a tax document and
which were never paid.

## Producing it {#usage}

*Accounting → Reporting → Open Advances Saldo (XLSX)*:

| Field | Meaning |
|---|---|
| Company | the company to report on (shown with several companies) |
| Include Settled Advances | also list advances with nothing open, nothing waiting and nothing unpaid |

**Export XLSX** downloads `Advances Saldo - <company>.xlsx`.

By default an advance is listed if **any** of these holds: its open amount is
not zero, it is waiting for a tax document, or it is not paid or only partly
paid. Cancelled advances are never listed.

## What the workbook contains {#output}

Two sheets, **Issued advances** and **Received advances**, with the same
columns, one row per advance, sorted by date and number:

| Column | Meaning |
|---|---|
| Number | `ADV…` or `PADV…` |
| Partner, Date, Currency | the customer or supplier, the advance's date, its currency |
| Total | the advance invoice's total including VAT |
| Paid | issued: the payments received; received: the sum of the linked payments |
| Paid Date | the date of the last payment |
| Tax Documented | the gross total of the **posted** tax documents |
| Deducted | the gross amount deducted on **posted** final invoices |
| Open (Paid − Deducted) | what has been paid and not yet deducted |
| Payment Status, Accounting Status | as on the advance |

Only posted invoices count as deducted, on both sheets. For issued
advances that includes deductions on the parent order's final invoice and
deductions of an advance without an order made with *Link Advance
Invoices*. *Paid* on issued advances includes completed payments only, not
card payments that are merely authorised.

All amounts are in the advance's own currency, without conversion or totals.
Sheet names and column headings are in the language of the user who exports.

## Limitations {#limitations}

- The report shows the state at the moment it is exported. It has no "as at"
  date, so it cannot reproduce a past month end.
