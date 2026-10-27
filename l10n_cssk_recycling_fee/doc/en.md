---
title: CZ/SK Recycling Fee (recyklační příspěvek / recyklačný poplatok)
summary: The take-back fee for electrical equipment and batteries priced from your collective scheme's dated tariff, stated on every invoice line as the statutes require, and summed per category for your declaration to the scheme.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A producer, distributor or retailer of electrical and electronic equipment
pays its collective scheme (*kolektivní systém* / *organizácia zodpovednosti
výrobcov*) a fee per piece or per kilogram placed on the market, and both
countries require that fee to be stated when the equipment is sold. For
portable batteries the opposite holds: the take-back cost must **not** be
stated separately.

This module adds that to Odoo on top of the OCA module `account_ecotax`,
which already knows ecotax classifications, several per product, and a fee
sub-line per invoice line. It adds what is specific to Czechia and Slovakia:

- **dated rates** per classification, in the scheme's currency (CZK or EUR),
  chosen by the invoice date;
- a classification tied to a **market** (CZ or SK), applied only by companies
  of that country;
- the fee **printed under every invoice line** in the statutory wording, and
  a document total;
- **portable batteries** computed and reported, but never printed;
- a **period report** per category for the declaration to the scheme.

The sales-order side is described under [Sales orders](#sales-orders).

## Legal background {#legal}

**Czech Republic** — [zákon č. 542/2020 Sb., o výrobcích s ukončenou
životností](law:cz/2020/542):

- **§ 73 odst. 1**: the producer, distributor and last seller of new
  electrical equipment must state the costs of take-back, treatment, recovery
  and disposal per piece or per kilogram **separately from the price**,
  *"zejména formou samostatného údaje na daňovém dokladu"* (in particular as
  a separate item on the tax document). **§ 99 odst. 1** says the same for
  tyres.
- **§ 73 odst. 2**: the amount stated may not exceed the costs known to the
  producer when the equipment was placed on the market; for a producer in a
  collective scheme, that is the contribution it pays the scheme. Hence the
  scheme's tariff as the rate.
- **§ 73 odst. 3**: obligations under the price regulations are unaffected.
- **§ 85 odst. 3**: for new portable batteries, these costs *"nesmějí být …
  uváděny odděleně"* — they may not be stated separately.
- **§ 125 odst. 2 písm. i) and l)**: not stating the costs, stating more than
  allowed, or stating them for portable batteries is an offence.
- The Ministry of the Environment's methodological guideline on § 73 and § 99
  (revised 26 October 2021) asks for the fee per item on the tax document and
  shows model invoices with the fee included in the unit price; the module
  follows that presentation.

**Slovakia** — [zákon č. 79/2015 Z. z. o odpadoch](law:sk/2015/79):

- [§ 34 ods. 1 písm. d)](law:sk/2015/79#paragraf-34.odsek-1.pismeno-d): the
  producer of electrical equipment states, on the packaging, the label *"alebo
  na daňovom či inom obdobnom doklade vyhotovenom pri jeho predaji"* (or on
  the tax or similar document issued on sale), the **recyklačný poplatok**
  covering collection, transport and treatment of household waste equipment.
- [§ 37 ods. 1 písm. a)](law:sk/2015/79#paragraf-37.odsek-1.pismeno-a): the
  distributor states the fee on sale where the producer stated it.
- [§ 46 ods. 2](law:sk/2015/79#paragraf-46.odsek-2) and
  [§ 48 ods. 1 písm. d)](law:sk/2015/79#paragraf-48.odsek-1.pismeno-d): for
  portable batteries the costs may not be stated separately.

Neither statute prescribes a separate invoice line, so the module offers
both: the fee **included** in the price with a per-line statement (the
default), or **on top** as its own line.

## Setting it up {#setup}

1. **Classifications** — *Accounting → Configuration → Ecotax →
   Classification*, one per tariff line of your scheme. Labels are in English
   (the module has no Czech or Slovak catalogue yet):
   - **Scheme Country** — CZ or SK. Only a classification with a country is
     treated as a statutory recycling fee; one without behaves exactly as in
     OCA.
   - **Ecotax Type** — *Fixed* (per piece) or *Weight based* (per kg);
     **Category**, **Ecotax collector** (the scheme), **Product Status**
     (*Domestic* = household, *Professional*).
   - **Dated Rates** — *Valid From*, *Valid To* (empty for the rate in force)
     and *Rate*, net of VAT, in the classification's currency (filled from the
     country: CZK, EUR). Two rates of one classification may not overlap. The
     OCA single-amount fields become read-only and show today's rate; a daily
     scheduled action rolls them over when a new rate starts.
   - **Show on Documents** — untick for **portable batteries**.
2. **Products** — on the *Accounting* tab, add the classification(s); a
   product sold in both countries can carry a CZ and an SK one, and each
   company takes only its own. Enter the **weight** in kg for a per-kg
   classification. A distributor can enter a **fixed amount** on the product's
   classification line — the fee its supplier actually paid, in the
   classification's currency; it then replaces the tariff.
3. **Presentation** — *Accounting → Configuration → Settings*, block
   **Recycling Fee**: *Included in the price* (default) or *Separate line on
   top of the price*.

The module creates the ecotax **categories** — the six categories of
electrical equipment (EEE1–EEE6) and five battery categories (portable, LMT,
SLI, industrial, electric vehicle). It ships **no tariffs**: they are each
scheme's price list.

## On the invoice {#invoice}

Each customer invoice line gets its fee from:

- the rate valid on the **invoice date** (or the accounting date while there
  is none);
- the quantity converted to the product's own unit (a line sold by the dozen
  owes twelve pieces);
- for a per-kg classification, the product weight; the fee per piece is
  rounded to the currency's two decimals;
- conversion at the invoice date when the invoice is in another currency
  than the rate.

Under the line description the printed invoice shows, in the national wording
of the classification's country:

    z toho recyklační příspěvek 100,00 Kč (0,50 Kč/kg × 2,000 kg = 1,00 Kč/ks)
    z toho recyklačný poplatok 3,60 € (0,90 €/ks)

followed by *bez DPH* when the line's price includes VAT, and the original
amount with the exchange rate when the invoice is in another currency. A
total row closes the document: *Recyklační příspěvek celkem bez DPH* /
*Recyklačný poplatok spolu bez DPH*. OCA's English *Eco Part* column and
total are hidden on such documents. Fees of classifications with *Show on
Documents* unticked are neither printed nor counted in that total.

**Posting.** On posting, the fee is priced once more on the final invoice
date, and a customer invoice or credit note whose classification has **no
rate valid on that date** is refused (unless a fixed amount is used). Once
posted, the fee is frozen: later tariff or weight changes do not rewrite it;
resetting the invoice to draft prices it afresh.

## Report for the scheme {#report}

*Accounting → Reporting → Management → Recycling Fees* (in Slovak
*Účtovníctvo → Výkazy → Manažment*, in Czech *Účetnictví → Výkazy →
Správa*) shows pieces, kilograms and fee from **posted customer invoices and
credit notes** (credit notes negative), per country, category,
classification, scheme and period, in the scheme's currency whatever the
invoice currency. Pivot, list and graph views; filters for CZ, SK, household
and professional. Portable batteries are included.

*Print → Recycling Fees (XLSX)* exports the selected rows: a summary sheet per
country, scheme, category, classification, product status and rate basis, and
a second sheet with the invoice lines.

## Sales orders {#sales-orders}

With the Sales app and OCA `account_ecotax_sale`,
[module:l10n_cssk_recycling_fee_sale](module:l10n_cssk_recycling_fee_sale)
installs itself and adds:

- **Fees on order lines**, priced from the rate valid on the **order date**,
  with the same market filter and unit conversion. The invoice prices again
  at its own date, because the invoice is the tax document the statutes
  speak of.
- The product's **fixed amount** is carried from the order to the invoice.
- **On-top mode.** When the presentation is *Separate line on top of the
  price*, set a **Recycling Fee Product** (a service) in the same settings
  block. The **Update Recycling Fee** button on the order adds one line per
  classification and VAT treatment, priced at the sum of the fees, with the
  VAT of the goods it belongs to (a price-included tax is grossed up, since
  the tariff is net). The fee product's income account is used, its taxes are
  not. Pressing the button again regenerates the lines; once they are
  invoiced it refuses. Portable batteries get no line.

## Limitations {#limitations}

- The rate is chosen by the **invoice date**, while § 73 odst. 2 ties the
  amount to when the producer placed the item on the market. A distributor
  selling old stock across a tariff change should use the fixed amount on the
  product.
- Rates are not shipped; enter your scheme's price list.
- The report is built from customer invoices. If goods are delivered in one
  period and invoiced in another, reconcile that in the declaration.
  Intra-EU sales and exports are included and must be filtered out where the
  scheme does not count them.
- In on-top mode the separate fee lines are created only from a **sales
  order**; an invoice created without an order shows the per-line statement
  but no fee line, so the fee is not charged on top.
- Quotations and orders do not print the per-line statement; the invoice
  does.
- No tyre category is shipped; tyres (CZ § 99) can be set up the same way.
- The user interface is in English; the statutory phrases on the invoice are
  in Czech or Slovak.
