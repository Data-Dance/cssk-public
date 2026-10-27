---
title: SK Import Customs Declaration (JCD)
summary: The Slovak customs declaration for imported goods as an accounting document — import VAT onto the right return rows, duty into the stock value, and the deduction held back until the confirmed customs document is on file.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

Goods bought from outside the EU are released into free circulation on a
**customs declaration** (*colné vyhlásenie*, historically the *JCD*, *jednotný
colný doklad*). One import scatters three things across the books:

1. **Duty and customs charges** (*clo a colné poplatky*), which belong in the
   acquisition cost of the goods;
2. **Import VAT** (*daň pri dovoze*), which must reach the right rows of the VAT
   return;
3. **The customs document itself**, without which the import VAT may not be
   deducted.

This module records the declaration as one document and posts all three from
it. It reuses the import taxes of Odoo's Slovak chart of accounts and leaves
the reporting to the VAT return, so nothing about the tax return is
reimplemented here.

## Legal background {#legal}

All references are to the [VAT Act](law:sk/2004/222) unless stated otherwise.
Statutory terms are given in Slovak, as on the form.

- **The taxable amount.** Under
  [§ 24](law:sk/2004/222#paragraf-24) the base is the customs value
  (*colná hodnota*), increased — where not already included — by duties,
  taxes and other charges payable on import (other than the VAT itself), and
  by related costs such as commission, packing, transport and insurance up to
  the first place of destination in Slovakia.
- **The right to deduct.**
  [§ 49 ods. 2 písm. d)](law:sk/2004/222#paragraf-49.odsek-2.pismeno-d) lets
  the payer deduct VAT it self-assessed on import or paid to the customs
  authority.
- **The document condition.** The right can be exercised only if the payer
  *"má dovozný doklad potvrdený colným orgánom, v ktorom je platiteľ uvedený
  ako príjemca alebo dovozca"* —
  [§ 51 ods. 1 písm. d)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-d).
  [§ 51 ods. 2](law:sk/2004/222#paragraf-51.odsek-2) sets the window: no
  earlier than the period in which the right arose, and no later than the
  last period of that calendar year, provided the document is held by the
  filing deadline.
- **Self-assessment at import.**
  [§ 84a ods. 2 and 3](law:sk/2004/222#paragraf-84a.odsek-2) let a payer that
  is established in Slovakia, holds a Slovak VAT number and holds an
  **authorised economic operator** (AEO) authorisation compute the import VAT
  itself and declare it in its VAT return, instead of having it assessed by the
  customs office. This depends on the payer's status, not on the shipment.
  Under [§ 85l](law:sk/2004/222#paragraf-85l) it applies to imports whose tax
  liability arose after 30 June 2025, and under
  [§ 21 ods. 2](law:sk/2004/222#paragraf-21.odsek-2) the liability arises on
  the day the customs declaration is accepted.
- **Duty in the stock value.** Acquisition cost includes the costs related
  to acquiring the asset —
  [§ 25 ods. 6 písm. a) of the Accounting Act](law:sk/2002/431#paragraf-25.odsek-6.pismeno-a).
- The customs procedure itself — the declaration and its MRN — is governed by
  the [Union Customs Code](law:eu/reg/2013/952).

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Dovoz tovaru (JCD)**, shown
only for companies using the Slovak chart of accounts:

| Setting | Default | Purpose |
|---|---|---|
| Import clearing account | 379000 | Carries the notional import base (see [Posting](#posting)). Change it if your accountant prefers another account. |
| Customs duty product | *Clo (colný poplatok)* | The service product through which the duty is added to the stock value. It must have an expense account, on the product or its category. |
| Predvolený režim dane | daň zaplatená colnému orgánu | The regime new declarations start with. Choose self-assessment only if the company meets the § 84a conditions. |

The account and the product are filled in automatically when the module is
installed, for every company with the Slovak chart, unless already set.

Before the first import, check two things:

- **Products are valued by FIFO or average cost.** Odoo applies landed costs
  only to such product categories; on standard cost the duty cannot be
  capitalised.
- **Historical rates (optional).** With
  [module:l10n_cssk_vat_return_base](module:l10n_cssk_vat_return_base)
  installed, a declaration dated before a rate change is taxed at the rate in
  force on its date — for example 20 % rather than 23 % for a standard-rate
  import before 1 January 2025. Without it, the current rate is used and you
  have to check older declarations yourself.

## Entering a declaration {#usage}

*Accounting → Accounting → Colné vyhlásenia (JCD)*, then *New*.

1. **Colné vyhlásenie.** The acceptance date, the **MRN** of the confirmed
   declaration, and the customs office as the partner you owe the duty to.
2. **Hodnoty.** *Colná hodnota*, *Clo* and *Iné colné poplatky* from the
   declaration.
3. **Daň pri dovoze.** The regime, the rate band (23 %, 19 % or 5 %, named
   after today's rates), and the taxable amount. The base defaults to customs
   value + duty + other charges; **edit it** when the declaration's base
   includes more, such as transport to the first place of destination.
   *Použitá sadzba* shows the rate that will actually post for the
   declaration's date.
4. **Väzby.** The foreign supplier's invoices and the goods receipts the duty
   belongs to.
5. **Attach the confirmed customs document** in the chatter.

Until both the MRN and an attachment are present, the form shows a warning and
**refuses to post**: that is the § 51 ods. 1 písm. d) condition, enforced.
Self-assessment is likewise refused on a declaration accepted before
1 July 2025.

Then click **Zaúčtovať**.

## What posting creates {#posting}

- **A bill from the customs office**, in the first purchase journal, dated
  with the declaration and referenced by the MRN:
  - the taxable amount on the clearing account twice — once with the import
    tax, once negative without it — so the notional base nets to zero and only
    the VAT is real;
  - the duty on the duty product's expense account;
  - other charges on the company's default expense account.
- **A landed cost** (*Rozpustenie cla*) over the linked receipts, splitting the
  duty by current cost, **validated** at once so the duty moves into the stock
  value. Its cost line credits the same expense account the bill debited, so
  the duty is not counted twice. If Odoo cannot apply the landed cost — a
  product on standard cost, for instance — the declaration does not post at
  all, rather than posting the bill alone.

Pay the bill like any other. A posted declaration cannot be cancelled from the
form; to correct one, reverse the bill with a credit note and enter the
declaration again.

## On the VAT return {#vat-return}

Reported by [module:l10n_sk_vat_return](module:l10n_sk_vat_return) through the
tax tags of Odoo's Slovak chart:

| Regime | Rows of the return |
|---|---|
| Daň zaplatená colnému orgánu | deduction only: r. 22 (19 %), r. 22a (5 %), r. 23 (23 %); the base is not reported |
| Samozdanenie pri dovoze (§ 84a ods. 3) | base r. 11c–11e, tax r. 12c–12e, deduction r. 23a–23c |

## Limitations {#limitations}

- Duty is capitalised only on FIFO or average-cost products, and only when
  receipts are linked. *Iné colné poplatky* are expensed, not capitalised.
- The form does not check that the company qualifies for self-assessment
  under § 84a (AEO status, establishment); it only refuses the regime before
  1 July 2025.
- The deduction is posted on the declaration date. The § 51 ods. 2 window for
  a document that arrives later is not managed.
- This is an accounting document only: nothing is filed with the customs
  authority.
- The default taxable amount and the account mapping are a starting point and
  should be reviewed with your accountant.
