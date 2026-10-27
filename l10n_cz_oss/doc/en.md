---
title: CZ OSS VAT Return (OSSEI1, Union scheme)
summary: The Czech One-Stop-Shop return for the Union scheme as the EPO form OSSEI1, validated against the official schema.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A Czech VAT payer or identified person registered for the One-Stop-Shop
**Union scheme** (*zvláštní režim jednoho správního místa — režim Evropské
unie*) files a quarterly return of the VAT charged on distance sales and on
services to consumers in other EU states. This module turns the return
computed by [module:l10n_cssk_oss_base](module:l10n_cssk_oss_base) into the
EPO form **OSSEI1** (*DAP OSS — režim EU — Přiznání k DPH*) and checks it
against the official schema before it is attached.

Everything about preparing the return — the rows, corrections, exchange rates
and the export steps — is described in the
[shared guide](module:l10n_cssk_oss_base#usage). This page covers what is
Czech.

## Legal background {#legal}

All references are to the [VAT Act, No. 235/2004 Sb.](law:cz/2004/235);
statutory terms are given in Czech.

- **Who may use the scheme.** Under [§ 110l odst. 1](law:cz/2004/235) a person established in
  Czechia (or, without an EU establishment, dispatching goods from here) who
  is a *plátce* or *identifikovaná osoba* and does not use the Union scheme in
  another member state. Registration is applied for under [§ 110p](law:cz/2004/235).
- **One tax office for everyone.** The special scheme is administered by the
  *Finanční úřad pro Jihomoravský kraj* ([§ 110a odst. 3](law:cz/2004/235)), not by the company's
  own office. The form therefore carries no tax-office code.
- **Electronic filing only.** Form filings in the special scheme, except the
  registration, are made electronically through the electronic portal
  ([§ 110o odst. 1](law:cz/2004/235)).
- **Period and deadline.** The tax period is the calendar quarter ([§ 110zb](law:cz/2004/235));
  the return is due by the end of the following month, also when nothing was
  supplied, and the deadline does not move to the next working day ([§ 110zc](law:cz/2004/235)).
- **Amounts.** Tax is stated in euro to two decimal places *bez
  zaokrouhlování* (without rounding); conversion uses the ECB rate for the
  last day of the period or the next day of publication, and for a correction
  the rate used for the original supply ([§ 110ze](law:cz/2004/235)).
- **Corrections.** A correction is part of the return for the period in which
  the payer learned of the facts, and cannot be made after three years from
  the deadline of the original return ([§ 110zd](law:cz/2004/235)).

## The form {#form}

The module produces one form, **OSSEI1**, structure version **01.01.04** of
13 December 2021, valid for every quarter from Q3 2021. That is the Czech way
of versioning: EPO publishes a single schema, `ossei1_epo2.xsd`, and replaces
it in place, and a return for an old quarter is filed in the structure current
at the time of filing. There is therefore **one open-ended form version**,
*DAP OSS — režim EU (OSSEI1)*, and nothing is chosen by year.

Neither the schema nor the structure version in the file (`verzePis`) can show
that it is out of date — a stale schema validates a stale file perfectly. The
module pins the schema by size and checksum, and a test fails if the bundled
schema does not match. When Finanční správa publishes a new structure, the
module must be updated.

What the file contains:

| Part | Content |
|---|---|
| `VetaD` | quarter, year, DIČ without the `CZ` prefix, company name, `A` for a return with data or `N` for a nil return, and the start or end date when the registration began or ended during the quarter |
| `VetaP` | DIČ |
| `VetaR` | one per member state of consumption × rate × goods (`G`) or services (`S`): the state supplied from, rate type `Z` (standard) or `S` (reduced), rate, taxable amount and VAT in euro; Greece as `EL` |
| `VetaO` | one per corrected quarter and member state: the correction of VAT in euro, with its sign |

## Setting it up {#setup}

- The company's **Tax ID** must be a Czech DIČ: `CZ` followed by 8 to 10
  digits. The export refuses anything else before EPO would.
- The form version is installed with the module. Choose
  *DAP OSS — režim EU (OSSEI1)* on each return.
- Set up Odoo's OSS taxes as the
  [shared guide](module:l10n_cssk_oss_base#setup) describes.

## Filing {#usage}

1. Prepare and compute the return under *Účetnictví → Výkazy → Zákonné výkazy
   → Přiznání k DPH OSS* and confirm the ECB rates.
2. **Exportovat XML** (*Export XML*). The file is validated against OSSEI1 and
   attached.
3. File it through the Finanční správa electronic portal (EPO) — by loading
   the file there, or by sending it from Odoo with
   [module:l10n_cz_epo](module:l10n_cz_epo) through **Podat** (*File it*).
4. **Označit jako podané** (*Mark Submitted*) to keep the filed copy.

Pay the tax in euro, by bank transfer to the tax office's euro account,
quoting the reference number of the return ([§ 110h](law:cz/2004/235)). The module does not
create the payment.

## Limitations {#limitations}

- **Rounding.** § 110ze odst. 1 asks for euro amounts to two decimals without
  rounding. The module rounds the VAT of each row half-up to cents, so a row
  can differ by one cent from a truncated figure. Check this with your tax
  adviser before filing.
- Only the Union scheme (OSSEI1). The non-Union scheme (OSSNI1), the import
  scheme (OSSII1) and the MOSS return for quarters before Q3 2021 (OSSDI1) are
  not built.
- A correction that has to be filed with the member state of consumption
  directly, after the three-year period, is not prepared here.
- A new EPO structure needs a module update; there is no warning other than
  EPO rejecting the file.
- The checks are those described in the
  [shared guide](module:l10n_cssk_oss_base#limitations); EPO's own content
  checks run only when the file is submitted or checked there.
