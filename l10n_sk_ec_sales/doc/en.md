---
title: SK EC Sales List (Súhrnný výkaz)
summary: The Slovak EC sales list — súhrnný výkaz — computed from the intra-EU supply taxes of Odoo's Slovak chart and exported as Finančná správa XML in the vzor in force for the period.
verified: 19.0.1.4.0
---

## What it is for {#purpose}

A Slovak VAT payer that supplies goods or services to customers identified for
VAT in another EU member state reports them on the **súhrnný výkaz** (*EC sales
list*, SV), filed electronically with the Financial Administration
(*Finančná správa*).

This module is the Slovak layer of
[module:l10n_cssk_ec_summary_base](module:l10n_cssk_ec_summary_base), which
holds the screens and the workflow — preparing the list, reviewing lines,
exporting and filing are described [there](module:l10n_cssk_ec_summary_base#usage).
This module adds the Slovak transaction codes, the XML templates and official
schemas of both vzory, a check of the codes and VAT prefixes, and codes the
standard taxes of Odoo's Slovak chart.

## Legal background {#legal}

All references are to [§ 80 of the VAT Act](law:sk/2004/222#paragraf-80).
Statutory terms are given in Slovak.

- **Who files.** A payer that supplied goods exempt under § 43 ods. 1 to a
  person identified for VAT in another member state, transferred its own goods
  exempt under § 43 ods. 4, took part in a triangular trade as the first
  customer (*prvý odberateľ*, § 45), supplied a service with its place of
  supply in another member state under § 15 ods. 1 for which the customer pays
  the tax, or dispatched goods under call-off stock
  ([§ 80 ods. 1](law:sk/2004/222#paragraf-80.odsek-1)). A person registered
  under § 7 or § 7a files for each calendar quarter in which it supplied such
  a service ([ods. 3](law:sk/2004/222#paragraf-80.odsek-3)).
- **Monthly or quarterly.** The rule is a calendar month. A quarterly list is
  allowed if the value of goods (ods. 1 písm. a) to c)) does not exceed
  **50 000 eur** in the quarter and in each of the previous four quarters; once
  it does, the payer files separately for each month of that quarter
  ([ods. 2](law:sk/2004/222#paragraf-80.odsek-2)).
- **Which period, which amount.** Supplies are reported for the period in
  which the tax liability arose, in euros, rounded to whole euros — below
  0.5 down, from 0.5 up ([ods. 6](law:sk/2004/222#paragraf-80.odsek-6)). A
  correction of the taxable amount under § 25 is reported, as the amount of the
  correction, for the period in which it was notified to the customer
  ([ods. 7](law:sk/2004/222#paragraf-80.odsek-7)).
- **Corrections.** Before the filing deadline an error is corrected by an
  **opravný súhrnný výkaz**; after it, by a **dodatočný súhrnný výkaz**,
  *"v ktorom uvedie len doplnené alebo opravené údaje"* — listing only the
  added or corrected data ([ods. 8](law:sk/2004/222#paragraf-80.odsek-8)).
- **Deadline.** Electronically, **within 25 days** after the end of the
  period ([ods. 9](law:sk/2004/222#paragraf-80.odsek-9)).

On the form, goods are reported **without a code**, a triangular trade with
code **1** and a service with code **2**. Internally the module calls goods
code **0** and writes it as an empty code in the XML.

## Form versions {#version}

The Financial Administration keeps one schema per vzor and keeps the old
ones, so each period is filed in the vzor in force at that time. The module
installs both, and a list is offered only the one valid for its period:

| Version | Valid | Schema | Shape |
|---|---|---|---|
| Súhrnný výkaz 2010 (do 31. 12. 2019) | 1. 1. 2010 – 31. 12. 2019 | `svdph2010.xsd` | 27 records per page |
| Súhrnný výkaz 2020 (od 1. 1. 2020) | from 1. 1. 2020 | `svdph20.xsd` | 12 records + 12 call-off-stock records per page |

The 2020 vzor arrived with the call-off-stock rules in force from
1 January 2020. Both schemas are byte-identical to the copies the Financial
Administration publishes (checked 9 September 2026); neither file states a
revision, so a later change to them cannot be seen from inside Odoo.

Both versions offer the statement types *Riadny*, *Opravný* and *Dodatočný*,
which tick the matching box of *druh súhrnného výkazu* in the XML.

## Setting it up {#setup}

When the module is installed, it sets the transaction code on the intra-EU
taxes of every company that uses the Slovak chart of accounts at that moment,
unless a code is already there:

| Tax of Odoo's Slovak chart (English name / Slovak name) | Code |
|---|---|
| 0% EU M / *0% EÚ T* — supply of goods to the EU | 0 (no code on the form) |
| 0% EU T / *0% EÚ TRI* — triangular trade | 1 |
| 0% EU S / *0% EÚ S* — supply of services to the EU | 2 |

Mind the names: *T* means goods (*tovar*) in the Slovak name but triangular in
the English one.

The export also needs the company's VAT number and the tax office set as
**Default tax authority** — see
[setting up the framework](module:l10n_cssk_ec_summary_base#setup). The
header of the form is filled from the company: name, street and house
number, ZIP, city, phone and e-mail. The house number (*číslo*) is the number
at the end of **Street** ("Hlavná 12" gives *ulica* "Hlavná" and *číslo*
"12"), or the street-number fields where the address is kept split; *Street 2*
is filed as the house number only when it holds nothing but a number.

## Preparing and filing {#usage}

Follow the [shared workflow](module:l10n_cssk_ec_summary_base#usage) at
*Accounting → Reporting → Statutory Reports → EC Sales List*. On top of the
shared checks, the export of a Slovak list refuses:

- a line whose code is other than 0, 1 or 2;
- a line whose customer VAT number does not start with a plausible country
  prefix (an ISO country code, or EL or XI);
- a service (code 2) to a Northern Ireland (XI) number — XI is valid for goods
  only.

The country code (*kód štátu*) is the prefix of the customer's VAT number, as
the poučenie lists it: **EL** for Greece, **XI** for Northern Ireland.

Amounts are rounded to whole euros half away from zero (−9.50 becomes −10),
line by line; the total in the header is the sum of the rounded lines.

There is no electronic channel for Slovak filings in this module: upload the
exported XML on the Financial Administration's portal, then click **Mark
Submitted** — or **File it** to record the manual filing and keep the receipt.
The person making the declaration and the date go on the **Hlavička** tab:
*Meno a priezvisko*, *Telefón* and *E-mail* of the konateľ or authorised
person (the 2010 vzor has no e-mail) and *Dátum vyhlásenia*; left empty, the
date of the export is used.

**A dodatočný súhrnný výkaz lists only what changed**, as
[§ 80 ods. 8](law:sk/2004/222#paragraf-80.odsek-8) asks. On **Compute** the
module compares the recomputed period with what was filed for it — the
statements of the same period marked submitted, or recorded as historical
filings, taken in the order they were filed — and keeps:

- a **new** record, as it is;
- a record whose value (in whole euros, as exported) **changed**, with its
  correct value;
- a record filed earlier that is **gone**, with the value 0.

Unchanged records are left out. A dodatočný výkaz with no filed statement of
its period recorded here is refused: mark the original submitted, or import it
as a historical filing, first. An *opravný* list, which replaces the original
before the deadline, still lists the whole period.

## Limitations {#limitations}

- **A dodatočný výkaz is compared with what is recorded here.** A filing
  made outside Odoo and not recorded as a historical filing is invisible to
  the comparison.
- **Call-off stock** (ods. 1 písm. e) to g)) is not supported; the
  call-off-stock records of the 2020 vzor are always empty.
- **Corrections of the taxable amount** are reported for the period of the
  credit note's taxable supply date or *VAT period declared* — set it to the
  period in which the correction was notified to the customer (ods. 7).
- The 50 000 eur threshold for quarterly filing is not checked.
- A service supplied to a customer who has applied for, but not yet received,
  a VAT number (the last sentence of ods. 6) is not handled; a line without a
  VAT number blocks the export.
- A street that does not end in a number is written whole, with the house
  number empty.
