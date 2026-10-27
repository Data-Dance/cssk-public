---
title: CZ VAT Control Statement (Kontrolní hlášení)
summary: The Czech kontrolní hlášení (DPHKH1) — sections A.1 to B.3 computed from the books with the 10 000 CZK split, checked against the form's requirements and exported as the EPO XML in the current structure for any period.
verified: 19.0.1.9.1
---

## What it is for {#purpose}

A Czech VAT payer files a **kontrolní hlášení** (VAT control statement)
alongside its VAT returns. It lists the payer's invoices — individually above
10 000 CZK, in totals below — so that the tax administration can match each
supplier's output tax against its customer's deduction.

This module is the Czech part of the shared control statement. It adds the
sections of form **DPHKH1**, the rules that decide which section a document
belongs to, the checks the official form needs and the EPO XML template. The
workflow — creating a statement, computing, exporting, marking it filed,
corrections — is described in
[the shared guide](module:l10n_cssk_kv_kh_base#usage).

It requires Odoo's Czech chart of accounts (`l10n_cz`) and
[module:l10n_cz_statutory](module:l10n_cz_statutory), which holds the filer's
details for EPO filings. It works in Community and Enterprise.

## Legal background {#legal}

All references are to the VAT Act, zákon č. 235/2004 Sb., o dani z přidané
hodnoty. Statutory terms are given in Czech, as on the form.

- **Who must file.** A payer files a kontrolní hlášení for a period in which
  it made a taxable supply in Czechia (or received an advance for one), in
  which it received a supply on which it must declare the tax itself or on
  which it deducts tax charged by another payer, or in which it performed
  certain investment-gold transactions —
  [§ 101c](law:cz/2004/235). The statement contains the payer's
  identification, the data on supplies and advances, the deductions claimed
  and the identification of customers and suppliers —
  [§ 101d](law:cz/2004/235).
- **Electronically, in the prescribed structure.** The kontrolní hlášení must
  be filed electronically; a filing not made in the prescribed manner, format
  or structure is ineffective — [§ 101a](law:cz/2004/235).
- **Deadlines.** A legal person files for each calendar month, within 25 days
  after its end. A natural person files within the deadline for its VAT
  return, so monthly or quarterly according to its tax period. The deadlines
  cannot be extended — [§ 101e](law:cz/2004/235).
- **Corrections.** Before the deadline, a filed statement can be replaced by
  an **opravné** kontrolní hlášení, and the previous one is disregarded. An
  error found after the deadline must be corrected by a **následné**
  kontrolní hlášení within 5 working days of finding it —
  [§ 101f](law:cz/2004/235). The tax office's request to change, complete or
  confirm the data is also answered by a následné hlášení: within 17 days of
  its delivery to a data box, otherwise within 5 working days —
  [§ 101g](law:cz/2004/235).
- **Penalties.** A late statement costs a fixed 1 000 CZK when filed
  unprompted, 10 000 CZK when filed only after a request, 30 000 CZK when a
  request to change or confirm data is not answered, and 50 000 CZK when the
  statement is not filed even after a request; the last three are halved for
  natural persons, quarterly payers and single-member limited liability
  companies whose member is a natural person — [§ 101h](law:cz/2004/235). No penalty arises for the first
  delay of the first or second kind in a calendar year —
  [§ 101j](law:cz/2004/235).

## The form {#forms}

Unlike the Slovak side, the Czech tax administration publishes **one**
structure for the kontrolní hlášení, the file `dphkh1_epo2.xsd`, and
overwrites it in place when it changes. A statement for any period — a
následné hlášení for 2021 filed today included — is submitted in the current
structure. Differences between periods are expressed by fields that apply
only to some periods, not by older forms.

The module therefore ships a single, open-ended version, **Kontrolní hlášení
(aktuální struktura)**, valid from 1. 1. 2016 with no end date:

| | |
|---|---|
| Structure | DPHKH1, version 03.01.15 of 11. 8. 2026 (written as `verzePis`) |
| XML | EPO `Pisemnost` envelope with `DPHKH1` inside |
| Schema | `dphkh1_epo2.xsd`, checked byte for byte against the published copy on 27 October 2026 |
| Earliest period | 1. 1. 2016 — documents with an earlier tax point belong on a different EPO form (*Výpis z evidence*), which this module does not produce |

The structure version is not part of the schema, and a new schema still
validates an old file, so a change published by the tax administration is not
detected automatically. The version is therefore pinned in
`data/SCHEMA_VERSION`, with the procedure for checking it against the
published structure, and a test keeps the template's `verzePis` equal to the
pin. When the published structure changes, the module must be updated.

## Setting it up {#setup}

Besides the [shared setup](module:l10n_cssk_kv_kh_base#setup):

- **Filer's details.** Tax office, territorial office, the person authorised
  to sign and the person who prepared the filing come from
  [module:l10n_cz_statutory](module:l10n_cz_statutory). The XML header
  (*VetaP*) is filled from there.
- **Reverse-charge taxes.** On installation the module marks the § 92a
  reverse-charge purchase taxes of the Czech chart (21 % and 12 %). The
  chart's *0% RC* sales tax is recognised by its VAT-return row (ř. 25), and
  other recipient-liable purchases — EU acquisitions and services, services
  from outside the EU (ř. 12 / 13) — by the supplier's VAT number and the
  tax's row; none of them needs the mark.
- **Kód předmětu plnění.** Sections A.1 and B.1 require the code of the
  reverse-charge supply (gold, real estate, construction work, goods of
  Annex 5, emission allowances and the other codes of the form). Set it on the
  product, field *Kód předmětu plnění (§92a)* under the product category, or on
  the reverse-charge tax, where the field appears for marked taxes. The
  product's code wins over the tax's. A document whose lines carry different
  codes is reported on one row per code, under the same document number.
- **Counterparty DIČ.** A.1, A.4, B.1 and B.2 identify the other party by its
  DIČ; for A.2 the supplier's EU VAT number decides whether a purchase is an
  acquisition from another member state.

## Sections {#sections}

How the module fills each section. Amounts are split into the basic rate
(20 % and more, `zakl_dane1` / `dan1`), the reduced rate (`zakl_dane2` /
`dan2`) and the second reduced rate of 10 % in force until 31. 12. 2023
(`zakl_dane3` / `dan3`, also used for later corrections of such supplies), and
written in whole crowns.

| Section | What goes there |
|---|---|
| A.1 | Issued invoices with a reverse-charge sales tax (§ 92a): customer's DIČ, document number, date of the taxable supply, base (one, whatever the rate), kód předmětu plnění. |
| A.2 | Received supplies on which you declare the tax (§ 108 odst. 2 a 3): acquisitions and services from another member state, and services or other supplies from a supplier outside the EU. Country (as the VAT number gives it: `EL` for Greece, `XI` for Northern Ireland; empty for a supplier outside the EU), VAT number, the supplier's document number, base and tax. |
| A.4 | Issued invoices with VAT whose document total including VAT exceeds 10 000 CZK (by absolute value, so a large credit note too) **and** whose customer has a Czech DIČ. A correction for an uncollectible receivable is always reported here, whatever its amount. |
| A.5 | One total of all other issued invoices with VAT — up to 10 000 CZK, or to a customer without a Czech DIČ. |
| B.1 | Received invoices with a § 92a reverse-charge purchase tax: supplier's DIČ, document number, base, kód předmětu plnění. |
| B.2 | Received invoices with VAT whose document total including VAT exceeds 10 000 CZK, under the **supplier's** number (*Reference faktury*). Corrections for uncollectible receivables always. |
| B.3 | One total of all other received invoices with VAT. |

A supplier from another member state registered for Czech VAT and invoicing
under its CZ number makes a domestic supply: the VAT number on the document,
not the partner's country, decides. A zero-rated issued invoice to a partner
in another member state is left out of the statement (it belongs in the EC
sales list); one that charges Czech VAT is a domestic supply and is reported in
A.4/A.5. An import of goods (§ 23) is not reported in the kontrolní hlášení at
all.

The 10 000 CZK limit is measured on the **whole** document including VAT;
lines without VAT are not reported but still count towards it. A line with no
VAT is never reported in A.4/A.5 or B.2/B.3.

The date reported is the document's *DUZP*, else its invoice date. The
uncollectible-receivable flag (`zdph_44`) is taken from the document's field
*Oprava u nedobytné pohledávky* (`P`, or `A` for the § 44 wording valid to
31. 3. 2019).

The control totals (*VetaC*) are computed from the sections as the form
defines them: A.1 in `pln_rez_pren`, B.1 in `rez_pren23` / `rez_pren5`, all of
A.2 in `celk_zd_a2`, and the reduced-rate totals including the second reduced
rate.

## Filing types and corrections {#usage}

The statement types are **Řádné** (B), **Opravné** (O, *řádné/opravné* on the
form), **Následné** (N) and **Následné/opravné** (E). Prepare and export the
statement as in the [shared guide](module:l10n_cssk_kv_kh_base#usage). Czech
specifics:

- A **následné** hlášení is not a difference against the filing it corrects:
  it repeats all the data of the period with the corrections applied, and the
  module computes it in full. Create it from the filed statement with the
  *Opravné / následné* button, change the type to *Následné* and compute.
- For a následné hlášení fill in **Důvody zjištěny dne** (the day the reasons
  were found) or, when it answers a request, **Č.j. výzvy** (the request's
  reference, in the form `99999999/99/9999-99999-999999`).
- **Odpověď na výzvu** gives the quick answer to a request when nothing
  changes: *B – Nemám povinnost podat KH* or *P – Potvrzuji správnost
  naposledy podaného KH*. Such a filing carries only the header, no sections,
  and needs the č.j. výzvy.

Before rendering, the export stops and names the documents at fault when:

- a row in A.1, A.4, B.1 or B.2 has no DIČ of the counterparty;
- a row in A.1, A.2, A.4, B.1 or B.2 has no date of the taxable supply;
- a row in A.1 or B.1 has no kód předmětu plnění;
- a následné hlášení has neither the discovery date nor the č.j. výzvy, or a
  quick answer has no č.j. výzvy.

To send the file to EPO from Odoo, see [module:l10n_cz_epo](module:l10n_cz_epo).

## Limitations {#limitations}

- **EU suppliers charging Czech VAT.** A received invoice from a partner
  whose VAT number is from another member state goes to A.2 even when the
  supplier charged Czech VAT. If the supplier is registered here, invoice it
  through a contact whose Tax ID is its CZ number, and the document is reported
  in B.2.
- **Fixed values.** The special schemes for travel services and used goods
  (`kod_rezim_pl`) are never indicated — every A.4 row is written as an
  ordinary supply — and the proportional deduction under § 75 (`pomer`) is
  always written as *N*.
- The section rules are a best effort; the § 92a code list and the
  uncollectible-receivable corrections in particular still need confirmation
  by a Czech accountant. Review each statement before filing.
