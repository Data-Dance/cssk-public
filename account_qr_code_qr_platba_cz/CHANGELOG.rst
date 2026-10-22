=========
Changelog
=========

All notable changes to **account_qr_code_qr_platba_cz** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
