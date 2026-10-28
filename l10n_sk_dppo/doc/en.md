---
title: SK Corporate Income Tax Return (DPPO)
summary: The Slovak corporate income tax return — every official form edition since 2013, the accounting result from the books, the tax computation with the rate and minimum tax of the year, and an XML file checked against the Financial Administration's schema.
verified: 19.0.1.4.7
---

## What it is for {#purpose}

Every Slovak company files the *daňové priznanie k dani z príjmov
právnických osôb* (DPPO) once a year. This module supplies that form to the
income tax return screen of
[module:l10n_cssk_income_tax_base](module:l10n_cssk_income_tax_base), whose
guide describes the common workflow — creating a return, computing it,
overriding rows, exporting, marking it filed and posting the tax. This page
covers what is Slovak:

- the rows of each official form edition (*vzor*) from 2013 to 2025, with the
  Financial Administration's schema (XSD) for each;
- **r100**, the accounting result before tax, computed from the books;
- the **tax computation** from r100 to the tax payable, with the rate and the
  minimum tax of the year, on the editions where the module computes it;
- the rows of a supplementary return (*dodatočné priznanie*);
- with [module:l10n_sk_fs](module:l10n_sk_fs) installed, a check that r100
  agrees with the financial statements (see [below](#zavierka)).

The tax adjustments themselves — which expenses are not deductible, which
income is exempt, the loss carried forward — are the accountant's entries.

## Legal background {#legal}

References are to the [Income Tax Act](law:sk/2003/595). Statutory terms are
given in Slovak, as on the form.

- **Starting point.** A taxpayer keeping double-entry books starts from the
  *výsledok hospodárenia* —
  [§ 17 ods. 1 písm. b)](law:sk/2003/595#paragraf-17.odsek-1.pismeno-b). That
  is row r100.
- **Rate.** For a legal entity
  [§ 15 písm. b) bod 1](law:sk/2003/595#paragraf-15.pismeno-b.bod-1) taxes
  the base reduced by the tax loss at **10 %** if its taxable income
  (*zdaniteľné príjmy (výnosy)*) for the period does not exceed 100 000 €,
  **24 %** if it exceeds 5 000 000 €, and **21 %** otherwise. Under
  [§ 52zzzb ods. 4](law:sk/2003/595#paragraf-52zzzb.odsek-4) these rates
  apply first to a tax period beginning on or after 1 January 2025. For 2024
  the wording then in force set 15 % up to 60 000 € and 21 % above.
- **Minimum tax.**
  [§ 46b ods. 2](law:sk/2003/595#paragraf-46b.odsek-2) sets a *minimálna
  daň* by taxable income: 340 € up to 50 000 €, 960 € up to 250 000 €,
  1 920 € up to 500 000 € and 3 840 € above. It is halved for an employer of
  enough disabled employees
  ([ods. 3](law:sk/2003/595#paragraf-46b.odsek-3)), charged as 1/12 per
  month for a period shorter than twelve months
  ([ods. 6](law:sk/2003/595#paragraf-46b.odsek-6)), and not charged in the
  cases of [ods. 7](law:sk/2003/595#paragraf-46b.odsek-7), such as the first
  period of a new company. A minimum tax paid above the computed tax can be
  credited in the next three periods
  ([ods. 5](law:sk/2003/595#paragraf-46b.odsek-5)). For tax periods
  beginning on or after 1 January 2026 the wording in force adds a fifth band
  of 11 520 € above 5 000 000 €
  ([§ 52zzzj ods. 5](law:sk/2003/595#paragraf-52zzzj.odsek-5)).
- **The earlier *daňová licencia*.** Until 2017, § 46b set a *daňová
  licencia* of 480 €, 960 € or 2 880 € by VAT status and turnover. Under
  [§ 52zk](law:sk/2003/595#paragraf-52zk) it applied for the last time to a
  period ending on 31 December 2017, or to a fiscal year (*hospodársky rok*)
  ending in 2018.
- **Tax loss.** A tax loss may be deducted over at most five consecutive
  following periods, up to 50 % of the base, or in full for a
  *mikrodaňovník* —
  [§ 30 ods. 1](law:sk/2003/595#paragraf-30.odsek-1). Row r410.
- **Small amounts.** Tax payable computed in the return is not paid if it
  does not exceed 5 € — [§ 46](law:sk/2003/595#paragraf-46).
- **Deadline.** The return is filed, and the tax paid, within three calendar
  months after the end of the period —
  [§ 49 ods. 2](law:sk/2003/595#paragraf-49.odsek-2); a notice to the tax
  office can extend it under
  [§ 49 ods. 3](law:sk/2003/595#paragraf-49.odsek-3).

## Setting it up {#setup}

There are no settings. Before the first return, check the company record
(*Settings → Users & Companies → Companies*), because the header of the XML
is filled from it:

| Company field | Goes to |
|---|---|
| DIČ (from [module:l10n_sk_base](module:l10n_sk_base)), or *Tax ID* without its "SK" if empty | DIČ |
| *Company ID* | IČO |
| Company name | obchodné meno (first 75 characters) |
| Street / ZIP / City / Country | sídlo — the house number is the number at the end of *Street* (*Hlavná 1141/11*); *Street2* is used only when it holds nothing but a number |
| NACE code of the company's contact ([module:partner_nace](module:partner_nace)) | SK NACE (0 when empty) |
| *Právna forma* of the company's contact (`l10n_sk_trade_registry`) | právna forma |

Optional modules that feed the return:

- **`account_asset_tax`** (tax depreciation). Rows **r150** (accounting
  depreciation above tax depreciation, added back) and **r250** (tax
  depreciation above accounting depreciation, deducted) are then filled
  from the asset tax register. Without it both stay 0 unless you override
  them.
- **[module:l10n_sk_vat_registration](module:l10n_sk_vat_registration).**
  The *daňová licencia* depended on whether the company was a VAT payer on
  the last day of the period. With this module the registration date decides,
  or the registration category when no date is set; without it, or when
  neither is filled in, any company with a *Tax ID* counts as a VAT payer.

## Form editions {#versions}

When you create a return, choose the **Version** for the period. The list
offers every edition whose validity overlaps the period, so a fiscal year
(*hospodársky rok*) spanning two years offers two — choose the one the
Financial Administration prescribes for that period. What the module
computes depends on the edition:

| Version | Periods | Computed by the module |
|---|---|---|
| DPPO 2013, DPPO 2014 | 2013; 2014 | r100 (and r150/r250) only |
| DPPO 2015 | 2015–2016 | tax computation, rate 22 %, *daňová licencia* |
| DPPO 2017, 2018, 2019 | one year each | tax computation, rate 21 %, *daňová licencia* where § 52zk still applies it (see below) |
| DPPO 2020, 2021, 2022 | 2020; 2021; 2022–2023 | r100 (and r150/r250) only |
| DPPO 2024 | 2024 | tax computation, 15 % / 21 %, minimum tax |
| DPPO 2025 | 2025 | tax computation, 10 % / 21 % / 24 %, minimum tax |

On the editions marked "r100 only" you enter every other row yourself,
including the tax.

On the 2018 and 2019 editions r810 is 0 unless the period is a fiscal year
(*hospodársky rok*) ending in 2018: [§ 52zk](law:sk/2003/595#paragraf-52zk)
abolished the *daňová licencia* for every later period. The rows stay on
those forms because a licencia paid for 2015–2017 can still be credited
under § 46b ods. 5; enter that credit yourself.

There is **no edition for 2026 yet.** The Financial Administration had not
published the 2026 form (`dppo2026.xsd`) when this version was checked on
27 October 2026, and the module does not make one up. If you enter a period
that starts in 2026, the return warns that no form version covers it and
cannot be saved. The edition will be added once the form is published.

The rate and the minimum-tax amounts are stored on each edition, not in the
program. An edition whose rate is missing refuses to compute rather than
guess one.

## Computing the return {#usage}

**r100 — výsledok hospodárenia pred zdanením.** The balance of classes 5
and 6 for the period, without income tax (591, 592, 595) and without the
transfer of profit shares to partners (596). Only posted entries count.

**Rows you enter** (tick *Override*, type the amount, compute again):

- the add-backs r110–r180 and the deductions r210–r290, except r150/r250
  when the asset module fills them;
- r302–r308, r320, r330 (the other adjustments of the base) and **r410**,
  the tax loss deducted;
- r501–r503, r610 (tax relief), r710 (foreign tax credit), r1040
  (advance payments), r1060–r1071 (tax on special bases);
- **r560**, taxable income. It defaults to the balance of class 6, which
  includes income that is not taxable; correct it when that differs, because
  both the rate and the minimum tax are chosen from it.

**Rows the module computes** on editions with the tax computation:

| Row | Computed as |
|---|---|
| r200 | r110 + r130 + r140 + r150 + r170 + r180 |
| r300 | r210 + r220 + … + r290 |
| r301 | r100 + r200 − r300 |
| r310 | r301 + r302 + … + r306 − r307 + r308 |
| r400 | r310 − r320 − r330 |
| r500 | r400 − r410, never below 0 |
| r510 | r500 − r501 − r502 − r503 |
| r550 | the rate for r560 |
| r600 | r510 × r550, if r510 is positive |
| r700, r800 | r600 − r610, then − r710 |
| r810 | the minimum tax (or *daňová licencia*) for r560, 1/12 per month for a shorter period |
| r820, r830 | the positive difference between r810 and r800, on the row the edition uses for it |
| r900 | r810, when the minimum tax exceeds the tax |
| r1050 | the higher of r800 and r810 |
| r1080 | r1050 + r1060 + r1070 + r1071 |
| r1100 / r1101 | r1080 − r1040: tax to pay if above 5 €, or the overpayment as a negative amount |

Amounts are rounded half up to cents. A row you override is never
overwritten, so you can take over any of them — the halved minimum tax under
§ 46b ods. 3 or an exemption under ods. 7 is entered by overriding r810.
The credit of minimum tax paid in earlier years (the r830 table and the rows
after it up to r1000) is not computed.

The tax entry described in the
[framework guide](module:l10n_cssk_income_tax_base#provision) books r1050;
it is available on the 2024 and 2025 editions only.

## Supplementary return {#amendments}

Created with **Amended / corrective** from a submitted return (see the
[framework guide](module:l10n_cssk_income_tax_base#amendments)). Set the
*Statement Type* to *Dodatočné*. On compute, the rows of the last known tax
are filled from the previous return and the difference rows as *this return
minus the previous one*:

| Last known | Difference | From |
|---|---|---|
| r1120 | r1130 | r1050, tax or minimum tax |
| r1140 | r1150 | r400, tax loss |
| r1160 | r1170 | r1060, tax under § 17f |
| r1180 | r1190 | r1070, tax under § 51e |
| r1191 | r1192 | r1071, tax under § 51ea |

A chain of supplementary returns works, since each one restates the full
return.

## The XML file {#xml}

**Export XML** produces the *dokument* of the chosen edition and checks it
against that edition's XSD as published by the Financial Administration. It
contains the header — DIČ, IČO, name, registered office, period and the
return type (*riadne / opravné / dodatočné*) — and every row of the body.
It does **not** contain, and you must complete before filing:

- the telephone and e-mail; the SK NACE code and the legal form when the
  company has none (see [Setting it up](#setup));
- the header declarations (e.g. *mikrodaňovník*, the halved or unpaid
  minimum tax, the credit of minimum tax), all written as "no";
- the tables of the form (A to K), the assignment of part of the tax
  (§ 50), the person signing the return, the number of attachments, the
  request for a refund of an overpayment.

The date of the declaration is the day of the export. The § 50 recipient,
the oprávnená osoba and the stála prevádzkareň are left empty — earlier
versions filled them with the company's own IČO, name and address.

The schema accepts the file with these left empty; the tax office will not
accept the return without the parts that apply to you.

## Comparison with the financial statements {#zavierka}

With this module, [module:l10n_sk_fs](module:l10n_sk_fs) and the Slovak
bundle [module:l10n_sk_datadance](module:l10n_sk_datadance) installed, the
bridge [module:l10n_sk_dppo_fs](module:l10n_sk_dppo_fs) installs itself
and adds the button **Porovnať s účtovnou závierkou** to a computed return.
It finds the financial statements (*Účtovná závierka UZPODv14 (SK)*) of the
company covering the return's period — preferring one with exactly the same
dates — and compares r100 with row 56 of the *výkaz ziskov a strát*
(*výsledok hospodárenia za účtovné obdobie pred zdanením*). Both are the
same accounting result, so they must agree to within 0.50 €;
a difference means the two filings disagree, usually because of an overridden
r100 or a different period.

The result is stored as a comparison on the return — the *Comparisons*
button opens it — and is kept separately from any other comparison of the
same return. If no financial statements exist for the period, the button
says so and compares nothing.

## Limitations {#limitations}

- **2026 is not covered** until the Financial Administration publishes the
  2026 form (see [Form editions](#versions)). The 2025 edition does not know
  the 11 520 € minimum-tax band that applies to periods beginning on or after
  1 January 2026; do not file a 2026 period on it.
- **2013, 2014 and 2020–2023** compute r100 only; the tax is yours.
- r560 defaults to the whole of class 6; on the 2015–2019 editions, which
  have no r560, the *daňová licencia* band is chosen from class 6 too.
- The tables and declarations listed under [The XML file](#xml) are not
  produced.
- Most body rows are labelled only with their number; read them against the
  official form and its instructions (*poučenie*).
- The row definitions and the tax computation should be reviewed by your
  accountant before the first filing.
