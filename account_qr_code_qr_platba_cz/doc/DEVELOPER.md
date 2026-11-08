# account_qr_code_qr_platba_cz: developer notes

Not user documentation: this file is not rendered into a page.

## Implementation

The code is generated **offline** — it builds the SPD string
(`SPD*1.0*ACC:...*AM:...*CC:...`) directly from the invoice data and renders
it as a QR code, with **no external service**. It registers as an extra
payment-QR method on `res.partner.bank` and reuses Odoo's standard
QR-code-on-invoice plumbing, so it works on both Community and Enterprise.
