=========
Changelog
=========

All notable changes to **l10n_sk_vrp2_account** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.2.3.0] — 2026-10-06
-------------------------

Fixed
~~~~~

- **The printed QR encoded the wrong thing.** The receipt report rendered
  ``qr_content`` — VRP2's ``dataBase64``, a 2 KB base64 dump of the whole
  receipt — as the QR code. The QR on every official VRP2 receipt (four
  decoded, invoice payments and sales alike) is just the ``receiptId``,
  which is what the report now encodes. The field is relabelled "Receipt
  Data" and shown only in debug mode.
- **Storno ``vatPayer`` / ``version``.** The storno body sent
  ``bool(company.vat)`` and the clock; the web app sends the register's
  ``organization.vatPayer`` and ``cashRegister.version`` (the 2026-07-15
  capture's version equals that day's dashboard version, not its time). Both
  now come from the dashboard via ``_vrp2_valid_receipt_header()``.

[19.0.2.2.4] — 2026-09-13
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

[19.0.2.2.3] — 2026-09-13
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

[19.0.2.2.2] — 2026-09-13
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

[19.0.2.2.1] — 2026-09-13
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

[19.0.2.2.0]
------------

- **Storno verified and corrected against a real capture (2026-07-15);
  ``[VERIFY LIVE]`` removed.** A storno is not a dedicated endpoint — it is an
  ordinary ``POST /v5/receipt/create/valid`` receipt carrying a single negative
  ``CORRECTION`` item that references the original receipt:

  - the correction line holds ``referenceReceiptId`` = the original ``receiptId``
    (``vrp2_receipt_uuid``), ``receiptItemName`` reconstructed from the original
    request's ``invoiceNumber`` ("Úhrada faktúry: <n>"), ``vatRate`` 0, and a
    negative ``priceWithVat``;
  - the payment is an ``EXPENSE`` (refund) for the negated sum;
  - top-level ``vatPayer`` comes from ``company.vat``.

  The previous payload (top-level ``referenceReceiptId``, ``CASH`` payment,
  ``invoiceNumber``/``roundingAmount`` fields, no ``items``) was a pre-capture
  guess and is gone.
- Storno reverses the **actually fiscalized** amount: it reads the original
  request's payment sum (the rounded paid amount when 5-cent cash rounding was
  applied) rather than the pre-rounding invoice total, so a rounded original
  leaves no cash residual. Identical to the total when no rounding was applied.
- ``_create_storno`` now takes a **row lock** on the original receipt and
  re-checks ``is_stornoed`` before firing, so a double click / racing call can't
  issue two fiscal stornos for one receipt. Dropped its unused ``payment_type``
  argument (a storno is always an ``EXPENSE``).
- **Mass "Fiscalize in VRP2" hardened against mid-batch failure.**
  ``_vrp2_fiscalize`` now validates every selected invoice offline first (any
  precondition still fails the whole batch before a byte reaches the FS), then
  fiscalizes one invoice at a time inside its own savepoint. Once at least one
  receipt has been issued remotely, a later failure is caught and recorded
  (error-state ``vrp2.receipt`` + invoice chatter) instead of raised — a rolled
  back transaction can't retract a receipt that already exists at the Financial
  Administration. A failure of the *first* invoice still raises (fail-fast; also
  preserves the single-invoice action's behaviour). Same design as the Register
  Payment flow.

[19.0.2.1.0]
------------

- **Optional Register Payment fiscalization (brought back, opt-in).** New
  company setting ``vrp2_fiscalize_on_payment`` ("Fiscalize invoice payments in
  VRP2", Accounting ▸ Settings ▸ VRP2). When enabled, the standard Register
  Payment wizard shows a "Fiscalize in VRP2" checkbox (+ Cash/Card type) and
  issues a VRP2 receipt for the payment it creates — payment and receipt in one
  transaction (a VRP2 error rolls both back). Off by default, so the manual
  "Fiscalize in VRP2" button / list mass action stay the only path unless a
  company opts in.
- The payment path links ``payment_id`` and fiscalizes the **payment amount**
  (supports partial payments → one receipt per payment), reusing the shared
  ``vrp2.receipt._create_for_invoice(move, payment_type, amount, payment)``.

[19.0.2.0.0]
------------

- **Removed the Register Payment wizard integration.** The customer registers
  the Odoo payment separately; this module now only *fiscalizes*. Deleted
  ``account.payment.register`` extension + its view; ``vrp2.receipt`` is created
  directly from the invoice (no ``account.payment`` required) via
  ``_create_for_invoice``.
- **Fiscalize on a single invoice**: "Fiscalize in VRP2" button (CASH) on the
  invoice form (hidden once an active receipt exists) → downloads the receipt
  PDF.
- **Mass action** on the invoice list: "Fiscalize in VRP2" fiscalizes every
  selected customer invoice and returns ONE merged PDF of the official VRP2
  receipts (``odoo.tools.pdf.merge_pdf``).
- **0.05 € rounding** (semantics confirmed from the VRP2 web app's app.js,
  2026-06-26): ``_vrp2_invoice_dto`` sends ``priceWithVat`` as the EXACT total;
  when ``vrp2_round_5c`` is on, a CASH payment line is rounded to the nearest
  0.05 € (``zaokruhli5``, round-half-up in integer cents) and ``roundingAmount``
  carries the signed delta so ``priceWithVat + roundingAmount == payment sum``.
  Non-cash payments stay at 2 decimals. ``useRounding`` reflects the setting.
  (The toggle itself is client-side only in the VRP2 web app — see base.)
- **Hidden invoice-list column** ``vrp2_has_active_receipt`` ("VRP2 Fiscalized")
  = a confirmed, non-stornoed invoice receipt exists (stored + searchable).
- **Storno**: "Storno (VRP2)" button on the invoice (only when an active
  receipt exists) issues a ``storno``-type receipt linked to the original and
  marks the original cancelled. **[VERIFY LIVE]** endpoint/payload
  (``vrp2.client._create_storno``, ``_vrp2_storno_dto``) pending a real capture.

[19.0.1.1.0]
------------

- create/invoice payload + response **verified** against a real "Úhrada
  faktúry" capture (2026-06-18); ``[VERIFY LIVE]`` markers removed:

  - ``_vrp2_invoice_dto()`` rewritten — flat object (no ``dto`` wrapper), no
    VAT/item breakdown; emits ``version``, ``priceWithVat``,
    ``payments:[{type,sum,currency,exchangeRate,amount}]``, ``invoiceNumber``,
    ``roundingAmount``, ``useRounding``.
  - ``_apply_vrp2_response()`` maps ``receiptNumber``/``receiptId``/``id``/``okp`` and
    stores VRP2's official ``pdfBase64`` as an attachment + ``dataBase64`` as the
    QR payload. Removed PKP (online VRP issues OKP only).
  - ``vrp2.receipt``: new ``vrp2_receipt_uuid``, ``pdf_receipt``/``pdf_filename``
    fields and a "Print Official Receipt" action serving VRP2's PDF.

- Note: 5-cent cash-rounding semantics still pending a rounded-cash capture
  (sample total was round; sends roundingAmount 0).

[19.0.1.0.0]
------------

- Initial release: pay customer invoices via VRP2, no POS dependency.

  - ``vrp2.receipt`` retention model (number, fiscal codes, QR, raw
    request/response, chatter) with list/form views and a menu under
    Accounting ▸ Customers.
  - Register Payment wizard extended with "Fiscalize in VRP2" + payment
    type; payment and fiscal receipt created in one transaction.
  - "Pay & Fiscalize (VRP2)" button and a VRP2 Receipts smart button on
    customer invoices.
  - Printable QWeb receipt report.
  - **[VERIFY LIVE]** ``account.move._vrp2_invoice_dto()`` and
    ``vrp2.receipt._apply_vrp2_response()`` — the create/invoice payload and
    response field names are not covered by the captured HAR; confirm against
    a real "Úhrada faktúry" capture or the VRP2 API spec.
