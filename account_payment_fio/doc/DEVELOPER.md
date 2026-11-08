# account_payment_fio: developer notes

Not user documentation: this file is not rendered into a page.

## Validation

Problems are collected and reported together, at confirmation time, instead of
one `UserError` per attempt.
