============================================================
Advance Invoices — Bank Statement Matching (OCA Reconcile)
============================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Runs the advance-invoice matching inside the OCA reconciliation widget's auto-reconcile.**

Plugs ``sale_order_advance_invoice_payment_match`` into OCA
``account_reconcile_oca``: the advance matching pass runs before the OCA
auto-reconcile (reconcile models + invoice matching), so statement lines
paying an advance invoice are matched, paid and reconciled first; they then
show as reconciled in the OCA widget.

Auto-installs when both dependencies are present. The matching itself
remains governed by the company's "Auto-match bank statements" setting.

.. rubric:: Module facts

- **Technical name:** ``sale_order_advance_invoice_payment_match_oca``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``sale_order_advance_invoice_payment_match``, ``account_reconcile_oca``

Authors: Data Dance s.r.o.
