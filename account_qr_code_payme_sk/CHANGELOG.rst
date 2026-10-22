=========
Changelog
=========

All notable changes to **account_qr_code_payme_sk** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-07-18
-------------------------

Added
~~~~~

- Payment identification (``PI``) uses the structured ``/VS…/SS…/KS…`` form
  when the invoice provides its payment symbols (via
  ``l10n_cssk_payment_symbols`` context).

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Slovak **payme** payment QR code as a ``res.partner.bank`` QR method, rendered on
  reports via the shared frame provider.
- Builds the payme.sk payment-link URL (SBA Payment Link standard 2.0) from the
  IBAN, amount, EUR currency, payment identification (PI), creditor name, and an
  optional message.
