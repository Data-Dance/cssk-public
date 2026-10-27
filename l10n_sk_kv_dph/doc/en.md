---
title: SK VAT Control Statement (KV DPH)
summary: The Slovak kontrolný výkaz DPH — sections A.1 to D.2 computed from the books, checked against the form's requirements and exported as the Finančná správa XML in the form version in force for the period.
verified: 19.0.2.4.0
---

## What it is for {#purpose}

A Slovak VAT payer files a **kontrolný výkaz DPH** (VAT control statement)
for every period for which it files a VAT return. It lists invoices one by
one — issued and received — so that the tax administration can match each
supplier's output tax against its customer's deduction.

This module is the Slovak part of the shared control statement. It adds the
Slovak sections, the rules that decide which section a document belongs to,
the checks the official form needs and the XML templates for every form
version since 2014. The workflow — creating a statement, computing, exporting,
marking it filed, corrections — is described in
[the shared guide](module:l10n_cssk_kv_kh_base#usage).

It requires Odoo's Slovak chart of accounts (`l10n_sk`) and works in
Community and Enterprise.

## Legal background {#legal}

All references are to the [VAT Act](law:sk/2004/222). Statutory terms are
given in Slovak, as on the form.

- **Who and when.** A payer must file the kontrolný výkaz electronically for
  every tax period for which it files a VAT return, within 25 days after the
  end of the period —
  [§ 78a ods. 1](law:sk/2004/222#paragraf-78a.odsek-1). No statement is due
  for a period whose return reports no supplies at all, or only supplies
  exempt under § 43 or § 47 with no deduction other than import VAT.
- **What it contains.** [§ 78a ods. 2](law:sk/2004/222#paragraf-78a.odsek-2)
  sets the breakdown: data from every invoice the payer was obliged to issue
  for taxable supplies, including the domestic reverse charge under § 69
  ods. 12 písm. f) to j) (sections A.1, A.2); data from received invoices
  where the payer is liable as recipient, or where it deducts tax charged by
  another payer (B.1, B.2); corrections of invoices (C.1, C.2); and other
  taxable supplies (D.1, D.2).
- **Which invoices must be issued.** The obligation to invoice exists towards
  another taxable person or a legal person —
  [§ 72 ods. 1 písm. a)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-a).
  Supplies to private individuals are therefore not itemised: they go into
  the totals of section D.
- **Reverse-charge goods.** For goods under
  [§ 69 ods. 12](law:sk/2004/222#paragraf-69.odsek-12) písm. f) and g)
  (cereals and technical crops of chapters 10 and 12; metals of chapter 72 and
  headings 7301, 7308, 7314) the statement also carries the first four digits
  of the customs tariff code and the quantity
  ([§ 78a ods. 5](law:sk/2004/222#paragraf-78a.odsek-5)); for písm. h) and i)
  (mobile phones, integrated circuits) the kind and quantity of goods.
- **Simplified invoices** (receipts) are reported as totals of the base, tax
  and deducted tax. When the deducted tax from simplified invoices reaches
  **3 000 eur** in a period, the totals must be broken down by supplier —
  [§ 78a ods. 6](law:sk/2004/222#paragraf-78a.odsek-6).
- **Section D.** Supplies recorded in an **eKasa** cash register are reported
  as total turnover by rate (D.1); other supplies not itemised elsewhere as
  totals of base and tax by rate (D.2) —
  [§ 78a ods. 8](law:sk/2004/222#paragraf-78a.odsek-8).
- **Corrections.** An error found before the filing deadline is corrected by
  an **opravný** kontrolný výkaz, which replaces the original. An error found
  after the deadline is corrected by a **dodatočný** kontrolný výkaz, which
  carries only the added or corrected data —
  [§ 78a ods. 12](law:sk/2004/222#paragraf-78a.odsek-12). A request from the
  tax office to remedy a filed statement must be answered within five working
  days ([§ 78a ods. 13](law:sk/2004/222#paragraf-78a.odsek-13)).
- **Penalties.** Not filing, filing late, or filing incomplete or incorrect
  data can be fined up to 10 000 eur, and up to 100 000 eur when repeated —
  [§ 78a ods. 15](law:sk/2004/222#paragraf-78a.odsek-15).
- **The form.** The layout (*vzor*) is set by a regulation of the Ministry of
  Finance and the statement is filed as XML following the data interface the
  Financial Directorate publishes; a statement delivered otherwise is
  disregarded — [§ 78a ods. 16](law:sk/2004/222#paragraf-78a.odsek-16).

## Form versions {#forms}

The Slovak tax administration publishes a separate XSD for every *vzor* and
keeps the old ones. A period is filed in the *vzor* that was in force for
that period, so a dodatočný statement for 2022 still uses the 2016 form. The
module ships all four, each as a version record with its own template and
schema:

| Version | Periods | XML root | Schema | Difference |
|---|---|---|---|---|
| KV DPH 2014 | 1. 1. 2014 – 31. 3. 2016 | `KVDPH` | `kv_dph_2014.xsd` | a single section B.3 for all simplified invoices |
| KV DPH 2016 | 1. 4. 2016 – 30. 6. 2023 | `KVDPH_2016` | `kv_dph_2016.xsd` | B.3 split into B.3.1 and B.3.2 |
| KV DPH 2023 | 1. 7. 2023 – 31. 12. 2024 | `KVDPH_2023` | `kv_dph_2023.xsd` | same sections, new root and namespace |
| KV DPH 2025 | from 1. 1. 2025 | `KVDPH_2025` | `kv_dph_2025.xsd` | same sections, new root and namespace |

When you create a statement, only the version valid for its period is
offered. The four schemas were checked byte for byte against the copies
published by the Finančná správa on 19 August 2026. A schema file does not say
when it was revised, so a later revision of a published file is not detected
automatically.

## Setting it up {#setup}

Besides the [shared setup](module:l10n_cssk_kv_kh_base#setup):

- **Reverse-charge taxes.** On installation the module marks the Slovak
  chart's reverse-charge purchase taxes — domestic reverse charge, intra-EU
  acquisitions of goods and, with [module:l10n_sk_vat_return](module:l10n_sk_vat_return),
  services received from the EU — and creates for each Slovak company a sales
  tax **0 % Prenos daňovej povinnosti (§69 ods. 12, A.2)**. Use that tax on
  invoices for § 69 ods. 12 supplies; it is what puts them into A.2.
- **Customers' identification.** Whether an issued invoice is itemised in A.1
  or summed in D.2 depends on whether the customer is a taxable person. Odoo
  has no such field, so the module treats a customer with an IČ DPH (*Tax
  ID*) **or** an IČO (*Company ID*) as a business and anyone else as a private
  individual. Fill in the IČO of domestic business customers, including
  sole traders, or their invoices will be summed in D.2.
- **§ 69 ods. 12 goods.** On the product form, *Accounting* tab, block
  **Kontrolný výkaz DPH**: set *Tovar podľa § 69 ods. 12 (KV DPH A.2)* to
  písm. f), g), h) or i) for such goods, and for f) and g) the *Číselný kód
  tovaru (KV DPH)*. Without that code the product's customs (HS / Intrastat)
  code is used, if one of the modules that provide it is installed. The code
  must fall into the chapters the Act names for that category. Invoice these
  goods in kilograms, tonnes, metres or pieces — the only units the form
  accepts. Leave the field empty for the other § 69 ods. 12 supplies, such as
  construction work under písm. j), for which A.2 carries only the base.
- **Simplified invoices.** On a vendor bill, tick *Zjednodušená faktúra
  (KV DPH B.3)* next to the bill date for receipts and other simplified
  invoices. A received document without a partner is treated the same way.
- **eKasa registers (D.1).** On the journal that records the sales of an
  eKasa cash register, open *Advanced Settings* and set **Control-statement
  section override** (block *VAT control statement*) to `D.1`. Every VAT line
  of that journal is then reported as eKasa turnover in D.1 instead of D.2.
  Invoices issued to businesses should go through an ordinary sales journal,
  so that they still reach A.1.

## Sections {#sections}

How the module fills each section. A document with several VAT rates gives
one row per rate.

| Section | What goes there |
|---|---|
| A.1 | Issued invoices with Slovak VAT at a non-zero rate, to a customer with an IČ DPH or IČO. Zero-rated and exempt supplies (exports, § 28–42) are left out. |
| A.2 | Issued invoices with a reverse-charge sales tax (§ 69 ods. 12). For goods of písm. f)–i): the commodity code or kind of goods, quantity and unit. |
| B.1 | Received invoices with a reverse-charge purchase tax: domestic reverse charge, intra-EU acquisitions of goods, services received from the EU. |
| B.2 | Other received invoices with VAT, under the **supplier's** invoice number (*Bill Reference*). |
| B.3.1 / B.3.2 | Received simplified invoices: one total in B.3.1 while the tax **deducted** from them in the period is below 3 000 eur ([§ 78a ods. 6](law:sk/2004/222#paragraf-78a.odsek-6)); from 3 000 eur deducted, totals per supplier in B.3.2. A receipt deducted at 50 % counts half. Up to March 2016, one total in B.3. |
| C.1 | Credit notes and debit notes (*ťarchopisy*) issued to customers that are taxable persons, with the corrected invoice's number. A debit note reports a positive difference. |
| C.2 | Credit notes and debit notes received, with the corrected invoice's number; also corrections of deducted tax under § 53b recorded with `l10n_sk_par53b`. |
| D.1 | eKasa turnover: the VAT lines of journals whose control-statement section is set to `D.1` (see [Setting it up](#setup)). |
| D.2 | Taxable supplies to customers with neither IČ DPH nor IČO (or with no partner), and their credit notes: totals of base and tax at the basic rate (20 % and more) and at the reduced rates. |

Outside the statement altogether: intra-EU supplies (they belong in the EC
sales list), and supplies to an EU customer **without** Slovak VAT on them. A
supply to an EU customer on which Slovak VAT is charged — a private person,
typically — is a domestic supply and is reported in A.1 or D.2.

**Dates and amounts.** The supply date (*Den*) is the *Taxable Supply Date*,
else the invoice date; for a tax due on payment, the payment date. The
deducted tax (*Odpočítaná daň*) on B.1, B.2, C.2 and B.3 is the part of the
tax its repartition sends to the VAT account: a vehicle tax that deducts 50 %
reports half. A § 50 coefficient is honoured the same way only if it is set
in the tax's repartition.

A debit note counts as a correction when it is raised with Odoo's **Debit
Note** button (module `account_debit_note`), which links it to the invoice it
corrects.

**Correcting a row by hand.** Every section tab except D.2 has an
**Override** toggle on its rows. Tick it and the amount columns become
editable; the corrected amounts survive a recompute and are re-applied to the
row with the same identity. D.2 files its rate-band columns, which are not
overridable.

## Filing types and corrections {#usage}

The statement types are **Riadny** (R), **Opravný** (O) and **Dodatočný** (D).
Prepare and export the statement as in the
[shared guide](module:l10n_cssk_kv_kh_base#usage). Slovak specifics:

- **Opravný** before the deadline: create it from the filed statement with
  *Dodatočný / opravný*, choose *Opravný* and compute. It contains the full
  list, as the original did.
- **Dodatočný** after the deadline: the same button, type *Dodatočný*. On
  compute the module compares the fresh result with the last known full state
  of the period and keeps only the differences: a new or changed row is
  reported with *kód opravy* 2, and the original values of a changed or
  removed row with *kód opravy* 1. Unchanged rows are dropped. A second
  dodatočný statement compares against the state after the first, so chained
  corrections stay consistent.

Before rendering, the export stops and names the documents at fault when:

- a row in A.2, B.2 or B.3.2 has no IČ DPH of the counterparty, or one that is
  not Slovak (these sections take only `SK` + 10 digits);
- a document number is longer than the 32 characters the form allows (spaces
  are removed automatically; the number is not shortened, because the tax
  administration matches it against the supplier's own filing);
- a row in A.1, A.2, B.1 or B.2 has no supply date;
- a C.1 or C.2 row has no number of the corrected invoice (enter it as
  *Original document number* on the credit note; on a vendor credit note the
  *Source Document* is read too, unless it names a purchase order);
- an A.2 row of písm. f) or g) goods has no commodity code or one outside the
  statutory chapters, or a row of § 69 ods. 12 goods has a unit that converts
  to none of kg, t, m, ks.

The XML carries the company's IČ DPH, name and address, the filing type and
the period (year and month, or year and quarter).

## Limitations {#limitations}

- **D.1 (eKasa) is not derived from the documents.** Only journals set to
  `D.1` report there; any other point-of-sale or cash-register sale without
  an identified business customer is reported in **D.2**.
- **Debit notes** reach C.1 / C.2 only when linked to the invoice they
  correct (the *Debit Note* button). One raised as a plain invoice is still
  reported in A.1 / B.2.
- The A.1 / D.2 split relies on the IČ DPH or IČO being recorded on the
  partner. A business customer without either is summed in D.2; the export
  logs a warning for D.2 customers marked as companies or previously reported
  in A.1, but the warning is not shown on screen.
- Triangular trade and the self-assessment of import VAT are not marked as
  reverse charge, pending an accountant's confirmation, so they do not appear
  in B.1.
- The 5 000 eur invoice threshold that applies to mobile phones and integrated
  circuits under § 69 ods. 12 písm. h) and i) is not checked; set the product
  category only on goods that qualify.
- The `ONP` attribute of C.1 / C.2 (correction of an uncollectible receivable,
  available from the 2023 form) is never filled.
- The section rules are a best effort; the § 69 ods. 12 goods list and D.1 in
  particular still need confirmation by a Slovak accountant. Review each
  statement before filing.
