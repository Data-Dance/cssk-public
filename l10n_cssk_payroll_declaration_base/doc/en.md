---
title: CZ/SK Payroll Declarations
summary: The common ground of the Czech and Slovak payroll filings — the Payroll Declarations menu, the Generate / Mark Submitted workflow, corrections, form versions, and how payslips are read from either payroll engine.
verified: 19.0.1.5.0
---

## What it is for {#purpose}

Every Czech and Slovak payroll filing in this localization — the monthly
social and health insurance reports, the tax overviews, the pension record
sheets, the registrations — is a separate module. They all work the same
way, because they are built on this one. This page describes what they have
in common; each form's own page describes its content.

The module adds the **Payroll Declarations** menu, the version table of the
statutory forms, and the machinery behind every filing record: the period,
the states, the XML export with its schema check, corrections, and the
reading of payslips. It depends neither on Odoo Enterprise *Payroll* nor on
the OCA *payroll* app; it reads payslips from whichever of the two is
installed. It installs itself as a dependency of the forms and does nothing
on its own.

## The forms built on it {#forms}

| Country | Module | Form | Filed to |
|---|---|---|---|
| SK | [module:l10n_sk_hr_payroll_mvp](module:l10n_sk_hr_payroll_mvp) | Mesačný výkaz poistného a príspevkov | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_vpp](module:l10n_sk_hr_payroll_vpp) | Výkaz poistného a príspevkov (irregular income) | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_rlfo](module:l10n_sk_hr_payroll_rlfo) | Registration and deregistration of employees | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_eldp](module:l10n_sk_hr_payroll_eldp) | Evidenčný list dôchodkového poistenia | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_health](module:l10n_sk_hr_payroll_health) | Mesačný výkaz preddavkov na poistné (dávka 514) | health insurers |
| SK | [module:l10n_sk_hr_payroll_monthly_tax_overview](module:l10n_sk_hr_payroll_monthly_tax_overview) | Prehľad o zrazených a odvedených preddavkoch | Finančná správa |
| SK | [module:l10n_sk_hr_payroll_annual_tax_report](module:l10n_sk_hr_payroll_annual_tax_report) | Hlásenie o vyúčtovaní dane | Finančná správa |
| CZ | [module:l10n_cz_hr_payroll_pvpoj](module:l10n_cz_hr_payroll_pvpoj) | Přehled o výši pojistného (PVPOJ) | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_eldp](module:l10n_cz_hr_payroll_eldp) | Evidenční list důchodového pojištění | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_onz](module:l10n_cz_hr_payroll_onz) | Oznámení o nástupu / skončení zaměstnání | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_health](module:l10n_cz_hr_payroll_health) | Přehled o platbě pojistného zaměstnavatelem (PPPZ) and the Hromadné oznámení zaměstnavatele (HOZ) | health insurers |
| CZ | [module:l10n_cz_hr_payroll_annual_tax_settlement](module:l10n_cz_hr_payroll_annual_tax_settlement) | Vyúčtování daně z příjmů fyzických osob ze závislé činnosti | Finanční správa |

The Slovak payroll as a whole is described in
[the Slovak payroll guide](module:l10n_sk_hr_payroll_base#declarations).

## The workflow {#workflow}

Every form appears under *Payroll Declarations* as its own menu item. A
filing record covers one company and one period:

1. **New**, then choose the **Year** and **Month**. Both default to the
   current month, so change them when preparing last month's filing. The
   record shows the period's first and last day. *Payment Date* is the payday
   reported where the form asks for one (on the Slovak forms *denVyplaty*);
   left empty, the period end is used.
2. Check the **Version** (see [Form versions](#versions)). The picker offers
   only the versions of the form being prepared.
3. Click **Generate**. The module checks the master data the form needs (each
   form adds its own checks — company identifiers, birth numbers, addresses),
   collects the period's payslips, builds one row per employee, renders the
   XML, checks it against the official XSD and attaches it. The state becomes
   *Generated*.
4. Download the XML and file it on the authority's portal. No form in the
   family sends anything by itself.
5. Click **Mark Submitted**. The XML that was generated becomes the **Filed
   XML**, is added to the **Filed history**, the date is recorded, and the
   record is locked: it can neither be regenerated nor deleted.
6. **Reset to Draft** unlocks it again. The filed copy and the history are
   kept, so what was actually sent stays on record even if the figures are
   regenerated later.

Confirm the period's payslips before generating: drafts are not counted (see
[Which payslips are counted](#payslips)).

Generating stops with a message when the period has no payslips, when no
version applies, or when the XML does not pass the schema. Every step is
logged in the chatter.

## Corrections {#corrections}

The authorities accept amendments to a filing they already have, and each
spells them differently — *opravný*, *dodatočný*, *storno*. The record has a
**Correction Type** with up to four values, shown in English:

| Value | Meaning |
|---|---|
| Regular | the ordinary filing for the period |
| Corrective | replaces a filing already sent |
| Supplementary | adds to a filing already sent, which stays valid |
| Cancellation | withdraws a filing that should not have been sent |

A form offers only the values its authority accepts, and only those that
have been checked against the authority's rules. At present:

| Form | Correction types offered |
|---|---|
| SK Prehľad o zrazených a odvedených preddavkoch | Regular, Corrective |
| SK Hlásenie o vyúčtovaní dane | Regular, Corrective, Supplementary |
| CZ PPPZ | Regular, Corrective |
| all other forms | Regular only — file corrections on the portal |

For anything other than *Regular*, **Generate** refuses unless a filing of
the same form for the same company and period is already *Submitted* — an
amendment to something never filed would be rejected. The period is compared
by its first and last day, so for an annual form the month the record was
created in does not matter. Where the authority
needs to match the amendment to the original, enter its reference in
**Correction Reference**.

An amendment is built from the period's payslips as they are now, exactly
like the regular filing; see [Limitations](#limitations).

## Which payslips are counted {#payslips}

Unless a form's own page says otherwise, a filing for a period counts every
payslip of the company that

- **ends** inside the period — a payslip belongs to the period its end date
  falls in, so one crossing a month or year boundary is counted exactly once,
  in the period where it ends, and
- is **confirmed**: *Done* on the OCA engine, *Validated* or *Paid* on
  Enterprise. Draft payslips (and *Waiting* ones on the OCA engine) are
  ignored, as are cancelled ones. Confirm the period's payslips before
  clicking *Generate*.

From those payslips the module sums the salary-rule lines by code, per
employee and in total. The rule codes differ slightly between the Enterprise
and OCA engines (for example the Slovak income tax advance is one line on
the OCA engine and one line per tax band on Enterprise); the module knows
both spellings, so a form gives the same result on either engine.

Each employee row also carries, by default:

| Row value | Taken from |
|---|---|
| assessment base (*Vz Base*) | the employee's **GROSS** for the period |
| insured days (*Insured Days*) | the days of employment inside the period, read from all the employee's contract versions (contract start and end); the whole period when no version has a contract start date |
| worked hours (*Worked Hours*) | the hours of all the employee's worked-days lines, absences included |

Individual forms take these values or compute their own; check the form's
page.

## Form versions {#versions}

The authorities change their forms and schemas from time to time. Each form
vintage is a record under *Payroll Declarations → Configuration →
Declaration Versions*: report code, country, **Valid From** / **Valid To**,
the XML template, the expected root element and the XSD file. A new vintage
is shipped as a new version record with its own template and schema; old
vintages stay available.

A new filing record proposes the version of its form that is valid **today**
in the country of your current company, and changes it when you change the
year or month. **Generate** settles it: it switches to the version of this
form valid for the period (an annual form looks at 1 January, an event-based
form at its events) and refuses a period no version covers. When a form has
been discontinued — a version with a *Valid To* and no successor — the
message says so and, where the form knows it, names what replaced it.
The versions are readable by every internal user and maintained by *Employees
/ Administrator*; normally you never edit them.

## Company settings {#company}

The company form of a Czech or Slovak company has a **Payroll Reporting**
tab. For a Czech company it holds the employer identification the ČSSZ forms
need: the **ČSSZ variable symbol (VS)** and the **OSSZ code** of the locally
competent district social security administration. The forms refuse to
generate without them. Other modules add their own fields to the same tab.

## Delivery and receipts {#delivery}

*Mark Submitted* records that someone filed the XML, and opens a
**submission** for it in *Draft* — the record that holds how the XML reached
the authority, whether it was accepted, and the receipts that prove it. It is
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base)'s, which
every payroll declaration uses; find it under *Accounting → Reporting →
Statutory Reports → Submissions*. See
[Filing a return](module:l10n_cssk_submission_base#usage) there.

## Limitations {#limitations}

- **Corrections to earlier months are not separated.** A payslip is counted
  in the month of its own period. A back payment or correction entered on
  this month's payslip for an earlier month is reported in this month; it
  does not produce, and is not moved into, an amendment of the earlier
  month. An amendment is generated from the amended month's payslips as they
  stand, not as a difference against what was filed, so a *Supplementary*
  filing contains the full figures unless the form's own template handles
  it. Compare the amendment with the filed copy before sending it.
- **The year** can be chosen from 2020 to next year.
- **Submission is recorded, not performed.** Nothing is sent to an authority
  by this module or the forms built on it.
- **The schema check proves the shape, not the figures.** Reconcile the
  first filing of every form by hand.
