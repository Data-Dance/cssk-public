---
title: Advance Invoices (Sales)
summary: Advance (proforma) invoices as their own documents, a tax document for every payment received on them, and the deduction of the advance on the final invoice.
verified: 19.0.2.8.0
---

## What it is for {#purpose}

In Czech and Slovak practice an advance is handled in three documents:

1. the **advance invoice** (CZ *zálohová faktura*, SK *zálohová* or
   *preddavková faktúra*) — a request for payment, not an accounting or tax
   document, and not posted;
2. the **tax document for the payment received** (CZ *daňový doklad k přijaté
   platbě*, SK *faktúra k prijatej platbe*) — issued once the money has
   arrived, because the VAT falls due on the day of payment;
3. the **final invoice** (CZ *vyúčtovací* / *konečná faktura*, SK *vyúčtovacia
   faktúra*) — the whole supply, from which the advance and the VAT already
   declared on it are deducted, so the VAT is paid only once.

Odoo's own down payments post an invoice for the advance straight away. This
module instead keeps the advance invoice as a separate quotation-like
document, numbered `ADV00001`, `ADV00002`…, which the customer can pay by QR
code, through the customer portal or by bank transfer. Only the payment and
the tax document reach the ledger.

The module is country-neutral. The Czech and Slovak account wiring comes from
the localization add-ons described under [Localization add-ons](#localization).
The supplier side is [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice).

## Legal background {#legal}

**Slovakia** — [zákon o DPH](law:sk/2004/222):

- If a payment is received before the supply, the tax liability on the
  payment arises on the day it is received —
  [§ 19 ods. 4](law:sk/2004/222#paragraf-19.odsek-4).
- A payer must issue an invoice when it receives a payment before the supply
  of goods or services to another taxable person or legal entity —
  [§ 72 ods. 1 písm. f)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-f) and
  [písm. g)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-g) — within
  15 days of receiving the payment **or** by the end of the calendar month in
  which it was received —
  [§ 73 ods. 1 písm. b)](law:sk/2004/222#paragraf-73.odsek-1.pismeno-b).
- The invoice states the date the payment was received if it differs from
  the date of issue —
  [§ 74 ods. 1 písm. d)](law:sk/2004/222#paragraf-74.odsek-1.pismeno-d).

**Czech Republic** — [zákon č. 235/2004 Sb., o dani z přidané hodnoty](law:cz/2004/235):

- § 20a odst. 2: a payment received before the supply creates the obligation
  to declare VAT on the day it is received — unless the supply is not yet
  known with sufficient certainty, which § 20a odst. 3 defines as knowing at
  least the goods or service, the VAT rate and the place of supply.
- § 28 odst. 1 písm. d) requires a tax document on such a payment, and
  § 28 odst. 8 sets the deadline: 15 days from the day the obligation arose.
- § 36 odst. 2: the tax base is the payment received less the VAT.
- § 37a: on the final invoice the base is the difference between the whole
  supply and the advances already taxed. If the difference is negative, the
  rate and exchange rate used on the advances apply.

## Setting it up {#setup}

*Sales → Configuration → Settings*, block **Invoicing**:

| Setting | What it does |
|---|---|
| Advance Tax Documents Journal | The journal the tax documents go to. Installing the module creates a general journal **TDADV** for the company and selects it. |
| Advance Clearing Account | A reconcilable account on which the payment and the tax document meet, e.g. 324001. |
| Received Advance Account (short-term) | Carries the net received advance until the final invoice, e.g. 324000. |
| Received Advance Account (long-term) | The same for advances marked *Long-term Advance*, e.g. 475000. |

Without a localization add-on you fill in the three accounts yourself.

Before the first advance, also check:

- **A bank account on the company** — the advance invoice prints a bank
  account of the company, preferably one in the order's currency, with a payment QR
  code when QR codes are enabled in the invoicing settings.
- **The *Advance* product** — created the first time an advance is made, it
  is the product of every advance line unless you choose *Include the ordered items* (see
  [below](#create)). Its customer taxes decide the VAT of such advances.

### Localization add-ons {#localization}

[module:l10n_cz_sale_order_advance_invoice](module:l10n_cz_sale_order_advance_invoice)
and
[module:l10n_sk_sale_order_advance_invoice](module:l10n_sk_sale_order_advance_invoice)
fill in the settings above for every company with the Czech or Slovak chart
of accounts — at installation, and again whenever the chart is loaded later,
for example for a new company:

| Role | Account | Czech name | Slovak name |
|---|---|---|---|
| Clearing account (created by the add-on, reconcilable) | 324001 | Přijaté zálohy – zúčtování (daňový doklad) | Prijaté preddavky – zúčtovanie (daňový doklad) |
| Received advances, short-term | 324000 | Přijaté provozní zálohy | Prijaté preddavky |
| Received advances, long-term | 475000 | Dlouhodobé přijaté zálohy | Dlhodobé prijaté preddavky |
| Journal TDADV | — | Daňové doklady k přijatým platbám | Faktúry k prijatým platbám |

Only empty settings are filled, so accounts you chose yourself are kept.

## Creating an advance invoice {#create}

On a confirmed sales order, click **Create Advance Invoice** and choose:

| Option | Result |
|---|---|
| Full amount | one *Advance* line per order line, priced at that line's subtotal |
| Percentage of total amount | one *Advance* line for the percentage of the untaxed total |
| Fixed amount | one *Advance* line for the untaxed amount you enter |
| **Include the ordered items** | the order's own products, quantities and VAT rates instead of *Advance* lines; for a percentage or a fixed amount the unit prices are scaled down and the quantities stay as ordered |

**Tick *Include the ordered items* whenever the order's VAT rate differs from
the *Advance* product's, or the order mixes rates.** Without it every advance
line carries the *Advance* product's taxes, and so does the tax document
raised on the payment. The final invoice then settles the difference, so no
VAT is lost or charged twice, but the VAT declared on the payment was at the
wrong rate.

The advance invoice opens as a new document linked to the order. On it:

- **Due Date** follows the payment terms; **Bank Account** and
  **Payment QR-code** choose what is printed.
- **Long-term Advance** sends the net advance to the long-term account.
  Tick it before the advance is confirmed.
- *Send by Email* and *Print* produce an "Advance Invoice" with the issue
  and due dates, the gross amounts without a VAT breakdown, and the bank
  account, the advance number as payment reference and the QR code.

The order gets an *Advance Invoices* section with a zero-quantity line per
advance, kept up to date with its state, payment date and tax document, and
an **Advance Invoices** smart button. Advance invoices do not appear under
*Quotations* or *Orders*. They have their own menu, *Sales → Orders →
Advance Invoices* and *Accounting → Customers → Advance Invoices*, which is
also where you create one without an order (see
[Advances without an order](#standalone)).

Confirming an advance never creates a delivery: the goods are delivered from
the original order.

## Receiving the payment {#payment}

The **Payment Status** of an advance (*Not Paid*, *Partially Paid*,
*Fully Paid*, *Overpaid*) follows the payments linked to it. The two smart
buttons below appear once the advance has been sent or confirmed and part of
it is still unpaid. A payment can arrive in four ways:

- **Online**, through the customer portal, when a payment provider is
  configured — the advance requires payment, like an online quotation. The
  payment is booked **to the clearing account**.
- **Register Payment** (smart button) — records a payment in a bank or cash
  journal, posted **to the clearing account**, and confirms the advance if it
  was still a quotation. The amount cannot exceed what is unpaid.
- **Link Manual Transfer** (smart button) — attaches an incoming payment that
  already exists for the same customer and is not linked to any invoice. If
  it was booked to the customer's receivable, a transfer entry in a
  miscellaneous journal moves it to the **clearing account**.
- **From the bank statement**, automatically or with a wizard, with
  [module:sale_order_advance_invoice_payment_match](module:sale_order_advance_invoice_payment_match).

## The tax document for the payment {#tax-document}

Once something is paid, the advance's **Accounting Status** moves from
*Nothing to Account* to **Waiting**, and the header shows **Create Invoice**.
Clicking it creates a draft tax document for the paid amount not yet covered
by an earlier tax document. Each instalment of a partly paid advance can
therefore have its own.

The tax document:

- is a customer invoice in the TDADV journal, split by VAT rate in proportion
  to the advance's lines;
- has the **payment date** as its taxable supply date and a line reading
  "Payment received for Advance Invoice ADV00042 on …";
- puts the net amount on the received-advance account (324000, or 475000 for
  a long-term advance) and the receivable on the **clearing account**;
- prints as **Tax Document**, with *Issue Date*, *Date Paid* in place of the
  taxable supply date, and no due date, payment instructions or QR code.

Check it and post it. Posting reconciles it on the clearing account with the
payments of that advance, and the status becomes **Accounted**.

The advance list shows the deadline in *Accounting Date Due*, turning red
once it has passed. It follows the company's country (see
[Legal background](#legal)):

| Country | Deadline |
|---|---|
| Czech Republic | 15 days after the payment |
| Slovakia | 15 days after the payment or the last day of that month, whichever is later (15 days for payments before 2016) |
| any other | 15 days after the payment |

## Settling on the final invoice {#final-invoice}

Invoice the order as usual (*Create Invoice* on the order). Every paid advance
is added below the regular lines in an *Advance Invoices* section, as a
negative line:

- **The part covered by posted tax documents**: the net amount those
  documents declared, on the received-advance account, with their VAT, so the
  VAT declared on the payment is given back. Documents at several rates are
  deducted one line per rate.
- **The part received but not covered by a posted tax document**: gross,
  without VAT, on the *Advance* product's income account. The final invoice
  then charges the VAT on that part itself.

Only what was **received** is deducted: a partly paid advance is deducted
for the part paid, not for its full amount. A tax document still in draft
covers nothing. An advance is deducted only once something has been paid on it,
and only together with regular
lines that are ready to invoice. If nothing else can be invoiced yet, for
example because nothing has been delivered, Odoo reports that there is
nothing to invoice.

**Foreign currency.** A deduction is converted at the rate its tax documents
were declared at, and so is the part of the supply the advance paid for. Only
the rest of the supply is converted at the final invoice's rate. A fully
prepaid supply therefore nets to zero VAT and leaves nothing on the
receivable, as § 37a requires for the Czech Republic.

## Advances without an order {#standalone}

An advance invoice created directly from the *Advance Invoices* menu has no
order. To settle it, open the final customer invoice while it is still a
draft and click **Link Advance Invoices**. You can pick confirmed advances of
the same customer with something paid on them that no other invoice deducts.
Each one is added exactly as on an order's final invoice: the part covered by
posted tax documents net with their VAT reversed, one line per rate, and the
rest of what was received gross without VAT.

## Limitations {#limitations}

- The tax document is not created on payment by itself: click **Create
  Invoice**, or let the bank matching add-on create it.
- A payment attached with *Link Manual Transfer* is moved to the clearing
  account only while its receivable leg is still open and the company has a
  miscellaneous journal other than the tax documents' one. Otherwise
  reconcile the tax document's clearing line with it yourself.
- Without a tax document, the deduction does not touch the clearing account,
  and the payment stays there until you clear it with a manual entry.
  Remember that the VAT liability arises on payment in both countries (with
  the Czech § 20a odst. 2 exception for a supply not yet known with
  sufficient certainty).
- Without *Include the ordered items*, the advance and its tax document use
  the *Advance* product's VAT rate, not the order's.
- Reverse-charge and intra-Community supplies are not handled specially:
  do not issue a tax document where the payment does not create a tax point.
