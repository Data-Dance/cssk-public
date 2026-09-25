=========
Changelog
=========

All notable changes to **account_qr_code_frame_provider** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-09-09
-------------------------

Fixed
~~~~~

- The generated QR is no longer transparent. It was drawn with
  ``back_color="transparent"`` onto a bare ``Image.new("RGBA", ...)`` canvas, so
  the quiet zone and the light modules came out at alpha 0 and whatever sat
  behind the image showed through them. Reports that wrap the image in a white
  div hid this; Odoo's own ``payment_custom.custom_state_header`` and
  ``website_sale.payment_confirmation_status`` render a bare ``<img>`` and did
  not, leaving the code unreadable on a dark page — and unscannable on any
  non-white ground. The frame's own margin stays transparent, so the branded
  frame is unchanged.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Shared QR-code frame rendering for the CZ/SK payment-QR modules: overrides
  ``res.partner.bank._get_qr_code_base64`` to draw a labelled frame around the
  generated QR image, driven by per-method frame-generation parameters
  (``_get_qr_code_frame_generation_params``).
- Invoice report hook (``views/report_invoice.xml``) so the framed QR can be placed
  on the invoice PDF.
- Base dependency for ``account_qr_code_pay_by_square_sk``,
  ``account_qr_code_payme_sk``, and ``account_qr_code_qr_platba_cz``.
