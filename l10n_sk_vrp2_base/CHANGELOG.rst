=========
Changelog
=========

All notable changes to **l10n_sk_vrp2_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.2.3.0]
------------

- **Fixed request/checksum body consistency.** The request body is now
  serialized **once** as compact JSON (``_compact_json``) and sent as those exact
  bytes via ``data=``; ``crpChecksum`` is computed over the same string. Before,
  the body went out through requests' ``json=`` (which inserts ``", "``/``": "``
  spaces) while the checksum was computed over compact JSON — so the checksummed
  bytes did not match the transmitted body. ``_crp_checksum`` now takes the
  already-serialized body string.
- Removed the guessed ``_create_storno`` client method (``POST
  /v5/receipt/create/storno`` never existed). A storno is an ordinary
  ``/v5/receipt/create/valid`` receipt — see l10n_sk_vrp2_account.

[19.0.2.2.0]
------------

- Added ``vrp2_round_5c`` ("Round to 0.05 €") on the credentials mixin, mirroring
  the VRP2 web app toggle "Zaokrúhľovať na 5 centov". **Confirmed against a
  capture (settings-rounding HAR): this toggle is purely client-side** — turning
  it off/on sends nothing to the server (the two ``setprofile`` saves were
  byte-identical with no rounding field, and it appears in no API
  request/response). So it is a local per-register preference, never synced; the
  fiscal effect is carried per-receipt via ``useRounding``/``roundingAmount``.
- Added ``vrp2.client._create_storno`` (POST ``/v5/receipt/create/storno``) for
  cancelling a prior receipt. **[VERIFY LIVE]**: endpoint + payload are a best
  guess pending a real storno capture.

[19.0.2.1.0]
------------

- Added computed ``vrp2_status`` (Not configured / Disconnected / Connected) on
  the credentials mixin, shown as a badge in the Accounting VRP2 settings.
  Login button now hidden once a session token exists.

[19.0.2.0.0]
------------

- Introduced ``vrp2.credentials.mixin`` (AbstractModel) holding the VRP2
  credentials + session + dashboard fields and the login/logout helpers.
  ``res.company`` now inherits it (= the "company default register" used by
  invoice payments); ``pos.config`` inherits it too for per-till registers.
- ``vrp2.client`` methods now take a generic ``holder`` (any record with the
  mixin) instead of a ``company`` — one login = one cash register (DKP), per
  the captured login/dashboard response.

[19.0.1.1.1]
------------

- Login success notification is now sticky and richer (business name, DKP,
  access role) so it is not missed as a fleeting toast.

[19.0.1.1.0]
------------

- Moved the VRP2 VAT-rate↔tax mapping out to ``pos_vrp2`` (only POS uses it;
  invoice-payment receipts carry no VAT breakdown). Removed from base:
  ``vrp2_tax_0..23`` + ``vrp2_vatlist_json`` fields, the ``_vrp2_vat_*`` helpers,
  the "Tax Mapping" settings block, and the VAT-list fetch in login. Base is
  now pure connection/session/dashboard.

[19.0.1.0.0]
------------

- Initial release. Communication layer extracted from ``pos_vrp2``:

  - ``vrp2.client`` API client with crpChecksum request signing
    (verified byte-for-byte against captured VRP2 traffic).
  - VRP2 credentials, session state and cached dashboard on ``res.company``.
  - VRP2 VAT-rate ↔ Odoo sales-tax mapping helpers.
  - Login / Logout actions surfaced in the Accounting settings.
