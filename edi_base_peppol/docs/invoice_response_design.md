# Design: Peppol Invoice Response support (`edi_base_peppol`)

Status: **IMPLEMENTED** (P0 inbound + P1 outbound) — 2026-08-03. Built into the
new provider-neutral **`edi_base_peppol`** module (not `edi_editel_peppol`);
live-validated against the Editel eXite test AP. **P2** (line-level
`LineResponse` disputes, `StatusReasonCode` action-code UI depth, schematron
validation, status history view) remains future work. The design below is the
as-built plan; §1b prior-art verification stands.
Scope: add **Peppol Invoice Response** (BIS 3.x, transaction **T111**) to the
existing Editel Peppol stack, in **both** directions:

- **Buyer side (outbound)** — accept / **reject** / **dispute** a received
  vendor bill by sending a Peppol Invoice Response back to the supplier.
- **Seller side (inbound)** — receive Invoice Responses for invoices *we*
  sent and record the buyer's business decision on the customer invoice.

This is the **business-level** response, distinct from the **MLR** (Message
Level Response, transaction T71) that the module already handles — MLR is the
*technical* "message received / rejected for syntax reasons" acknowledgement;
Invoice Response is the *business* accept/reject/dispute in the buyer's
approval-and-payment process.

---

## 1. The standard (reference)

| | MLR (already supported) | **Invoice Response (this design)** |
|---|---|---|
| CustomizationID | `urn:fdc:peppol.eu:poacc:trns:mlr:3` | `urn:fdc:peppol.eu:poacc:trns:invoice_response:3` |
| ProfileID | `…:bis:mlr:3` | `urn:fdc:peppol.eu:poacc:bis:invoice_response:3` |
| Transaction | T71 | **T111** |
| UBL root | `ApplicationResponse` 2.1 | `ApplicationResponse` 2.1 (same root) |

Both share the **same UBL root** and the **same eXite transport** (eXite
auto-derives `applicationReference` → `Invoice`/`CreditNote`/`ApplicationResponse`
from the payload — confirmed), so **no connector changes** are needed.

**Response codes** (`cac:DocumentResponse/cac:Response/cbc:ResponseCode`,
UNCL4343 T111 subset):

| Code | Meaning | Our use |
|---|---|---|
| `AB` | Message acknowledged (readable invoice received) | ack |
| `IP` | In process | status |
| `UQ` | **Under query** (halted pending a query) | **dispute** |
| `CA` | **Conditionally accepted** (accepted under conditions) | conditional dispute |
| `AP` | Accepted (final approval, next step = payment) | accept |
| `RE` | **Rejected** (won't process further; expects credit note) | **reject** |
| `PD` | Paid | status |

**Clarification (mandatory for `RE` / `UQ` / `CA`)** in `cac:Response/cac:Status`:
- `cbc:StatusReason` — free text, and/or
- `cbc:StatusReasonCode` (`@listID`) — coded reason,
- `cac:Condition` (AttributeID + Description) — the disputed value,
- `cac:LineResponse` — dispute **specific invoice lines**.

Plus `cac:DocumentResponse/cac:DocumentReference/cbc:ID` = the invoice number
being responded to, `IssuerParty` (seller) / `RecipientParty` (buyer), and the
`SenderParty` / `ReceiverParty` endpoints for routing.

---

## 1b. Prior art in Odoo 19 — verified (CE + EE), 2026-08-03

Checked both source trees (`/home/rex/Odoo/19.0` CE, `/home/rex/Odoo/19.0-EE`):

- **No reusable, transport-independent Invoice Response builder exists.**
  `account_edi_ubl_cii` (the module we reuse for the invoice body via
  `account.edi.xml.ubl_bis3`) does **not** build `ApplicationResponse` — only a
  stray `cbc:ResponseCode` entry in `tools/ubl_21_common.py`. EE has **nothing**
  for Peppol `invoice_response` (the only `ApplicationResponse` hits are
  `l10n_co_dian` Colombia and `l10n_br_avatax` Brazil — unrelated).

- **CE ships `account_peppol_response`** ("Peppol Business Response") which *does*
  implement the full accept/reject/dispute mechanism — **but it is coupled to
  Odoo's SAS proxy**: `depends: ['account_peppol']`, `auto_install: True`. Its
  send path (`account_edi_proxy_user._peppol_send_response`) POSTs **structured
  data** (`response_code` + `clarifications`) to `_call_peppol_proxy`; **the
  Odoo proxy server builds the actual ApplicationResponse UBL**. There is **no
  client-side UBL builder**. Inbound, it only `etree.fromstring`-parses the
  response to read the code + clarifications.

**Consequences for us** (we deliberately don't install `account_peppol`):
1. Confirmed — **we must build the ApplicationResponse UBL ourselves** (§4.4).
   This is *worse* reuse than the invoice case: for invoices we reuse
   `ubl_bis3` for the body; for the response there is **no body builder to
   reuse at all**.
2. **Do NOT depend on `account_peppol_response`** — it would drag in
   `account_peppol` + the proxy. Since we never install the proxy, that module
   never coexists with ours (no conflict), but we also can't borrow its models
   directly.
3. **Do mirror its code lists for interop.** Reuse the *values* (not the
   dependency) so a Data-Dance-issued response is understood by Odoo-proxy
   recipients and vice-versa:
   - response codes `AB/IP/UQ/CA/RE/AP/PD` (Odoo's `account.peppol.response.response_code`);
   - clarification reason/action codes — Odoo's `account.peppol.clarification`
     with `list_identifier` `OPStatusReason` / `OPStatusAction`, codes like
     `REF` References incorrect, `LEG` Legal information incorrect, `REC`
     Receiver unknown, `QUA` Item quality insufficient, `DEL` Delivery issues,
     `PRI` Prices incorrect, `QTY` Quantity incorrect, `ITM` Items incorrect,
     `PAY` Payment terms incorrect, `FIN` Finance incorrect, `PPD` Partially
     paid, `UNR` Not recognized, `OTH` Other, `NON` No issue.
   Ship these as our own small data (an `edi.peppol.clarification` model or a
   Selection), carried in `StatusReasonCode @listID="OPStatusReason"` /
   `"OPStatusAction"` in the UBL we build.

---

## 2. Where it fits our architecture

Keep the existing axes: `provider = editel` (transport), `doc_family = peppol`.
An Invoice Response is another **UBL `ApplicationResponse`**, so it reuses:

- the `edi.message` lifecycle + eXite `sendInterchange`/`receiveInterchange`,
- the inbound classification-by-root-element + `_peppol_parse_envelope`,
- the `peppol_move_id` link and the commit-tolerant inbound dispatch.

The **only new discriminator** is the **CustomizationID**: an `ApplicationResponse`
is either an MLR (`mlr:3`) or an Invoice Response (`invoice_response:3`).

### 2.1 Classification refactor (small, backward-compatible)

Today `_peppol_root_localname()` maps the `ApplicationResponse` root to the
`message_type` token `"ApplicationResponse"`, and the dispatcher branches on
`message_type == "ApplicationResponse"` → `_peppol_process_mlr`.

Refine to sub-classify by CustomizationID:

```python
_MLR_CUSTOMIZATION = "urn:fdc:peppol.eu:poacc:trns:mlr:3"
_IR_CUSTOMIZATION  = "urn:fdc:peppol.eu:poacc:trns:invoice_response:3"

# ApplicationResponse -> message_type token:
#   mlr:3               -> "MLR"
#   invoice_response:3  -> "InvoiceResponse"
#   (other/unknown)     -> "ApplicationResponse"  (kept, logged, left in 'received')
```

`message_type` is a stored compute over the payload, so an `-u` recompute
**re-stamps existing MLR rows** (`ApplicationResponse` → `MLR`) automatically —
no data migration script needed. The dispatcher becomes:

```python
if rec.message_type == "MLR":              rec._peppol_process_mlr()
elif rec.message_type == "InvoiceResponse": rec._peppol_process_invoice_response()
elif rec.message_type in ("Invoice", "CreditNote"): rec._peppol_create_vendor_bill()
```

(For safety keep accepting the legacy `"ApplicationResponse"` token as MLR until
the recompute lands.)

### 2.2 Module boundary

**Recommendation: extend `edi_editel_peppol`** rather than spin a new module.
The `ApplicationResponse` parsing/classification/dispatch seams already live
here; a separate module would have to re-open all of them. Gate the new UI/flow
behind a config toggle so deployments that don't use Invoice Response are
unaffected. (If the surface grows, it can later be split into
`edi_editel_peppol_invoice_response` depending on this module — the seams make
that clean.)

---

## 3. Data model

### 3.1 `edi.message`
No new fields. New `message_type` values `"MLR"` / `"InvoiceResponse"` (§2.1).
The existing `sender_gln` / `receiver_gln` / `message_id` / `peppol_move_id`
carry the response's routing, its own `cbc:ID`, and the linked move.

### 3.2 `account.move`
Two independent axes — keep them separate from the MLR delivery badge
(`editel_peppol_response`, which stays as the *transport* MLR status):

**Seller side** (Invoice Responses received for invoices *we* sent):
```python
editel_peppol_ir_status = fields.Selection([
    ('AB','Acknowledged'), ('IP','In process'), ('UQ','Under query'),
    ('CA','Conditionally accepted'), ('AP','Accepted'),
    ('RE','Rejected'), ('PD','Paid')], readonly=True, copy=False)
editel_peppol_ir_reason = fields.Char(readonly=True, copy=False)   # latest reason
```
(latest wins; full history is the linked `edi.message` records.)

**Buyer side** (the response *we* sent for a vendor bill):
```python
editel_peppol_ir_sent_status = fields.Selection(<same selection>, readonly=True, copy=False)
```

**Buyer-side routing helpers** — to build the response we need the *original*
supplier invoice id + the supplier's Peppol endpoint. These are already on the
linked inbound `edi.message` (`message_id`, `sender_gln`), so expose them as
related/computed rather than duplicating:
```python
editel_peppol_source_msg_id  = fields.Many2one('edi.message', compute=…)  # inbound invoice msg
editel_peppol_supplier_endpoint = related/compute from that msg.sender_gln
```

---

## 4. Outbound flow — buyer rejects / disputes a vendor bill

### 4.1 UI
On the **vendor bill** form (`in_invoice`/`in_refund` that arrived via Peppol,
i.e. it has a linked inbound Peppol `edi.message`): a header button
**"Peppol Response…"** opening a wizard. Visible when
`editel_peppol_source_msg_id` is set; the *send* is EDI-gated.

### 4.2 Wizard `edi.peppol.invoice.response.wizard` (TransientModel)
```
move_id            : Many2one(account.move)  (context)
response_code      : Selection(RE/UQ/CA/AP/IP/PD/AB)  required
reason             : Text        (required when code in RE/UQ/CA)
reason_code        : Selection(BV/BW/SV/…)  optional
line_ids           : One2many -> per-invoice-line dispute (optional, P2)
```
On confirm → `move._editel_peppol_emit_invoice_response(response_code, reason, …)`.

### 4.3 Emit
```python
def _editel_peppol_emit_invoice_response(self, code, reason=None, reason_code=None,
                                         line_responses=None, queue_send=True):
    xml = self._editel_peppol_build_invoice_response(code, reason, reason_code, line_responses)
    msg = self.env['edi.message'].create({
        'direction': 'out', 'provider': 'editel', 'doc_family': 'peppol',
        'external_id': self.name, 'peppol_move_id': self.id,
        'company_id': self.company_id.id, 'state': 'ready',
    })
    msg._store_xml(xml, filename=…)        # message_type computes to "InvoiceResponse"
    if queue_send: msg._enqueue_send(self.env['editel.connector'])
    self.editel_peppol_ir_sent_status = code
    self.message_post(body=…)              # audit
    return msg
```
Routing inside the UBL:
- `SenderParty/EndpointID` = **our** company `peppol_eas`/`peppol_endpoint` (buyer),
- `ReceiverParty/EndpointID` = **supplier** endpoint (from the source inbound
  message `sender_gln`, or the partner's `peppol_endpoint`),
- `DocumentResponse/DocumentReference/ID` = the **supplier's** invoice number
  (source inbound message `message_id`).

No connector change: eXite base64s the UBL and auto-sets `applicationReference`.

### 4.4 UBL builder (core does NOT provide this)
`account_edi_ubl_cii` builds Invoice/CreditNote only, so we build the
`ApplicationResponse` ourselves. **Recommendation: a QWeb XML template**
(`templates/editel_peppol_invoice_response.xml`), consistent with how the
EDIFACT side renders its documents and easy to tweak per Peppol-version.
Skeleton:

```xml
<ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2" …>
  <cbc:CustomizationID>urn:fdc:peppol.eu:poacc:trns:invoice_response:3</cbc:CustomizationID>
  <cbc:ProfileID>urn:fdc:peppol.eu:poacc:bis:invoice_response:3</cbc:ProfileID>
  <cbc:ID t-esc="response_id"/>
  <cbc:IssueDate t-esc="issue_date"/>
  <cbc:IssueTime t-esc="issue_time"/>
  <cac:SenderParty><cbc:EndpointID t-att-schemeID="buyer_eas" t-esc="buyer_endpoint"/>…</cac:SenderParty>
  <cac:ReceiverParty><cbc:EndpointID t-att-schemeID="seller_eas" t-esc="seller_endpoint"/>…</cac:ReceiverParty>
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:ResponseCode t-esc="code"/>              <!-- RE / UQ / CA / AP … -->
      <t t-if="reason or reason_code">
        <cac:Status>
          <t t-if="reason_code"><cbc:StatusReasonCode t-att-listID="…" t-esc="reason_code"/></t>
          <t t-if="reason"><cbc:StatusReason t-esc="reason"/></t>
        </cac:Status>
      </t>
    </cac:Response>
    <cac:DocumentReference>
      <cbc:ID t-esc="invoice_id"/>
      <cbc:DocumentTypeCode t-esc="doc_type_code"/>  <!-- 380 invoice / 381 credit note -->
    </cac:DocumentReference>
    <cac:IssuerParty>…seller name…</cac:IssuerParty>
    <t t-foreach="line_responses" t-as="lr"><cac:LineResponse>…</cac:LineResponse></t>
  </cac:DocumentResponse>
</ApplicationResponse>
```
Optionally validate the rendered XML against the OpenPeppol Invoice-Response
schematron (`PEPPOL-EN16931-UBL-T111.sch`) in tests.

---

## 5. Inbound flow — seller receives an Invoice Response

Extend the existing `ApplicationResponse` handling:

1. `_peppol_parse_envelope` already returns `response_code`, `response_desc`,
   `referenced_id`, `supplier_endpoint`/`customer_endpoint`. **Add**:
   `customization` (from `cbc:CustomizationID`), `status_reason_code`,
   `status_reason`.
2. Classification stamps `message_type = "InvoiceResponse"` for `invoice_response:3`.
3. `_peppol_process_invoice_response`:
   - match the referenced document to **our sent customer invoice** by
     `DocumentReference/ID` == `move.name` (as MLR does),
   - set `move.editel_peppol_ir_status = response_code`,
     `move.editel_peppol_ir_reason = reason/desc`,
   - `message_post` a business note ("Peppol Invoice Response: Rejected — …"),
   - link `peppol_move_id`, mark `done`.
   - Unknown reference → log, leave message `done`/`received` (not an error).

Buyer's decision surfaces on the customer invoice as a badge (like the MLR one)
and in the **Peppol Messages** tab.

---

## 6. Access / security
- **Deciding** to reject/dispute is an AP business action → the wizard/button
  visible to `account.group_account_user` (or a dedicated approver group).
- **Sending** rides the EDI stack; the emit uses the same mechanics as invoice
  send. Read of linked `edi.message` from the move stays `sudo()` (as fixed for
  the status badge). The "Peppol Messages" tab stays `edi_base.group_edi_user`.

## 7. Config (`res.config.settings`)
- `editel.peppol.invoice_response.enabled` (bool, default off) — master toggle
  for the UI/flow.
- `editel.peppol.invoice_response.auto_ack` (bool, default off) — optionally
  auto-send `AB` (acknowledged) for every accepted incoming vendor bill.

---

## 8. Phasing & effort (static-validated; live against Editel test harness)

| Phase | Scope | Rough effort |
|---|---|---|
| **P0** | Inbound Invoice Response: classify by CustomizationID, parse, record `editel_peppol_ir_status`/reason on our sent invoices (chatter + badge). Reuses the MLR pattern. | ~0.5–1 day |
| **P1** | Outbound reject/dispute: wizard + QWeb builder + button on vendor bills + emit/send; `editel_peppol_ir_sent_status`. | ~2–3 days |
| **P2** | Line-level `LineResponse` disputes, `StatusReasonCode`/action code lists, schematron validation, status history view. | ~1–2 days |

## 9. Testing
- **Static**: `py_compile`, XML parse, manifest `ast.literal_eval`.
- **Unit**: build an Invoice Response → re-parse round-trip (codes, reference,
  endpoints); parse a canned sample → status mapping; schematron (P2).
- **Live** (Editel eXite test harness): (a) send a **reject**/**dispute** for a
  received (harness-inverted) vendor bill; (b) confirm an Invoice Response for a
  sent invoice is classified and recorded. Drive synchronously via `odoo shell`,
  same rig as the invoice/MLR tests.

## 10. Open items — `[VERIFY with Editel]`
1. **Does eXite route the `invoice_response` transaction?** Transport is
   identical to what already works (base64 UBL, auto `applicationReference`),
   so almost certainly yes — confirm the demo harness returns/accepts it.
2. **Recipient capability**: on the real Peppol network you may only send an
   Invoice Response to a participant whose SMP advertises the `invoice_response`
   document type. Not an issue for the test harness; relevant for production.
3. **Which supplier endpoint** to address on outbound — the source inbound
   invoice's `sender_gln` (authoritative for that document) vs the partner's
   stored `peppol_endpoint`. Prefer the former, fall back to the latter.
4. **`DocumentTypeCode`** value in `DocumentReference` (invoice `380` vs credit
   note `381`) — take from the source document.

## 11. Relationship to existing code (touch points)
- `models/edi_message.py`: `_UBL_ROOTS`/customization sub-classification,
  `_peppol_parse_envelope` (+customization, status reason), dispatcher branch,
  `_peppol_process_invoice_response`.
- `models/account_move.py`: new fields, `_editel_peppol_emit_invoice_response`,
  `_editel_peppol_build_invoice_response`, status computes.
- `wizards/edi_peppol_invoice_response_wizard.py` + view (new).
- `templates/editel_peppol_invoice_response.xml` (new QWeb).
- `views/account_move_views.xml`: buyer-side button + IR badges.
- `models/res_config_settings.py` + view: the two toggles.
- `CHANGELOG.rst` + manifest MINOR bump; likely `19.0.1.3.0`.
