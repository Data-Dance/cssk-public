---
title: Czech EET 2.0 (Electronic Registration of Sales)
summary: Registers contact payments received outside the till — cash, card or QR paid at the counter — with the Czech EET 2.0 system, keeps every data message with its confirmation code, retries until the tax authority has accepted it, and renews the cash-register certificate on its own.
verified: 19.0.1.3.0
---

## What it is for {#purpose}

From **1 January 2027** every Czech business that takes **contact payments** —
money received in personal contact with the customer or in its premises,
whether cash, a card on the terminal or a QR code scanned at the counter — must
report each such sale to the Financial Administration (*Finanční správa*) at the
moment it happens. This is **EET 2.0**, the second edition of the electronic
registration of sales.

This module is the Odoo side of it. It holds the **cash-register certificate**
(*pokladní certifikát*) issued by the Financial Administration, builds and signs
the data message for each sale, sends it to the EET 2.0 gateway and stores the
**confirmation code** (*POK, potvrzovací kód*) that comes back. Sales made at a
Point of Sale till are registered by
[module:l10n_cz_eet2_pos](module:l10n_cz_eet2_pos); this module registers the
contact payments booked in accounting — a customer paying an invoice in cash at
the office, a card payment taken at the counter, a QR code scanned in the shop.

## Legal background {#legal}

The [act on the registration of sales (zákon o evidenci tržeb)](law:cz/2026/180),
No. 180/2026 Sb., in force from 1 January 2027. Certificates and evidence units
can be set up in the tax portal from 1 November 2026, and the production
gateway accepts messages from that date in a transitional regime.

- A **registered sale** is a payment received in personal contact with the
  business, or in its premises or vehicle in connection with the goods or
  service (§ 5 and § 6). The payment method is irrelevant: cash, card, bank
  transfer, QR code, vouchers, tokens or crypto-assets all count when they
  happen that way. The same QR code paid from home is **not** a contact payment.
- The sale must be registered **no later than when it takes place**. For a card
  or QR payment that moment is when the customer **issues the payment order**,
  not when the money arrives (§ 16 odst. 2).
- The message carries only the taxpayer's EIČ, the evidence unit, the cash
  register, a sequence number, the date and time, and the **total amount in
  CZK** (§ 17). No items, no VAT breakdown, no customer data, no payment method.
- The business sets a **response time limit** of at least 2 seconds (§ 19).
  When the gateway does not answer in time, the sale still goes through and the
  message must be sent as soon as the cause has passed, **at the latest within
  48 hours**; the duty does not lapse after that (§ 20).
- A refund or correction is registered as a **negative sale** (§ 8).
- Top-ups and redemptions of gift cards, e-wallets and similar means usable
  only in a limited network are registered in two dedicated items (§ 17
  odst. 2); see [module:l10n_cz_eet2_pos_loyalty](module:l10n_cz_eet2_pos_loyalty).
- The act requires **no receipt**. Printing the POK on a receipt is voluntary.
- The EIČ is the taxpayer's DIČ (§ 18). Certificates are valid for one year.

Whether a given payment is a contact payment is a judgement for you and your
adviser; the module records what you flag, it does not decide for you.

## Setting it up {#setup}

### 1. In the tax portal {#portal}

In **MOJE daně → DIS+**, register your **evidence units** (*evidenční
jednotky*: each shop, vehicle or "outside premises" activity). Each receives a
number, two to nine digits ending in 1 to 4. Then generate one or more
**cash-register certificates** and download each as a `.p12` file with its
password.

### 2. Company settings {#settings}

*Accounting → Configuration → Settings*, block **Czech EET 2.0**, tick
**Enable EET 2.0**:

| Setting | What it does |
|---|---|
| EET 2.0 Environment | *Playground* for testing, *Production* for real sales. A playground confirmation code ends in `-ff` and fulfils no legal duty. |
| EET 2.0 Taxpayer EIC | Your EIČ, `CZ` plus 8 to 10 digits. Pre-filled from the company's VAT number when that has the right shape. |
| EET 2.0 Default Unit ID | The evidence unit number from DIS+ used when a journal or till names none. |
| EET 2.0 Certificate | The certificate messages are signed with; see below. |
| EET 2.0 Response Time Limit (s) | How long a till waits for the gateway before letting the sale through, at least 2 seconds, 5 by default. |
| EET 2.0 Warn After Attempts | After this many failed attempts a warning is logged. Sending itself never stops. |
| EET 2.0 Renew Certificate (days before expiry) | How many days before a certificate expires its renewal starts automatically; 0 switches renewal off. |

### 3. Certificates {#certificates}

*EET 2.0 → Configuration → Certificates*: create a record per certificate, pick
its environment, upload the `.p12` and enter its password. The EIČ in the
certificate and its validity are read from the file. **Test certificate** sends
a message in *verification mode*: the gateway checks everything and answers
without recording a sale, so you can prove the certificate and the connection
on the production gateway without registering anything. A playground
certificate can only be used against the playground, and the other way round.

### 4. Which payments are registered {#scope}

On each bank or cash journal, tab *Advanced Settings*, block **Czech EET 2.0**:

| Field | What it does |
|---|---|
| EET 2.0 Contact Payments | New customer payments in this journal are proposed as contact payments. |
| EET 2.0 PoS ID (id_pokl) | The cash register name sent for this journal, up to 20 characters; the journal code when empty. |
| EET 2.0 Unit ID (id_jednotky) | The evidence unit for this journal; the company default when empty. |

Every customer payment then carries its own **EET 2.0 Contact Payment** flag,
proposed from the journal and editable until the sale is accepted. This is
where you tell the two cases apart that the law treats differently and that
land on the same bank account: a QR code scanned at the counter (tick) and the
same code paid from home (untick). Payments received from suppliers are never
registered, and neither are the payments Odoo books when a Point of Sale
session closes — the till has already registered those orders.

## How a sale is registered {#flow}

When a flagged payment is posted, Odoo queues a **message** and the scheduled
job sends it within about two minutes. *EET 2.0 → Messages* lists them all, and
each payment shows its **EET 2.0 Status**, its **EET 2.0 POK** and an *EET 2.0*
button opening its messages.

| Status | Meaning |
|---|---|
| To Send, Retry Scheduled | Waiting for the next attempt. |
| Accepted | The gateway issued a POK. Done. |
| Verified | A verification-mode test succeeded; no sale was recorded. |
| Rejected | The gateway refused the message for good (invalid signature, wrong EIČ, schema error). Fix the cause and press **Requeue**. |
| Error | The message could not be built, typically because no valid certificate was available. It is retried hourly and re-queued automatically when a certificate is uploaded or selected. |

What happens when the gateway is unreachable follows the act: attempts are
repeated with growing intervals until 48 hours after the sale, then **every
hour for as long as it takes**. A message that crosses the 48-hour line is
flagged **Past 48 h** and an activity is raised for an EET 2.0 manager, so the
backlog never ages in silence. Every attempt is a new message with a new
identifier, as the Financial Administration's methodology requires; the earlier
identifiers stay on the record under *Previous attempts*, and the request and
response XML are kept for support.

**Refunds and reversals.** Resetting a posted payment to draft or cancelling it
registers a **negative sale** of the same amount, dated at the reversal, in the
same cash register and sequence. Posting the payment again registers a new
sale. A customer refund paid out from a flagged journal is registered as a
negative sale as well.

**Amounts.** The message is always in CZK. A payment in another currency is
converted at the company's rate for the day of the sale, and the original
amount and currency are kept on the message.

## Certificate renewal {#renewal}

A cash-register certificate lives one year. The module renews it through the
Financial Administration's **CA EET 2.0** service without a visit to the
portal: the set number of days before expiry it asks for a follow-up
certificate, downloads it as a **new certificate record**, sends a
verification-mode message with it, and only when the gateway accepts does it
switch the company to the new certificate, archive the old one and confirm the
download to the authority. **Renew with CA EET** on the certificate runs the
same cycle by hand, and the **Renewal** status shows where it stands. When the
verification fails or the authority rejects the request, the old certificate
stays in use and an EET 2.0 manager gets an activity. A separate daily check
raises warnings 30, 14 and 7 days before expiry.

## Limitations {#limitations}

- The address of the certificate authority for **playground** certificates is
  our reading of the published specification, which lists three environments
  without saying which non-production one serves the playground. Production
  renewal is unaffected. Both addresses are system parameters an administrator
  can change.
- The module cannot tell a contact payment from a remote one; the journal
  default and the payment flag are your decision.
- A **copy of a production database** must not register sales. Odoo's database
  neutralisation (used by Odoo.sh staging builds and *duplicate with
  neutralise*) switches EET 2.0 off on every company of the copy; certificates
  and settings stay, so the copy can be switched back on against the playground.
- The *EET OFF* regime for the smallest sole traders is a choice made with the
  tax office, not a setting here; a company in it simply leaves EET 2.0 off.
- Registration on behalf of another taxpayer (*pověření*, *zastoupení*) is
  carried in the message but has no configuration screen yet.
