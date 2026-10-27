---
title: CZ/SK VAT Return — Shared Engine
summary: The screens and the workflow behind the Slovak and Czech VAT returns — compute the rows from tax tags, check them against the journal items, export the official XML and keep the filed copy.
verified: 19.0.1.11.0
---

## What it is for {#purpose}

This module is the common engine of the VAT return (*daňové priznanie k DPH*
in Slovakia, *přiznání k DPH* in the Czech Republic). On its own it files
nothing: the form itself — its rows, the official XML schema and the
country's rules — comes from
[module:l10n_sk_vat_return](module:l10n_sk_vat_return) or
[module:l10n_cz_vat_return](module:l10n_cz_vat_return). What this module adds
is everything the two share:

- the **VAT Return** screen, where a return is created, computed, reviewed,
  exported and marked as filed;
- the **form versions** (*vintages*) that say which rows, which XML template
  and which XSD apply to which periods;
- an evaluator that sums posted journal items by their **tax tags**, so it
  works the same on Community and Enterprise without Odoo's report engine;
- a drill-down from every row to the journal items behind it;
- the retained filed copy, amendments, and historical tax rates for imports.

## Before the first return {#setup}

- **The company** needs its VAT number (*Tax ID*) — the export refuses to run
  without it — and its tax office: *Accounting → Configuration → Settings*,
  field **Tax Authority**, or the same field on the company form.
- **The country module** must be installed. It brings the form versions,
  which the engine needs to compute anything.
- **Access.** Accounting users can create, compute and export returns.
  Only Accounting administrators can edit form versions and **reset a filed
  return to draft**.

## Preparing a return {#usage}

*Accounting → Reporting → Statutory Reports → VAT Return*, then *New*.

| Field | What to enter |
|---|---|
| Company | The filing company (defaults to the current one). |
| Date From / Date To | The first and last day of the tax period. |
| Period Type | *Monthly* or *Quarterly* — written into the XML as the month or the quarter of *Date From*. |
| Version | The form vintage. The list offers only versions of the company's fiscal country valid in the period; see [Form versions](#versions). |
| Statement Type | Regular, corrective or supplementary — the choices come from the version. |

Then click **Compute**. The return moves to *Preview* and its **Lines** tab
fills with one row per line of the form.

**Which documents belong to the period.** The two sides of the return are
dated differently, as the law dates them:

- **Customer invoices and credit notes** count in the period of their
  **taxable supply date** (*Taxable Supply Date*); without one, their
  accounting date decides.
- **Vendor bills and everything else** count in the period of their
  **accounting date**, because that is the usual period in which the
  deduction is claimed. A journal entry with a taxable supply date follows
  that date instead.
- Where a document records a **VAT period declared** (a field added by the
  localisation core), that date wins on either side — for a deduction claimed
  later than the supply, or a correction declared in the period the
  corrective document arrived.

Only posted entries with tax tags are read.

## Reviewing the lines {#lines}

Each row has a code (the form's own, e.g. `r03` or `obrat23`), a name and a
**Value**. A row is one of three kinds:

- **tax tags** — the signed sum of the balances of journal items carrying the
  row's tags. The ✓ column says whether the drill-down adds up to the value,
  and **Documents** opens those journal items grouped by document;
- **aggregate** — a formula over other rows (shown greyed, with the formula in
  *Derivation*);
- **manual** — a figure the journal cannot supply (a carried-forward excess
  deduction, a coefficient, a difference against an earlier return). It is 0
  until you enter it.

To enter or correct a figure, tick **Override** on the row, type the
**Manual Value** and press **Compute** again. Overridden rows are highlighted,
keep their value on every recompute, and feed the aggregate rows that depend
on them.

The header shows **Rows tie out** when every tag row reconciles with its
journal items, or a red **Unreconciled rows** button listing those that do
not. A row that collects only its share of a tag (a country-specific split,
such as the Slovak § 69 ods. 3 rows before 2021) drills into, and reconciles
against, that share only.

## Settlement and the excess deduction {#settlement}

The **Settlement** tab follows an excess deduction (*nadmerný / nadměrný
odpočet*) from one period to the next:

| Field | Meaning |
|---|---|
| Previous period | The return of the preceding period. |
| Excess deduction from prior period | What the previous return carried forward; **Carry excess deduction** fills it (and *Previous period*) from that return. |
| Excess deduction to carry forward | The part of this period's excess deduction you do not have refunded; it cannot exceed the excess deduction of the period. |
| To pay / (refund) | Own tax − excess deduction − carried in + carried out; positive is tax to pay, negative a refund. |

The fields can be changed while the return is a draft or a preview. Which
rows are the own tax and the excess deduction is set by the country's form
version; the tab does not change any row of the form itself.

## Exporting the XML {#export}

**Export XML** (from *Preview* or *Exported*) runs, in this order:

1. a check that the company has a VAT number;
2. the content checks the country module defines (*kontrolné pravidlá*);
   an error stops the export with the rule named;
3. rendering of the version's XML template;
4. validation against the version's official XSD. A version without a schema
   refuses to export rather than produce an unvalidated file.

The file is attached to the return (*Xml Attachment*) and the return becomes
*Exported*. You can recompute and export again as often as needed until it is
marked submitted.

## Filing and the filed copy {#submission}

File the XML on the tax authority's portal, or through a channel module such
as [module:l10n_cz_epo](module:l10n_cz_epo). Then:

- **Mark Submitted** freezes the exported XML as the filed copy, adds it to
  the **Filed history**, stamps the date and posts a note in the chatter. It
  also opens a delivery record in draft — the place where the portal's receipt
  belongs. Its state shows in the header as **Delivery**.
- **File it** opens (or creates) that delivery record. With several channels
  installed you choose one; with only the manual channel it records who filed
  it on the portal and holds the receipts.
- A submitted return is locked: it cannot be recomputed, exported again or
  deleted. **Reset to Draft** (administrators only) reopens it; the filed copy
  and the history are kept.

## Corrections and supplementary returns {#amendments}

On a submitted return, **Amended / corrective** creates a new draft linked to
it (*Amends*), carrying over its manual overrides. On the new return:

1. choose the right **Statement Type** — the copy starts with the original's;
2. fill in the **Difference identification date**, which the form requires on
   a return that amends another (it defaults to today);
3. correct the accounting, **Compute**, review, export and file as usual.

What the country form needs beyond that (for example the Slovak difference
row) is described on the country page.

## Form versions {#versions}

*Accounting → Configuration → CZ/SK Localization → VAT Return Versions* lists
the vintages the country modules ship. Each one holds its validity dates, the
rows with their tag formulas or aggregate formulas, the submission types, the
XML template and the XSD. They are data maintained by the country module:
change them only on an accountant's instruction. An archived version still
appears on returns for its own periods, so archiving only tidies the list.

## Historical VAT rates {#historic-rates}

When a company loads the Slovak or Czech chart of accounts (and when the
country module is installed), the rates that were in force before today's are
generated as **archived** taxes, cloned from today's tax of the same kind so
they report on the same rows. They exist for importing older documents; they
never appear when you raise a new invoice. Find them under *Accounting →
Configuration → Taxes* with the filters *Archived* and **Historical rate**;
the tax form shows **Rate In Force From**, **Rate In Force Until** and
**Derived From**. Which rates are generated is listed on the country page.
To generate them for a company again (it is safe to repeat), an accounting
manager opens the company under *Settings → Companies* and runs **Create
historical VAT rates** from the *Action* menu.

When a historical rate exists, other localisation modules use it to tax a
document at the rate in force on its date.

## Historical filings {#legacy}

A return imported from a previous system is a **Historical filing**: a record
of what was filed, marked with a ribbon. It cannot be recomputed, exported or
submitted. Its one action, **Compare with computed**, recomputes the period
from the books and records the differences under *Accounting → Reporting →
Statutory Reports → Filed vs computed*. To correct such a period, create an
amendment from it; the amendment is an ordinary return.

## Limitations {#limitations}

- The version is not chosen for you: pick it on each return. The dates are not
  checked to form a whole month or quarter. *Period Type* is checked only
  against the periods the version allows (every shipped version allows both).
- A rate check that only warns (an implied rate that matches no statutory
  rate) is written to the server log and is not shown on screen; only errors
  stop the export.
- The ✓ column compares absolute amounts, so a sign error does not show
  there.
- An amendment copies the original's statement type; nothing changes it for
  you.
- The engine computes what the tags say. A tax with wrong tags, or a document
  posted without tags, reaches the wrong row or none; review the
  **Documents** drill-down before filing.
