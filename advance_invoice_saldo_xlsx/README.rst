===============================================
Advance Invoices — Open Advances Saldo (XLSX)
===============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**XLSX saldo of issued and received advance invoices: paid, tax-documented, deducted and open amounts.**

One workbook, two sheets:

* **Issued advances** (``sale_order_advance_invoice``): per advance —
  total, paid, paid date, tax-documented amount, amount already deducted
  on the final invoice, open saldo (paid − deducted), payment and
  accounting statuses.
* **Received advances** (``purchase_order_advance_invoice``): the mirror
  columns from the supplier side.

By default only advances with an open saldo (or still waiting for a tax
document / payment) are listed; a checkbox includes the settled ones.
Launched from Accounting → Reporting.

.. rubric:: Module facts

- **Technical name:** ``advance_invoice_saldo_xlsx``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``report_xlsx``, ``sale_order_advance_invoice``, ``purchase_order_advance_invoice``

Authors: Data Dance s.r.o.
