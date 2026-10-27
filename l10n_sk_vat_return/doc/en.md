---
title: SK VAT Return (Daňové priznanie k DPH)
summary: The Slovak VAT return computed from the tax tags of Odoo's Slovak chart, in the form vintage of each period, exported as the Finančná správa XML and validated against its XSD.
verified: 19.0.1.13.0
---

## What it is for {#purpose}

The Slovak layer of the [shared VAT-return engine](module:l10n_cssk_vat_return_base).
It supplies:

- every **vzor** (form vintage) of the *daňové priznanie k dani z pridanej
  hodnoty* published as an XSD since 2012, each with its rows, XML template and
  the official schema;
- the row definitions, wired to the tax tags of Odoo's Slovak chart
  (`l10n_sk`), and the Slovak content checks;
- the difference row of a *dodatočné daňové priznanie* filled from the
  original return;
- purchase taxes for **services received from the EU**, which the stock chart
  lacks;
- a wizard for the **§ 53b correction** of deducted tax on unpaid bills;
- the archived pre-2025 rates (20 % and 10 %) for importing older documents.

How to create, compute, review, export and file a return is described on the
[engine's page](module:l10n_cssk_vat_return_base#usage); this page covers what
is Slovak.

## Legal background {#legal}

References are to the [VAT Act](law:sk/2004/222) unless stated otherwise.

- **Tax period.** The calendar month
  ([§ 77 ods. 1](law:sk/2004/222#paragraf-77.odsek-1)). A payer may choose the
  calendar quarter once more than 12 months have passed since it became a
  payer and its turnover for the preceding 12 consecutive months was below
  EUR 100 000 ([§ 77 ods. 2](law:sk/2004/222#paragraf-77.odsek-2)).
- **Deadline.** A payer established in Slovakia files the return within
  **25 days after the end of each tax period** and pays its *vlastná daňová
  povinnosť* in the same time
  ([§ 78 ods. 2 písm. a)](law:sk/2004/222#paragraf-78.odsek-2.pismeno-a));
  the *vlastná daňová povinnosť* is the positive difference between the tax
  due and the deductible tax
  ([§ 78 ods. 1](law:sk/2004/222#paragraf-78.odsek-1)).
- **Electronic filing.** A VAT payer must deliver its filings to the
  Financial Administration electronically —
  [§ 14 ods. 1 písm. a) of the Tax Procedure Act](law:sk/2009/563#paragraf-14.odsek-1.pismeno-a).
- **Excess deduction.** A *nadmerný odpočet* is offset against the next
  period's own tax liability and refunded if it cannot be
  ([§ 79 ods. 1](law:sk/2004/222#paragraf-79.odsek-1)); a monthly payer that
  meets the conditions of
  [§ 79 ods. 2](law:sk/2004/222#paragraf-79.odsek-2) has it refunded at once
  and marks this in the return
  ([§ 79 ods. 3](law:sk/2004/222#paragraf-79.odsek-3)).
- **Corrective and supplementary returns.** Before the filing deadline a
  payer may replace its return with an *opravné daňové priznanie*
  ([§ 16 ods. 1](law:sk/2009/563#paragraf-16.odsek-1)); after it, a payer that
  finds the tax should be higher or the excess deduction lower must file a
  *dodatočné daňové priznanie* by the end of the month following the discovery
  ([§ 16 ods. 2](law:sk/2009/563#paragraf-16.odsek-2) of the Tax Procedure Act).
- **§ 53b.** A payer must correct deducted tax to the extent it has not paid
  for a domestic supply, in the period in which the 101st day from the due
  date falls ([§ 53b ods. 1 písm. a)](law:sk/2004/222#paragraf-53b.odsek-1.pismeno-a)),
  and may correct the correction in the period it pays
  ([§ 53b ods. 4](law:sk/2004/222#paragraf-53b.odsek-4)).

## Form vintages {#versions}

Finančná správa publishes one XSD per vzor and keeps the old ones, and a
period is filed on the vzor that was in force for it. The module ships one
version per vzor:

| Version (as listed) | Periods | Schema |
|---|---|---|
| DPH (vzor 1. 1. 2012 – 31. 12. 2017) | 2012 – 2017 | `dph2012.xsd` |
| DPH (vzor 1. 1. 2018 – 31. 12. 2019) | 2018 – 2019 | `dph2018.xsd` |
| DPH (vzor 1. 1. 2020 – 31. 12. 2020) | 2020 | `dph2020.xsd` |
| DPH (vzor do 30. 6. 2025) | 1. 1. 2021 – 30. 6. 2025 | `dph2021.xsd` |
| DPH 2025 | from 1. 7. 2025 | `dph2025.xsd` |

All five are the official files, kept byte for byte with their checksums
recorded in the module. On a return, the *Version* list offers the one valid
for the period.

Three things about the vintages are worth knowing:

- **January to June 2025 is filed on the 2021 vzor**, although the rates
  changed on 1 January 2025. The 2021 form has a single reverse-charge row pair
  `r09`/`r10` and two domestic rate bands; the 2025 vzor split them by rate
  (`r01a`, `r09a`, `r09b`, `r11a`–`r11e`, `r18a`, `r23a`–`r23c` …). The 2021
  version therefore collects into each of its rows every tag the later form
  split it into.
- **The 2018 and 2020 schemas are identical**, but the forms are not: row 18
  is the tax on deregistration under § 81 in 2018–2019 and the tax under
  § 48ca, § 48d and § 48e in 2020. They are two versions so that each period
  carries its own meaning; schema validation cannot tell them apart.
- **The 2012–2020 vzory number their rows differently** from 2021 (from row 11
  onwards, by two), and report the reverse charge on services from a foreign
  supplier under [§ 69 ods. 3](law:sk/2004/222#paragraf-69.odsek-3) on rows
  `r11`/`r12`, apart from the other reverse charges on `r09`/`r10`. The Slovak
  chart has one reverse-charge tax family for both, so for those periods the
  module splits them by the **supplier's country**: a supplier outside Slovakia
  goes to `r11`/`r12`, a Slovak one (or one with no country) to `r09`/`r10`.
  A tax used for one paragraph only can say so in **SK § 69 paragraph
  (pre-2021 vzory)** on the tax form (*Advanced Options*, purchase taxes):
  a dedicated domestic-construction prenos tax is *§ 69 ods. 2 a 9 až 12*
  whoever the supplier is.

There is no version for periods before 2012.

## Setting it up {#setup}

Beyond the [engine's setup](module:l10n_cssk_vat_return_base#setup):

- **Company data used in the XML header**: the VAT number (*IČ DPH*; the *DIČ*
  is written as the same number without `SK`), the tax office from **Daňový
  úrad** (its submission code), the name, the street and house number, ZIP,
  city, phone and e-mail. The house number (*číslo*) is the number at the end
  of **Street** ("Mlynská 1234/5" gives *ulica* "Mlynská" and *číslo*
  "1234/5"), or the street-number fields where the address is kept split.
  **Street 2** is never filed as the house number; a street that does not end
  in a number is written whole with *číslo* empty.
- **Service products bought from the EU** need the right vendor tax; see
  [below](#eu-services).

## The Slovak return {#usage}

The statement types are *Riadny*, *Opravný* and *Dodatočný*. Rows `r01` to
`r29` (with their lettered variants on the 2025 vzor) come from the tax tags of
the Slovak chart, which are named after the rows. In addition:

| Row | How it is filled |
|---|---|
| r17 (daň celkom) | Sum of the tax rows. |
| r18, r18a, r19 | The XML carries the **total** deduction per rate. On screen these totals are the rows named *(internal) odpočet — …*; the rows coded `r18`, `r18a`, `r19` show only their own tag. |
| r30, r31 | Manual: deduction at registration, refunds to travellers. |
| r32 / r33 | Computed: own tax liability or excess deduction, whichever the net comes to. |
| r34 | Manual: the excess deduction of the previous period being offset. |
| r35 | Computed: r32 − r34, not below zero. |
| r36 | On a *dodatočný* return, filled on **Compute** as (r32 − r33) of this return minus (r32 − r33) of the return it amends, unless you overrode it. |
| r37 | Manual. |

Rows named *(internal) …* are working rows; they are not boxes of the form.

**Content checks at export.** The export stops if r32 or r33 is negative, if
both are positive, or if r34 is higher than r32. It also checks that each tax
row is its base row times one of the rates valid for the vzor (19, 5 and 23 %
on the 2025 vzor); that check only warns, and the warning goes to the server
log, not to the screen.

**The amended return** carries its *Deň zistenia rozdielu*
(*datumZisteniaDdp*) into the XML only when its type is *Dodatočný*.

## The first page of the form (Hlavička) {#header}

A Slovak return has a **Hlavička** tab, editable while the return is a draft
or a preview:

| Field | What it fills |
|---|---|
| Postavenie osoby | Who files, as ticked on the first page: *Platiteľ dane (§ 4)* (the default), *Osoba registrovaná pre daň podľa § 7 alebo § 7a*, *Iná osoba povinná podať priznanie (§ 78 ods. 3, 4 a 9)*, *Zdaniteľná osoba podľa § 3 ods. 5*, *Daňový zástupca podľa § 69a* or *§ 69aa* (the last only for periods from 1. 1. 2018). |
| Splnenie podmienok § 79 ods. 2 | Tick it when you meet the conditions for a refund of the excess deduction within 30 days. Offered only to a VAT payer with a monthly period, and exported as 1 only when the return shows an excess deduction (`r33`). |
| Dátum vyhlásenia | The date of the declaration; left empty, the date of the XML export is used. |
| Oprávnená osoba | Name, phone and e-mail of a person filing on the company's behalf, for example a representative under § 9 daňového poriadku. Leave empty when the company files itself. |

Odoo cannot check the § 79 ods. 2 conditions (12 months as a payer, arrears
of at most 1 000 €); ticking the box is your declaration.

## Services received from the EU {#eu-services}

Odoo's Slovak chart maps every purchase tax, under the *Eu intra* fiscal
position, to the acquisition of **goods** (rows 07/08), so a service from an
EU supplier lands on the wrong row. This module adds:

- domestic purchase taxes **23% S**, **19% S** and **5% S** (scope Services);
- their EU counterparts **23 % EÚ S**, **19 % EÚ S** and **5 % EÚ S**, which
  self-assess the tax under § 69 ods. 3 on rows 09b/10b, 09/10 and 09a/10a and
  deduct it.

Set the *S* tax as the vendor tax of your service products. On a bill from an
EU supplier the fiscal position then replaces it with the *EÚ S* tax; goods
keep their usual tax and still go to rows 07/08. The taxes are added to every
Slovak company when the module is installed or upgraded, only where missing.

## § 53b correction of deducted tax {#par53b}

*Accounting → Accounting → Oprava odpočítanej dane (§ 53b)* opens a wizard:

| Field | Meaning |
|---|---|
| As of date | The day the overdue period is measured to; the correction entries get this date. |
| Days overdue | Default 100. |
| Denník opráv | A general journal for the entries. |
| Protiúčet (náklad) | The account the corrected tax is moved to, usually 548. |

It lists posted vendor bills, unpaid or partly paid, whose due date is at least
that many days before the date, that deducted tax and have not been corrected
yet. **Vygenerovať opravy** posts one entry per bill: the deducted tax times
the unpaid share, credited to the input-VAT account with the row 29 tag and
debited to the chosen account. Row `r29` of the return picks it up.

Once a corrected bill is paid (fully or in part), the bill shows the button
**Znovu uplatniť odpočet (§ 53b ods. 4)**: it posts the mirror entry for the
paid share, dated today, never more than was corrected. The bill's *Other
Info* tab shows its *Stav § 53b* and the correction entries.

## Historical rates {#historic-rates}

On install and whenever a company loads the Slovak chart, the module creates
the rates no longer in force as archived taxes (see the
[engine's page](module:l10n_cssk_vat_return_base#historic-rates)):

| Rate | In force | Cloned from |
|---|---|---|
| 20 % | 1. 1. 2011 – 31. 12. 2024 | today's 23 % taxes; their reverse-charge tags are moved from 09b/10b back to 09/10, the rows that existed then |
| 10 % | 1. 1. 2007 – 31. 12. 2024 | today's 19 % taxes |

The 19 % standard rate of 2004–2010 is not generated: today's 19 % taxes are
the reduced rate, and a second family with the same name would collide.

## Limitations {#limitations}

- The filer status only sets the box on the first page. The rows are computed
  the same way for every filer: a person registered under § 7 or § 7a has no
  right of deduction, so check that its return shows none.
- The § 79 ods. 2 conditions are declared by you, not verified.
- The *Settlement* tab tracks the carry-forward of an excess deduction for
  the amount to pay, but does not fill `r34`: enter the amount being offset
  on `r34` with **Override**. Rows r30, r31 and r37 are manual too.
- The § 53b wizard dates its entries on the day you choose; run it for the
  period in which the 101st day falls.
- The reduced-rate row mapping of the 2021 vzor (r01/r02 collecting 19 % and
  5 %) is derived from the structure of the forms, not from a filed return;
  have it confirmed before importing a reduced-rate history.
- Nothing is filed from here: export the XML and submit it on the portal of
  Finančná správa, then mark the return submitted.
