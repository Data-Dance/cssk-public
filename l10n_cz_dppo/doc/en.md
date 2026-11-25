---
title: CZ Corporate Income Tax Return (DPPDP9)
summary: The Czech corporate income tax return — row 10 from the books, the accountant's adjustments, the tax computation of Part II, and an EPO file checked against the Financial Administration's schema, with the balance sheet and profit and loss statement filed inside it.
verified: 19.0.1.8.0
---

## What it is for {#purpose}

A Czech company files the *přiznání k dani z příjmů právnických osob*
(form DPPDP9) once a year. This module supplies that form to the income tax
return screen of
[module:l10n_cssk_income_tax_base](module:l10n_cssk_income_tax_base), whose
guide describes the common workflow — creating a return, computing it,
overriding rows, exporting, marking it filed and posting the tax. This page
covers what is Czech:

- the rows of **Part II** (*II. oddíl*, the computation of the tax), from
  row 10 to row 340;
- **row 10**, the accounting result before tax, computed from the books;
- the header of the return — its kind, the tax period, the taxpayer type;
- the **balance sheet** (*Rozvaha*) and the **profit and loss statement**
  (*Výkaz zisku a ztráty*) filed inside the return, taken from
  [module:l10n_cz_fs](module:l10n_cz_fs);
- the XML file for the EPO portal, checked against the official schema.

## Legal background {#legal}

References are to the [Income Taxes Act](law:cz/1992/586) unless stated
otherwise. Statutory terms are given in Czech, as on the form.

- **Starting point.** A taxpayer that keeps accounts starts from the
  *výsledek hospodaření* (profit or loss) —
  [§ 23 odst. 2 písm. a)](law:cz/1992/586). That is row 10.
- **Rate and rounding.** The rate is **21 %** for periods beginning on or
  after 1 January 2024 and **19 %** for earlier ones — the rate in force on
  the first day of the period (zákon č. 349/2023 Sb.,
  čl. XVI bod 1) — and the tax is the rate
  times the base reduced by the deductible items, rounded down to whole
  thousands of CZK — [§ 21 odst. 1](law:cz/1992/586); the rounding is also
  stated in [§ 20 odst. 11](law:cz/1992/586).
- **Tax loss.** A tax loss may be deducted in the five periods following the
  one for which it was assessed, or in the two preceding ones —
  [§ 34 odst. 1](law:cz/1992/586).
- **Donations.** The value of donations for the purposes listed in the law
  is deducted from the base already reduced under § 34 —
  [§ 20 odst. 8](law:cz/1992/586).
- **Tax period.** [§ 21a](law:cz/1992/586) names four kinds: a) calendar
  year, b) fiscal year (*hospodářský rok*), c) the period from the decisive
  day of a merger or division, d) an accounting period longer than twelve
  months.
- **The statements filed with the return.** An entity that is not required
  to have its statements audited may draw them up in the abridged scope
  (*zkrácený rozsah*) —
  [§ 18 odst. 4 of the Accounting Act](law:cz/1991/563). The accounting
  currency may be CZK or, as the functional currency, EUR, USD or GBP —
  [§ 24a of the Accounting Act](law:cz/1991/563).

## Setting it up {#setup}

There are no settings. Before the first return, check the company record,
because the header of the file is filled from it:

| Company field | Goes to |
|---|---|
| *Tax ID* (DIČ), without the `CZ` prefix | DIČ |
| Company name | short name (first 20 characters) |
| *Tax Authority* (*Finanční úřad*, from [module:l10n_cz_statutory](module:l10n_cz_statutory)) — its submission code | the tax office the return is addressed to |
| *Tax Office (CZ)* — its workplace code | the territorial office (*územní pracoviště*) |
| *NACE (main activity)* (from [module:partner_nace](module:partner_nace)) | CZ-NACE |

## The return {#usage}

When you create a return, the only **Version** is *DPPDP9*, valid from
1 January 2021 with no end date: the Finanční správa files every period in
the current structure, which accepts periods from 2021. The **Statement Type** is one of *Řádné*,
*Opravné*, *Dodatečné* or *Dodatečné-opravné*.

**Header** (block *Druh přiznání*, editable until the return is exported):

| Field | Meaning |
|---|---|
| Typ daňového přiznání | Why the return is filed: *A – za zdaňovací období* (the default) or one of the special cases — entering liquidation, before a merger, before a change of the tax period, and so on. |
| Zdaňovací období (§ 21a) | Filled from the dates: a calendar year is a), another twelve-month period b), a longer one d). Set c) yourself for the period from a merger's decisive day; a shorter period keeps what you set. |
| Typ poplatníka | *1 – ostatní* by default; change it for a non-resident, a public-benefit taxpayer, an investment fund and the like. |
| Důvody zjištěny dne | Shown and required for a *Dodatečné* or *Dodatečné-opravné* return: the day the reasons for it were found. |

**Rows:**

| Row | Kind | Computed as |
|---|---|---|
| ř. 10 Výsledek hospodaření před zdaněním | from accounts | class 6 minus class 5, without 591, 592, 593, 595, 599 (income tax) and 596 (profit share transferred to partners) |
| ř. 50 Rozdíl, o který účetní odpisy převyšují daňové | from the asset register | accounting depreciation minus tax depreciation of the year, where it is positive; see [below](#depreciation) |
| ř. 20–63 bez ř. 50 (ostatní položky) | entered | the other items increasing the result, as one figure |
| ř. 70 Mezisoučet — zvýšení VH | computed | the row above + ř. 50 |
| ř. 150 Rozdíl, o který daňové odpisy převyšují účetní | from the asset register | tax depreciation minus accounting depreciation of the year, where it is positive |
| ř. 100–162 bez ř. 150 (ostatní položky) | entered | the other items reducing the result, as one figure |
| ř. 170 Mezisoučet — snížení VH | computed | the row above + ř. 150 |
| ř. 200 Základ daně | computed | ř. 10 + ř. 70 − ř. 170 |
| ř. 230 Odečet daňové ztráty | entered | the tax loss deducted |
| ř. 240 Odečet podle § 34 ve znění do 31. 12. 2004 | entered | the old § 34 odst. 3–10 and 12 deductions; normally empty |
| ř. 242 Odečet na podporu výzkumu a vývoje | entered | § 34 odst. 4, § 34a–34e |
| ř. 243 Odečet na podporu odborného vzdělávání | entered | § 34 odst. 4, § 34f–34h |
| ř. 250 Základ daně snížený o položky podle § 34 | computed | ř. 200 − ř. 230 − ř. 240 − ř. 242 − ř. 243, never below 0 |
| ř. 260 Odečet bezúplatných plnění (§ 20 odst. 8) | entered | donations actually deducted, within the statutory cap |
| ř. 270 Základ daně zaokrouhlený | computed | ř. 250 − ř. 260, rounded down to whole thousands |
| ř. 280 Sazba daně | computed | 21 (19 for a period beginning before 2024), if ř. 270 is above 0 |
| ř. 290 Daň | computed | ř. 270 × ř. 280 % |
| ř. 300 Slevy na dani (§ 35) | entered | tax credits |
| ř. 310 Daň po slevách | computed | ř. 290 − ř. 300 |
| ř. 340 Celková daňová povinnost | computed | ř. 310 |

Apart from ř. 50 and ř. 150, you enter the items of rows 20–63 and 100–162
as one figure each; the individual items behind them are not on the screen
and are not filed. The tax entry
described in the [framework guide](module:l10n_cssk_income_tax_base#provision)
books ř. 340.

## Balance sheet and profit and loss statement {#statements}

The return can carry the financial statements inside the file, as the form
allows. First compute and review the *Rozvaha* and the *Výkaz zisku a
ztráty* for the same period (*Accounting → Reporting → Statutory Reports →
Balance sheet* and *Income statement*, from
[module:l10n_cz_fs](module:l10n_cz_fs)). Then, in the return's block
*Financial statements filed with the return*, link both:

- **Rozvaha** — a balance sheet of the company with the same end date;
- **Výkaz zisku a ztráty** — a profit and loss statement with exactly the
  same period.

The export then files them in the scope of the linked statements — full
(*plný rozsah*, `uv_rozsah` P) when both are full-scope versions, abridged
(*zkrácený rozsah*, Z) when both are abridged — under
Decree 500/2002 Sb., in thousands of CZK (rounded half away from zero), with
the prior-period column: the assets with gross, adjustment (*korekce*) and
net amounts, the liabilities and the profit and loss statement (by nature)
with current and prior figures. Every row of the filed scope is filled
from the row of the statement with the same designation; the account
mapping is the one in `l10n_cz_fs`, not a second one.

The export refuses, with a message naming the problem:

- only one of the two statements linked — link both or neither;
- one statement in full scope and the other abridged — the form states one
  scope for both, so compute both in the full scope (always allowed) or both
  abridged;
- a statement of another company, of another kind, or of another period;
- a statement not yet computed, or computed on a version that lacks a row
  the form needs;
- a balance sheet version that does not keep *korekce* separately, or a row
  whose *korekce* is negative (a debit balance on an accumulated
  depreciation or allowance account — correct the booking);
- an accounting currency other than CZK, EUR, USD or GBP.

With no statements linked, the return is exported without them, and a note
in the chatter reminds you to attach the financial statements to the filing
as an attachment (*E-příloha*) instead.

## Handing the statements to the commercial register {#registry}

A company (*obchodní korporace*) may hand its financial statements to the
collection of documents (*sbírka listin*) of the commercial register
through the income tax return instead of filing them with the registry
court: [§ 21b of the Accounting Act](law:cz/1991/563). The tax office passes
them on, and the duty to publish is met when the return is filed (§ 21b
odst. 6). The request is the form *Žádost o předání účetní závěrky do sbírky
listin veřejného rejstříku* (25 5404/I), filed in the return as the record
`VetaUZ`.

On the return, group **Sbírka listin (§ 21b zákona o účetnictví)**:

| Field | What it does |
|---|---|
| Účetní závěrka nebyla schválena / nebyla ověřena auditorem | Tick where the figures come from statements not yet approved by the general meeting, or not yet audited. Filed in the header whether or not you ask for the handover. |
| Předat účetní závěrku do sbírky listin | Adds the request to the file. |
| Předat Rozvahu, Předat Výkaz zisku a ztráty | The scope of the request (§ 21b odst. 3). Both are ticked by default; untick the Výkaz zisku a ztráty where the company does not publish it (a small or micro unit with no audit duty, § 21a odst. 9). The statements handed over are the ones [linked to the return](#statements). |
| E-mail pro potvrzení | Where the tax office confirms the handover. Optional. |
| Příloha účetní závěrky, Přehled o peněžních tocích, Přehled o změnách vlastního kapitálu | Files you upload; each goes into the return as a prescribed e-attachment and is part of the request. |

The attached files are filed with the return even without the request: the
notes are part of the statements attached to every return.

The export refuses a request the tax office would not pass on: one that
names the Rozvaha or the Výkaz zisku a ztráty while no statements are
linked, one that names nothing, a malformed e-mail, a file of a type EPO
does not take (DOC, DOCX, RTF, XLS, XLSX, PDF, JPG, JPEG, TXT, CSV, or one of
them signed or zipped) and files of more than 10 240 kB together. A request
without the notes is exported, with a reminder in the return's history.

## Comparing with the financial statements {#compare}

The return starts from the accounting result: ř. 10 (*výsledek hospodaření
před zdaněním*) is the same figure as the row *\*\* Výsledek hospodaření před
zdaněním* of the *Výkaz zisku a ztráty*. Once the return is computed, the
button **Porovnat s účetní závěrkou** checks that.

It takes the profit and loss statement linked to the return; with none
linked, a computed statement of the company for exactly the same period (the
most recent one, drafts and cancelled ones aside). The comparison screen
then shows ř. 10, the statement's figure and the difference. A difference
means the two filings disagree on the accounting result. The usual causes:
ř. 10 entered by hand, an entry posted after the statement was computed
(recompute it), or a row of the statement whose accounts were edited.

The button only reports; it does not stop the export.

## Accounting and tax depreciation: ř. 50 and ř. 150 {#depreciation}

The return states the difference between the depreciation of tangible and
intangible assets claimed in the books and the depreciation under § 26 to 33
of the Income Tax Act on one of two rows: ř. 50 where the accounting
depreciation is higher (the difference increases the result), ř. 150 where
the tax depreciation is higher (it reduces it). Never both. This is the
instruction to the two rows in the Financial Administration's *Pokyny*
25 5404/1 and in the EPO schema.

With the tax depreciation register installed
([module:account_asset_tax](module:account_asset_tax) with
[module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax)) the
two rows are filled when the return is computed:

- **tax depreciation** is the tax plan's amount for the calendar year of
  every asset of the company that has a plan;
- **accounting depreciation** is the depreciation of the same assets posted
  in the period. Draft depreciation entries do not count, so post the year's
  depreciation first.

Both rows are filed (`kc_ii60_50`, `kc_ii170_150`) and are part of the
subtotals ř. 70 and ř. 170. To file a different figure, tick *Override* on
the row and type it. Without the register both rows are 0 and you type the
difference the same way.

Returns computed before version 19.0.1.7.0 keep the subtotal you typed on
ř. 70 or ř. 170: the tax base does not change when the module is upgraded.
Such a return carries a note. Check whether your typed subtotal already
contains the depreciation difference; to have the subtotal computed, clear
*Override* on ř. 70 / ř. 170, type the remaining items on the *ostatní
položky* row and compute again.

## Limitations {#limitations}

- **The register request is not checked by EPO from here.** The file
  validates against the schema; the portal's own checks run when you load
  it. The request is for companies that keep accounts under Decree
  No. 500/2002 Sb. and do not publish through the Czech National Bank;
  statements under international standards (`pr11_uzmus`) are not filed.
  The notes, the cash-flow statement and the statement of changes in equity
  are files you prepare outside Odoo.
- **ř. 50 and ř. 150 are computed for calendar-year periods only.** The tax
  plan is kept by calendar year, so for a hospodářský rok or any period that
  crosses a year end both rows stay 0, the return says so in its history,
  and you type the difference.
- **Only assets with a tax plan count.** Accounting depreciation of an asset
  that has no tax plan (for example one depreciated in the books only) is
  not in ř. 50; add it to the *ostatní položky* row or override ř. 50.
- A subtotal typed on ř. 70 or ř. 170 must equal its rows (the *ostatní
  položky* row plus ř. 50 or ř. 150); the export refuses one that does not,
  because the file would carry rows that do not add up.
- The difference between the tax and the accounting residual value of an
  asset sold or scrapped (ř. 40 / ř. 160) is not computed.

- **Donations are not capped.** Enter on ř. 260 the amount actually
  deducted: at most 10 % of ř. 250, or 30 % for periods ending between
  1 March 2022 and 28 February 2027 (as the row instruction in the Financial Administration's EPO schema states). The
  module subtracts what you enter.
- **Amounts entered on ř. 240 before version 19.0.1.3.1 are not moved.**
  That row used to stand for research and development, vocational training
  and donations together; split such an amount onto ř. 242, ř. 243 or
  ř. 260 and compute again.
- Only Part II is produced, and only the rows above. Its other rows (for
  example 201, 210, 220, 241 and 251) and every attachment table of the form
  (depreciation by group in table B of annex 1, tax loss, credits, foreign tax and so on) are not; the
  schema accepts the file without them.
- Periods beginning before 2021 cannot be entered; the structure does not
  accept them. For 2021–2024 the rows above are filed as they are; a row that
  differed in an older wording of the form is yours to check.
- The micro scope (M) is not filed; a micro entity can link abridged
  statements. The C.II.3. / C.III. placement of accruals is not filed either:
  the statements use D.
- Each row is rounded to thousands on its own, so where many small items are
  involved a total can differ by a thousand or two from the sum of its
  rounded items; check such totals before filing.
- The header codes (kind of return, taxpayer type) and the full set of
  adjustments should be confirmed with your accountant before the first
  filing.
