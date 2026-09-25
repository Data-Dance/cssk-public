# Design: line-level disputes for Peppol Invoice Response (`edi_base_peppol`)

Status: **proposal / design** — 2026-08-06. Extends the shipped Invoice Response
(header-level accept/reject/dispute) with **`cac:LineResponse`** so a buyer can
dispute *specific invoice lines*, and a seller can see *which lines* a buyer
disputed. This is the deferred **P2** item from
[`invoice_response_design.md`](invoice_response_design.md).

---

## 1. The UBL (what we add)

The Peppol Invoice Response already carries a header `cac:Response`; line detail
is added as zero-or-more `cac:LineResponse` inside `cac:DocumentResponse`:

```xml
<cac:DocumentResponse>
  <cac:Response><cbc:ResponseCode>UQ</cbc:ResponseCode> … </cac:Response>   <!-- header -->
  <cac:DocumentReference><cbc:ID>INV/2026/00001</cbc:ID> … </cac:DocumentReference>
  <cac:LineResponse>                                <!-- 0..n -->
    <cac:LineReference>
      <cbc:LineID>2</cbc:LineID>                    <!-- references the invoice line's cbc:ID -->
    </cac:LineReference>
    <cac:Response>
      <cbc:ResponseCode>RE</cbc:ResponseCode>       <!-- per-line status -->
      <cac:Status>
        <cbc:StatusReasonCode listID="OPStatusReason">QTY</cbc:StatusReasonCode>
        <cbc:StatusReason>Quantity billed exceeds delivered</cbc:StatusReason>
      </cac:Status>
    </cac:Response>
  </cac:LineResponse>
</cac:DocumentResponse>
```

Typical pattern: header code `UQ`/`RE`, with the specific problems carried
per-line. Header stays required; line responses are additive.

## 2. The line-ID mapping — the crux (verified)

`cac:LineResponse/cac:LineReference/cbc:LineID` must reference the disputed
**invoice line's `cbc:ID`**. Odoo core sets that deterministically:

- `account_edi_xml_ubl_20.py:972` → `line_node['cbc:ID'] = line_idx`, and only
  **product** lines become `cac:InvoiceLine`s (`:429`). So the UBL line `cbc:ID`
  is the **1-based index over the move's product lines** (our generated invoice
  shows `<cbc:ID>1</cbc:ID>`).

Consequences for the two directions:

- **Inbound (buyer disputed *our* sent invoice):** we generated the UBL, so
  `LineID = N` maps to **our N-th product line** — a safe positional map. (We
  can also cross-check against our stored outbound UBL.)
- **Outbound (we dispute a *received* vendor bill):** we must reference the
  **supplier's** line IDs, not assume ours. Read the source UBL (stored on the
  linked inbound `edi.message`), extract each `InvoiceLine`/`CreditNoteLine`
  `cbc:ID` in order, and correlate to our bill's product lines **by position**
  (core imports lines in UBL order). Emit the *supplier's* `cbc:ID` in
  `LineID`, not a re-derived one.

New helpers in `edi.message` / `account.move`:

```python
# edi.message
def _peppol_ubl_line_ids(self, xml_content):
    """Ordered list of InvoiceLine/CreditNoteLine cbc:ID from a UBL invoice/
    credit note payload (positional line identifiers)."""

# account.move
def _peppol_product_lines(self):
    """invoice_line_ids filtered to display_type='product', in sequence."""

def _peppol_line_ubl_id(self, move_line, source_xml=None):
    """The UBL cbc:ID to reference for a given product move line. For a sent
    invoice: str(position). For a received bill: the source UBL's cbc:ID at
    that position (falls back to str(position))."""
```

Positional mapping is robust for Odoo↔Odoo and for the standard numbering; a
foreign system that numbers lines non-sequentially is handled by reading the
source UBL's actual `cbc:ID`s (outbound) and by best-effort match + a logged
warning when a `LineID` can't be resolved (inbound).

## 3. Data model

**Seller side (inbound — record which of *our* lines the buyer disputed):**
new fields on `account.move.line`:
```python
peppol_ir_line_status = fields.Selection(PEPPOL_RESPONSE_CODES, readonly=True, copy=False)
peppol_ir_line_reason = fields.Char(readonly=True, copy=False)
```
Shown as a badge/column on the invoice line list, so AP sees the flagged lines
in place. (Header `peppol_ir_status` still carries the overall decision.)

**Buyer side (outbound — choose which lines to dispute):** a transient line
model backing the wizard One2many:
```python
class PeppolInvoiceResponseLineWizard(models.TransientModel):
    _name = 'edi.peppol.invoice.response.line.wizard'
    wizard_id      = fields.Many2one('edi.peppol.invoice.response.wizard', ondelete='cascade')
    move_line_id   = fields.Many2one('account.move.line', required=True, domain=…product lines of the bill)
    response_code  = fields.Selection(PEPPOL_RESPONSE_CODES, required=True, default='RE')
    reason_ids     = fields.Many2many('edi.peppol.clarification', domain=[('list_identifier','=','OPStatusReason')])
    note           = fields.Char()
```

No persistent per-line model on the buyer side is needed — the sent UBL (stored
on the `edi.message`) is the record; the header `peppol_ir_sent_status` stays as
the summary.

## 4. Parse extension (`_peppol_parse_envelope`, ApplicationResponse branch)

Add a `line_responses` list to the returned dict:
```python
line_responses = []
for lr in root.iterfind(f'{{{CAC_NS}}}DocumentResponse/{{{CAC_NS}}}LineResponse'):
    line_responses.append({
        'line_id':      _text(lr.find(f'{{{CAC_NS}}}LineReference/{{{CBC_NS}}}LineID')),
        'code':         _text(lr.find(f'{{{CAC_NS}}}Response/{{{CBC_NS}}}ResponseCode')),
        'reason_code':  _text(lr.find(f'{{{CAC_NS}}}Response/{{{CAC_NS}}}Status/{{{CBC_NS}}}StatusReasonCode')),
        'reason':       _text(lr.find(f'{{{CAC_NS}}}Response/{{{CAC_NS}}}Status/{{{CBC_NS}}}StatusReason')),
    })
```
(Only populated for `InvoiceResponse`; MLRs have none.)

## 5. Process extension (`_peppol_process_invoice_response`)

After recording the header status, map each line response to a move line and
stamp it:
```python
prod_lines = move._peppol_product_lines()
for lr in parsed.get('line_responses', []):
    ml = move._peppol_move_line_for_ubl_id(lr['line_id'], prod_lines)   # positional
    if not ml:
        _logger.info("Peppol IR %s: line ref %r not resolvable on %s", self.id, lr['line_id'], move.name)
        continue
    ml.peppol_ir_line_status = lr['code'] or False
    ml.peppol_ir_line_reason = _fmt(lr['reason_code'], lr['reason'])
```
Chatter summarises the disputed lines.

## 6. Builder extension (`_peppol_build_invoice_response`)

Accept `line_responses` (list of dicts: `move_line`, `code`, `clarifications`,
`note`). For each, resolve the UBL line id from the **source** invoice UBL and
emit:
```python
'<cac:LineResponse><cac:LineReference><cbc:LineID>%s</cbc:LineID></cac:LineReference>'
'<cac:Response><cbc:ResponseCode>%s</cbc:ResponseCode>%s</cac:Response></cac:LineResponse>'
```
reusing the existing `_xe` quote-safe escaping and the same `<cac:Status>`
rendering as the header. Guard: a line with code in `RE`/`UQ`/`CA` needs a
reason (same rule as the header).

## 7. Wizard + views

- Wizard gains `line_ids` (One2many above) rendered as an editable list under
  the header response. A helper button "Load bill lines" pre-fills a row per
  product line (default code = the header code) so the user just ticks/edits the
  disputed ones; empty `line_ids` = header-only response (today's behaviour).
- `account.move._peppol_emit_invoice_response` gains a `line_responses` param,
  passed through to the builder; wizard `action_send` builds it from `line_ids`.
- Invoice-line list view (seller side): add `peppol_ir_line_status` as an
  optional badge column, visible when set.

## 8. Edge cases

- **Credit notes:** read `CreditNoteLine` (not `InvoiceLine`) for the source
  line ids; `_peppol_ubl_line_ids` handles both roots.
- **Unresolvable `LineID`** (foreign numbering, deleted line): skip + log; never
  raise (keep the header response recorded).
- **Header vs line consistency:** we don't force it — Peppol allows header `UQ`
  with per-line `RE`. The wizard defaults line codes to the header code for
  convenience.
- **Re-response:** a later Invoice Response overwrites the per-line fields (last
  wins), same as the header.

## 9. Effort

Moderate — ~1–1.5 days: parse + process + builder extensions, the line wizard
model + view, two `account.move.line` fields + a list column, and the line-id
mapping helpers. No transport/connector changes; rides the same
`ApplicationResponse` classification and provider hooks. Optional follow-on:
Schematron validation of the emitted response (`PEPPOL-EN16931-UBL-T111.sch`).

## 10. Touch points

- `models/edi_message.py`: `_peppol_parse_envelope` (+`line_responses`),
  `_peppol_process_invoice_response`, `_peppol_ubl_line_ids`.
- `models/account_move.py`: `_peppol_build_invoice_response` (+`line_responses`),
  `_peppol_emit_invoice_response` (+param), `_peppol_product_lines`,
  `_peppol_line_ubl_id` / `_peppol_move_line_for_ubl_id`.
- `models/account_move_line.py` (new): the two per-line fields.
- `wizards/`: the line-wizard model + One2many + view.
- `views/`: invoice-line badge column.
- `CHANGELOG.rst` + manifest MINOR bump.
