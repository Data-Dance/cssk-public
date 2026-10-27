---
title: Point of Sale — SK Virtual Cash Register (VRP2)
summary: Registers every paid Point of Sale order in Finančná správa's virtual cash register (VRP 2) — sales itemized with their VAT rates, returns against the original receipt, invoiced orders as invoice payments — and prints the fiscal data on the till's ticket.
verified: 19.0.5.1.1
---

## What it is for {#purpose}

With this module each Point of Sale till in Odoo works as its own **virtual
cash register** (*virtuálna registračná pokladnica*, VRP) of Finančná správa.
When the till syncs a paid order, Odoo issues the receipt in VRP 2 and keeps
its number, identifiers and the official PDF on the order:

- an ordinary sale becomes an **itemized receipt** with each item's VAT rate;
- a refund becomes a **return** (*vrátenie tovaru*) against the original
  receipt — refunding a whole order is VRP's storno of the sale;
- returned deposit packaging is recorded as *vrátené obaly*;
- an order that was invoiced becomes a **receipt for invoice payment**
  (*úhrada faktúry*), as in
  [module:l10n_sk_vrp2_account](module:l10n_sk_vrp2_account).

The ticket printed at the till carries the VRP receipt number, the cash
register code, the receipt identifier, the OKP and the QR code, and the
official PDF is one click away.

The products and categories each till sells must also exist in its VRP
catalogue; the module pushes them there (or pulls them from VRP).

## Legal background {#legal}

The [act on the recording of sales (zákon o evidencii tržieb)](law:sk/2025/384),
in force since 1 January 2026:

- The virtual cash register is one of the three kinds of *pokladnica eKasa*
  ([§ 2 písm. b)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-b)): a service of
  Finančné riaditeľstvo provided exclusively through its mobile applications
  and client web environment
  ([§ 2 písm. e)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-e)).
- A seller must register each *tržba* — a payment received at the point of sale
  in cash or by means replacing cash, card payments and vouchers included
  ([§ 2 písm. u)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-u)) — without
  undue delay after receiving it ([§ 3 ods. 1](law:sk/2025/384#paragraf-3.odsek-1)).
- The receipt must be printed and handed to the buyer immediately; *"iný
  doklad vyhotovený pokladnicou eKasa o prijatí tržby predávajúci nesmie
  kupujúcemu odovzdať"* — [§ 8 ods. 1](law:sk/2025/384#paragraf-8.odsek-1)
  lists its mandatory content.
- When money is returned for returned goods, a complaint, or deposit pallets,
  crates and packaging, the seller must hand over a receipt too; for returned
  deposit packaging without the original receipt's identifier —
  [§ 8 ods. 4](law:sk/2025/384#paragraf-8.odsek-4).
- A receipt for an invoice payment carries the invoice number and no items or
  VAT — [§ 8 ods. 2](law:sk/2025/384#paragraf-8.odsek-2).

**Which document goes to the customer** is a decision for you and your adviser.
Odoo's ticket with the fiscal block reproduces the identifying data of the VRP
receipt but is printed by Odoo; the official receipt is VRP's own PDF, which
the module stores and opens with *VRP2 doklad (PDF)*.

## Setting it up {#setup}

### 1. VAT mapping (once per company) {#tax-mapping}

*Point of Sale → Configuration → Settings*, block **VRP2 - Slovak Virtual Cash
Register**, **VRP2 Tax Mapping**: choose the Odoo sales tax for each VRP rate
you use (*VRP2 Tax 0%*, *5%*, *19%*, *23%*; the *10%* and *20%* slots are for
rates no longer in force). Only sales taxes of the current company are
offered.

The mapping decides which products are pushed to VRP (a product whose tax is
not mapped is not) and which VAT a pulled product gets.

### 2. Payment methods {#payment-methods}

Each POS payment method has a **VRP2 Payment Type**, shown after its journal:
*Hotovosť* (cash), *Platobná karta* (card), *Poukážky* (vouchers), *Stravné
poukážky* (meal vouchers) or *Iné* (other). It defaults from the journal — cash
journal → *Hotovosť*, bank journal → *Platobná karta* — so check vouchers and
other tenders. A method with no type (a customer account) is not a cash
register payment: an order paid with it cannot be registered and ends in
*VRP2 Error*.

### 3. The till {#till}

*Point of Sale → Configuration → Point of Sales*, open the till. Block **VRP2
Fiscal Receipts**:

| Field | What it does |
|---|---|
| Enable VRP2 | This till registers its sales in VRP. |
| Fiscalize Automatically | Issue the receipt as soon as the till syncs a paid order (default). Without it, orders are registered only by hand. |
| Round to 0.05 € | Mirrors *Zaokrúhľovať na 5 centov* in the VRP web application: the cash part of a payment is rounded to 5 cents. |
| Odoo Cash Rounding | Shown when rounding is on; see below. |
| VRP2 Login, VRP2 Password | The login of **this till's** register from the eKasa zone of the Finančná správa portal. |

Then click **Login**. The line below shows the business name, the register's
DKP and the access granted (*Read* / *Write*). **Load Credentials from
Company** copies the company register's login (set up as described in
[module:l10n_sk_vrp2_account](module:l10n_sk_vrp2_account#connection)) into
the till — then invoice payments and this till's sales go to the same register.

Rules the module enforces:

- **One login, one till.** A VRP login is one cash register; it cannot be
  entered on two tills.
- **Odoo's cash rounding must match VRP's.** With *Round to 0.05 €* on, the till
  needs Odoo cash rounding with a 0.05 *Nearest* rounding method that adds a
  rounding line, applied to cash only; switching VRP2 or rounding on fills this
  in from an existing 0.05 rounding method. With *Round to 0.05 €* off, Odoo
  must not round at all. Otherwise saving the till is refused — the cash count
  would never agree with the register's report (18.48 in Odoo, 18.50 in VRP).

### 4. The catalogue {#catalogue}

VRP prints item names from the register's own catalogue, and each item on a
receipt refers to it by its service code. After logging in, on the till:

- **Push to VRP2** sends this till's catalogue to its register: the top-level
  POS categories (only those the till offers, when it has *Restrict
  Categories*), and every product of the till's company that is *available in
  POS*, can be sold, has a mapped tax and is in one of those categories, with
  its price including VAT, barcode, internal reference and category. A product
  created in VRP receives its **VRP2 Service Code**.
  A push **removes only what it created**: a category or product that this
  till's pushes put on the register and that the till no longer offers is
  deleted (category) or deactivated (product) there. Anything else on the
  register — typed into the VRP app, pushed by another till or another
  database — is left alone. Odoo remembers per till which entry stands for
  which category or product, so two tills each keep their own codes.
- **Pull from VRP2** does the opposite: it creates or updates POS categories and
  products in Odoo from the register's catalogue (name, price converted to
  excluding VAT, VAT, barcode, internal reference), as service products
  available in POS.

On the product form (tab *Point of Sale*, group *VRP2*):

| Field | Meaning |
|---|---|
| VRP2 Service Code, Synced to VRP2 | Set by the first push. Each till sells under the code its own register gave the product; a product with no code on that till cannot be sold there. |
| VRP2 Returnable Packaging | A deposit-bearing package (*zálohovaný obal*); taking it back is recorded as *vrátené obaly*. |
| VRP2 Favourite | Show among the favourites in VRP. |
| VRP2 Special Regulation | The legal wording for 0 % items (exempt, reverse charge, travel agencies, works of art, used goods, collectors' items). See [Limitations](#limitations). |
| VRP2 Note | Internal note for VRP, not printed. |

A top-level POS category has a **VRP2 Short Name** for VRP's tabs; if empty,
the first two letters of the name are used.

Push again whenever you rename a product, change its price or tax, or add one.

## At the till {#usage}

Sell as usual. When the order is paid and synced:

1. Odoo issues the VRP receipt (when *Fiscalize Automatically* is on).
2. Before the ticket prints, the till fetches the result and prints the fiscal
   block: **POKLADNIČNÝ DOKLAD č. 0019**, *Kód pokladnice*, *ID dokladu*, *OKP*
   and the QR code of the receipt identifier.
3. **VRP2 doklad (PDF)** on the receipt screen opens VRP's official PDF.

If VRP refuses or cannot be reached, **the sale is never blocked**: the cashier
gets a warning *The VRP2 receipt was NOT issued*, the ticket says *Doklad
nebol zaevidovaný vo VRP2* instead of the fiscal block, and the order is marked
*VRP2 Error*. The till does not retry by itself, because after a timeout VRP
may already hold the receipt.

### What is sent {#receipt-content}

| Order | Receipt in VRP |
|---|---|
| Sale | Itemized: each line with its unit price incl. VAT, discount, quantity, VAT rate and service code. |
| Refund of an order registered in VRP | Return items that refer to the original receipt and carry the item name exactly as VRP printed it; the money paid out as an expense. |
| Returned deposit packaging with no sale to refer to | *Vrátené obaly* item, keeping its service code. |
| Invoiced order | Receipt for invoice payment with the invoice number and the payments, no items. |

Payments are reported by the payment method's *VRP2 Payment Type*. Only the
**cash** part is rounded to 5 cents; a receipt that returns money is never
rounded. VRP computes the receipt total itself; if it differs from Odoo's by
tax rounding (at most 5 cents) the difference is absorbed by the largest
non-cash payment.

An order is refused, and ends in *VRP2 Error*, when:

- a product has no VRP2 service code (push the catalogue first);
- a line has more than one tax, a non-percentage tax, or a VAT rate VRP does
  not know;
- goods are returned without referring to the order they were sold on (refund
  from that order in the POS), or that order has no VRP receipt yet;
- goods are returned against an **invoiced** order (cancel its invoice-payment
  receipt instead), or the order is an invoiced refund;
- a payment method has no VRP2 payment type;
- non-cash payments exceed the total while cash was also paid.

## Orders in the back office {#orders}

*Point of Sale → Orders → Orders*: the order form has a **VRP2 Fiscalization**
group with the *VRP2 Status* (*Not Fiscalized*, *Fiscalized*, *Error*),
receipt number, receipt UUID (what the QR code encodes), date, OKP and the
error message. **Print VRP2 Receipt** downloads the official PDF.

**Fiscalize in VRP2** (POS managers) registers a paid order that is not yet
registered — after an error, or when automatic registration is off. From the
order list the same action handles many orders; each failure is recorded on its
order without undoing the others, and a notification tells you how many were
registered, failed and skipped. The filters **VRP2 Error** and **Not
Fiscalized in VRP2** find the orders that need attention, and *VRP2 Status*
and *VRP2 Receipt Number* can be shown as list columns.

**Before you re-send an order in error after a timeout, check the register's
receipt list in the VRP portal**: VRP may already hold that receipt, and
sending it again registers the sale twice.

## Limitations {#limitations}

- **VRP2 Special Regulation is sent only for a product whose VRP tax is 0 %**,
  as VRP's own app does; on any other rate it is ignored. For an exempt item
  the receipt must state the exemption
  ([§ 8 ods. 1 písm. n)](law:sk/2025/384#paragraf-8.odsek-1.pismeno-n)), so
  set it on every 0 % product before pushing the catalogue.
- An entry pulled from the register, or pushed before version 19.0.5.1.0, is
  updated by a push but never deleted or deactivated by it; remove it in the
  VRP app when it is no longer sold.
- Products with a zero price are pushed without a price. Pulled products are
  created as services; the catalogue list is not paged, so a very large VRP
  catalogue may be pulled incompletely (a warning goes to the server log).
- Vouchers exchanged for goods, deducted advances, foreign currency and sales
  on behalf of another seller are not mapped.
- An order sold while the till is offline is printed without the fiscal block
  and registered when the till syncs.
- Upgrading does not re-check existing tills: one with VRP2 on and mismatched
  Odoo cash rounding keeps working until its settings are next saved.
- The module drives the same interface the VRP web application uses, which
  Finančná správa does not publish for third parties. A change on their side
  can stop it working until the module is updated.
