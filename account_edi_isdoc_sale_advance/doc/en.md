---
title: ISDOC — Czech Advance Invoices
summary: Exports the tax document for a received advance payment as ISDOC type 5 (6 for its credit note) and reports advances deducted on the final invoice as deposits.
verified: 19.0.1.0.0
family: account_edi_isdoc#advances
---

Maps the advance chain of [module:sale_order_advance_invoice](module:sale_order_advance_invoice) to ISDOC: a tax document for a received payment (*daňový doklad k přijaté platbě*) is exported as document type **5**, its credit note as **6**, and on the final invoice each advance deduction is reported as a taxed or untaxed deposit, with the number and variable symbol of the advance's tax document and the VAT already claimed, instead of as an ordinary line.

It installs itself when [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) and [module:sale_order_advance_invoice](module:sale_order_advance_invoice) are both installed, and has no settings.
