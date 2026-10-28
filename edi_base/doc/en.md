---
title: EDI Base
summary: The common ground of every EDI and Peppol connection — the EDI message log, its states, sending and receiving, and the partner settings all providers share.
verified: 19.0.1.9.1
---

## What it is for {#purpose}

Every electronic document Odoo exchanges with a trading partner through an
EDI provider — an order, an order response, a despatch advice, an invoice, a
Peppol e-invoice or a business response — is recorded as one **EDI message**.
This module provides that log and the machinery around it:

- the **EDI → Messages** list, where every inbound and outbound document of
  every provider is kept with its raw XML;
- the **states** a message passes through and the buttons that move it on;
- how an outbound message is **handed to the provider** and how inbound
  documents are **collected**, stored and processed;
- the **GLN** of every contact and a per-customer switch for automatic
  sending.

On its own it connects to nothing. A provider module does the transport:

| Provider | Modules |
|---|---|
| Editel (eXite) | `edi_editel_*` |
| GRiT (Orion) | `edi_grit_*` |
| ePošťák (Peppol access point) | [module:edi_epostak_peppol](module:edi_epostak_peppol) |

What happens to orders, deliveries and invoices is described in the guides
for the sales side, [module:edi_base_sale](module:edi_base_sale), the
purchase side, [module:edi_base_purchase](module:edi_base_purchase), and
Peppol e-invoicing, [module:edi_base_peppol](module:edi_base_peppol).

## Setting it up {#setup}

1. **Give people access.** The **EDI** menu is visible only to members of two
   groups, set on the user (*Settings → Users*):

   | Group | Can |
   |---|---|
   | EDI User | see the EDI menu, the messages and the EDI tabs on documents |
   | EDI Manager | everything above, plus **Send**, **Reprocess** and creating or changing messages |

   An administrator is **not** in either group by default; add yourself
   first. Sending a Peppol invoice creates an EDI message, so whoever sends
   one needs **EDI Manager** (see [Peppol e-invoicing](module:edi_base_peppol#limitations)).
2. **Record your own GLN** on your company's contact (field **GLN**, tab
   *Sales & Purchase*), and the GLN of every EDIFACT trading partner. Peppol
   connections identify parties by their Peppol address instead — see
   [the Peppol guide](module:edi_base_peppol#setup).
3. **Install and configure the provider.** Its settings appear in
   *Settings → EDI*, or from *EDI → Configuration → Settings* (system
   administrators only).

### Contacts {#partners}

On the contact form, tab *Sales & Purchase*:

| Field | What it does |
|---|---|
| GLN | The contact's Global Location Number. Odoo shows it only on delivery addresses; here it is shown on every contact, because any EDI party — your company, the customer, the invoicee, the delivery point — is identified by it. Contacts can be searched by GLN. |
| Override EDI auto-send | Off (default): outbound EDI messages for this customer or vendor follow the provider's global auto-send settings. On: the provider modules show per-document choices (*always* / *never* / *default*) that take precedence for this company and all its contacts. |

Two more fields belong to the EDIFACT providers and are described
[below](#gs1).

## The message log {#messages}

*EDI → Messages* lists every message, newest first. Red rows are in error,
orange rows carry a warning or come from a test environment, grey rows are
done. Filters: *Inbound*, *Outbound*, *Test Mode*, *Production*, *Errors*,
*Pending* (draft, ready or received), *Done*, *Peppol BIS3*; grouping by
provider, message type, direction, state or partner.

The message form shows:

| Field | Meaning |
|---|---|
| Document Name | the file name of the document |
| Provider | the transport (Editel, GRiT, ePošťák, …) |
| Document Family | *EDIFACT* or *Peppol BIS3* — the document standard, independent of the provider |
| Message Type | ORDERS, ORDRSP, DESADV, INVOIC, … for EDIFACT; Invoice, CreditNote, MLR, InvoiceResponse for Peppol |
| Direction | Inbound / Outbound |
| Environment | the provider's test or production mode, stamped when the message was created; a test message carries a **TEST** ribbon |
| Partner | resolved from the sender's (inbound) or receiver's (outbound) GLN or Peppol address |
| Message ID, Message Date, Sender GLN, Receiver GLN | read from the document itself; for Peppol, the "GLN" fields hold the Peppol endpoints |
| External Reference, Customer / Vendor Reference | your document number and the counterparty's order number, so one conversation (order → response → despatch → invoice) can be searched by one reference |
| Provider Interchange ID, Transmission UUID | the provider's own identifiers — quote them to the provider's support |
| Error Details, Blocking Level | why the message failed, and whether it is a warning or an error |
| XML Content | the document, indented for reading |

The XML is always stored as an attachment of the message; documents up to
1 MB are also shown inline. Links to the order, delivery, invoice or bill the
message belongs to are added by the sale, purchase and Peppol modules, which
also put an **EDI Messages** tab on those documents.

A message belongs to the **company of the document it was created for**, not
to the company the user happened to be working in, and it is sent and
processed as that company.

## States {#states}

| State | Outbound | Inbound |
|---|---|---|
| Draft | created, not yet prepared | — |
| Ready | generated and waiting to be sent (automatic sending off, or waiting for you) | — |
| Queued | handed over for sending, not yet accepted by the provider | — |
| Sent | accepted by the provider | — |
| Received | — | stored, waiting to be processed or being reprocessed |
| Error | sending failed; see *Error Details* | processing failed; the document is kept |
| Done | finished: for some providers this means delivery to the recipient was confirmed (see the provider's guide) | processed: the order, bill or response was created or recorded |

What *Sent* and *Done* prove differs by provider. For ePošťák, *Sent* means
the access point accepted the document for transport and only *Done* means
the recipient's access point received it — see
[delivery status](module:edi_epostak_peppol#statuses).

## Sending {#sending}

Provider modules create outbound messages from documents — automatically
when a document is confirmed or posted, if automatic sending is on, or when
you press the provider's send button. To send or re-send a message yourself:

- **Send** on the message form (EDI Manager), for outbound messages in
  *Draft*, *Ready*, *Queued* or *Error*;
- several at once: select them in the list, *Actions → Send (queue
  dispatch)*. A dialog lists what will be sent and what will be skipped
  (inbound messages, messages already sent or done) before anything happens.

Sending clears the previous error, moves the message to **Queued** and writes
a line on the order, delivery or invoice it belongs to ("… queued for
dispatch via …").

### How a queued message leaves {#dispatch}

Each provider declares one of two ways:

- **Job queue.** The message becomes a background job of the OCA job runner
  (`queue_job`), linked to the message by
  [module:edi_base_queue_job](module:edi_base_queue_job). The Editel and GRiT
  connectors work this way and install it. A message with jobs shows a
  **Queue Jobs** button; on the job, the *Related* button opens the message,
  and the job list can be filtered by message. A job is attempted up to five
  times.
- **Scheduled action.** *EDI: send queued messages (no job runner)* runs every
  2 minutes and sends up to 100 queued messages of the providers registered
  for it — ePošťák is one. Each message is sent on its own: a temporary
  failure (the provider unavailable, a rate limit) leaves it **Queued** with a
  warning in *Error Details* and a *Retry Not Before*: the provider's own
  Retry-After, else a pause that doubles with each attempt (2, 4, 8 …
  minutes, at most an hour). After five temporary failures — a rate limit
  does not count as one — it moves to **Error** with the last reason; so does
  any other failure at once. Sending it again starts the count afresh. One unsendable message does not stop or undo the
  others, and each message's outcome is saved before the next is sent, so a
  run that is interrupted keeps what the provider already accepted. When the
  run's time is up, the rest stay queued for the next run.

The choice is the provider's, not the database's, so a database with both
never sends one message twice.

## Receiving {#receiving}

Each provider has its own scheduled action that collects new documents. For
every document:

1. If a message with the same message ID from the same provider was already
   received, the document is skipped as a duplicate (and acknowledged). A
   provider family can make this stricter: for Peppol the sender, the
   receiver and the document kind must match as well — see
   [receiving Peppol documents](module:edi_base_peppol#receiving).
2. Otherwise it is **stored first**, with its XML, as a message in *Received*.
3. It is then processed — an order, a bill, a response is created or recorded
   — and the message moves to **Done**. If processing fails, the message moves
   to **Error** with the reason in *Error Details*; the document is not lost.
4. The document is acknowledged to the provider, so it is not delivered again.

When the provider reports that more documents are waiting, the collection
runs again at once instead of waiting for the next interval.

**Reprocess** (EDI Manager, inbound messages in *Received* or *Error*) runs
step 3 again — typically after you have created a missing product or
recorded a contact's GLN.

### Matching products {#products}

Inbound order and delivery lines are matched to products in this order:

1. the **barcode** — tried as sent, without leading zeros, and padded to 8,
   12, 13 and 14 digits, because partners disagree on padding EAN codes;
2. the sender's own code for the product (*Vendor Product Code* on the
   product's vendor line), if the sender is known;
3. the product's **internal reference**.

If a line matches nothing, the whole incoming order fails by default and the
error lists every unmatched line (EAN, quantity, price, names and codes)
with the advice to create the products and reprocess.
[module:edi_base_sale_pending](module:edi_base_sale_pending) changes that, see
[pending lines](module:edi_base_sale#pending-lines).

## Variable symbol {#variable-symbol}

Where a message carries a variable symbol — the supplier's bank details in an
outbound INVOIC, the paid bill in a REMADV — it is the symbol a Czech or
Slovak payment order uses: **digits only, at most ten**. It is the
*Variable Symbol* from [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols)
when that is installed; otherwise the digits of the *Payment Reference*, else
of the invoice number (on a vendor bill, of the supplier's number), keeping
the last ten. `INV/2026/00012` becomes `202600012`. When there are no digits
at all the element is left out.

## EDIFACT party identity (GS1) {#gs1}

[module:edi_base_gs1](module:edi_base_gs1), installed with the Editel and
GRiT providers, adds the GS1 party settings EDIFACT exchanges need and Peppol
does not:

| Where | Field | Meaning |
|---|---|---|
| Contact | EDI Communication Endpoint | The contact whose GLN owns the EDI mailbox, used as sender/recipient of the envelope while the buyer, invoicee and delivery place keep their own GLNs. Set it on the company; its contacts inherit it. Empty: the contact's own GLN. |
| Contact | EDI DESADV in SSCC mode | Despatch advices for this customer use the SSCC package structure instead of a flat list of articles. Set on the company; its contacts inherit it. |
| Warehouse (form, next to the address) | EDI GLN (Delivery Point) | The GLN of the warehouse as the delivery place in outbound documents and for matching incoming despatch advices; the company's GLN is used when empty. |

## Limitations {#limitations}

- Dates and times in EDIFACT documents are read and written in the time zone
  of the system parameter `edi.timezone` (default `Europe/Bratislava`).
- For EDIFACT documents, duplicate detection compares the interchange's
  message ID and the provider only; Peppol adds the sender, the receiver and
  the document kind (see
  [Peppol limitations](module:edi_base_peppol#limitations)).
- Messages cannot be deleted from the user interface; nobody has delete
  rights on them.
