==========================================
Fiscal Receipt Capture — Employee Expenses
==========================================

The expense sink for ``l10n_cssk_receipt_capture``, and the reason the framework
earns its keep on Community.

Odoo's **Expenses** app is Community (LGPL-3) — the whole submit / approve / post
flow, the mail alias, the attachment upload. The only Enterprise piece is the one
that *reads* the receipt: ``hr_expense_extract``, which ships an image to Odoo's
IAP extract server on paid credits. A Slovak receipt does not need reading. Its
figures are already in the eKasa system, exact, free and line by line.

Two directions
==============

**From a receipt** — *Create Expenses* on a captured receipt.

**From the Expenses app** — uploading receipt images creates one captured
receipt per attachment and hands each to the capture providers. The familiar
"drop your receipts here" flow therefore gains the QR lookup without the
Enterprise module. A receipt that nothing can read is left exactly as Odoo left
it, waiting rather than guessing.

One receipt, one expense — whatever its VAT rates
=================================================

An employee files receipts, and a receipt has lines; that is the hierarchy
people expect, so a receipt is one expense. ``hr.expense`` however holds one
amount and applies all its taxes to it as one base — food at 5 % and alcohol at
23 % would become a 28 % tax on everything. A receipt with several rates is
therefore one expense carrying every rate's tax, with its VAT figure and its
journal entry built from the receipt's own recap: a base and a VAT line per
rate, for employee-paid and company-paid expenses alike. A rate the recap lists
at 0.00 (tap water) is left out. The expense is checked against the receipt's
total and VAT when it is created, and one whose amount or taxes were edited
away from the receipt refuses to post.

Grouping receipts by business trip is deliberately not done here: a trip is a
statutory document of its own (cestovný príkaz, vyúčtovanie pracovnej cesty)
and belongs in a module that also computes the travel allowances.

Any purchase tax works
======================

``hr.expense`` computes its taxes from the amount as a tax-included total
(``special_mode="total_included"``), whether or not the tax itself is
price-included. So a receipt's €57.85 splits into 47.03 + 10.82 with the
chart's ordinary tax-excluded 23 % tax — the same tax the vendor-bill path
uses, which refuses a tax-included one. An earlier version demanded
tax-included taxes here, which made expenses and bills mutually exclusive on
one company's rate map.

What the employee sees
======================

The uploader is usually an employee with no access to accounting records, and
the captured receipt is one. So the receipt is handled with superuser rights,
and the employee reads the outcome on their own expense: a banner when the
receipt could not be read or needs checking, with the reason; the same reason
posted on the expense; and a notification summarising the upload. Only
accountants see the link to the receipt itself.

**Scan Receipt** in the Expenses app scans a receipt's QR code and lands the
employee on the resulting expense. A receipt another employee has already
claimed is refused.

A receipt that reads cleanly fills the uploaded expense — one expense per VAT
rate, since an expense carries one tax, the uploaded one taking the first rate.
Above the simplified-invoice limit it is a single expense at the gross amount
with no VAT: the VAT is not deductible from the receipt and is part of the
cost.

Configuration
=============

*Settings ▸ Accounting ▸ Fiscal Receipt Capture*: the expense category to use,
and whether uploads in the Expenses app are captured.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
