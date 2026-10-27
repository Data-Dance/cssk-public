---
title: Fiscal Receipt Capture — Employee Expenses
summary: Turns a captured receipt into one employee expense with its VAT posted rate by rate, and reads receipts uploaded or scanned in the Expenses app.
verified: 19.0.1.1.0
family: l10n_cssk_receipt_capture#expenses
---

Adds **Create Expenses** to a captured receipt — one expense for the whole receipt, whatever its VAT rates, with the VAT figure and the journal entry built rate by rate from the receipt's recap — and makes the Expenses app read receipts: each image an employee uploads becomes a captured receipt and, when it reads cleanly, fills its expense; **Scan Receipt** and **My Receipts** appear under *Expenses → My Expenses*. An expense edited away from its receipt refuses to post, and a receipt claimed as expenses cannot also become a vendor receipt.

It needs [module:l10n_cssk_receipt_capture](module:l10n_cssk_receipt_capture) and Odoo's Expenses app (Community). Its settings, *Capture on Expense Upload* (on by default) and *Receipt Expense Category*, are under *Expenses → Configuration → Settings*; with the AI reader installed, every upload is a paid reading.
