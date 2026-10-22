=========
Changelog
=========

All notable changes to **account_qr_code_pay_by_square_sk** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-07-18
-------------------------

Added
~~~~~

- Fills the VariableSymbol / ConstantSymbol / SpecificSymbol payload
  positions when the invoice provides its payment symbols (via
  ``l10n_cssk_payment_symbols`` context); per the PAY by square spec the
  OriginatorsReferenceInformation is then left empty.

[18.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Slovak **PAY by square** payment QR code (SBA specification 1.1.0) as a
  ``res.partner.bank`` QR method, rendered on reports via the shared frame provider.
- Encodes the pay-by-square sequence (IBAN, amount, currency, due date,
  beneficiary, VS/KS/SS symbols, note) as an LZMA-compressed, CRC-checksummed
  data model per the SBA table-15 layout.
