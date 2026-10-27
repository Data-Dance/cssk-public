---
title: ISDOC — Received Advance Invoices
summary: Imported ISDOC proformas create a received advance instead of a bill to be posted, and the supplier's tax documents for your payment go to the advance journal and accounts, linked to their advance.
verified: 19.0.1.0.1
family: account_edi_isdoc#received-advances
---

Routes imported advance documents into [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice). A **proforma** (type 4) creates a received advance over the document's gross amount, and the draft bill the import made is flagged as not to be posted. The same proforma imported again — same supplier, same supplier's number, advance not cancelled — creates no second advance: the new draft is linked to the existing one. A **tax document for your payment** (type 5, credit note 6) is moved to the received advance tax documents journal, takes its taxable supply date from the file, has its lines moved to the paid-advances account and the payable to the clearing account, and is linked to the matching open advance — by order reference, variable symbol or unique paid amount; when that is ambiguous, the chatter asks you to link it by hand. It adds the product *Advance payment (imported)*.

It installs itself when [module:account_edi_isdoc](module:account_edi_isdoc) and [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice) are both installed; the journal and accounts are those set up for received advances.
