# account_qr_code_pay_by_square_sk: developer notes

Not user documentation: this file is not rendered into a page.

## Implementation

The code is generated **offline** — it builds the PAY by square sequence
(CRC32 checksum, LZMA1/XZ compression, base32 encoding) entirely in Python and
does **not** call any external service. It registers as an extra payment-QR
method on `res.partner.bank` and reuses Odoo's standard QR-code-on-invoice
plumbing, so it works on both Community and Enterprise.
