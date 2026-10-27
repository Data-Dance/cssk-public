---
title: CZ/SK Corporate Income Tax Return
summary: The screen on which the corporate income tax return (DPPO) is prepared — the accounting result from the books, the accountant's adjustments, the tax computation, a schema-checked XML file and the year-end tax entry.
verified: 19.0.1.5.7
---

## What it is for {#purpose}

A company's income tax return starts from the profit or loss in its books and
then adjusts it for tax: expenses the law does not accept are added back,
income that is not taxed is taken out, a tax loss from earlier years is
deducted, and only then is the tax computed. This module gives that work one
record per tax period — the **income tax return** — and does the parts that
are arithmetic:

- the **accounting result** (profit before income tax) is summed from the
  posted journal items of the period;
- the **adjustments** are typed in by the accountant, row by row;
- the rows that are pure arithmetic over other rows are recomputed;
- the return is exported as XML and checked against the official schema of
  the form, then marked as filed.

This module is the shared part. It contains no form of its own: the rows,
the rules and the XML layout come from the country module —
[module:l10n_sk_dppo](module:l10n_sk_dppo) for the Slovak *daňové priznanie k
dani z príjmov právnických osôb* and
[module:l10n_cz_dppo](module:l10n_cz_dppo) for the Czech *přiznání k dani z
příjmů právnických osob* (DPPDP9). Install one of those; this module comes
with it. Without a country module the menu exists but there is no form
version to choose.

## The return, step by step {#usage}

*Accounting → Reporting → Statutory Reports → Income Tax (DPPO)*, then *New*.

1. **Header.** Choose the period (*Date From*, *Date To*), then the
   **Version** — the edition of the official form (*vzor* / *tiskopis*). The
   list offers only versions of the company's fiscal country that are valid
   for some part of the period. Then the **Statement Type**: ordinary,
   corrective or supplementary return, as the country module names them.
   Save. If no version covers the period — typically because the authority
   has not yet published the form for that year — a warning says so as soon
   as the dates are entered, and the return cannot be saved.
2. **Compute.** Fills the *Lines* tab and moves the return to *Preview*.
   Each row shows its kind:

   | Kind | Where the value comes from |
   |---|---|
   | Accounting result (P&L) | The balance of the listed accounts over the period, posted entries only. |
   | Asset book-vs-tax depreciation difference | The difference between accounting and tax depreciation for the period, read from the tax depreciation module `account_asset_tax` when it is installed; 0 otherwise. |
   | Aggregate | A formula over other rows, recomputed every time. |
   | Manual | Entered by you. |

3. **Enter the adjustments.** In the row, tick **Override** and type the
   amount in *Manual Value*. The same works on a computed row when you need to
   correct it. Then click **Compute** again: overridden rows keep your
   amount, and every row that depends on them is recomputed from it. A manual
   row without an override is reset to 0 on every compute, so always tick the
   box.
4. **Check the figures.** For a row computed from accounts, the magnifier
   button **Documents** lists the journal items behind it, grouped by account,
   and the ✓ column says whether they still add up to the row. If they do not
   — typically because entries were posted after the last compute — the
   header shows a red **Unreconciled rows** button; when everything ties out
   it shows a green **Rows tie out**. The *Derivation* column shows the
   formula of a computed row, or *manual input*.
5. **Export XML.** Renders the file, checks it against the official schema
   (XSD) stored on the form version, and attaches it to the return; the state
   becomes *Exported*. If the schema rejects the file, or the company has
   neither a *Tax ID* nor a Slovak *DIČ*, nothing is attached and the message
   says why. A version without a schema refuses to export at all.
6. **File the return** on the tax authority's portal, then click **Mark
   Submitted**. The exported file is frozen as the filed copy, the date is
   recorded, and the state becomes *Submitted*. **File it** opens a delivery
   record for the filing, where the receipt (*potvrdenie* / *potvrzení o
   podání*) can be kept; one is opened automatically when you mark the return
   submitted.

A submitted return cannot be deleted. **Reset to Draft** reopens it — only
for an Accounting administrator — and keeps every filed copy: each filed file
stays listed on the return even after a new one replaces it.

## Corrective and supplementary returns {#amendments}

On a submitted return, **Amended / corrective** creates a new draft return
linked to it (*Amends*), carrying over the original's lines and your
overrides as the starting point. Change its *Statement Type* to the
corrective or supplementary type, correct what changed, and compute it
again. The country module fills the rows that compare the two returns where
its form has them (on the Slovak return, the *posledná známa daň* and the
difference rows).

## The year-end tax entry {#provision}

Once the return is computed, the block **Income-tax provision (591/341)**
shows the tax the form version designates as the bookable tax (the Slovak
row r1050, the Czech row ř. 340), and **Post tax provision** books it:

- debit the income tax expense account (the first account whose code starts
  with **591**), credit the income tax liability (the first starting with
  **341**);
- dated on the last day of the period, in the journal chosen in the block or
  else the company's first miscellaneous journal. The two accounts can also
  be chosen in the block (*Tax expense account*, *Tax payable account*) when
  the chart has none under 591 and 341.

This is the current income tax (*splatná daň z príjmov* / *daň z příjmů
splatná*) that closes the profit and loss statement and the balance sheet of
the year. **Reverse provision** cancels it with a reversing entry. The button
appears only when the tax is above zero and only on form versions that
designate a tax row.

## Limitations {#limitations}

- **The tax adjustments are yours.** The module computes the accounting
  result and the arithmetic; it does not decide which expenses are
  non-deductible or which income is exempt.
- The accounting result counts **posted** entries only. Recompute after the
  last closing entries are posted.
- The tax entry books the **full** tax of the return. On a supplementary
  return, book the difference yourself: posting again would book the tax
  twice.
- The tax entry looks up its accounts by code prefix (591, 341). If the chart
  has no such account, choose them in the block.
- There is no screen for the form versions, their rows or rates. Changing
  them requires an administrator with technical access.
- Filing itself happens on the authority's portal; *Mark Submitted* only
  records it.
