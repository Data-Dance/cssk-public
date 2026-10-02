==================================================================
CZ/SK Recycling Fee (recyklační příspěvek / recyklačný poplatok)
==================================================================

The take-back fee for electrical and electronic equipment and batteries, as the
Czech and Slovak statutes require it to appear on a sale: a dated tariff per
scheme category, priced per piece or per kilogram, stated on every invoice line
it belongs to, and summed per category and period for the producer's
declaration to its collective scheme.

It is built on OCA ``account_ecotax`` (vendored unchanged from
``OCA/account-fiscal-rule`` 19.0). The sale-order side is
``l10n_cssk_recycling_fee_sale``, which installs automatically with ``sale``.

What the law requires
=====================

Czech Republic — zákon č. 542/2020 Sb., o výrobcích s ukončenou životností
--------------------------------------------------------------------------

* **§ 73 odst. 1** (electrical equipment): the producer, distributor and last
  seller *"jsou povinni při prodeji nového elektrozařízení uvádět odděleně od
  ceny elektrozařízení náklady na zpětný odběr, zpracování, využití a odstranění
  … které připadají na jeden kus … nebo jeden kilogram …, a to zejména formou
  samostatného údaje na daňovém dokladu"*. **§ 99 odst. 1** says the same for
  tyres.
* **§ 73 odst. 2**: the amount shown may not exceed what the producer pays its
  collective scheme (§ 46 odst. 1) — hence the scheme's dated tariff.
* **§ 73 odst. 3**: the price regulations (cenové předpisy) are unaffected — the
  price the customer pays is still the full price.
* **§ 85 odst. 3** (portable batteries): the take-back cost *"nesmí být … uváděn[y]
  odděleně"* — disclosure is **prohibited**.
* **§ 125 odst. 2 písm. i) a l)**: omitting the fee, overstating it, or
  disclosing a portable-battery fee is an offence (up to 500 000 Kč).

MŽP's methodological guideline on § 73 / § 99 (Odbor odpadů, 26. 10. 2021, with
model invoices in its annex) settles the presentation:

* point 2.1 — the fee must be on the tax document, **per item**: the rate per
  piece or per kg, the quantity, the weight for a per-kg fee, the fee per piece,
  the fee for the line, and the sum for the document. *"Pouhé konstatování
  v závěru faktury, že v ceně výrobku je zahrnut recyklační příspěvek ve výši
  X,- Kč, je … nedostatečné."*
* the model invoices print the unit price **"vč. příspěvku na recyklaci"** — the
  fee **included** in the price — and close with *"Příspěvek na recyklaci celkem
  bez DPH"*;
* point 2.3 — call it "Recyklační příspěvek" / "Příspěvek na recyklaci", never
  "poplatek";
* point 2.4 — at most two decimals;
* point 2.5 — an invoice in another currency may convert the fee, but must show
  the exchange rate and the original CZK amount;
* point 2.6 — a shop must advertise the final price, fee included.

Slovakia — zákon č. 79/2015 Z. z. o odpadoch
--------------------------------------------

* **§ 34 ods. 1 písm. d)**: the producer shall *"pri predaji elektrozariadenia
  uvádzať na jeho obale alebo etikete alebo na daňovom či inom obdobnom doklade
  … výšku recyklačného poplatku"* (household EEE); **§ 37 ods. 1 písm. a)**
  obliges the distributor to pass it on where the producer stated it.
* **§ 46 ods. 2** and **§ 48 ods. 1 písm. d)**: portable batteries — the cost
  may **not** be stated separately.

The Slovak statute fixes *that* the amount is stated, not *how*. SEWA's guidance
(19. 9. 2023) asks for the amount to be quantified per type of equipment "ako
samostatná položka", i.e. as its own figure per item — which the per-line
statement is; it does not require a separate invoice line. No Slovak official
guidance equivalent to MŽP's was found.

So: **included, with the per-line "z toho …" statement, is the presentation of
the official CZ model invoices and satisfies the SK wording.** Neither statute
forbids a separate line (it is "odděleně od ceny" too), so it is offered as a
setting.

What the module does
====================

* **Dated rates.** An ``account.ecotax.classification`` gains a *scheme
  country*, a *currency* (defaults from the country: CZK / EUR) and dated rates
  (``date_from`` / ``date_to``, overlaps refused). The classification's OCA
  ``ecotax_type`` says whether the rate is per piece or per kg. Only
  classifications with a country use this; the rest behave exactly as upstream.
* **Per company market.** A product may carry a CZ and an SK classification; a
  document only takes those of its company's fiscal country.
* **Priced on the document.** Each invoice line gets its fee from the rate valid
  on the invoice date, the product weight (per kg), the quantity converted to
  the product's unit (a dozen is twelve pieces), rounded per piece to the
  currency, and converted at the invoice date if the invoice is in another
  currency. A distributor can fix the amount on the product (the fee its
  supplier paid), in the classification's currency.
* **Frozen once posted.** Later tariff or weight corrections do not rewrite a
  posted invoice; reset to draft re-prices. Posting re-prices once more on the
  final date and refuses an invoice whose fee has no valid rate.
* **Printed per line**, under the description, in the national wording::

      z toho recyklační příspěvek 100,00 Kč (0,50 Kč/kg × 2,000 kg = 1,00 Kč/ks)
      z toho recyklačný poplatok 3,60 € (0,90 €/ks)

  plus *"bez DPH"* when the line's price includes VAT, and
  *"= 60,00 Kč, kurz 25,0000 CZK/EUR"* for a foreign-currency invoice; and a
  total row *"Recyklační příspěvek celkem bez DPH"* / *"Recyklačný poplatok spolu
  bez DPH"*. OCA's English "Eco Part" column and total are suppressed on such
  documents.
* **Portable batteries** — untick *Show on Documents*: the fee is computed, kept
  in the price and reported, and never printed.
* **Period report** (Accounting → Reporting → Recycling Fees): pivot / list /
  graph of pieces, kilograms and fee per country, category, classification and
  collective scheme, from posted customer invoices and credit notes (credit
  notes negative), in the scheme's currency. *Print → Recycling Fees (XLSX)*
  exports the selection summed per category, with the invoice lines on a second
  sheet.
* **Categories** — the six EEE categories of Directive 2012/19/EU Annex III
  (CZ příloha č. 1, SK príloha č. 6) and the five battery categories of
  Regulation (EU) 2023/1542 are created as ``account.ecotax.category`` records.
  Tariffs are **not** shipped: they are each scheme's price list, and differ
  between schemes and contracts.

Configuration
=============

1. Accounting → Configuration → Ecotax → Classification: one classification per
   tariff line of your scheme; set *Scheme Country*, *Category*, *Collector* (the
   scheme), per piece / weight based, *Domestic* (household) or *Professional*,
   and the dated rates. For portable batteries untick *Show on Documents*.
2. On each product: add the classification(s) on the Accounting tab, and the
   weight in kg if any classification is per kg.
3. Invoicing settings → *Recycling Fee*: included (default) or on top.

Design decision: build on OCA ``account_ecotax``
================================================

``account_ecotax`` (Akretion, AGPL-3, on OCA 19.0) already has what is not
country-specific: a classification per tariff line (fixed or weight based,
household/professional, category, sector, collector), several classifications
per product and per variant, a sub-line per document line holding the fee, the
sale-order side (``account_ecotax_sale``) including the SO → invoice hand-over,
and the "fee included in the price" model. Rebuilding that would duplicate a
maintained OCA module for no gain.

What it lacks is exactly the CZ/SK part, and each gap is an extension, not a
rewrite: dated rates (one static amount only), a scheme country and currency, a
per-piece quantity that respects the unit of measure, a frozen posted document,
the prohibition on disclosing portable-battery fees, the statutory per-line
wording, and a declaration report. That is this module.

Consequence to be aware of: the module sits on third-party AGPL code, so it can
only ever be distributed under AGPL — it cannot be dual-licensed into the
proprietary Enterprise line the way a module we wholly own can.

Limitations
===========

* The rate is chosen by the **invoice date**. § 73 odst. 2 ties the amount to
  what was paid when the producer *placed the item on the market*; a distributor
  selling old stock across a tariff change should fix the amount on the product.
* Rates are not shipped; enter your scheme's price list.
* The report is built from customer invoices. Placing on the market is the
  statutory trigger; if goods are delivered in one period and invoiced in
  another, reconcile in the declaration. Intra-EU sales and exports are included
  and have to be filtered out where the scheme does not count them.
* The on-top mode generates the separate lines on the **sales order** (button
  *Update Recycling Fee*); invoices created without an order get the per-line
  statement only.
* Tyres (CZ § 99) work the same way technically but no tyre category is shipped.
* Translations of the UI strings into Czech and Slovak are not done yet; the
  statutory phrases are verbatim in the source and need none.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>
* Built on ``account_ecotax`` by Akretion and the Odoo Community Association.

License: AGPL-3.0 or later (see the LICENSE file).
