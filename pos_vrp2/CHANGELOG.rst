=========
Changelog
=========

All notable changes to **pos_vrp2** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

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
