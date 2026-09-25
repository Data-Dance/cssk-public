================
Advance Invoices
================

Advance invoices (proforma / *zálohová* / *preddavková faktura*) with tax
documents on received payments and automatic settlement on the final invoice —
the Czech and Slovak advance-payment flow, done the statutory way.

.. contents:: Contents
   :local:

Features
========

* An advance invoice is its **own sale order** (``is_advance_invoice``), payable
  by **QR code**, **manual payment** or by **linking a bank transfer**.
* A wizard creates advances for the **full amount**, a **percentage**, or a
  **fixed amount**, optionally copying the order's product lines.
* On payment, a **tax document** (CZ *daňový doklad k přijaté platbě*, SK
  *faktúra k prijatej platbe*) is produced in a dedicated journal, with the
  taxable supply date set to the payment date and the statutory **15-day**
  deadline tracked.
* The advance is **deducted** on the final invoice and the advance VAT is
  **reversed**, so VAT is paid only once.
* **Long-term advances** can be routed to a separate account (475).
* Clear **payment** and **accounting** statuses on every advance.

Configuration
=============

Install the matching localization and everything is wired automatically:

* **Czech Republic** — ``l10n_cz_sale_order_advance_invoice``
* **Slovakia** — ``l10n_sk_sale_order_advance_invoice``

Otherwise configure the journal and accounts under
**Settings → Sales → Advance Invoices**.

Documentation
=============

* **Interactive cheat sheet** — ``static/description/advance_invoice_cheat_sheet.html``:
  step through the proforma → payment → tax document → final invoice → settlement
  flow and watch the journal entries fill the T-accounts (CZ/SK, with/without tax
  document, short/long-term).
* **Reference** — ``static/description/advance_invoice_reference.html`` (from
  ``docs/advance_invoice_cheat_sheet.rst``): the same flow as narrative text with
  worked journal entries.

Companion modules
=================

* ``l10n_cz_sale_order_advance_invoice`` — Czech chart wiring + docs
* ``l10n_sk_sale_order_advance_invoice`` — Slovak chart wiring + docs
* ``account_edi_isdoc_sale_advance`` — ISDOC export of advances and tax documents

Credits
=======

Author: **Data Dance s.r.o.** — https://www.datadance.eu
License: AGPL-3.0 or later (see the LICENSE file).