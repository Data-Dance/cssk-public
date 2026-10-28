---
title: CZ/SK Localization — Shared Core
summary: The common foundation of the Czech and Slovak statutory modules — settings, tax offices, IČO checking, the VAT period of a document, the life cycle of a statutory filing and the filed-versus-computed comparison.
verified: 19.0.1.18.1
---

## What it is for {#purpose}

Every Czech and Slovak statutory module of this localization — VAT returns,
control statements, EC sales lists, financial statements, income-tax returns
— builds on this module. You rarely install it on purpose: it comes with the
first of them, or with the full suites
[module:l10n_cz_datadance](module:l10n_cz_datadance) and
[module:l10n_sk_datadance](module:l10n_sk_datadance).

What it gives you directly:

- one **settings block** for the whole localization;
- the registry of **tax offices** and **entity types** the filings use;
- an **IČO check** on Czech and Slovak contacts;
- the **taxable supply date** on invoice lists and a **VAT period declared**
  date on documents, with optional VAT deferral entries;
- the **statutory footprint** of a posted document;
- the **life cycle shared by all statutory filings** — compute, export,
  mark submitted, amend — and the **filed vs computed** comparison screens;
- a **statement account mapping** for charts that do not use the standard
  account codes.

It depends only on Odoo's `account` and `mail`, so it works on Community and
Enterprise.

## Settings {#setup}

*Accounting → Configuration → Settings*, block **Czech / Slovak
Localization**:

| Setting | What it does |
|---|---|
| Extra accounting menus (Community) | Installs OCA `account_usability`, which adds the accounting menus Enterprise has (general ledger, journals, aged balances…). Shown on Community only. |
| Financial reports (Community) | Installs OCA `account_financial_report`: general ledger, trial balance, partner ledger, aged balance, journal ledger. Shown on Community only. |
| Default tax authority | The tax office (*daňový úrad* / *finanční úřad*) your filings are addressed to. Only offices of the company's fiscal country are offered. |
| VAT declared in a later period | An account for VAT deferral entries — see [VAT deferral](#vat-deferral). Empty: off. |
| Year-end closing journals | The journals holding the year-end closing and reopening entries (e.g. *UZAVIERKA*, *OTVORENIE*). Their entries are left out of the financial statements, the income-tax return and the financial reports, so that closing the year does not wipe out the balance sheet and the profit and loss. Leave empty if the year is never closed in this database. |

The full suites add their own switches to this block, one per optional module.

## Your company {#company}

On the company form (*Settings → Companies*), after *Country*:

- **Tax Authority** — the same field as *Default tax authority* above.
- **Entity Type** — legal entity or natural person, from the
  [entity types](#registries) of the company's country; some forms change
  with it.

The commercial-register entry (*Spoločnosť zapísaná v obchodnom registri…* /
*zapsaná v obchodním rejstříku…*) goes in Odoo's own **Trade Registry** field
on the company, which the Slovak and Czech localizations print on the invoice.
This module used to offer a separate *Registration Info* field that no
document printed; it is gone from the form, and upgrading copies a value
entered there into *Trade Registry* if that was empty.

## Contacts and the IČO {#partners}

On contacts whose country is the Czech Republic or Slovakia:

- The company registry field is labelled **IČO**, and it is shown on
  individuals too (Odoo normally shows it only on companies), because a
  sole trader buying online is created as a person and still has an IČO.
- The IČO is **checked when you save**: it must have 6 to 8 digits and a
  valid check digit (the weighted modulo-11 used by both countries). A wrong
  value is refused with a message naming the company — typing the company name,
  the VAT number or `Test` into the field is no longer possible.
- A valid IČO is stored **with leading zeros to eight digits**: `580007`
  becomes `00580007`.
- **Entity Type** appears before the VAT number, for classifying the partner
  in statutory forms.

Contacts of other countries are not checked: a German `HRB 12345` is accepted
as it is.

## Tax offices and entity types {#registries}

*Accounting → Configuration → CZ/SK Localization*:

- **Tax Authorities** — the offices filings are addressed to, each with a
  stable code, the code written into the XML (*Submission Code*) and, for a
  Czech territorial workplace (*územní pracoviště*), the regional office it
  belongs to. The Czech and Slovak statutory modules load the offices; you
  normally only pick one. The offices listed are those of the fiscal
  countries of the companies currently **selected** in the company switcher:
  working in a Czech and a Slovak company at once, you see both.
- **Person / Entity Types** — legal entity, natural person and similar
  categories per country, loaded the same way.
- **Statement account mapping** — see [below](#account-mapping). Visible to
  accounting administrators.

## VAT period of a document {#vat-period}

### Taxable supply date

The customer invoice and bill lists get a **Taxable Supply Date** column
(optional, shown by default), and the search gets a filter and a grouping by
it. The taxable supply date (*deň dodania* / *DUZP*) decides the VAT period of
a sale.

### VAT period declared {#vat-period-declared}

On invoices, credit notes and bills, after the due date, **VAT period
declared** names the period in which the VAT is reported when that differs
from the usual date. Leave it empty in the normal case.

The statutory returns choose the period of each document like this:

| Document | Period |
|---|---|
| Customer invoice, customer credit note | *VAT period declared* if filled; otherwise the taxable supply date; otherwise the accounting date |
| Vendor bill, refund, any other entry | *VAT period declared* if filled; otherwise the accounting date |

Fill it on a bill whose deduction you claim later than the period it is booked
in, on a correction declared in a later period, or on a document entered late.
The legal background is in [Legal background](#legal).

### VAT deferral entries {#vat-deferral}

When *VAT period declared* falls in a later month than the accounting date,
the VAT return reports the tax later, but account 343 still carries it in the
month of booking, so 343 no longer agrees with the return. If you set an
account in **VAT declared in a later period**, posting such a document also
creates two journal entries in the first miscellaneous journal:

1. on the accounting date, the tax is moved from the VAT account to the
   deferral account;
2. on the declared date, it is moved back. If that date is still ahead, the
   entry is posted automatically when it comes.

Only tax lines that take part in the tax closing are moved. The entries carry
no taxes or tax tags, so no return reads them. The document shows
**VAT deferral: *n* entries** with a link to them; each entry shows the
document under *VAT Deferral Of*. Resetting the document to draft, cancelling
it, or changing the declared date cancels the entries (and creates new ones
where still needed).

## Legal background {#legal}

The *VAT period declared* exists because the deduction may be claimed later
than the supply:

- **Czech Republic** — the deduction may be claimed at the earliest for the
  period in which its conditions (above all, holding the tax document) are met,
  and no later than the end of the second calendar year after the year the
  right arose: [§ 73 odst. 2 and 3 of the VAT Act No. 235/2004 Sb.](law:cz/2004/235).
- **Slovakia** — the deduction is made at the earliest in the period the right
  arose and at the latest in the last period of that calendar year, provided
  the payer holds the invoice by the deadline for that return; otherwise in the
  period the invoice arrives:
  [§ 51 ods. 2 of the VAT Act No. 222/2004 Z. z.](law:sk/2004/222#paragraf-51.odsek-2).

The module records the period you choose. It does not check that the choice
respects these limits.

## Statutory footprint {#footprint}

A posted invoice or journal entry has a **Statutory footprint** button
(accounting users only). It lists the statutory report rows the document feeds
— form, row code and description — and, where a filing for the period already
exists, the filing with a link to it. An empty *Filing* column means no return
for that period has been generated yet; the rows are what it would feed. Which
forms appear depends on the statutory modules installed.

## Statutory filings: the common life cycle {#filings}

The VAT return, control statement, EC sales list and the other forms are
separate modules, but they share one life cycle provided here:

| Step | Button | What happens |
|---|---|---|
| Draft → Preview | *Compute* | the rows are computed from the ledger |
| Preview → Exported | *Export XML* | content checks run, the XML is produced and validated against the official schema, and attached. A failed check blocks the export; a **warning** does not, but it is shown in a notification, posted to the chatter and kept in *Export warnings* until the next export — read it before filing |
| Exported → Submitted | *Mark Submitted* | the exported XML is frozen as the **filed copy** (*Filed XML*), the date is recorded and the filing is locked: it can no longer be recomputed, re-exported or deleted |
| | *File it* | opens a delivery record for the authority's receipts — see [module:l10n_cssk_submission_base](module:l10n_cssk_submission_base) |
| Submitted → Draft | *Reset to Draft* | accounting administrators only; the filed copy is kept |
| | *Dodatočný / opravný* | on a submitted filing: creates a draft amendment linked to the original |

Every XML ever marked submitted stays in **Filed history**, so after a reset,
recompute and resubmit the originally filed copy is still there. Enter the
confirmation number from the portal in **Submission reference**.

**Historical filings.** A filing migrated from a previous system is in state
*Historical filing*: it records what was actually filed and cannot be
computed, exported or submitted. It can be amended, and it can be compared
with what Odoo computes for its period (*Compare with computed*, see below).

## Filed vs computed {#comparisons}

*Accounting → Reporting → Statutory Reports → Filed vs computed*:

- **Comparisons** — one line per filing and per basis of comparison, with the
  counts of rows that agree, findings, rows still to review, and the totals.
- **Rows to review** — the individual rows across all comparisons, filtered to
  those needing an answer.

A comparison is created by a button on a filing. *Compare with computed* on a
historical filing puts it beside what Odoo computes for the same period; the
Slovak suite adds comparisons of one filing with another and with account 343
(see [module:l10n_sk_datadance](module:l10n_sk_datadance)). **Compared against**
says which of these the right-hand column holds:

| Compared against | Right-hand column |
|---|---|
| The filing, recomputed | what Odoo computes for the filing's period |
| The ledger | the balance in the accounts, e.g. 343 |
| Another filing | a different filing for the same period |

Each row has a **result**:

| Result | Meaning |
|---|---|
| Agrees | same figure on both sides |
| Amount differs | same row, different amount |
| Same amount, different row | the two sides put the same amount on different rows (shown as a linked pair) |
| Only the filing has it / Only we compute it | the row exists on one side only |
| Vocabularies not mapped | the two sides use row codes that cannot be matched |
| Difference is expected | a structural gap, e.g. the control statement covers less than the return |
| Informational, not a control | shown for information, never a finding |

Work through the findings by setting a row's **status** — *Asked the
accountant*, *Filing was right*, *Filing was wrong*, *We are wrong*,
*Understood, no action* — and writing what the accountant said in **Note**.
The answer and the note survive a re-run: re-running updates the figures only.
A row that no longer appears on either side is kept and marked *No longer
compared* rather than deleted.

The comparison's own state follows its rows — *Everything agrees*, *To
review*, *Being worked through*, *Every difference answered* — and cannot be
set by hand. When you have reviewed the whole comparison, click **Sign off**;
*Withdraw sign-off* removes it. A re-run does not remove a sign-off.

## Statement account mapping {#account-mapping}

The statutory statements read balances by **account code**, using the codes
of the standard chart of accounts. A chart taken over from another system often
uses its own analytical codes — `461001` for a long-term bank loan where the
Slovak balance sheet expects `461100` — and such an account lands on no row.

*Accounting → Configuration → CZ/SK Localization → Statement account mapping*
(accounting administrators) lets you keep your chart and say under which code
an account is reported:

| Field | Meaning |
|---|---|
| Account | your account |
| Balance side | *Any balance*, or *Debit balance only* / *Credit balance only* — e.g. a bank account reported as a short-term bank loan only when it is overdrawn |
| Reported code | the code the statement reads it as, e.g. `461200`; a plain code, no spaces or operators |

A side-dependent mapping applies only to balance-sheet (as-of) balances; in
the profit and loss the account keeps its own code. An account can have either
one *Any balance* mapping or debit and/or credit mappings, not both. The
mapping applies to the preview, the XML and the drill-down alike.

## Limitations {#limitations}

- The IČO check proves the number is well formed, not that it exists; checking
  against the register is done by other modules.
- *VAT period declared* is not checked against the statutory time limits.
- VAT deferral entries go to the first miscellaneous journal of the company;
  the journal cannot be chosen. A company with none gets an error on posting.
- *Export warnings* are shown on the filing's chatter and in the export
  notification; the filing forms do not yet show them as a banner.
