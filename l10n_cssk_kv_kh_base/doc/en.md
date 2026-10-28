---
title: CZ/SK VAT Control Statement
summary: The screens and the engine shared by the Slovak kontrolný výkaz DPH and the Czech kontrolní hlášení — sections computed from posted documents, checks before export, an XSD-validated XML file and a record of what was filed.
verified: 19.0.2.4.0
---

## What it is for {#purpose}

Slovakia and Czechia both require VAT payers to file, alongside the VAT
return, a document-by-document statement of their invoices: the Slovak
**kontrolný výkaz DPH** (KV DPH) and the Czech **kontrolní hlášení** (KH).
The forms differ, but the work is the same — sort every posted document that
carries VAT into the form's sections, check it, produce the official XML and
keep the filed copy.

This module is that common part: the *VAT Control Statement* menu and form,
the assignment of a section to each journal item, the drill-down to the source
documents, the export pipeline and the filing record. On its own it files
nothing. The country module supplies the sections, the decision rules and the
official XML:

- [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph) — Slovak KV DPH,
- [module:l10n_cz_kh](module:l10n_cz_kh) — Czech kontrolní hlášení.

The legal background, the form versions and the section-by-section rules are
described on those pages. It does not use Odoo Enterprise's report engine, so
it works the same in Community and Enterprise.

## Setting it up {#setup}

Install the country module; this one comes with it. Then check:

- **The company's VAT number** (*Tax ID*) is filled in. Every export carries
  it as the filer's identification and refuses to run without it.
- **Reverse-charge taxes are recognised.** The section rules decide on a flag
  on each tax, *Reverse charge* (*Prenos daňovej povinnosti* /
  *Přenesení daňové povinnosti*). The country module sets it on the
  reverse-charge taxes of Odoo's Slovak or Czech chart of accounts — when it is
  installed, whenever a chart is loaded for a new company, and on upgrade. On
  a reverse-charge tax you create yourself, tick **Reverse charge** on the tax
  form (*Advanced Options*), shown for Slovak and Czech taxes.
- **A journal for one section.** A journal can send all its VAT lines to one
  section, ahead of the rules: *Advanced Settings* tab of the journal, block
  *VAT control statement*, field **Control-statement section override** —
  the section code as the form prints it, e.g. `D.1` for the journal of a
  Slovak eKasa cash register. Leave it empty on ordinary journals.
- **Partners carry their VAT numbers.** Most detail sections identify the
  counterparty by its VAT number, and the export names every document whose
  partner lacks one where the form requires it.

Two configuration lists sit under
*Accounting → Configuration → CZ/SK Localization*:

| Menu | What it holds |
|---|---|
| Control Statement Versions | One record per official form structure: validity dates, the sections it contains, the XML template and root element, the official XSD the export is validated against, and the value threshold that splits detail rows from aggregates. Shipped by the country modules; there is normally nothing to change. |
| Control Statement Types | The kinds of filing per country (Slovak *riadny / opravný / dodatočný*, Czech *řádné / opravné / následné / následné/opravné*) and the code each writes into the XML. |

## How documents reach a section {#sections}

Every posted journal item that carries a tax is given a control-statement
section when it is posted. The country module's rules decide which; the
common behaviour is:

- **Invoices and credit notes** take their direction (supplied or received)
  from the document type. A **journal entry** carrying VAT is classified by its
  taxes when they all point the same way (all sales or all purchase taxes);
  a mixed entry is left out.
- **Reverse charge is tested first**, so a self-assessed supply never falls
  through to the ordinary sections.
- **Taxes based on payment** (*Tax Exigibility: Based on Payment*) are
  reported when the payment makes them due, not when the invoice is posted.
  The row describes the invoice — its partner and number — but carries the
  payment's date and amount, one row per payment. A payment that is
  un-reconciled within the same period cancels out.
- **Which period.** Supplies made are reported in the period of their
  *Taxable Supply Date*, or of the accounting date where there is none.
  Received documents are reported in the period in which the deduction is
  claimed: the accounting date, or a later period recorded on the document
  (*VAT period declared*). This is the same rule the VAT return modules use,
  so the two agree on what a period contains.
- **Credit notes.** A credit note created from its invoice is linked to it,
  and the statement reports the original's number from that link. For a
  credit note created by hand, enter the corrected document's number in
  *Original document number* (*Other Info* tab), shown only on a Czech or
  Slovak company's credit notes that have no link.
- **Journal entries carrying VAT** can declare what their type cannot: on the
  entry's *Other Info* tab, **VAT direction** (supplied or received) and **VAT
  correction** (whether it is a credit note / correction). With *VAT
  correction* set to *Correction*, *Original document number* appears too.
  Leave both empty on invoices.
- **Per line**, the journal items list of a document has two optional
  columns: **Control-statement section** (the stored section) and
  **Control-statement VAT**, which replaces the partner's VAT number for one
  line (a foreign branch with its own number).

A section is stored on the journal item. If documents are changed in a way the
rules cannot see — a company's fiscal country changed, for instance — the
stored sections must be recomputed by an administrator; recomputing the
statement alone is not enough.

## Preparing and filing a statement {#usage}

*Accounting → Reporting → Statutory Reports → VAT Control Statement*, then
*New*.

1. Fill in the **company**, the **period** (*Date From*, *Date To*) and
   whether it is a **monthly or quarterly** filing; then pick the **version**
   (only versions valid for the period are offered) and the **statement type**.
   A period the version does not allow (its *Allow Monthly* / *Allow
   Quarterly*) is refused.
2. Click **Compute**. The sections are filled from the posted documents of the
   period and the statement moves to *Preview*. Each section has its own tab.
   You can compute again as often as needed while the statement is in draft or
   preview; every compute rebuilds the sections from the books.
3. **Review.** The ✓ column shows whether the journal items behind a row add
   up to the row's base and tax. The **Documents** button on a row opens those
   journal items, grouped by document, with the base, rate, VAT and VAT
   deducted of each — the last two differ where only part of the tax is
   deductible, such as fuel at 50 %. Aggregate rows list all the documents they
   summarise. Correct a wrong row on the document and compute again. Where a
   country module offers it (the Slovak sections except D.2), a row can also be
   corrected in the statement: tick **Override** and edit its amounts; the
   correction survives a recompute and is re-applied to the row with the same
   identity, and one whose row disappeared is reported in the chatter.
4. Click **Export XML**. Before anything is rendered the export checks:
   - the company's VAT number and the master data the official form requires
     (the country module names the documents at fault);
   - content rules: a detail row whose tax is not base × rate stops the export
     when it is off by a factor of two or more, and a taxable row with a base
     but no tax stops it always. Smaller differences (rounding) and other
     warnings do not stop it: they are listed in a yellow banner at the top
     of the statement and in the chatter until the next export.

   The XML is then validated against the official XSD held on the version and
   attached to the statement (*Xml Attachment*). The statement is now
   *Exported*. You can export again after recomputing.
5. **File the XML** with the tax authority, then click **Mark Submitted**. The
   filed copy is frozen (*Filed XML*, *Submitted Date*), added to the filing
   history, and the statement is locked against recompute and export.
6. Marking it submitted also opens a **submission** record that holds the
   delivery and the authority's receipts (see
   [module:l10n_cssk_submission_base](module:l10n_cssk_submission_base)).
   **File it** opens a new one and lets you choose the channel: the manual
   portal channel records that it was filed by hand; with
   [module:l10n_cz_epo](module:l10n_cz_epo) installed, a Czech filing can be
   signed and sent to EPO directly. The badge in the header shows the delivery
   state (delivered, accepted, rejected…).

A statement marked submitted cannot be deleted. The *Comparisons* button
appears once the statement has been compared with the books or with another
filing.

## Corrections {#amendments}

- **Reset to Draft** reopens an exported or submitted statement. Only an
  accounting administrator may do it. The copies already filed stay in the
  filing history.
- **Dodatočný / opravný** (Slovak) or **Opravné / následné** (Czech), on a
  submitted statement, creates a new draft
  linked to it (*Amends*). Choose the statement type of the correction, fix
  the accounting, then compute and export as usual. How the correction is
  computed depends on the country: a Slovak *dodatočný* statement contains
  only the changed rows, a Czech *následné* hlášení repeats the whole period.
  See the country pages.

**Historical filings** — statements imported from a previous system as a
record of what was filed — have the state *Historical filing*. They cannot be
recomputed, exported or submitted.

## Limitations {#limitations}

- Nothing is filed by this module itself; filing is done by hand on the tax
  portal or through a submission channel module.
- Export warnings that do not stop the export (rounding differences, opposite
  signs of base and tax, and the country modules' warnings) are logged on the
  server only. You see errors, not warnings.
- The section of a journal item is stored. After a change of fiscal country,
  or after the rules themselves change, the stored sections must be recomputed
  by an administrator before statements are computed again.
- The Czech section tabs do not offer *Override*: the Czech rows file their
  per-rate columns, which the override does not carry. Correct the document
  instead.
- The section rules are a best effort and the country pages list what remains
  to be confirmed with an accountant. Review every statement before filing.
