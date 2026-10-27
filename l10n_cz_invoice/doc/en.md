---
title: CZ Invoice (statutory PDF)
summary: Adds the payment symbols and the statutory VAT phrases — exemption and "daň odvede zákazník" — to the printed Czech invoice.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Odoo's invoice PDF, together with the Czech chart of accounts (`l10n_cz`),
already prints most of what a Czech *daňový doklad* needs: both parties'
names, addresses and tax numbers (for Czechia Odoo labels the VAT number
**DIČ**), the customer's IČO, the document number, the issue date and the
date of the taxable supply (*DUZP*), the lines, the tax base and tax per
rate. This module adds what is missing:

1. the **variable, constant and specific symbol** next to the invoice dates;
2. the **statutory phrase** an exempt or reverse-charge supply must carry,
   chosen from the taxes on the invoice and the customer's country;
3. with OCA payment modes installed, the **payment method** (*Forma úhrady*)
   — see [below](#payment-mode).

Everything it prints appears only on documents of a company whose country is
the Czech Republic.

The customer's DIČ is deliberately **not** printed a second time: in Czechia
the DIČ *is* the VAT number (`CZ` + digits), and Odoo already prints it.

## Legal background {#legal}

The particulars of a tax document are set by
[§ 29 of the Czech VAT Act (zákon č. 235/2004 Sb.)](law:cz/2004/235).
Two of the items in its odstavec 2 depend on the kind of supply, and those
are what the module prints:

- **Exemption** — § 29 odst. 2 písm. a): an exempt supply carries a reference
  to the provision of the Act or of EU law, or another statement that the
  supply is exempt. The module cites the Act: **§ 64** (goods dispatched to a
  person registered for VAT in another member state) and **§ 66** (export of
  goods outside the EU).
- **Reverse charge** — § 29 odst. 2 písm. c): when the customer is the person
  liable to declare the tax, the document carries the words *„daň odvede
  zákazník“*. For domestic supplies the regime is set by **§ 92a** and the
  sections that follow it; for a service to a business in another member
  state the place of supply is the customer's state (**§ 9 odst. 1**) and the
  customer pays the tax there.
- **Triangular trade** — § 29 odst. 2 písm. e): the document the middle person
  of a triangular trade issues to the customer states that it is a triangular
  trade.

The phrases are printed in Czech whatever the language of the invoice, with
an English gloss in brackets.

## Setting it up {#setup}

1. **Payment symbols.** They come from
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols), which
   is installed with this module. Its settings decide how the variable symbol
   is formed and whether a default constant symbol is used — see
   [setting up payment symbols](module:l10n_cssk_payment_symbols#setup).
2. **Flag your domestic reverse-charge taxes.** *Accounting → Configuration →
   Taxes*, open the sales tax you use for supplies in the reverse-charge
   regime (the Czech chart has `0% RC` for this) and tick **CZ Reverse Charge
   phrase (§92a)** (*CZ formulace o přenesení daňové povinnosti*), next to
   *Tax Type*. No tax is flagged on installation.

   If another Czech localization with its own reverse-charge flag on taxes
   (the field `l10n_cz_reverse_charge`) is installed, a tax flagged there
   counts as well. The two flags are separate on purpose, so ticking this one
   does not change that module's reporting.
3. **Triangular trade (optional).** If you act as the middle person of a
   triangular trade, create a 0 % sales tax for it and tick **CZ Triangular
   trade phrase (§17)** (*CZ formulace o třístranném obchodu*) on it. The
   Czech chart has no such tax.
4. **Goods or services.** The phrase for a 0 % tax depends on whether the line
   is goods or a service. The tax's *Tax Scope* decides (the Czech chart's
   `0% EU G` / `0% EX G` are goods, `0% EU S` / `0% EX S` services); for a tax
   without a scope, the product's type decides, and a line with neither counts
   as goods.

## What the invoice shows {#invoice}

### Payment symbols

*Variabilní symbol*, *Konstantní symbol* and *Specifický symbol* in the row
with the invoice date and due date, each only when it has a value. These
labels are always in Czech.

### Statutory phrases {#phrases}

The phrase is worked out each time from the invoice's taxes and the
**commercial partner** of the customer (the company, not the contact person).
It is printed under the terms and conditions note. The rows are checked in
this order; a reverse charge excludes the rest, and an invoice to an EU
business can get more than one phrase when it mixes goods, services and a
triangular trade.

| Situation | Printed |
|---|---|
| Any line has a reverse-charge flagged tax | *Daň odvede zákazník — přenesení daňové povinnosti podle §92a zákona o DPH (Reverse charge).* |
| Customer in another EU country with a VAT number, a tax flagged for triangular trade | *Třístranný obchod — zjednodušený postup, daň odvede zákazník (§29 odst. 2 písm. c) a e) zákona o DPH; čl. 141 a 197 směrnice 2006/112/ES).* |
| Customer in another EU country with a VAT number, a 0 % line of goods | *Osvobozeno od daně podle §64 zákona o DPH (Intra-Community supply of goods).* |
| Customer in another EU country with a VAT number, a 0 % line of services | *Daň odvede zákazník — místo plnění podle §9 odst. 1 zákona o DPH (čl. 196 směrnice 2006/112/ES, Reverse charge).* |
| Customer outside the EU, a 0 % line of goods | *Osvobozeno od daně podle §66 zákona o DPH (Exempt — export of goods).* |
| Otherwise (a service to a customer outside the EU included) | nothing |

The same rules apply to customer credit notes. Odoo's Czech taxes
`0% EU G` and `0% EU S` also carry their own English legal notes (articles
138 and 196 of the Directive), which Odoo prints as well.

### Your own note

When the automatic phrase is wrong or not enough, write the correct text into
**Invoice Legal Note (manual)** (*Zákonná poznámka faktury (ručně)*), on the
*Invoice Lines* tab under the terms and conditions, on customer invoices and
credit notes. It is printed after the automatic phrase. It is not copied when
the invoice is duplicated.

## Payment method on the invoice {#payment-mode}

With OCA's `account_payment_mode` installed,
[module:l10n_cz_invoice_payment_mode](module:l10n_cz_invoice_payment_mode)
installs itself and prints the invoice's **Payment Mode** under the heading
*Forma úhrady*, in the same row as the payment symbols — for example
*Převodem* or *Hotově*, whatever you named your payment modes. It is printed
only when the invoice has a payment mode, and only for a Czech company.
`account_payment_mode` itself prints only the mode's note, at the foot of
the invoice.

## Limitations {#limitations}

- A domestic exempt supply with a 0 % tax sold to a foreign customer gets the
  § 64 or § 66 phrase too, and a domestic exempt supply to a Czech customer
  gets none.
- The rule does not check the customer's VAT number in VIES and does not know
  the legal reason for a particular exemption. Have your accountant confirm
  it for your tax set-up.
- The phrases are in Czech with an English gloss; the symbol labels are
  always Czech.
