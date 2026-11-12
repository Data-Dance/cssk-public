---
title: SK Corporate Income Tax Return (DPPO)
summary: The Slovak corporate income tax return — every official form edition since 2013, the accounting result from the books, the tax computation with the rate and minimum tax of the year, and an XML file checked against the Financial Administration's schema.
verified: 19.0.1.11.1
---

## What it is for {#purpose}

Every Slovak company files the *daňové priznanie k dani z príjmov
právnických osôb* (DPPO) once a year. This module supplies that form to the
income tax return screen of
[module:l10n_cssk_income_tax_base](module:l10n_cssk_income_tax_base), whose
guide describes the common workflow — creating a return, computing it,
overriding rows, exporting, marking it filed and posting the tax. This page
covers what is Slovak:

The published MF/014309/2026-721 edition additionally offers an unsigned
official PDF download for the native body, Tables A/B and entered identity
and declarations. See [the paper output](#official-pdf) for its current scope.

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

- **`account_asset_tax`** (tax depreciation). Table B is then filled from
  the asset tax register, and rows **r150** (accounting depreciation above
  tax depreciation, added back) and **r250** (tax depreciation above
  accounting depreciation, deducted) follow from it — see
  [Tables A and B](#tables). Without it Table B stays empty unless you
  enter it.
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
| DPPO 2013, DPPO 2014 | 2013; 2014 | r100 and Tables A/B (r130, r150, r250) only |
| DPPO 2015 | 2015–2016 | tax computation, rate 22 %, *daňová licencia* |
| DPPO 2017, 2018, 2019 | one year each | tax computation, rate 21 %, *daňová licencia* where § 52zk still applies it (see below) |
| DPPO 2020, 2021, 2022 | 2020; 2021; 2022–2023 | r100 and Tables A/B (r130, r150, r250) only |
| DPPO 2024 | 2024 | tax computation, 15 % / 21 %, minimum tax |
| DPPO 2025 | 2025 | tax computation, 10 % / 21 % / 24 %, minimum tax |

On the editions marked "r100 only" you enter every other row yourself,
including the tax.

On the 2018 and 2019 editions r810 is 0 unless the period is a fiscal year
(*hospodársky rok*) ending in 2018: [§ 52zk](law:sk/2003/595#paragraf-52zk)
abolished the *daňová licencia* for every later period. The rows stay on
those forms because a licencia paid for 2015–2017 can still be credited
under § 46b ods. 5; enter that credit yourself.

The published **MF/014309/2026-721** form has a native calculation registry.
Its legal applicability follows the filing deadline; its electronic schema
is a separate publication step (see [the published-form section](#published-2026)).

The rate and the minimum-tax amounts are stored on each edition, not in the
program. An edition whose rate is missing refuses to compute rather than
guess one.

## Computing the return {#usage}

**r100 — výsledok hospodárenia pred zdanením.** The balance of classes 5
and 6 for the period, without income tax (591, 592, 595) and without the
transfer of profit shares to partners (596). Only posted entries count.

**Rows you enter** (tick *Override*, type the amount, compute again):

- the add-backs r110–r180 and the deductions r210–r290, except r130,
  r150 and r250, which come from [Tables A and B](#tables);
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

## Tables A and B {#tables}

Part III of the form itemises two rows of the body: **Table A** (*Položky,
ktoré nie sú daňovými výdavkami*) is the breakdown of r130, **Table B**
(*Odpisy hmotného majetku*) the reconciliation behind r150 and r250. Each
row of both tables is a line of the return, coded by table and row: `a06`
is row 6 of Table A, `b02` row 2 of Table B.

| Line | Content (DPPO 2015 onwards) | Computed as |
|---|---|---|
| a01 – a16 | the items of Table A; a16 = other items | entered |
| a17 | úhrn | a01 + … + a16 |
| b01 | accounting depreciation of tangible assets | asset register, or entered |
| b02 | tax depreciation before b04, without b05 | asset register, or entered |
| b03 | unclaimed part of a leased asset's depreciation (§ 19 ods. 3 písm. a)) | entered |
| b04 | depreciation not claimed because it was suspended (§ 22 ods. 9) | asset register, or entered |
| b05 | proportional depreciation in the year of sale (§ 22 ods. 12) | asset register, or entered |
| b06 | depreciation included in the tax base | b02 − b03 − b04 + b05, never below 0 |
| **r130** | | a17 |
| **r150** | | b01 − b06 when positive |
| **r250** | | b06 − b01 when positive |

The 2013 and 2014 editions have a shorter Table A (a15 is the úhrn of
a01 – a14) and a four-row Table B with the tax depreciation on b01 and the
accounting depreciation on b02; there r150 = b02 − b01 and r250 = b01 − b02,
when positive.

With [module:account_asset_tax](module:account_asset_tax) installed, b01,
b02, b04 and b05 are read from the tax register for assets on a tangible
asset account (anything but 01x). b04 is the charge a suspended year would
have carried, b05 the whole months held in the year of sale for an asset
marked for § 22 ods. 12. b03 is always yours. With b03 at 0, r150 and r250
are the company-wide difference between accounting and tax depreciation, as
before.

Any of these lines can be overridden, the derived ones too. When a table
carries a value, an overridden r130, r150, r250, a17 or b06 must agree with
it: the export refuses a return where they differ, as the Financial
Administration's form does. A return that types r150 straight onto the main
row and leaves Table B empty is exported as before.

In the XML file a table row that nobody filled is left empty.

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
- the tables of the form other than A and B (C to K), the assignment of part of the tax
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

- **The new published form's XML adapter is pending.** Its native calculation
  includes the11,520 minimum band; do not substitute the obsolete2025 XML.
- **2013, 2014 and 2020–2023** compute r100 and Tables A/B only; the tax is yours.
- The meaning of rows 3 and 4 of the 2013/2014 Table B is not stated in
  their instructions; enter them from the form.
- r560 defaults to the whole of class 6; on the 2015–2019 editions, which
  have no r560, the *daňová licencia* band is chosen from class 6 too.
- The tables and declarations listed under [The XML file](#xml) are not
  produced.
- Most body rows are labelled only with their number; read them against the
  official form and its instructions (*poučenie*).
- The row definitions and the tax computation should be reviewed by your
  accountant before the first filing.

## Published MF/014309/2026-721 {#published-2026}

The version list uses the applicable **legal filing deadline**, including an
effective extension entered in *Applicable legal filing deadline*. Leave that
field empty for the ordinary three-calendar-month deadline. A fiscal period
July2025–June2026 ordinarily uses the earlier form; an effective extension to
March2027 requires the new one. December2025–November2026 already requires the
new form without an extension. A late actual filing date changes neither rule.
The minimum-tax top band still depends on when the period began.

The native return supports the published2026 layout for ordinary periods
starting in2026 and later. The announcement applies where the last day of
the filing deadline falls after31December2026, subject to later replacements.
This includes an ordinary2027 first year filed in2028; a name ending26 is
not a legal restriction to filing during2027.

Row310 is now the accountant's section17k adjustment; the former subtotal
moves315. Sports306 shifts the vehicle, practical-training and CFC inputs.
The11,520 minimum above5million applies only to periods starting from2026.
Record any section46b exemption or halving as a reviewed row810 override;
the override then flows into subsequent amounts and the tax provision.

The official paper form and instructions are published. The official XML
adapter is a separate publication step: its schema was not in the reviewed
catalog. Calculation is available; XML export gives an explicit explanation
until the official electronic version is installed. It never emits2025 XML
for the new form. Source hashes and applicability are in
`data/FORM_PUBLICATION.json`.

## Official paper output {#official-pdf}

After computing the return, complete **Official form inputs** and use
**Official form PDF**. Identity comes from the company and the selected native
contact; the form additionally records the legal-form code, SK NACE, authorized
person's entered names and relationship, declaration date and applicable
declarations. A supplementary return requires its actual discovery date.

The download overlays the original 21-page MF/014309/2026-721 template, whose
source and SHA256 are pinned in `static/forms/SOURCES.json`. The body and
Tables A/B use the saved native return rows, including reviewed overrides.
Changed ledger sources or calculation inputs require recomputation. Entered
minimum-tax declarations must agree with row 810 and its period-sensitive
amount. Values exceeding the actual printed boxes are rejected explicitly.

The paper adapter supports the core, A/B and entered Table I/D facts. Nonzero
claims requiring other tables or annexes require their related entered inputs
and adapter before printing; they are never silently omitted. The five
original attached pages are retained, with the same DIČ and counted in the
declaration. Table I continuation pages are counted additionally.

The PDF is an unsigned review/download snapshot. It leaves the tax return in
its current state and does not create XML or mark it filed. An equal snapshot
reuses its attachment; changing identity creates another snapshot and preserves
the exact prior bytes. Electronic filing still needs the published XML adapter.

### Table I entered transactions {#table-i}

On **Official form inputs**, enter each transaction or loan in **Table I**.
Choose a native related contact and enter the published two-digit transaction
code (01–37 for transactions, 01–05 for loans) and the three-digit official
code of the counterparty's tax residence. Classification and significance
remain reviewed accountant facts; the published instruction code list is the
reference. Codes are checked for format/range and never silently truncated.

Transactions record a signed effect, aggregation and a permanent-establishment
link under section 2(r). The effect is a disclosure, including effects in later
periods; it is **not a second posting or an amount to add to row 400**. Loans
record the highest principal during the period and the closing principal. The
closing principal cannot exceed the highest principal. The separate
below-threshold declaration covers only transactions not already aggregated
into an entered row. These facts must agree with the front-page declaration.

The printed original has four transaction rows and five loan rows. More rows
create clearly marked continuation copies of the original Table I pattern,
with continuous ordinals and annex numbers. Each section permits at most
99 rows. Where more facts exist, the accountant must apply the published
reporting priorities and retain the remaining transfer-pricing documentation;
the programme does not silently discard any entered row. Inputs copy with a
native amendment, are scoped to their company and cannot change on an
exported/submitted return without the native reset workflow.

### Table D prior tax losses {#table-d}

Enter the published column, original loss period and amount, prior deductions
and the deduction claimed this period. Ordinary section 30 losses occupy
columns 4–8 in chronological order. The current period's new loss stays in
row 400; it first appears in Table D on a later return. An optional link to
the native original return checks its company, period and negative row 400.
Opening facts can also be entered from reviewed external records.

The following-tax-period number is a reviewed ordinal from 1 to 5, including
short periods. It is not an elapsed-calendar-year calculation. An immediately
following period must be number 1. The remaining balance is calculated from
the original amount less prior/current deductions; after period 5 the unused
balance expires and the future balance is zero. Special incentive columns
1–3 remain entered legal qualifications; a column 1 deduction also requires
its explanation in **Official form special records**.

**Apply reviewed Table D deduction** transfers the sum to the existing native
row 410 override and recomputes the existing tax return. It validates the
newly recomputed base before committing. Ordinary losses have the published
50% limit; a currently qualifying micro-taxpayer can use the full base for
eligible losses starting from 2021. Other qualifications remain reviewed
facts; known contradictory micro declarations are rejected. The total cannot
exceed the positive row 400 or the unconsumed original loss.

Changing Table D facts requires applying them again. Both the PDF and native
tax provision reject a mismatch with row 410. Review other existing manual
inputs before final output. Native provision/reversal
remains the accounting workflow; no second tax ledger is created. All eight
columns and the total are printed across the original pages 7–8. Special
records wrap within the original page 15 field and reject over-capacity text
instead of silently cutting it off.

This bounded adapter is still a review/download path: remaining nonzero
special claims need their adapters before the full
paper filing is complete. Later published form or legal changes require the
normal publication refresh; this edition is not a guarantee of future portal
acceptance.

### Ordinary double-entry Tables F/L and advance tax {#table-fl}

Table F reads operating/financial revenue and costs before income tax from
the existing posted ledger, with the same account exclusions as native row
100. Revenue less costs must equal row 100. For reviewed imported accounting
figures, enter the two source amounts and retain their evidence explicitly.
This is form evidence; it does not create another accounting ledger.

Table L starts with F revenue. Enter every taxable-income adjustment with
its signed amount, description, related three-digit return row and reviewed
classification evidence. The linked net adjustment cannot exceed that
return row's amount. **Apply reviewed Table L revenue** transfers its total
to the existing row 560 override and recomputes the return. Changed facts
must be applied again before PDF output or a provision using these facts.
Zero-adjustment returns still print L1 and L99. All entered adjustments are
printed. The original pattern has 26 slots numbered 2–21 and 23–28, skipping
22. It is preserved: marked continuation copies supply missing row 22, then
29–98, with annex numbers. More than 97 adjustments require reviewing the published
form capacity; none are silently omitted.

For this published edition, row 1110 defaults to row 500 times the row 550
rate, less row 610, before the deductions in rows 501–503. Existing explicit
accountant overrides remain available. Only a reviewed historic relief
under sections 35/35a of Act 366/1999 uses the explicit legacy flag, retained
evidence, a positive row 610 and zero row 1110; the printed field is then
left blank. The flag does not infer legal eligibility.

Table K uses continuous whole-euro rectangles. Amounts and totals above four digits are right-aligned at the ordinary font size when they fit the actual rectangle. Cent digits retain their separate printed cells; an amount wider than the physical field is refused rather than clipped.
