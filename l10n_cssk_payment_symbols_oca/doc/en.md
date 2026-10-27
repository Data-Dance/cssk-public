---
title: CZ/SK Payment Symbols — Bank Matching (OCA)
summary: Matches incoming payments to invoices by the exact variable symbol in OCA's bank reconciliation.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#bank-matching
---

Adds an exact variable-symbol pass to the automatic reconciliation of the OCA reconciliation widget (`account_reconcile_oca`), the usual choice on Odoo Community. It runs before OCA's own invoice matching, which compares the payment label with the invoice number and so rarely finds a Czech or Slovak payment, whose payer quotes only the variable symbol.

It installs itself when both the payment symbols module and `account_reconcile_oca` are installed, and has no settings.
