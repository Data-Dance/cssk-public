# account_qr_code_payme_sk: developer notes

Not user documentation: this file is not rendered into a page.

## Implementation

The link is assembled locally from the invoice data — the module builds the
payme URL per the SBA *Payment Link* standard 2.0 and renders it as a QR code.
It registers as an extra payment-QR method on `res.partner.bank` and reuses
Odoo's standard QR-code-on-invoice plumbing, so it works on both Community and
Enterprise.
