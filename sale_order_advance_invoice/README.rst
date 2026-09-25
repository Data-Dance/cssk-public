==========================
Sale Order Advance Invoice
==========================

Country-neutral engine for the **advance-invoice / proforma** flow used in
Czech and Slovak accounting (*zálohová / preddavková faktúra*). An advance is
its own sale order — payable by QR code, manual payment or by linking a bank
transfer — that produces a **tax document on the received payment** (CZ *daňový
doklad k přijaté platbě*, SK *faktúra k prijatej platbe*) and is **settled
(deducted)** on the final invoice, so VAT is paid only once.

The base module is chart-agnostic. Install a localization layer to wire the
statutory accounts and journal automatically:

* ``l10n_cz_sale_order_advance_invoice`` — Czech chart
* ``l10n_sk_sale_order_advance_invoice`` — Slovak chart

Features
========

* An advance invoice is its **own sale order** (``is_advance_invoice``), linked
  back to the parent order, payable by **QR code**, **manual payment** or by
  **linking an existing bank transfer**.
* On payment, a **tax document for the received advance** is produced in a
  dedicated journal, with the taxable-supply date set to the payment date.
* The advance is **deducted** on the final invoice and the advance VAT is
  **reversed**, so the customer is not taxed twice.
* Standalone advance invoices can be **linked** to a final customer invoice
  after the fact.
* Clear **payment** and **accounting** statuses on every advance; advance
  tracking lines on the parent order.

Usage
=====

On a sale order, use **Create Advance Invoice** to raise an advance (full,
percentage or fixed amount). Collect the advance by QR, by **Register Payment**,
or by **Link Manual Transfer**; the tax document is generated on payment. When
billing the order, the advance is deducted on the final invoice; standalone
advances can be attached with **Link Advance Invoices** on a draft customer
invoice. Without a localization installed, set the journal and accounts under
*Settings ▸ Sales ▸ Advance Invoices*.

Wizards
=======

* **Create Advance Invoice** (``sale.advance.invoice.wizard``) — raises an
  advance invoice for a sale order. Open it from the **Create Advance Invoice**
  button in the order header; choose *Full amount*, *Percentage* or *Fixed
  amount* (and an optional description), then **Create Advance Invoice**. A new
  advance sale order is created and opened.
  Tick **Include the ordered items** to list the order's own products on the
  advance, each with its own VAT rate, instead of a single generic *Advance*
  line. An order mixing rates can only be advanced correctly this way: the rate
  reaches the ledger through the tax document raised on payment, and the
  deduction on the final invoice is then split by rate to give it back. For a
  percentage or a fixed amount the unit prices are scaled in proportion and the
  quantities stay as ordered. An advance never procures: delivery belongs to
  the parent order.
* **Register Manual Payment** (``sale.order.manual.payment.wizard``) — records a
  manual customer payment against an advance invoice. Launched by the **Register
  Payment** button on the advance order; pick the amount, date, journal and
  payment method, then **Create Payment**. The advance is confirmed and the
  payment linked.
* **Link Manual Bank Transfer** (``sale.order.manual.transfer.link.wizard``) —
  attaches an already-recorded inbound bank payment to an advance order. Open via
  the **Link Manual Transfer** button on the advance; choose the unreconciled
  payment, then **Link**.
* **Link Standalone Advance Invoices** (``account.move.link.advance.invoice.wizard``)
  — links one or more standalone advance invoices to a final customer invoice.
  Open with **Link Advance Invoices** on a draft customer invoice, select the
  eligible advances, then **Link**; they are added as deduction lines (net with
  VAT reversal when a tax document exists, gross otherwise).
* **Advance-aware down-payment wizard** (extends ``sale.advance.payment.inv``) —
  the standard *Create Invoices* wizard is forced into the *delivered* method on
  advance-invoice orders so the advance flow stays consistent.

Documentation
=============

* ``docs/advance_invoice_cheat_sheet.rst`` — worked walk-through of the
  proforma → payment → tax document → final invoice → settlement flow, with
  journal entries (CZ/SK, with/without tax document, short/long-term).
* ``docs/index.rst`` — feature and configuration overview.
* ``CHANGELOG.md`` — release history.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
