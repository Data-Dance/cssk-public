---
title: SK Virtual Cash Register (VRP2) — Invoice Payments
summary: Registers the cash or card payment of a customer invoice in Finančná správa's virtual cash register (VRP 2) as a receipt for invoice payment, keeps the official receipt in Odoo, and cancels it by storno when needed.
verified: 19.0.2.4.0
---

## What it is for {#purpose}

A Slovak business that takes payment for an issued invoice in cash or by card
at its premises has to register that payment in a cash register as a
*pokladničný doklad — úhrada faktúry* (receipt for invoice payment). Many
small businesses use the **virtual cash register** (*virtuálna registračná
pokladnica*, VRP) that Finančná správa provides free of charge instead of a
hardware till.

This module connects Odoo to VRP 2 so that you do not have to retype each
invoice payment into the VRP web application:

- **Fiscalize in VRP2** on a posted customer invoice issues the receipt and
  downloads the official PDF;
- the same action on the invoice list does it for many invoices at once and
  returns one PDF;
- optionally, the *Pay* wizard issues the receipt for the payment it registers;
- **Storno (VRP2)** cancels an issued receipt;
- every receipt is kept in Odoo with its number, identifiers, the official PDF
  and the data exchanged with VRP.

It only registers the payment with Finančná správa. Recording the payment in
Odoo is your normal payment flow, and nothing about the invoice's accounting
changes.

The connection itself (login, the company's register) is provided by
[module:l10n_sk_vrp2_base](module:l10n_sk_vrp2_base), installed automatically
with this module and described [below](#connection). Sales at a till are
handled by [module:pos_vrp2](module:pos_vrp2).

## Legal background {#legal}

The [act on the recording of sales (zákon o evidencii tržieb)](law:sk/2025/384),
in force since 1 January 2026:

- **The virtual cash register** is a service established by Finančné
  riaditeľstvo, provided exclusively through its mobile applications and its
  client web environment —
  [§ 2 písm. e)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-e). It is one of the
  three kinds of *pokladnica eKasa*
  ([§ 2 písm. b)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-b)).
- **What must be registered.** A *tržba* (sale proceeds) is a payment received
  at the point of sale in cash or by other means replacing cash, including
  card payments; a payment received as an advance or a balance counts too —
  [§ 2 písm. u)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-u). The seller must
  register it without undue delay after receiving it —
  [§ 3 ods. 1](law:sk/2025/384#paragraf-3.odsek-1).
- **A receipt for invoice payment** carries the invoice number and must
  **not** carry the item lines, VAT base, rates and VAT amounts —
  [§ 8 ods. 2](law:sk/2025/384#paragraf-8.odsek-2). The VAT is on the invoice.
  That is why the receipts issued here have a single line *Úhrada faktúry:
  &lt;invoice number&gt;* and no VAT breakdown.
- **Cash is rounded to 5 cents.** The receipt carries the rounding of the
  price — [§ 8 ods. 1 písm. p)](law:sk/2025/384#paragraf-8.odsek-1.pismeno-p)
  — which the act on prices (zákon č. 18/1996 Z. z., § 3 ods. 4) prescribes
  for a price paid in cash only: a remainder under 2.5 cents down, from
  2.5 cents up, and a price of 1 or 2 cents up to 5 cents. A card payment is
  never rounded.
- **Handing it over.** The seller must hand the buyer the receipt printed by the
  cash register immediately; it may instead be sent electronically if the buyer
  agrees and asks before it is printed —
  [§ 8 ods. 1](law:sk/2025/384#paragraf-8.odsek-1). The PDF this module
  downloads is VRP's own receipt; print it or, with the buyer's consent, use
  *Email Receipt*.

Whether a particular payment is a *tržba* (for instance a bank transfer is not
one) is for you and your accountant to decide; the module registers whatever
you tell it to.

## Connecting the company's register {#connection}

One VRP 2 login belongs to exactly one cash register (identified by its *kód
pokladnice*, DKP). Invoice payments are registered on the **company's**
register, set up in *Accounting → Configuration → Settings*, block **VRP2 - Slovak
Virtual Cash Register**:

1. **VRP2 Connection** — enter the register's *VRP2 Login* and *VRP2
   Password* from the eKasa zone of the Finančná
   správa portal, and click **Login**. The *VRP2 Status* badge
   changes to *Connected*.
2. **VRP2 Cash Register Info** then shows what VRP reports for the register:
   its DKP, business name, DIČ, IČO and IČ DPH. Check them — they are what the
   receipts will carry.
3. **Round to 0.05 €** — mirrors the setting *Zaokrúhľovať na 5 centov*
   in the VRP web application. When on, a **cash** payment is rounded to the nearest 5 cents on the receipt and the difference is
   reported as rounding. VRP does not tell Odoo how you set it in the web
   application, so set it here to match. On by default.
4. **Fiscalize invoice payments** — offers the
   VRP choice in the *Pay* wizard (see [below](#on-payment)). Below it,
   **VRP2 cash rounding** names the cash rounding (*Accounting → Configuration
   → Cash Roundings*) whose profit and loss accounts receive the 5-cent
   difference of a rounded cash payment.

The session renews itself when it expires; **Logout** ends it. The password
and the session token are visible to administrators only. The login
notification also shows the access VRP grants it (*VRP2 Role*: *Read* or
*Write*); issuing receipts needs a login with write access.

Tills in the Point of Sale have their **own** registers and logins, set on each
till; see [module:pos_vrp2](module:pos_vrp2#setup).

## Registering an invoice payment {#usage}

### From the invoice {#from-invoice}

On a **posted customer invoice** that has no active VRP receipt, click
**Fiscalize in VRP2**, choose how the customer paid — **Cash** or **Card**,
nothing is preselected — and click **Fiscalize**. The module issues the
receipt and downloads the official PDF.

- The receipt is for the **full invoice total**. For a partial payment, use
  [the Pay wizard](#on-payment).
- This does not register a payment in Odoo. Register it as usual — for a
  rounded cash payment, at the rounded amount, writing off the difference.

### Several invoices at once {#mass}

In *Accounting → Customers → Invoices*, select the invoices, then *Actions →
Fiscalize in VRP2*, then choose *Cash* or *Card* for all of them. Credit notes
in the selection are skipped. Each invoice gets its own receipt (full total)
and you get one PDF with all of them.

All the invoices are checked before anything is sent: if one is not posted,
is not a customer invoice or already has a receipt, nothing is sent at all.
If VRP refuses one invoice after others have already been registered, the
registered ones are kept and the failure is recorded on that invoice (a
receipt in state *Error* and a message in the chatter), so you can retry it.

### When registering the payment {#on-payment}

With **Fiscalize invoice payments** on and the company logged in, the *Pay*
wizard on customer invoices shows two more fields after *Memo*:

| Field | Meaning |
|---|---|
| Fiscalize in VRP2 | Issue a receipt for the payment being registered. Ticked by default. |
| VRP2 Payment Type | *Cash* or *Card*. Only cash is rounded to 5 cents. |

The receipt is for the **payment amount**, so a partial payment registers the
part paid. One receipt per invoice: with several invoices, untick *Group
Payments*, otherwise the wizard refuses.

A **cash** payment with *Round to 0.05 €* on is booked at the amount the
customer actually hands over:

- Paying the whole invoice of 18.48 in cash, the payment is registered as
  18.50 and the 0.02 is written off to the profit account of the *VRP2 cash
  rounding* (to its loss account when rounding down). The receipt shows 18.48
  as the price, 0.02 as rounding and 18.50 as paid. Without a VRP2 cash
  rounding set, the wizard refuses before anything is sent.
- A partial cash payment must already be a multiple of 0.05 €; otherwise the
  wizard refuses.
- Several invoices at once in cash are accepted only when none of them needs
  rounding; otherwise pay them one by one. If the first receipt
fails, nothing is saved — neither payment nor receipt. If a later one fails,
the payments are kept, the failure is recorded on its invoice, and you issue
that receipt again from the invoice.

## Cancelling a receipt (storno) {#storno}

**Storno (VRP2)** on an invoice with an active receipt issues a VRP storno: a
new receipt with one negative correction line referring to the original and
paid out as an expense from the register. The storno reverses exactly the
amount the original receipt registered, including any 5-cent rounding. The
original receipt is then marked *Cancelled* and the invoice can be registered
again.

A storno touches neither the invoice nor any payment in Odoo. A credit note
cannot be registered as an invoice payment; cancel the original receipt
instead.

## The receipts {#receipts}

*Accounting → Customers → VRP2 Receipts* lists every receipt, and the invoice
shows them through its **VRP2 Receipts** button. A hidden column *VRP2
Fiscalized* can be shown in the invoice list.

On a receipt:

- **Receipt Type**: *Invoice Payment* or *Storno*; status: *Confirmed*,
  *Error* or *Cancelled* (stornoed).
- **Receipt Number**, **Receipt UUID** (VRP's receipt identifier, `V-…` — the
  value the QR code on the official receipt encodes), **OKP** and
  *Fiscalized On*.
- **Print Official Receipt** downloads VRP's PDF; **Email Receipt**
  asks VRP to email the receipt to the customer's address.
- The data sent and received are kept on a technical tab for audit.

The report *VRP2 Receipt* prints an Odoo summary (*Pokladničný doklad — úhrada
faktúry*) with the register's identification and a QR code of the receipt
identifier. The document to hand over is VRP's own PDF.

## Limitations {#limitations}

- Fiscalizing from the invoice or the list always registers the **full
  total**; the payment itself, and the write-off of any cash rounding, are
  yours to register.
- The *Fiscalize in VRP2* button is shown on any posted customer invoice,
  even when the company is not connected to VRP; the error appears only when
  you click it.
- Only customer invoices. Down payments, vouchers, foreign-currency payments
  and deposits/withdrawals of cash are not handled.
- After a timeout, VRP may already hold a receipt that Odoo recorded as failed.
  Check the register's receipt list in the VRP portal before issuing it again.
- The module drives the same interface the VRP web application uses, which
  Finančná správa does not publish for third parties. A change on their side
  can stop it working until the module is updated.
