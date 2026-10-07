=========
Changelog
=========

All notable changes to **l10n_sk_vrp2_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.2.4.0] — 2026-10-06
-------------------------

Added
~~~~~

- ``vrp2_register_version`` and ``vrp2_vat_payer`` on the credentials
  mixin, cached from the dashboard (``cashRegister.version``,
  ``organization.vatPayer``), and ``_vrp2_valid_receipt_header()``, which
  refreshes them and returns the ``vatPayer`` / ``version`` every
  ``/v5/receipt/create/valid`` body must carry. All three captured valid
  receipts sent the dashboard's version, not the clock.
- ``vrp2_round2`` / ``vrp2_round4`` / ``vrp2_round5``: the web app's
  ``zaokruhli2/4/5``, including its two oddities — an amount under 5 cents
  rounds AWAY from zero to ±0.05, and a half rounds towards +∞ (JavaScript
  ``Math.round``), so −1.025 → −1.00.
- ``vrp2.client._get_receipt_data`` (``GET /v4/receipt/getdata``).

Fixed
~~~~~

- ``_get_receipt_list`` sent a GET; the web app POSTs a paging/filter/ordering
  body to ``/v4/receipt/receiptlist``.

Changed
~~~~~~~

- ``crpOs`` reports app version 3.1.9, which the 2026-10-06 capture shows the
  web app now sends (was 3.1.3). The checksum algorithm and compact JSON were
  re-verified byte-for-byte against that capture's three POSTs.

[19.0.2.3.4] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

[19.0.2.3.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The model's own name was never exported.** ``_description`` is what
  labels a record's type in breadcrumbs and the technical model list, and
  ``tools/i18n_export_offline.py`` emitted no ``model:ir.model,name:`` line
  at all — the entries already in the catalogues had come from an older
  DATABASE export. So every model added since had no entry and its name
  could not be translated. The exporter now emits it, and the missing
  entries are merged and filled.

[19.0.2.3.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **A field label was being INVENTED, not missing.** ``fields.Float("Night
  work %", ...)`` passes ``string`` positionally, and
  ``tools/i18n_export_offline.py`` read it from keyword arguments only — so it
  fell back to deriving a label from the field name and wrote "Noc Pct" into
  the catalogue where Odoo's own export writes "Night work %". Every
  translation keyed to the derived form was therefore keyed to a msgid the
  runtime never looks up: present, valid, and dead.
- The exporter now reads the positional slot, which differs per field type
  (``Many2one`` puts ``comodel_name`` first, ``One2many`` two arguments,
  ``Many2many`` four, ``Selection`` its selection). Positional ``selection``
  lists are extracted too, which is where the stupne-náročnosti and VRP2
  receipt-state labels had been going missing entirely.
- Catalogues regenerated against the corrected msgids and re-translated.

[19.0.2.3.1] — 2026-09-13
-------------------------

Added
~~~~~

- **Slovak catalogue — the module had none.** Generated with
  ``tools/i18n_export_offline.py`` (no database is available here) and verified
  back through Odoo's own ``PoFileReader``, so every entry resolves to the
  record it belongs to rather than importing as code strings only.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
