---
title: SK Invoice (statutory PDF)
summary: Adds the customer's DIČ, the payment symbols and the statutory VAT phrases — exemption and reverse charge — to the printed Slovak invoice.
verified: 19.0.1.0.4
---

## What it is for {#purpose}

Odoo's invoice PDF, together with the Slovak chart of accounts (`l10n_sk`),
already prints most of what a Slovak *faktúra* needs: both parties' names,
addresses and VAT numbers (IČ DPH), the customer's IČO, the invoice number and
dates, the lines, the tax base and tax per rate, and the company's trade
registry entry. This module adds the three things it is missing:

1. the customer's **DIČ** under their address;
2. the **variable, constant and specific symbol** next to the invoice dates;
3. the **statutory phrase** a VAT-exempt or reverse-charge supply must carry,
   chosen from the taxes on the invoice and the customer's country.

Everything it prints appears only on documents of a company whose country is
Slovakia, so it does no harm in a multi-company database with other
countries.

## Legal background {#legal}

The content of an invoice is set by
[§ 74 ods. 1 of the Slovak VAT Act](law:sk/2004/222#paragraf-74.odsek-1). Two
of its items depend on the kind of supply, and those are what the module
prints:

- **Exemption** —
  [§ 74 ods. 1 písm. h)](law:sk/2004/222#paragraf-74.odsek-1.pismeno-h): with
  an exempt supply, the invoice states a reference to the provision of the Act
  or of Directive 2006/112/EC, or the words *„dodanie je oslobodené od
  dane“*. The module cites the Act:
  [§ 43](law:sk/2004/222#paragraf-43) for goods dispatched to a VAT-registered
  customer in another member state, and
  [§ 47](law:sk/2004/222#paragraf-47) for goods exported outside the EU.
- **Reverse charge** —
  [§ 74 ods. 1 písm. k)](law:sk/2004/222#paragraf-74.odsek-1.pismeno-k):
  when the customer is the person liable to pay the tax, the invoice carries
  the words *„prenesenie daňovej povinnosti“*. That covers the domestic
  supplies listed in [§ 69 ods. 12](law:sk/2004/222#paragraf-69.odsek-12)
  (scrap metal, emission allowances, construction work and others) and a
  service supplied to a taxable person established in another member state,
  whose place of supply is the customer's country under
  [§ 15 ods. 1](law:sk/2004/222#paragraf-15.odsek-1).

The phrases are printed in Slovak whatever the language of the invoice, with
an English gloss in brackets.

§ 74 asks for the parties' *identifikačné číslo pre daň*, which in Slovakia is
the IČ DPH and which Odoo prints already. The DIČ is not on that list; the
module prints it because Slovak customers routinely expect to see it.

## Setting it up {#setup}

1. **Record the customer's DIČ.** On the contact, the field **DIČ** (added by
   [module:l10n_sk_base](module:l10n_sk_base)). It is not derived from the VAT
   number.
2. **Payment symbols.** They come from
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols), which
   is installed with this module. Its settings decide how the variable symbol
   is formed and whether a default constant symbol is used — see
   [setting up payment symbols](module:l10n_cssk_payment_symbols#setup).
3. **Flag your domestic reverse-charge taxes.** *Accounting → Configuration →
   Taxes*, open the sales tax you use for supplies under § 69 ods. 12 and tick
   **SK Reverse Charge (§69/12)** (*SK prenesenie daňovej povinnosti*), next to
   *Tax Type*. No tax is flagged on installation: the Slovak chart has no
   dedicated sales tax for these supplies, so you choose which one it is.
4. **Check the scope of zero-rated taxes.** For intra-EU sales the module
   tells goods from services by the tax's **Tax Scope** (*Goods* / *Services*).
   The Slovak chart's `0% EU M` and `0% EU S` already carry it. For a
   zero-rated tax with no scope, the product type decides (a service product
   counts as a service, anything else as goods).

## What the invoice shows {#invoice}

### Customer DIČ

`DIČ: 2020123456` under the customer's VAT number, when the DIČ is recorded.

### Payment symbols

*Variabilný symbol*, *Konštantný symbol* and *Špecifický symbol* in the row
with the invoice date and due date, each only when it has a value. The labels
follow the language of the invoice: Slovak for a Slovak-speaking customer,
English (*Variable Symbol*, …) otherwise.

### Statutory phrases {#phrases}

The phrase is worked out each time from the invoice's taxes and the
**commercial partner** of the customer (the company, not the contact person).
It is printed under the terms and conditions note. The rules, in order:

| Situation | Printed |
|---|---|
| Any line has a tax flagged *SK Reverse Charge (§69/12)* | *Prenesenie daňovej povinnosti podľa §69 ods. 12 zákona o DPH (Reverse charge).* — and no other automatic phrase |
| Customer in another EU country, with a VAT number, and a zero-rated line for **goods** | *Dodanie oslobodené od dane podľa §43 zákona o DPH (Intra-Community supply of goods).* |
| Customer in another EU country, with a VAT number, and a zero-rated line for **services** | *Prenesenie daňovej povinnosti — miesto dodania služby podľa §15 ods. 1 zákona o DPH (Reverse charge, services).* |
| Customer outside the EU and a zero-rated line for **goods** | *Oslobodené od dane podľa §47 zákona o DPH (Exempt — export of goods).* |
| A domestic customer, or a taxed supply | nothing |

An invoice with both goods and services to an EU customer gets both of the
two middle phrases. A service to a customer outside the EU gets no phrase:
it is outside the scope of Slovak VAT and there is no exemption to cite.

A **triangular trade** (the chart's `0% EU T` tax) is deliberately left out
of the § 43 rule: Odoo prints its own note for it, citing article 141 of the
Directive.

"Zero-rated" means any tax with a rate of 0 % on the line. Odoo's Slovak
taxes `0% EU M` and `0% EU S` also carry their own English legal notes
(articles 138 and 196 of the Directive), which Odoo prints as well; the
Slovak phrase comes in addition to them.

The same rules apply to customer credit notes.

### Your own note

When the automatic phrases are not enough — a different exemption, a
contract reference — write it into **Invoice Legal Note (manual)**
(*Zákonná poznámka faktúry (ručne)*), on the *Invoice Lines* tab under the
terms and conditions, on customer invoices and credit notes. It is printed
after the automatic phrase. It is not copied when the invoice is duplicated.

## Limitations {#limitations}

- The phrase is a rule of thumb based on the tax rate and the customer's
  country. It does not know the legal reason for a particular exemption and
  does not check the customer's VAT number in VIES. Have your accountant
  confirm it for your tax set-up, and use the manual note where it does not
  fit.
- Only the exemptions under § 43 and § 47 are recognised. A domestic exempt
  supply (§ 28 to § 42a) gets no phrase; write it into the manual note.
- The reverse-charge phrase always cites § 69 ods. 12, which is right for
  domestic reverse charge only. If you flag a tax used for other
  reverse-charge situations, the citation will be wrong.
- The module adds no dates. The date of supply prints only when the
  invoice's *Delivery Date* is filled in (Odoo fills it from deliveries when
  Inventory is installed); if it differs from the issue date, § 74 ods. 1
  písm. d) requires it on the invoice.
- The statutory phrases are in Slovak with an English gloss; they are not
  translated into the customer's language.
