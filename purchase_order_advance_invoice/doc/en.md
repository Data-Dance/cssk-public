---
title: Received Advance Invoices (Purchase)
summary: Suppliers' advance (proforma) invoices as purchase documents, the payment to them, the supplier's tax document on that payment and the deduction on the final bill.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

This is the supplier side of
[module:sale_order_advance_invoice](module:sale_order_advance_invoice). When
a supplier asks for an advance, you deal with:

1. the **received advance invoice** (CZ *přijatá zálohová faktura*, SK
   *prijatá zálohová / preddavková faktúra*) — a request for payment, never
   posted;
2. **your payment** of it;
3. the **supplier's tax document on the payment** (CZ *daňový doklad
   k přijaté platbě*, SK *faktúra k prijatej platbe*) — the document that
   entitles you to deduct the VAT on the advance;
4. the **final bill**, from which the advance and its VAT are deducted.

The module registers the received advance invoice as a purchase order of its
own, numbered `PADV00001`, `PADV00002`…, and books only the payment and the
tax document.

## Legal background {#legal}

- **The supplier's side.** A payment received before the supply is taxed on
  the day it is received — Slovakia
  [§ 19 ods. 4 zákona o DPH](law:sk/2004/222#paragraf-19.odsek-4), Czech
  Republic [§ 20a odst. 2 zákona o DPH](law:cz/2004/235). The supplier must
  issue the tax document within 15 days of the payment or by the end of that
  month in Slovakia
  ([§ 73 ods. 1 písm. b)](law:sk/2004/222#paragraf-73.odsek-1.pismeno-b)),
  and within 15 days in the Czech Republic (§ 28 odst. 8).
- **Your deduction.** To deduct the VAT you must hold the supplier's tax
  document — Slovakia
  [§ 51 ods. 1 písm. a)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a),
  Czech Republic § 73 odst. 1 písm. a). In Slovakia the deduction is made at
  the earliest in the period in which the right arose and at the latest in
  the last period of that calendar year, provided you have the document by
  the filing deadline of the return in which you claim it; if you do not
  have it by the filing deadline for the last period of that year, you
  deduct in the period in which you receive it
  ([§ 51 ods. 2](law:sk/2004/222#paragraf-51.odsek-2)). In the Czech
  Republic the deduction can be claimed at the earliest for the period in
  which the conditions are met (§ 73 odst. 2). That is why the accounting
  date of the tax document is yours to choose (see [below](#tax-document)).

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Received Advance
Invoices**:

| Setting | What it does |
|---|---|
| Tax documents journal | The purchase journal for the suppliers' tax documents, e.g. PDADV. |
| Clearing account | A reconcilable **payable**-type account on which your payment and the tax document meet, e.g. 314001. |
| Paid advances account | The net paid advance until the final bill, e.g. 314000, with an optional long-term variant. |

Without a localization add-on you fill these in yourself.

### Localization add-ons {#localization}

[module:l10n_cz_purchase_order_advance_invoice](module:l10n_cz_purchase_order_advance_invoice)
and
[module:l10n_sk_purchase_order_advance_invoice](module:l10n_sk_purchase_order_advance_invoice)
fill in the settings above for every company with the Czech or Slovak chart
of accounts — at installation, and again whenever the chart is loaded later,
for example for a new company:

| Role | Account | Czech name | Slovak name |
|---|---|---|---|
| Clearing account (created by the add-on, payable, reconcilable) | 314001 | Poskytnuté zálohy – zúčtování (daňový doklad) | Poskytnuté preddavky – zúčtovanie (daňový doklad) |
| Paid advances | 314000 | Poskytnuté provozní zálohy | Poskytnuté preddavky |
| Paid advances, long-term | — (left empty) | | |
| Journal PDADV (purchase) | — | Daňové doklady k odeslaným platbám | Faktúry k odoslaným platbám |

Only empty settings are filled, so accounts you chose yourself are kept.

## Registering a received advance invoice {#register}

*Purchase → Orders → Received Advance Invoices* (also *Accounting →
Vendors → Received Advance Invoices*), then *New*. Enter the supplier and the
lines as on the supplier's advance invoice, with the VAT rates it states.
Optionally choose the **Parent Purchase Order** it belongs to, and tick
**Long-term Advance** to use the long-term account (when one is configured).

A purchase order with advances shows an **Advances** smart button.

**With Inventory.** The goods are received on the parent purchase order,
never on the advance: with
[module:purchase_order_advance_invoice_stock](module:purchase_order_advance_invoice_stock),
which installs itself when Inventory is present, confirming or paying an
advance creates no receipt, even when its lines are stockable products.

## Paying it {#payment}

On the advance:

- **Register Payment** — creates and posts a supplier payment from a bank or
  cash journal **to the clearing account**, and confirms the advance. The
  amount cannot exceed what is unpaid.
- **Link Payment** — attaches a supplier payment that already exists for the
  same supplier and is not linked to another advance.

**Payment Status** (*Not Paid*, *Partially Paid*, *Fully Paid*, *Overpaid*),
**Amount Paid** and **Paid Date** follow the linked payments.

## Registering the supplier's tax document {#tax-document}

Once something is paid, the **Accounting Status** becomes **Waiting for Tax
Document** and **Tax Document Expected By** shows the deadline. When the
supplier's tax document arrives, click **Register Received Tax Document**:

| Field | Meaning |
|---|---|
| Supplier's Document Number | the number exactly as the supplier printed it (required) — it is the reference of the bill |
| Document Date | the date of issue |
| Accounting Date | the period in which you claim the deduction; defaults to the document date (see [Legal background](#legal)) |
| Taxable Supply Date | the day the supplier received the payment; defaults to your payment date |
| Amount (Tax Included) | the gross amount of the document; defaults to the paid amount not yet covered by a tax document |

This creates a **draft vendor bill** in the tax documents journal, split by
VAT rate in proportion to the advance's lines, with the net amount on the
paid advances account and the payable on the **clearing account**. Check it
against the paper and post it. Posting reconciles it on the clearing account
with the advance's payments, and the status becomes **Accounted** once the
tax documents cover the whole paid amount.

The **Tax Documents** smart button lists them.

## Deducting on the final bill {#deduction}

- **From the parent purchase order**: *Create Bills* adds a deduction for every
  paid advance not yet fully deducted to the newest draft bill.
- **Any draft vendor bill**: **Deduct Advance Invoices** offers the
  supplier's advances with something left to deduct.

The deduction is:

- **for the part covered by posted tax documents** — a negative copy of each
  line of the tax documents: the net amount on the paid advances account with
  the same VAT, so the input VAT deducted on the advance is reversed;
- **for the part paid but not covered by a posted tax document** — a single
  negative line for that amount, on the paid advances account, without VAT.

Only what is still left is deducted. A bill that comes after an earlier
deduction takes the documented part first and copies the tax documents' lines
only for what of them is left.

## Chasing the supplier {#chasing}

The scheduled action *Received Advance Invoices: chase overdue tax
documents* runs daily. For every advance still waiting for a tax document
after **Tax Document Expected By**, it schedules a to-do activity "Advance
tax document overdue — chase …" (once). The list has the filters **Waiting
for Tax Document**, **Tax Document Overdue** and **Unpaid**.

The expected date follows the company's country (see
[Legal background](#legal)): 15 days after your payment in the Czech
Republic; in Slovakia 15 days after the payment or the end of that month,
whichever is later (15 days for payments before 2016); 15 days anywhere else.
The activity has its own type, *Chase Advance Tax Document*, so it is
scheduled once whatever language the scheduled action runs in.

## Limitations {#limitations}

- The advance is an ordinary purchase order underneath. Do not use *Create
  Bills* on the advance itself.
- **Link Payment** does not check which account the payment was booked to.
  Only a payment booked to the clearing account is reconciled with the tax
  document automatically.
- Without a tax document, the deduction goes to the paid advances account
  while the payment sits on the clearing account. Clear the two with a manual
  entry.
- Reverse-charge and intra-Community advances are out of scope: an advance
  payment creates no tax point there, so register no tax document for them.
