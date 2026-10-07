=========
Changelog
=========

All notable changes to **l10n_cssk_receipt_capture_expense** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0] — 2026-10-06
-------------------------

Added
~~~~~

- *Create Expenses* on a captured receipt: one ``hr.expense`` per VAT rate,
  since ``hr.expense`` carries a single tax set, with the resulting set checked
  against the receipt's total and VAT before it is kept.
- ``hr.expense.cssk_receipt_id`` linking an expense back to its receipt, shown
  on the expense form.
- ``create_expense_from_attachments`` override: each uploaded receipt image also
  becomes a captured receipt and is offered to the capture providers, so the
  Community Expenses upload flow gains the eKasa QR lookup. A single-rate
  receipt that reads cleanly fills its expense in place; a multi-rate one is
  left to the split. Failure never breaks an upload.
- Refuses to create expenses when the mapped purchase tax is not
  price-included, naming the reason — ``hr.expense`` derives its net from the
  total, so a tax-excluded tax would overstate the expense.
- Company settings: receipt expense category, capture-on-upload toggle.

- The created expenses are flushed and re-read from the database before their
  totals are compared with the receipt, rather than trusting the in-memory
  values of stored computes written a moment earlier. (From the same review.)
