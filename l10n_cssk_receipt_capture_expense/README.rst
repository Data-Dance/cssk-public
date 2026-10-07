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

One expense per VAT rate
========================

``hr.expense`` carries a single ``tax_ids`` and a single amount. A receipt with
food at 5 %, tap water at 19 % and alcohol at 23 % therefore cannot be one
expense without discarding the VAT split — which is the deductible part. Each
row of the receipt's own recap becomes one expense, all pointing back at the
receipt, and the set is checked against the receipt's total and VAT before it is
kept.

Tax-included taxes are required, and said so
============================================

``hr.expense`` derives its unit price from the total, so a receipt's gross only
lands on the right base when the mapped purchase tax is **price-included**. With
a tax-excluded tax, €57.85 would be treated as a net amount and the expense
would total €71.16. Rather than post that, the module refuses and names the
cause.

Configuration
=============

*Settings ▸ Accounting ▸ Fiscal Receipt Capture*: the expense category to use,
and whether uploads in the Expenses app are captured.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
