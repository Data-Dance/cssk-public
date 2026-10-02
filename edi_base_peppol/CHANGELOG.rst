=========
Changelog
=========

All notable changes to **edi_base_peppol** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.5.1] — 2026-10-01
-------------------------

Added
~~~~~

- **Slovak translation, 101/101 terms** (``i18n/sk.po`` + ``.pot``, the module's
  first catalogue). Verified by loading it into a database and reading the
  strings back in ``sk_SK`` — field labels, help, both selection sets and the
  view text — not only by the exporter's own count, which was green while three
  groups were still English.

Changed
~~~~~~~

- **Renamed the company switch to "Allow e-invoicing via Peppol"** and said in
  the form what it means. "Send e-invoices via Peppol" read like the routing
  decision, which it is not, and competed for meaning with the per-contact
  ``Invoice sending`` field that actually makes that decision — it was taken for
  a duplicate of it. The field now states that it is a permission: on, the
  company MAY e-invoice; which documents do is per contact, and for contacts
  with no preference by ``Peppol scope``. Off, nothing of this company's goes
  out through Peppol whatever a contact says, and each invoice shows why on its
  Peppol badge. Also spelled out that **receiving vendor bills is unaffected** —
  the switch is outbound only, which was not obvious from either the label or
  the help.

[19.0.1.5.0] — 2026-10-01
-------------------------

Added
~~~~~

- **The e-invoice is a delivery channel on the contact.** Odoo's *Invoice
  sending* (``invoice_sending_method``, Accounting tab, now visible outside debug
  mode) gains *by e-invoice (Peppol)*, keyed ``edi_peppol`` so it is never
  confused with Odoo's own ``account_peppol``. An explicit choice on the contact
  wins: e-invoice routes to Peppol even outside the company's scope, any other
  method gives the PDF. With nothing chosen, the company's scope decides. A
  Slovak business inside the mandate that is set to another method shows a
  warning on the contact.
- **Send & Print** offers the e-invoice, checked by default instead of email
  when the invoice routes to Peppol, and sends through the installed EDI
  provider. If ``account_peppol`` is installed too, its method is dropped from
  the defaults: one invoice, one access point.

[19.0.1.4.0] — 2026-09-29
-------------------------

Changed
~~~~~~~

- **Peppol is per company.** Sending is enabled per company, and so are
  auto-send and the purchase journal for inbound bills (they were
  database-wide parameters). One database can hold a company that must send
  e-invoices and one that must not.
- **Every customer document says how it goes out:** Peppol e-invoice, PDF, or
  "Peppol, but blocked", with the reason, on the invoice. Under the company
  scope *Slovak mandate* only a domestic document to a business or public body
  (a company, or a partner with a VAT number) is an e-invoice; consumers, Czech
  and other foreign customers get the PDF, and a Slovak business without a
  Peppol address is *blocked* and noted in the chatter when auto-send is on.
  The scope *any customer with a Peppol address* is the former behaviour.

Upgrade note
~~~~~~~~~~~~

- The migration enables sending for every company whose partner has a Peppol
  address, keeps the former scope, copies the auto-send flag to every company
  and gives the configured purchase journal to its company: nothing changes
  until a company is switched to the Slovak mandate.

[19.0.1.3.0] — 2026-08-22
-------------------------

- **Fix: export through the partner's Peppol builder, not always the generic
  one.** ``_peppol_generate_ubl`` hard-coded ``account.edi.xml.ubl_bis3``, so a
  national BIS3 subclass registered by an l10n module never ran on the Peppol
  send path. For Slovakia that silently dropped ``l10n_sk_ubl_bis3``'s
  *variabilný symbol* → ``cbc:PaymentID`` (BT-83) mapping — the field the
  receiving bank reconciles on — from every invoice put on the network. The new
  ``account.move._peppol_builder`` resolves the builder from the customer's
  ``invoice_edi_format``, constrained to formats core marks ``on_peppol`` so a
  partner set to a non-Peppol format (Factur-X, …) cannot have that document
  handed to a Peppol transport, and falls back to ``ubl_bis3``.

  The fallback tests ``builder is None``, **not** truthiness: a builder is an
  ``AbstractModel`` whose recordset is empty and therefore falsy, so the
  natural-looking ``_get_edi_builder(fmt) or ubl_bis3`` silently discards every
  national builder. The first cut of this fix had exactly that bug and only a
  live send exposed it — ``cbc:PaymentID`` carried the raw invoice number
  instead of the VS. Regression-covered in ``tests/test_peppol_builder.py``.

  *Live-validated* 2026-08-22 against the ePošťák sandbox: the SK builder is
  selected and BT-83 carries ``202600002`` for invoice ``INV/2026/00002``.

[19.0.1.2.0] — 2026-08-03
-------------------------

- **Add: outbound Peppol Invoice Response** (buyer rejects/disputes a received
  vendor bill). A "Peppol Response…" button on Peppol-received vendor bills
  opens a wizard (response code ``RE``/``UQ``/``CA``/``AP``/… + coded reasons +
  free-text note); ``account.move._peppol_build_invoice_response`` renders the
  UBL ``ApplicationResponse`` (``invoice_response:3``) — sender = us (buyer),
  receiver = supplier, ``DocumentReference/ID`` = the supplier's invoice id —
  and ``_peppol_emit_invoice_response`` dispatches it via the provider hook and
  records ``account.move.peppol_ir_sent_status``. New ``edi.peppol.clarification``
  code list (``OPStatusReason`` / ``OPStatusAction``) mirrors Odoo core for
  interop. *Live-validated*: eXite accepted the built response.

[19.0.1.1.0] — 2026-08-03
-------------------------

- **Add: inbound Peppol Invoice Response.** An ``ApplicationResponse`` is now
  sub-classified by CustomizationID into ``MLR`` vs ``InvoiceResponse``; a
  received Invoice Response is matched to the sent customer invoice and its
  business decision recorded on ``account.move.peppol_ir_status`` /
  ``peppol_ir_reason`` (+ chatter + badge). Status-reason parsing added.

[19.0.1.0.0] — 2026-08-03
-------------------------

- Initial extraction of the **provider-neutral** Peppol BIS Billing 3.0 stack
  out of ``edi_editel_peppol`` so any transport provider (Editel eXite, GRiT
  Orion, …) can reuse it. Carries:

  - ``doc_family='peppol'`` registration; UBL classification (Invoice /
    CreditNote / ApplicationResponse) and envelope parsing on ``edi.message``;
    the inbound seams (dedup on ``cbc:ID``, ``doc_family`` stamping,
    commit-tolerant dispatch).
  - Outbound BIS3 invoice generation (``account.edi.xml.ubl_bis3``) with two
    transport hooks a provider implements — ``account.move._peppol_provider``
    (provider key) and ``_peppol_send`` (enqueue via the provider connector) —
    plus the "Send via Peppol" button, opt-in auto-send, and the derived
    ``peppol_status`` badge (read via ``sudo`` so viewing an invoice needs no
    EDI rights).
  - Inbound: UBL Invoice/CreditNote → **draft vendor bill** (core UBL decoder),
    and **MLR** (ApplicationResponse) → ``peppol_response`` on the sent
    document + chatter.
  - Provider-agnostic inbound dispatch keyed on ``doc_family='peppol'``.
  - The **Peppol Messages** tab (EDI-user gated) and a neutral Settings block.

  Config parameters are ``peppol.auto_send`` / ``peppol.purchase_journal_id``.
