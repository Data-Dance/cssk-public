---
title: Slovak eKasa Receipt Lookup
summary: Reads the QR code on a Slovak cash-register receipt (bloček) and fetches the receipt the seller registered in eKasa — items, VAT rates and the per-rate VAT recap — from Finančná správa's document-verification service.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

Every receipt printed by a Slovak cash register (*pokladnica eKasa*) carries a
QR code. Behind it, Finančná správa holds the receipt exactly as the seller
registered it: every item with its quantity and VAT rate, the VAT recap per
rate, and the seller's identification.

This module is a *provider* for
[module:l10n_cssk_receipt_capture](module:l10n_cssk_receipt_capture), the
receipt-capture framework. When a captured receipt has a Slovak eKasa QR code,
it asks the state's verification service for that receipt and fills the
captured receipt with the **seller's own registered figures** instead of a
reading of the photograph. Posting the receipt as a bill or expense is then
the framework's job.

Two kinds of QR code are understood:

| Receipt | What the QR code holds |
|---|---|
| On-line (the normal case) | only the receipt identifier: `O-` and 32 hexadecimal characters, or `V-` for a receipt from the virtual cash register (VRP) |
| Off-line (the till could not reach eKasa in time) | `OKP:cash-register code:date-time:number:total`, which the service accepts as a lookup key |

An off-line receipt receives its real identifier once the till has sent it to
eKasa; that identifier is what the module stores, so the same purchase cannot
be captured twice.

## Legal background {#legal}

Since 1 January 2026 receipts are governed by the
[act on the recording of sales (zákon o evidencii tržieb)](law:sk/2025/384),
which replaced the former act No. 289/2008 Z. z. on electronic cash registers
([§ 21](law:sk/2025/384#paragraf-21)).

- **The service.** [§ 2 písm. ai)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-ai)
  defines the *služba na overovanie dokladov* (document-verification service)
  as Finančné riaditeľstvo's service that, through the QR code on a receipt,
  lets one verify the receipt's data stored in the eKasa system and
  *"sprístupňovať a získavať tieto údaje"* (make those data available and
  obtain them).
- **Who may use it.** An *overovateľ* (verifier) is a person entitled to use the
  service after meeting the conditions of § 18 ods. 11 —
  [§ 2 písm. aj)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-aj).
- **The seller must tolerate it.**
  [§ 18 ods. 3](law:sk/2025/384#paragraf-18.odsek-3): the seller is obliged to
  tolerate (*"je povinný strpieť"*) Finančné riaditeľstvo making the stored
  data available through the service.
- **The verifier's duties.** Under
  [§ 18 ods. 11](law:sk/2025/384#paragraf-18.odsek-11) a verifier must, **before
  first using the service, notify Finančné riaditeľstvo of the IP address** it
  will access the service from, must send Finančné riaditeľstvo truthful results
  of its verifications, and must follow the conditions of use that Finančné
  riaditeľstvo determines and publishes on its website.

The module cannot check that the notification has been made, so it asks you to
declare it and refuses every lookup until you do (see [Setting it up](#setup)).
When this version was written, the conditions of use had not been published;
until they are, the notification means writing to Finančné riaditeľstvo
yourself.

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Slovak eKasa Receipt Lookup**
(below *Fiscal Receipt Capture*):

| Setting | What it does |
|---|---|
| Enable eKasa Lookup | Switches the lookup on for the current company. Off by default. |
| IP Address Notified (§ 18/11) | Tick it only once Finančné riaditeľstvo has been notified of the public IP address your Odoo server calls from. Until it is ticked, every lookup is refused with an explanation. |
| Notified IP Address, Notified On | The address you declared and the date. A record for you; the module does not compare it with the address actually in use. |
| Hourly Lookup Budget | Maximum lookups per clock hour, default 60. Zero means no lookups at all. |
| Lookup Timeout (s) | How long to wait for the service, default 30 seconds. |

Why the budget: the service allows roughly 60 lookups per clock hour
(hh:00–hh:59) per IP address and blocks an address that exceeds it. The module
counts its own calls per company and stops before the limit. The real limit is
per **address**: if several companies, or several databases, call from one
address, lower their budgets so that together they stay under it.

On installation, companies that already exist receive the default budget of 60.

The provider itself — *Slovak eKasa (QR lookup)*, limited to Slovakia — is
created by the module and is listed with the other capture providers.

## Capturing a receipt {#usage}

Use the receipt-capture framework as usual (*Accounting → Vendors → Fiscal
Receipts*): scan the QR code with the camera, type it in, or upload a photo.

- **From a photo**, the QR code is decoded on the server. If the receipt shows
  more than one code (a loyalty-app code above the fiscal one, for instance),
  only a code this module can parse is used. The scan screen tells you which
  code to scan: the one directly above *OVERTE DOKLAD POMOCOU QR KÓDU*.
- **If the code will not decode** but another reader (such as the AI reader)
  has read the identifiers printed beside it — the `UID` of an on-line receipt,
  or the OKP, cash-register code, date and time, number and total of an off-line
  one — the module rebuilds the lookup key from them and tries it. A printed
  `0-` is read as `O-` (they look alike in receipt fonts), and a receipt number
  printed as `202609/5` is tried as `5` first. A misread key finds nothing
  rather than a wrong receipt, and the registered total must match the
  photograph's total or the result is rejected.
- **What is filled in:** issue date (Bratislava time, wherever the person
  capturing it is), total, seller name, DIČ, IČ DPH, IČO and whether the seller
  is a VAT payer, the premises as a note, every item, and the VAT recap per
  rate. Two fields are added to the receipt form: **OKP** (the seller's
  verification code) and **Paragón** (a substitute receipt written out while
  the till was out of service).

How the figures are read matters for posting, so it is worth knowing:

- The VAT recap comes from the receipt's own per-rate summary. If the service
  returns none, it is computed from the items' rates and a warning is posted on
  the receipt.
- An item's price is the **VAT-inclusive line total**, not a unit price; the
  framework posts the line total, so a fuel receipt for 31.17 l at 57.85 € posts
  57.85 €.
- The seller's IČ DPH is stored as the service returns it, never derived from
  the DIČ — a member of a VAT group files under the group's number.

When the lookup fails, the receipt says why:

| Result | What happens |
|---|---|
| Switched off, IP not declared, budget spent | The eKasa provider steps aside and the next provider (for example the AI reader) may read the receipt instead. |
| Network failure | The receipt is left untouched and retried automatically later. |
| Not registered | Finančná správa holds no receipt for this code. Either the code was misread or the seller never registered the sale — which may be worth reporting. |
| Refused by the service | Usually the service's firewall rather than the receipt; not retried automatically. |

## The verification log {#log}

Every call to the service is recorded: *Accounting → Vendors → Fiscal Receipts
→ eKasa Verification Log*, and from a receipt through its **Lookups** button.
Each row shows when the call was made, the identifier or key asked about, the
receipt and the outcome (*Receipt found*, *Not registered*, *Refused by the
service*, *Network or transport error*). Refused and failed calls count against
the hourly budget too.

The log is your own record of what was verified. Users with invoicing rights
can read it; only accounting managers can edit or delete rows.

## Limitations {#limitations}

- **The duty to send verification results is not implemented.** § 18 ods. 11
  requires a verifier to send Finančné riaditeľstvo truthful results of its
  verifications; the module only keeps them in its local log. How results are
  to be sent depends on the conditions Finančné riaditeľstvo has yet to publish.
- The IP notification is a declaration you make. The module does not check it,
  nor that the declared address is the one your server uses.
- The hourly budget is counted per company. Companies or databases sharing one
  outgoing address share one real limit, which the module cannot see.
- The service has no published interface for third parties yet; the module
  calls it the way the public verification page does. If Finančná správa
  changes it, lookups fail until the module is updated.
- Only Slovak eKasa receipts. Czech and foreign receipts, and Slovak receipts
  whose code cannot be read at all, need another provider.
- The screens of this module are in English; there is no Slovak translation
  yet.
