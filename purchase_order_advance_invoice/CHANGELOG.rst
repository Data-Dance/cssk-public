=========
Changelog
=========

All notable changes to **purchase_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-07-18
-------------------------

Added
~~~~~

- "Received Advance Invoices" menu entry under Accounting → Vendors, just
  before Payments (visible to purchase and accounting users).

[18.0.1.0.0] — 2026-07-15
-------------------------

Added
~~~~~

- Initial release. Purchase-side mirror of ``sale_order_advance_invoice``:
  received proformas as their own ``PADV`` purchase orders (never posted),
  outbound payments to the reconcilable clearing account (wizard or
  link-existing-payment), "Register Received Tax Document" wizard creating
  a draft vendor bill in the dedicated purchase journal (net on the paid
  advances account, payable leg on the clearing account, supplier's number
  mandatory in ``ref``, taxable supply date = payment date, accounting date
  freely editable), automatic clearing reconcile on posting, automatic
  deduction of paid advances on bills created from the parent purchase
  order and a "Deduct Advance Invoices" wizard for standalone advances
  (net + taxes with a posted tax document, gross without), the
  received-advances register (kniha) with overdue-document filters and a
  daily chase-the-supplier activity cron.
