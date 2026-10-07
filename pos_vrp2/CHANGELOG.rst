=========
Changelog
=========

All notable changes to **pos_vrp2** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.5.0.0] — 2026-10-06
-------------------------

Sale and storno receipts verified against a capture of the official web app
(``docs/VRP2/vrp2.financnasprava.sk-sales_storno.har``: a two-item sale, then
its storno) and against the app's own receipt builder in that capture. The
test suite replays both, and compares the bytes that are sent, not just the
values.

Fixed
~~~~~

- **The sale receipt body was a guess and would not have been accepted.**
  Items carried ``name`` / ``priceWithVat`` as a line total / ``vatId``. VRP2
  takes ``priceWithVat`` as the UNIT price incl. VAT, ``discount`` as an
  absolute per-unit amount, ``quantity``, ``type: POSITIVE``, the catalogue
  ``serviceCode`` (VRP2 prints the catalogue name) and ``vatRate`` as a
  fraction (``0.19``), not the VAT-list id.
- **``version`` is the register's ``cashRegister.version`` from the
  dashboard, not the clock**, and ``vatPayer`` is
  ``organization.vatPayer``. In all three captured valid receipts the version
  equalled the dashboard's (``1662177617338``, a 2022 stamp); only the
  invoice-payment endpoint takes the current time.
- **Rounding mirrors the web app.** Only the CASH share is rounded to 0.05 €;
  the top-level ``priceWithVat`` is the item total plus that rounding, and
  VRP2 derives the printed ZAOKRÚHLENIE from it (the request has no
  ``roundingAmount``). A negative receipt with return items is never rounded:
  the captured storno refunds −18.48 against a sale paid 18.50, exactly as
  here.
- The body serializes like ``JSON.stringify`` (``1``, not ``1.0``); the
  checksum is computed over those bytes.

Added
~~~~~

- **Refunds are VRP2 returns.** A POS refund line becomes a ``REFUND`` item
  referencing the original order's ``receiptId``, named exactly as VRP2
  printed it on the original receipt (taken from the response's
  ``dataBase64`` and stored on the line as ``vrp2_item_name``; the captured
  name had a trailing space). Refunding a whole order is VRP2's storno of the
  sale, settled by one ``EXPENSE`` payment. A return that references no
  fiscalized order is refused.
- **Automatic fiscalization** (``vrp2_auto_fiscalize``, on by default) when
  the till syncs a paid order. It runs AFTER the sync transaction commits:
  ``sync_from_ui`` saves a batch of orders in one transaction, and a receipt
  issued inside it would outlive a rollback of the batch and be issued again
  on re-sync. A VRP2 failure never blocks the sale; the order is marked
  "VRP2 Error" (with a warning to check the portal after a timeout) and can
  be fiscalized again. The order row is locked ``NOWAIT`` during the call so
  an automatic and a manual attempt cannot both send.
- **Invoiced POS orders** are fiscalized as "Úhrada faktúry"
  (``/create/invoice``, no items), as ``l10n_sk_vrp2_account`` does — an
  itemized sale receipt would report the invoice's VAT a second time.
- ``vrp2_payment_type`` on POS payment methods (Hotovosť, Platobná karta,
  Poukážky, Stravné poukážky, Iné), defaulted from the journal; a customer-
  account method has none and its orders are refused.
- List: "Fiscalize in VRP2" mass action (failures recorded per order, never
  rolling back the others), VRP2 status/number columns, "VRP2 Error" and
  "Not Fiscalized in VRP2" filters. The till form shows the auto-fiscalize
  and 5-cent rounding settings.
- **Returned deposit packaging** ("vrátené obaly"). A product marked
  ``vrp2_returnable_packaging`` and taken back with no sale to refer to
  becomes a ``NEGATIVE`` item, which, unlike ``REFUND``, keeps its
  ``serviceCode`` (web app ``parseToAPI``). A negative receipt holding one is
  not rounded, the same rule as for returns.
- **Odoo's cash rounding must match VRP2's**, enforced: with "Round to
  0.05 €" on, the till needs Odoo cash rounding of 0.05 "Nearest", cash
  only; with it off, Odoo must not round. Enabling VRP2 sets it from an
  existing 0.05 rounding method, and the till form shows it. Otherwise Odoo
  records 18.48 where VRP2 records 18.50 and the cash count never agrees
  with the register's report.
- **The VRP2 receipt at the till.** Right after validation — before the
  automatic print — the till asks the server for the order's VRP2 receipt
  (``pos.order.vrp2_receipt_for_ui``) and prints its fiscal block on the
  ticket: POKLADNIČNÝ DOKLAD č. 0019, Kód pokladnice, ID dokladu, OKP and
  the QR of the receiptId, as on the official receipt. "VRP2 doklad (PDF)"
  on the receipt screen opens the official PDF. A receipt that failed is
  announced to the cashier and the ticket says "Doklad nebol zaevidovaný vo
  VRP2" instead of carrying a fiscal block. The call fiscalizes only an order
  the post-commit step never reached, and never retries an error by itself:
  after a timeout VRP2 may already hold the receipt. Reprints from the order
  history use the loaded fields. Covered by two browser tours.
- The POS no longer loads ``vrp2_pdf``, ``vrp2_qr_content`` or the request /
  response JSON with every order of its history.
- Slovak catalogue (the module had none), including the till's own strings
  and the five of the existing credentials widget, which the offline
  exporter had never extracted from ``static/``.

Changed
~~~~~~~

- ``vrp2_qr_content`` is relabelled "VRP2 Receipt Data". It holds
  ``dataBase64`` — the whole receipt as base64 JSON — and was never the QR:
  the QR on every official receipt (four decoded) encodes only the
  ``receiptId``.
- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

Known limits
~~~~~~~~~~~~

- Whether Odoo's own ticket carrying the fiscal block may stand in for the
  VRP2 document is a legal question this module does not answer; the
  official PDF is one click away on the receipt screen and on the order.
- Vouchers (``VOUCHER_EXCHANGE``), advance deductions (``DEDUCTED_ADVANCE``),
  foreign currency and "v mene iného predávajúceho" items are not mapped,
  deliberately: each waits for a capture of the real request.
- Upgrading does not check existing tills. One with VRP2 enabled and no
  matching Odoo cash rounding keeps working until its rounding or VRP2
  settings are next saved, and is then asked to fix it.

[19.0.4.6.0]
------------

- Login/Logout on the POS form are now OWL widgets that run the server action
  then reload the record in place, so the VRP2 status badge and button
  visibility update immediately (no dialog close, no manual refresh).

[19.0.4.5.0]
------------

- Hide "Load Credentials from Company" once the till is connected (a session
  token exists) — it's only useful before login.

[19.0.4.4.0]
------------

- Per-till VRP2 status badge (via mixin ``vrp2_status``) on the POS form; Login
  button hidden when already logged in (a token exists), Logout shown only
  when logged in.

[19.0.4.3.0]
------------

- "Load Credentials from Company" is now a client-side OWL widget: it fills
  the login/password into the form in memory (no save, no reload), so the POS
  quick-config dialog no longer closes. Backed by a ``vrp2_company_credentials``
  model method. Adds a ``web.assets_backend`` bundle.

[19.0.4.2.0]
------------

- "Load from Company" → renamed "Load Credentials from Company"; it now
  soft-reloads the form so the copied login/password actually appear.
- Login button is hidden until both VRP2 login and password are filled;
  Logout stays hidden until logged in.
- Tooltips added to Load / Push to VRP2 / Pull from VRP2 explaining each.
- Constraint: a VRP2 login can be used by only one POS (one login = one
  physical cash register).

[19.0.4.1.0]
------------

- Added a "Load from Company" button on the POS VRP2 section that prefills the
  till's VRP2 login/password from the company default register (the till still
  logs in itself to obtain its own session).

[19.0.4.0.0]
------------

- **Per-till VRP2 registers.** Each ``pos.config`` is now its own VRP2 cash
  register: it inherits ``vrp2.credentials.mixin``, so credentials/session/DKP
  live on the till. Login/Logout, Push/Pull and the dashboard now sit on the
  POS form (Settings ▸ Edit), and a till's sales fiscalize on its own
  register (``pos.order`` uses ``config_id``). Logging into a till also caches the
  national VAT list on the company for the tax mapping.
- Catalog push/pull (``_vrp2_push``/``_vrp2_pull``) now take the till as the
  session holder; VAT mapping is still derived from the company.
- Company-level POS settings keep only the VAT mapping (credentials moved to
  the tills; the company stays the invoice "default register").
- KNOWN LIMIT: ``product.template.vrp2_code`` is a single field, so the same
  product synced to multiple tills shares one code — correct for one register
  per product; true multi-till catalog needs per-(product,till) codes (future).

[19.0.3.2.0]
------------

- Took ownership of the VRP2 VAT-rate↔tax mapping (moved here from
  ``l10n_sk_vrp2_base``, where it didn't belong): ``vrp2_tax_0..23`` +
  ``vrp2_vatlist_json`` on ``res.company``, the ``_vrp2_vat_*`` helpers, the
  settings tax-mapping fields, and an ``action_vrp2_login`` override that
  caches the VRP2 VAT list after login.

[19.0.3.1.0]
------------

- Carried the **verified** create/invoice envelope into the POS sale-receipt
  scaffolding: flat body (no ``dto`` wrapper), ``version`` ms-epoch, ``payments``
  array ``{type,sum,currency,exchangeRate,amount}``, ``roundingAmount``/``useRounding``.
- Response mapping aligned with the verified format: ``receiptNumber``,
  ``receiptId`` (UUID), ``okp``, official ``pdfBase64`` stored as attachment,
  ``dataBase64`` QR payload; removed PKP. New ``vrp2_receipt_uuid``, ``vrp2_pdf``
  fields and a "Print VRP2 Receipt" action on ``pos.order``.
- **[VERIFY LIVE]** remaining: only the create/valid ``items[]`` shape (needs a
  POS sale-receipt capture); the request/response envelope is now confirmed.

[19.0.3.0.0]
------------

- POS order fiscalization scaffolding (server-side):

  - ``pos.order`` gains VRP2 fiscal fields (status, receipt number, OKP/PKP,
    QR, raw request/response) and a manager-only "Fiscalize in VRP2" action
    that calls ``/v5/receipt/create/valid`` and stores the result.
  - **[VERIFY LIVE]** ``pos.order._vrp2_build_receipt_dto()`` /
    ``_vrp2_apply_response()`` — sale-receipt payload + response field names are
    not in the captured HAR; confirm against a real capture or the VRP2 spec.
  - Auto-fiscalization at payment time and printing fiscal data on the POS
    receipt (OWL frontend) are deferred until the receipt DTO is verified.

- Catalog sync correctness fixes (HAR-independent):

  - Gross↔net price now uses the tax engine (``compute_all``) instead of a
    naive percentage; pull stores the correct net ``list_price``.
  - Warns when the VRP2 service list is truncated (no pagination yet).

[19.0.2.0.0]
------------

- **Structural:** communication layer (vrp2.client, VRP2 credentials/session,
  VAT mapping, Login/Logout) extracted into the new ``l10n_sk_vrp2_base``
  module. ``pos_vrp2`` now depends on it and keeps only the POS-specific
  category/product catalog sync. No functional change to POS behaviour.

[19.0.1.0.0]
------------

- Initial release: POS ↔ VRP2 catalog (category/product) push & pull,
  credentials UI, vrp2.client API client.
