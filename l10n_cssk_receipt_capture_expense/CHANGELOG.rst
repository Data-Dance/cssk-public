=========
Changelog
=========

All notable changes to **l10n_cssk_receipt_capture_expense** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a
Changelog. The ``19.0.x.y.z`` sections below are the 19.0 series' history,
kept verbatim: this branch reached 1.1.0 by one port rather than by those
releases, and the entries are what the port brought over.

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

- **DISCHARGED 2026-10-20 — do not port this again.** **Visibility, scan and
  the split (2026-10-19).** 18.0's expense bridge creates the receipt with the
  employee's rights (an AccessError for anyone without accounting rights),
  shows no outcome on the expense, and splits a multi-rate receipt by
  ``copy()``, which overrode the amounts. Port with the base module's rework.
  — Ported as 18.0.1.1.0 below.

- **DISCHARGED 2026-10-20 — do not port this again.** **No tax-included
  requirement (2026-10-19).** 18.0's ``hr.expense`` also computes with
  ``special_mode='total_included'`` (hr_expense.py:549), so the same refusal
  is wrong there. Drop it with the port. — Confirmed on this series at
  ``hr_expense.py:548``, and its ``account_move_line._compute_totals`` forces
  ``force_price_include`` for any line carrying an ``expense_id``. The
  requirement is gone here too.

[18.0.1.1.0] — 2026-10-20
-------------------------

Changed
~~~~~~~

- **Brought to 19.0's 1.1.0 in one step, from 18.0.1.0.0**: the outcome
  visible on the expense, *Scan Receipt* in the Expenses app, one receipt as
  one expense whatever its VAT rates, the employee's own receipts readable,
  and any purchase tax accepted. All of it is listed under 19.0.1.1.0 below.

- **18.0 only: the two overrides 19.0 puts on ``hr.expense`` sit on
  ``hr.expense.sheet`` here**, in ``models/hr_expense_sheet.py``. 19.0 deleted
  ``hr.expense.sheet`` and an expense posts itself; 18.0 reports expenses on a
  sheet, which writes BOTH journal entries at APPROVAL
  (``_do_approve`` → ``_check_can_create_move`` → ``_do_create_moves``) and
  builds the employee-paid bill itself in ``_prepare_bills_vals``. So the
  per-rate line expansion moved there, and the gate that refuses an expense
  edited away from its receipt moved to ``_check_can_create_move``: on
  ``action_post`` it would have run after the entry it is meant to vet had
  already been written. The company-paid half stays on ``hr.expense``, where
  ``_prepare_payments_vals`` lives in both series — reading the journal, the
  payment method and the outstanding account off the sheet.

  The per-rate amounts are each rate's gross in company currency on both
  series: an own-account sheet is always in the company currency here too
  (``hr_expense_sheet._compute_currency_id``), as is the ``price_unit`` core
  puts on the line.

- 18.0 has no ``hr.expense.untaxed_amount`` — only
  ``untaxed_amount_currency`` — and its own ``_compute_tax_amount`` likewise
  sets ``tax_amount`` alone, so the override does the same.

- **18.0 anchor, different from 19.0 on purpose.** 19.0's
  ``hr_expense.hr_expense_view_form`` opens its sheet with a
  ``div.oe_button_box``; 18.0's form has none, so the 19.0 xpath into it does
  not resolve and the view fails to load. The *Receipt* stat button and the
  two banners are placed just inside the sheet instead, where 19.0 core puts
  its own box, so the renderer lifts them into the control panel.

Fixed
~~~~~

- **18.0 only: the Expenses-app upload path had never done anything on this
  branch.** 19.0's ``create_expense_from_attachments`` returns
  ``expenses.ids``; 18.0's returns the ``act_window`` dictionary that opens
  them (hr_expense.py:595). The ported code tested
  ``isinstance(result, list)`` and always took the empty branch, so every
  receipt uploaded in the Expenses app since this module landed here was left
  unread — silently, because an upload that captures nothing looks exactly
  like an upload with no provider for it. The expenses are now found through
  the attachments, which works on both series.

- **18.0 only: a status note no longer needs the employee to have an e-mail
  address.** ``mail_thread._message_compute_author(raise_on_email=True)``
  refuses a post by a non-superuser whose author partner has no e-mail
  (mail_thread.py:2906); 19.0 dropped that requirement. These notes are
  written on the upload path, which exists to report a failure and must never
  break, so without an author e-mail the same note goes in through
  ``_message_log``.

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
