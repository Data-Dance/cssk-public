---
title: ePošťák — Peppol e-invoicing
summary: Sends and receives Peppol e-invoices and business responses through the Slovak access point ePošťák, with your own ePošťák contract or through the Data Dance hosted service.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

**ePošťák** is a Slovak Peppol access point. These modules connect Odoo to
it, so that the e-invoices prepared by
[Peppol e-invoicing](module:edi_base_peppol) actually leave and arrive:

| Module | Role |
|---|---|
| this module | makes ePošťák the transport for Peppol documents |
| [module:edi_epostak_base](module:edi_epostak_base) | the sandbox / production switch, the firm ID, the Peppol address checks |
| [module:edi_epostak_connector_sapi](module:edi_epostak_connector_sapi) | the connection itself: credentials, sending, collecting, delivery status, reachability check |
| [module:edi_epostak_broker_client](module:edi_epostak_broker_client) | only on the Data Dance hosted service: sends through the hosting broker instead of holding ePošťák credentials ([below](#broker)) |

Install this module and the connector. What is sent, when, and what happens
to received documents is decided by the Peppol module — its guide explains
[routing](module:edi_base_peppol#routing),
[sending](module:edi_base_peppol#sending),
[receiving](module:edi_base_peppol#receiving) and
[business responses](module:edi_base_peppol#responses). This guide covers
what is specific to ePošťák: the connection, what each status means and
what to do when something fails.

The Slovak e-invoicing obligation from 1 January 2027 is summarised in the
[legal background](module:edi_base_peppol#legal) of the Peppol guide.

## Setting it up {#setup}

Everything is in *Settings → EDI*, section **ePošťák**. The environment
applies to the whole database; the Firm ID, the credentials (on the hosted
service, the broker key) and the inbound poll belong to the **company you are
working in**. To set up another company, switch to it and fill in its own.

1. **Environment** (*ePošťák Environment*): **Sandbox** (default) or
   **Production**. While the sandbox is active a yellow banner says so;
   sandbox documents never reach the real Peppol network. Each environment
   keeps its own credentials, so switching does not erase them.
2. **Credentials** for the active environment — block *Credentials
   (Sandbox)* or *Credentials (Production)*: **Client ID** and **Client
   Secret** from your ePošťák account. The URL fields are prefilled and
   normally stay as they are. On the hosted service, fill in the broker
   instead ([below](#broker)).
3. **Configured key** tells you which kind of secret you entered — it cannot
   be read back from the password field:

   | Key | Firm ID |
   |---|---|
   | firm key (`sk_live_…`) | leave **ePošťák Firm ID** empty; the firm is implied |
   | integrator key (`sk_int_…`), speaking for several firms | **ePošťák Firm ID** is required: the UUID of the firm this database invoices as |

4. **Test Connection.** Saves the settings and tries to log in. With an
   integrator key and no Firm ID it lists the firms the key may act for, with
   their IČO and Peppol address; if there is exactly one, it fills in the
   company's Firm ID for you. It also names any other company that allows
   e-invoicing but has no ePošťák credentials of its own. Press it again to confirm. The result is always shown as
   a notification — a failure does not discard what you typed.
5. **Your company's Peppol address** — on your company's contact, tab
   *Invoicing*: **Peppol e-address (EAS)** `0245` and your **DIČ** as the
   endpoint (see [the Slovak identifier](module:l10n_sk_ubl_bis3#participant)).
   Every request to ePošťák is made as that participant. An endpoint under
   scheme 0245 that is not exactly ten digits is refused before anything is
   sent; eight digits is reported as an IČO, which is not routable.
6. **The company switches** in the same Settings page, block *Peppol BIS3
   (this company)* — allow e-invoicing, scope, automatic sending, purchase
   journal: see [the Peppol setup](module:edi_base_peppol#setup). With more
   than one Peppol provider installed, set **Peppol Transport** there; left
   empty, nothing goes through Peppol.
7. **Check a customer before the first invoice** — see
   [reachability](#reachability).

Only system administrators open Settings; to send and see EDI messages they
also need the EDI groups ([access](module:edi_base#setup)).

## Through the Data Dance hosted service {#broker}

On a database hosted by Data Dance,
[module:edi_epostak_broker_client](module:edi_epostak_broker_client) is
installed and the connection goes through the hosting service's broker
rather than straight to ePošťák. The database then holds **no ePošťák
credentials at all**. In *Settings → EDI → ePošťák*, block **Data Dance
broker**:

| Field | What it is |
|---|---|
| Broker URL | Setting it switches the database to broker mode; clearing it returns to a direct ePošťák contract |
| Broker key ID | identifies the key; not secret on its own — per company |
| Broker key | signs every request; shown once when it is issued — per company |

You receive these with the hosted service. The Client ID, Client Secret and
Firm ID are then neither used nor needed — the broker decides which companies
the database may act for. **Test Connection** asks the broker exactly that
and reports an error if it lists no company for this database.

Everything else — documents, statuses, collection, the reachability check —
works the same. Failures arrive already classified: the database's key was
refused, the document or address was refused (fix it, it will fail the same
way again), or the service is temporarily unavailable.

## What the statuses mean {#statuses}

The EDI message of an ePošťák document moves like this:

| State | Meaning |
|---|---|
| Ready | the file is generated, waiting to be sent |
| Queued | waiting for *EDI: send queued messages (no job runner)*, which runs every 2 minutes; a message whose send failed temporarily waits here too, with a warning in *Error Details* |
| **Sent** | ePošťák **accepted the document for transport** (HTTP 202). This is intake, **not delivery**. *Provider Interchange ID* holds ePošťák's document ID. |
| **Done** | ePošťák reports the document **delivered** to the recipient's access point |
| Error | sending failed, or ePošťák reports the document *rejected*, *send failed*, *delivery failed* or *validation failed*; *Error Details* holds "ePošťák status: …" with ePošťák's reason |

*Sent* becomes *Done* or *Error* through the scheduled action **ePošťák:
Query Outbound Delivery Status**, every 30 minutes, for up to 500 sent
messages per run. It needs **Track Delivery Status** on (default) and a key
allowed to read documents (scope `documents:read`). If ePošťák refuses the
status query, tracking is skipped for that run and the messages simply stay
*Sent* — so a message that stays *Sent* for a long time means "accepted, no
delivery confirmation yet", not "delivered".

Delivery to the recipient's access point is not the customer's acceptance.
Whether the customer accepts, disputes or pays the invoice arrives, if the
customer's system sends it, as an
[Invoice Response](module:edi_base_peppol#responses).

## When sending fails {#errors}

| What you see | Cause | What to do |
|---|---|---|
| *Error*, text about credentials, Peppol address, Firm ID or a missing element | a configuration or addressing problem found before sending | fix the setting or the contact named in the message, then **Send** |
| *Error*, an ePošťák code (e.g. validation) | ePošťák refused the document; it will fail the same way again | correct the invoice or the contact |
| *Queued*, blocking level *Warning*, with a reason in *Error Details* | a temporary problem: timeout, rate limit, ePošťák or its login unavailable | nothing — the next run of the send action tries again |

A temporary failure is **retried automatically** on every run of *EDI: send
queued messages (no job runner)*, every 2 minutes, until ePošťák accepts the
document or refuses it for good; there is no limit on the number of
attempts, and a *Retry-After* wait requested by ePošťák is not observed
beyond that interval. A permanent failure moves the message to *Error*,
where it stays until someone sends it again. One failed document does not
stop or undo the others sent in the same run. ePošťák's correlation ID, if
it gave one, is in brackets at the end of the error — quote it to ePošťák
support.

To retry, press **Send** on the EDI message (or *Actions → Send (queue
dispatch)* for several). It sends the **same file** again, and ePošťák
recognises it by its idempotency key (*Transmission UUID*, derived from the
file's content): if the earlier attempt had in fact got through before the
error, the repeat is collapsed instead of delivered twice. **Send via
Peppol** on the invoice generates the file anew; if anything in it changed,
it is a new document to ePošťák.

## Receiving {#receiving}

The scheduled action **ePošťák: Poll Inbound Documents** runs every
30 minutes. For every company with ePošťák credentials of its own it asks,
as that company, for the documents waiting for that company's Peppol address
(companies sharing one integrator key are still asked one Peppol address at a
time), 20 per page and up to 5 pages per run (*Documents per Poll Page*,
*Max Pages per Poll*), and runs again at once if more are waiting. Each
document is stored and processed as described in
[receiving e-invoices](module:edi_base_peppol#receiving), and only then
acknowledged to ePošťák, which removes it from the queue there. A document
whose content cannot be fetched is not acknowledged and is tried again next
time. The acknowledgement is between Odoo and ePošťák only; the sender
receives nothing from it.

Receiving fails silently unless you look, so the connector reports on
itself:

- **Last inbound poll** in Settings shows, for the company you are working
  in, "OK at … — N document(s) fetched", "FAILED at … — reason (last success:
  …)" or "Never polled".
- **Poll inbound now** runs that company's collection immediately and says
  what happened.
- After **Warn after N failed polls** consecutive failures (default 3; 0
  turns it off) a To-Do "Incoming ePošťák documents are not arriving" is put
  on your company's contact for the first EDI Manager (else an EDI User, else
  the administrator). It is closed automatically once collection works again.

## Checking a customer's Peppol address {#reachability}

On a contact with a Peppol address, **Check Peppol reachability** (next to
the endpoint, for EDI users) asks the Peppol directory through ePošťák
whether that address can receive Peppol BIS Billing 3.0 invoices and credit
notes:

| Answer | Meaning |
|---|---|
| Reachable on Peppol | registered, and accepts BIS 3.0 invoices and credit notes |
| Registered, but not for BIS3 billing | exists on the network, but sending invoices to it will be refused |
| Not registered on Peppol | the directory does not know it — the customer is not on Peppol yet, or the scheme or number is wrong (a Slovak DIČ is scheme 0245, an IČ DPH 9950) |

ePošťák's own reason is added when it gives one, and a note if the
participant is reported as not network-ready.

## Transfer tuning {#tuning}

Block *Transfer Tuning*; the defaults suit most databases.

| Setting | Default | Purpose |
|---|---|---|
| OAuth Scope | `documents:send documents:read documents:write` | rights requested at login; `documents:send` alone can send but not collect or track delivery |
| Track Delivery Status | on | query delivery status of sent documents |
| Warn after N failed polls | 3 | when to raise the To-Do about failed collection |
| Documents per Poll Page | 20 | 1 to 100 |
| Max Pages per Poll | 5 | pages per run before the collection re-schedules itself |
| Request Timeout (s) | 60 | per call to ePošťák |

## Limitations {#limitations}

- **One environment per database.** Sandbox or production applies to every
  company; the credentials and the Firm ID are each company's own. A company
  that allows e-invoicing without credentials of its own neither sends (its
  documents end in *Error*, naming the company) nor collects.
- A message keeps the environment it was created in while it is being
  sent; pressing *Send via Peppol* again generates it anew in the
  environment active **now** (see
  [sending](module:edi_base_peppol#sending)).
- A send that fails permanently is not retried automatically. A temporary
  failure is retried after ePošťák's Retry-After or a growing pause, at most
  five times (see [sending](module:edi_base#sending)).
- *Configured key* reads "No secret configured yet" in broker mode, which is
  expected there.
- Whether ePošťák is a certified provider of the delivery service under
  § 76a of the VAT Act is a question for ePošťák; this module does not check
  it.
