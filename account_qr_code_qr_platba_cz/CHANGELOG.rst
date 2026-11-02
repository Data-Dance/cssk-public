=========
Changelog
=========

All notable changes to **account_qr_code_qr_platba_cz** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carried over from 19.0 (19.0.1.1.1 – 19.0.1.1.4) on 2026-10-31.

Added
~~~~~

- ``PT:IP`` in every code: the payer's banking app is asked to execute the
  transfer as an instant payment (ČBA standard 1.2). Banks that cannot fall
  back to an ordinary transfer, so nothing is lost where it is unsupported.
- Czech translation.
- Tests of the SPD escaping and of the emitted key set.

Fixed
~~~~~

- **An asterisk in the payment reference broke the code.** ``*`` ends an SPD
  field, so a reference or account holder name containing one shifted every
  following field. ``MSG`` and ``RN`` now carry it as ``%2A`` (and ``%`` as
  ``%25``), as the QR Platba format specifies.
- A missing communication string (a draft invoice without a number) no longer
  raises; it is treated as empty.

Changed
~~~~~~~

- Registers at sequence **15** instead of 20, so it is evaluated before PAY by
  square, payme and core's SEPA ``sct_qr``. ``_build_qr_code_vals`` takes the
  first *eligible* method, and PAY by square is eligible on any EUR SEPA IBAN
  without consulting the debtor, so with every method tied at 20 the winner was
  decided by module load order and a Czech customer of a Slovak company was
  handed a Slovak code. This method gates itself on ``currency == CZK or
  debtor_partner.country_code == "CZ"``, so everyone else falls through.
- The module files carry the short AGPL-3 header that matches the manifest
  licence instead of the old proprietary header text.

[18.0.1.0.1] — 2026-07-18
-------------------------

Added
~~~~~

- Emits ``X-VS`` / ``X-SS`` / ``X-KS`` when the invoice provides its payment
  symbols (via ``l10n_cssk_payment_symbols`` context); ``RF:`` prefers the
  variable symbol over digits-of-communication.

[18.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Czech **QR Platba** (credit-transfer) payment QR code as a ``res.partner.bank`` QR
  method, rendered on reports via the shared frame provider.
- Builds the Short Payment Descriptor string (``SPD*1.0*...``, CBA standard 1.2):
  account (ACC), amount (AM), currency (CC), message (MSG) and reference (RF),
  with VS/KS/SS carried as ``X-`` fields.
