# l10n_cssk_receipt_capture_expense: developer notes

Not user documentation: this file is not rendered into a page.

## Design

`hr.expense` computes its taxes from the amount as a tax-included total
(`special_mode="total_included"`), whether or not the tax itself is
price-included. So a receipt's €57.85 splits into 47.03 + 10.82 with the
chart's ordinary tax-excluded 23 % tax — the same tax the vendor-bill path
uses, which refuses a tax-included one. An earlier version demanded
tax-included taxes here, which made expenses and bills mutually exclusive on
one company's rate map.

The uploader is usually an employee with no access to accounting records, and
the captured receipt is one. So the receipt is handled with superuser rights,
and the employee reads the outcome on their own expense: a banner when the
receipt could not be read or needs checking, with the reason; the same reason
posted on the expense; and a notification summarising the upload. Only
accountants see the link to the receipt itself.
