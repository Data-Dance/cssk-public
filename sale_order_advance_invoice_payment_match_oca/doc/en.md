---
title: Advance Invoices — Bank Statement Matching (OCA Reconcile)
summary: Runs the advance-invoice matching inside the automatic reconciliation of the OCA reconciliation widget.
verified: 19.0.1.0.1
family: sale_order_advance_invoice_payment_match#bank-reconciliation
---

Runs the advance-invoice matching before the automatic reconciliation of the OCA reconciliation widget (`account_reconcile_oca`), ahead of its reconciliation models and invoice matching. A transaction that pays an advance is matched, paid and reconciled first and then shows as reconciled in the widget. The pass runs only when the widget actually reconciles, not when it merely computes a proposal.

It installs itself when both the advance-invoice bank matching and `account_reconcile_oca` are installed. It has no settings of its own: it works only for companies with *Auto-match bank statements* switched on.
