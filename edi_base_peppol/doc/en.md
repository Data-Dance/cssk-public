---
title: Peppol e-invoicing (BIS Billing 3.0)
summary: Sends customer invoices and credit notes as Peppol BIS Billing 3.0 e-invoices, turns received e-invoices into draft vendor bills and handles business responses — through whichever EDI provider is installed.
verified: 19.0.1.6.0
---

## What it is for {#purpose}

**Peppol** is the European network for exchanging electronic invoices. A
company joins it through an **access point** (a Peppol service provider) and
is found on it by its **Peppol address** — a scheme code plus an identifier,
for example `0245:2020123456` for a Slovak company identified by its DIČ.
The invoice itself is a **Peppol BIS Billing 3.0** file: UBL 2.1 XML that
follows the European standard EN 16931.

This module does everything about the document and nothing about the
transport:

- decides, for every customer invoice and credit note, whether it goes out
  as an **e-invoice or as a PDF**, and says why ([routing](#routing));
- generates the BIS 3.0 file with Odoo's own builder and hands it to the
  installed provider ([sending](#sending));
- shows what happened to it ([statuses](#messages));
- turns received e-invoices and credit notes into **draft vendor bills**
  ([receiving](#receiving));
- records the **responses** your customers send back and lets you answer your
  suppliers ([responses](#responses)).

The transport — the connection to an access point — comes from a provider
module:

| Access point | Module |
|---|---|
| ePošťák | [module:edi_epostak_peppol](module:edi_epostak_peppol) |
| Editel eXite | `edi_editel_peppol` |
| GRiT Orion | `edi_grit_peppol` |

It does **not** use Odoo's own Peppol service (`account_peppol`). If that is
installed too, the two never send the same invoice: see
[routing](#routing).

For Slovak invoices, install
[module:l10n_sk_ubl_bis3](module:l10n_sk_ubl_bis3) as well. It identifies
Slovak parties by their DIČ and puts the variable symbol into the file where
the payer's bank looks for it; this module uses its builder automatically.

## Legal background {#legal}

**Slovakia.** All references are to the [VAT Act](law:sk/2004/222).

- **Until 31 December 2026** an electronic invoice may be issued only with the
  recipient's consent —
  [§ 71 ods. 1 písm. b)](law:sk/2004/222#paragraf-71.odsek-1.pismeno-b).
  For 2026 alone, [§ 85o ods. 21 and 22](law:sk/2004/222#paragraf-85o.odsek-22)
  waive that consent for an invoice in the European standard's data
  structure sent through a **delivery service** (*doručovacia služba*) to a
  business established in Slovakia that can receive it that way — except for
  supplies exempt under § 28 to § 43 and § 47 and for simplified invoices.
- **From 1 January 2027** e-invoicing is **mandatory**. Under § 85o ods. 2
  and 3 in the wording effective from that day, a VAT payer that supplies
  goods or services with the place of supply in Slovakia to a taxable person
  established in Slovakia, or to a non-taxable legal person established
  there, or receives a payment before such a supply, must issue an
  electronic invoice; exempt supplies (§ 28 to § 43 and § 47) and simplified
  invoices are excluded. Issuing it needs no consent; sending it other than
  through a delivery service does. Under ods. 4 an electronic invoice is a
  document with the particulars of § 74 ods. 1 in a format allowing
  automated processing and in a data structure that follows the European
  standard for electronic invoicing. A document changing it must be an
  electronic invoice too, quote the original's number and travel the same way
  (ods. 5), and the invoice must be issued within fifteen days (ods. 6). The
  invoice data are reported to the Financial Directorate through the
  delivery service, and handing the invoice to the delivery service fulfils
  that duty (ods. 9 to 11). E-invoices are kept for ten years (ods. 15). The
  same amendment adds **§ 71 ods. 5**: whoever must issue e-invoices must be
  able to send and receive them through a delivery service, and every
  domestic recipient of such supplies must be able to receive them.
  These provisions are not yet in the consolidated text in force today; the
  link leads to [§ 85o](law:sk/2004/222#paragraf-85o) as it stands now.
  By § 85o ods. 1 this regime is transitional, from 1 January 2027 to
  30 June 2030.
- **The delivery service** is provided by a certified provider entered in the
  register kept by the Financial Directorate
  ([§ 76a](law:sk/2004/222#paragraf-76a)). Whether your access point is
  such a provider is a question for the provider, not for Odoo.

**Czech Republic.** There is no general e-invoicing mandate. A tax document
may be electronic only if the customer agrees —
[§ 26 odst. 3 of the VAT Act](law:cz/2004/235). The Czech national format
ISDOC is described in [module:account_edi_isdoc](module:account_edi_isdoc).

**European Union.** Directive 2014/55/EU on electronic invoicing in public
procurement requires public contracting authorities to receive and process
invoices that comply with the European standard on electronic invoicing
(EN 16931) and one of its listed syntaxes (Article 7). Peppol BIS Billing 3.0
is a specification of EN 16931 in the UBL syntax.

## Setting it up {#setup}

1. **Install and connect a provider**, for example
   [ePošťák](module:edi_epostak_peppol#setup).
2. **Company settings.** *Settings → EDI*, block **Peppol BIS3 (this
   company)**. Every setting belongs to the company you are working in, so a
   Slovak company can e-invoice while its Czech sister does not:

   | Setting | What it does |
   |---|---|
   | Allow e-invoicing via Peppol | A permission, not a routing decision. Off: no customer invoice or credit note of this company leaves through Peppol, whatever a contact says. Receiving is not affected. |
   | Peppol scope | For contacts that state no preference: **Slovak mandate: domestic B2B and B2G only**, or **Any customer with a Peppol address** (default). See [routing](#routing). |
   | Auto-send Peppol on Invoice Post | Every posted document routed to Peppol is generated and queued at once. Off: use **Send via Peppol** or *Send*. |
   | Peppol Purchase Journal | Journal for received e-invoices. Empty: the company's first purchase journal. |

   **Peppol Transport** in the same block (database-wide) chooses which
   provider carries the documents when more than one is installed. It must
   be set then: with several installed and none chosen, nothing goes through
   Peppol and every invoice shows **blocked** with that reason. With a single
   provider it does not matter.
3. **Your company's Peppol address.** On your company's contact, tab
   *Invoicing*, group *Customer Invoices*: **Peppol e-address (EAS)** and the
   endpoint next to it. A Slovak company uses scheme **0245** with its
   **DIČ** (ten digits) — not the IČ DPH (scheme 9950) and not the IČO; see
   [the Slovak Peppol identifier](module:l10n_sk_ubl_bis3#participant).
4. **Each customer's and supplier's Peppol address**, in the same place.
5. **Invoice sending** on a contact (same group; Odoo normally hides it
   outside developer mode, this module shows it) says how that customer
   receives invoices. Choose **by e-invoice (Peppol)** to send every invoice
   of that customer through Peppol regardless of the scope. If the company
   works under the Slovak mandate and a Slovak business is set to anything
   else, the contact shows a warning that from 1. 1. 2027 its invoices must
   be e-invoices.
6. **Access.** The **Send via Peppol** and **Peppol Response…** buttons are
   shown to the *EDI User* group. Anyone who may edit the invoice can send
   it: posting with *Auto-send* on and **Send & Print** need no EDI group,
   and the EDI message is recorded on the user's behalf.

## E-invoice or PDF {#routing}

Every customer invoice and credit note shows how it goes out: a badge in the
form header once posted, and **Sent as** with **Why** at the top of the
*Other Info* tab.

| Sent as | Meaning |
|---|---|
| Peppol e-invoice | goes out through Peppol |
| PDF | goes out the usual way (email, print); Peppol does not apply |
| Peppol, but blocked | should go through Peppol but cannot: a Peppol address is missing |

The decision, in this order:

1. The company does not allow e-invoicing → **PDF**.
2. The contact's **Invoice sending** is *by e-invoice (Peppol)* → **Peppol**,
   or **blocked** if your company or the customer has no Peppol address.
3. It is *Peppol* — Odoo's own Peppol service → **PDF** as far as this module
   is concerned; Odoo's service sends it, so the invoice never leaves through
   two access points.
4. It is anything else, for example *by Email* → **PDF**.
5. Nothing is chosen on the contact, and the scope is the **Slovak mandate**:
   a company whose fiscal country is not Slovakia or that has no VAT number
   (not a VAT payer), a customer outside Slovakia, or a customer with no
   business identifier at all — not a company and without a VAT number, IČO
   or DIČ (treated as a consumer) → **PDF**. A sole trader with an IČO but
   no VAT number is a business: the mandate covers every taxable person.
6. Your company has no Peppol address → **blocked**. The customer has none →
   **blocked** under the Slovak mandate, **PDF** under *any customer with a
   Peppol address*.
7. Several Peppol transports are installed and **Peppol Transport** names
   none → **blocked**.
8. Otherwise → **Peppol**.

The rule for the Slovak mandate follows § 85o ods. 2 and 3 as far as the data
of a contact allow: a VAT payer supplying a taxable person (any business,
VAT-registered or not) or a non-taxable legal person established in
Slovakia. It does not look at the place of supply or at the taxes of the
invoice, so an exempt supply (§ 28 to § 43, § 47) to a Slovak business is
routed to Peppol like any other — allowed, though not required. Simplified
invoices are receipts, which are never sent. Where the law gives a different
answer for a customer, set **Invoice sending** on that contact.

## Sending {#sending}

A posted document routed to Peppol is sent in one of three ways:

- **Automatically on posting**, if *Auto-send Peppol on Invoice Post* is on.
  An invoice that would have gone but is blocked gets a chatter line
  "Not sent via Peppol: …" with the reason; one whose file fails Odoo's
  checks gets the same line with the errors and a *Peppol e-invoice not
  sent* activity for its salesperson. The invoice stays posted.
- **Send via Peppol** in the form header.
- **Send** (Odoo's *Send* dialog). The method **by e-invoice (Peppol)** is
  offered and ticked; when the contact has no *Invoice sending* chosen it
  replaces the email default, and Odoo's own Peppol method is unticked. A
  failure is shown in the dialog as "The e-invoice could not be sent".
  A document already queued or sent is skipped.

Sending generates the BIS 3.0 file with the builder of the customer's
**eInvoice format** if that is a Peppol format, otherwise with the format
Odoo suggests for the customer — for a Slovak customer with
[module:l10n_sk_ubl_bis3](module:l10n_sk_ubl_bis3) installed, the Slovak
one. If Odoo's checks of the EN 16931 and Peppol rules fail, nothing is sent
and the errors are listed. Otherwise an outbound EDI message is created, the
file stored on it, the message queued at the provider and a chatter line
written: "Invoice sent via Peppol: … (queued)".

Each document has **one** outbound message. Sending again reuses it with a
freshly generated file, through the transport and in the test or production
mode in force **now** — a document first tried in a test environment goes to
production once you have switched. While that message is *Queued* or
*Sent*, sending again is refused ("already being sent"); once it is *Done*
in production, too ("already delivered"): a delivered invoice is corrected
with a credit note, not sent twice.

## Statuses {#messages}

On the invoice:

| Field | Shows |
|---|---|
| Peppol Status | the state of the latest outbound message: *Ready*, *Queued*, *Sent*, *Error*, *Done* (see [states](module:edi_base#states)) |
| Peppol Delivery Response | the latest message-level response (MLR) from the network, as "code — description" |
| Peppol Invoice Response | the customer's latest business response, for example *Accepted* or *Rejected* |
| Peppol Response Reason | the reason the customer gave with it |
| Peppol Response Sent | on a vendor bill: the last response you sent to the supplier |

Accounting users see these badges without any EDI group. Members of the EDI
groups also get a **Peppol Messages** tab listing every message of the
document — the e-invoice, responses received and sent — and each message
links back through **Peppol Document**.

What *Sent* and *Done* prove depends on the access point. With ePošťák,
*Sent* is acceptance for transport and *Done* is delivery to the recipient's
access point — see [delivery status](module:edi_epostak_peppol#statuses).

## Receiving e-invoices {#receiving}

The provider collects documents addressed to your Peppol address (see
[receiving](module:edi_base#receiving) for the common steps). For a Peppol
invoice or credit note:

- a **draft vendor bill** is created — a credit note becomes a vendor credit
  note — in the *Peppol Purchase Journal*, or the company's first purchase
  journal, using Odoo's standard UBL import for the supplier, lines, taxes
  and amounts;
- the XML file is attached to the bill;
- the bill is **never posted automatically**; check it like any other bill;
- the supplier is recognised by its Peppol endpoint, and the message moves to
  *Done*. If the bill cannot be created, the message moves to *Error* and
  keeps the file; fix the cause and press **Reprocess**.

A document already received is skipped (and acknowledged, so the provider
stops delivering it) only when its number, its kind (invoice, credit note,
response), its sender's endpoint and its receiver's endpoint all match a
stored message. Two suppliers' invoices with the same number, an invoice
and a credit note sharing a number, or one supplier's invoices to two of
your companies are therefore separate documents. A document whose sender
endpoint cannot be read is always stored.

## Business responses {#responses}

Peppol carries two kinds of response, both as an *ApplicationResponse*
document:

- **Message level response (MLR)** — technical: whether a receiving system
  accepted the file;
- **Invoice Response** — business: what the buyer does with the invoice.

Status codes:

| Code | Meaning |
|---|---|
| AB | Acknowledged — received |
| IP | In process |
| UQ | Under query — disputed, waiting for an answer |
| CA | Conditionally accepted |
| AP | Accepted |
| RE | Rejected |
| PD | Paid |

**Responses from your customers.** An incoming response is matched to your
invoice or credit note by the document number it refers to, within the same
company. An MLR fills *Peppol Delivery Response*; an Invoice Response fills
*Peppol Invoice Response* and *Peppol Response Reason*; both write a chatter
line. A response that refers to a document Odoo does not know is kept as a
message, marked done, and linked to nothing.

**Your response to a supplier.** On a vendor bill that arrived through Peppol
(both parties having a Peppol address), **Peppol Response…** opens a dialog:

| Field | Purpose |
|---|---|
| Response | the status code above; defaults to *Rejected* |
| Reasons | coded reasons, e.g. *PRI — Prices incorrect*, *QTY — Quantity incorrect*, *REF — References incorrect* |
| Requested actions | what the supplier should do, e.g. *NCR — Issue a credit note*, *NIN — Issue a new invoice*, *PIN — Provide additional information* |
| Note | free text sent to the supplier |

A reason or a note is required for *Rejected*, *Under query* and
*Conditionally accepted*. The response is sent through the provider, the bill
shows **Peppol Response Sent**, and the chatter records it. Nothing is sent
back automatically — no response is generated when you post or pay a bill.

## Limitations {#limitations}

- A received document whose sender endpoint cannot be read is stored each
  time the provider delivers it, so a re-delivery of it appears as a second
  message.
- The Slovak-mandate rule is an approximation (see [routing](#routing)).
- Only customer invoices and credit notes are sent. Received e-invoices
  become drafts; Odoo does not answer them with an MLR.
- One Peppol transport serves the whole database; it cannot differ by
  company.
