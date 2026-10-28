---
title: CZ Corporate Income Tax Return (DPPDP9)
summary: The Czech corporate income tax return — row 10 from the books, the accountant's adjustments, the tax computation of Part II, and an EPO file checked against the Financial Administration's schema, with the balance sheet and profit and loss statement filed inside it.
verified: 19.0.1.5.0
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
| ř. 10 Výsledek hospodaření před zdaněním | from accounts | class 6 minus class 5, without group 59 (income tax and transfer accounts) |
| ř. 70 Mezisoučet — zvýšení VH | entered | total of rows 20–63, the items increasing the result |
| ř. 170 Mezisoučet — snížení VH | entered | total of rows 100–162, the items reducing the result |
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

You enter only the subtotals of rows 20–63 and 100–162; the individual
items behind them are not on the screen and are not filed. The tax entry
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

## Limitations {#limitations}

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
  (depreciation, tax loss, credits, foreign tax and so on) are not; the
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
