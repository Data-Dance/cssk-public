=========
Changelog
=========

All notable changes to **l10n_cssk_receipt_capture_expense** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- *Capture on Expense Upload* and *Receipt Expense Category* moved to the
  Expenses app's settings (block *Receipt Capture*), where whoever runs
  expenses looks; they were only under Invoicing ▸ Fiscal Receipt Capture.
- The *Receipt Expense Category* picker listed every product, not only those
  that can be expensed: Odoo drops a string domain on a related field.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **Visibility, scan and the split (2026-10-19).** 18.0's expense bridge
  creates the receipt with the employee's rights (an AccessError for anyone
  without accounting rights), shows no outcome on the expense, and splits a
  multi-rate receipt by ``copy()``, which overrode the amounts. Port with the
  base module's rework.

- **No tax-included requirement (2026-10-19).** 18.0's ``hr.expense`` also
  computes with ``special_mode='total_included'`` (hr_expense.py:549), so the
  same refusal is wrong there. Drop it with the port.

[19.0.1.1.0] — 2026-10-19
-------------------------

Added
~~~~~

- **The outcome is visible on the expense.** A banner states why a receipt could
  not be read or needs checking, the reason is posted on the expense, and the
  uploader gets a notification summarising the upload. Before, a failed reading
  left an "Untitled Expense, 0.00" and nothing else.
- **Scan Receipt** in the Expenses app (menu and list button): scans a receipt's
  QR and lands the employee on the resulting expense; refuses a receipt another
  employee has already claimed.
- A multi-rate receipt fills the uploaded expense and creates one more per VAT
  rate, instead of leaving it empty; above the simplified-invoice limit it is a
  single expense at the gross amount with no VAT.

Fixed
~~~~~

- **One receipt is one expense again, whatever its VAT rates.** A receipt
  with several rates became one expense per rate — three "expenses" for one
  restaurant bill — because ``hr.expense`` applies all its taxes to one base.
  The expense now carries every rate's tax and takes its VAT figure and its
  journal entry from the receipt's recap: a base and a VAT line per rate, on
  both the employee-paid receipt and the company-paid payment entry. Edited
  away from its receipt, it refuses to post. A 0.00 recap row is no longer a
  rate.
- The receipt's *Expenses* smart button rendered as an inline "1 Expenses"
  above the title: it sat in a second button box, which Odoo does not lift
  into the control panel. It is now in the form's own button box.
- **The receipt behind an expense was hidden from the employee who filed
  it** (and, on Community, from the accountant too). Every employee now
  reads the receipts behind their own expenses — including one an accountant
  captured on their behalf — through the link on the expense and *Expenses ▸
  My Expenses ▸ My Receipts*; never a colleague's.
- **Expenses refused the chart's ordinary taxes.** Creating expenses demanded a
  price-included purchase tax, on the belief that ``hr.expense`` would otherwise
  read the receipt's gross as a net. It does not — it computes with
  ``special_mode="total_included"`` whatever the tax says — while the
  vendor-bill path refuses price-included taxes, so on one company's rate map
  only one of the two could ever work. The requirement is gone; the created
  expenses are still checked against the receipt.

- An employee without accounting rights could not upload at all: the receipt
  is an accounting record and was created with the employee's rights. It is
  handled with superuser rights now; the employee reads its status through the
  expense, and only accountants see the link to it.
- The split copied the first expense, whose unit price then overrode the
  amounts given — three rates came out as three times the first.

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
