---
title: SK Monthly Health Insurance Statement (dávka 514)
summary: Published 2023+ text 514 from retained OCA payroll health assessments, with original/corrective filings and the common attachment archive. Legacy XML remains available for existing callers.
verified: 19.0.1.3.0
---

## What it is for {#purpose}

Build the monthly health statement for VšZP (25), Dôvera (24) or Union (27).
The menu opens **Published514 text (2023+)**. This format uses health facts
retained with the OCA payslip: the actual employee base and OP, both premium
rates, disability group, minimum top-up, insured calendar days, birth number
and insurer. It does not infer a rate by dividing rounded premium by gross.

Existing API callers keep the **Legacy XML** default. That older format is
structurally checked; acceptance against an authority-verified XSD is not
established. The new retained-assessment adapter is supplied by
[module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca). Another engine
needs its own equivalent adapter to generate the published text format.

## Legal background {#legal}

The [Health Insurance Act](law:sk/2004/580) governs monthly reporting (§20),
advance due dates (§17), OP (§16(16–18)) and the minimum advance (§16a).
The text writer follows the [interface published by VšZP](https://www.vszp.sk/files/platitelia/tlaciva-platitelov/vykaz-preddavkov-zamestnavatela/struktura-vykazu-1.rtf).
The SHA256 pin is recorded beside the codec, not substituted with a locally
modified XSD. File-format checks and actual acceptance by an insurer are
separate outcomes.

OP-eligible employment income and other income are separate report fields,
even when OP was not claimed. A written concurrent-employment opt-out under
§16a(5) is a separate fact from disability or state-insured status. Do not
select it merely because the person is a pensioner or receives a benefit.

## Setting it up {#setup}

On the employer, enter IČO, DIČ and the default health insurer. On each worker,
record the real birth number and insurer **before calculating payroll**.
Record the applicable disability/OP facts on the dated contract version.
A concurrent-employment minimum opt-out also needs the retained written
notice reference on that version.

For each text statement, choose its insurer and enter the payer number
assigned by that insurer, the employer's payment bank account, payment and
sending dates, batch sequence and legal form. The selected account must
belong to the employer; an unrelated party's valid IBAN is not accepted.

Enter reviewed registered counts for this insurer and for all insurers.
Registration is not inferred from positive premiums: a person on a whole
month of sickness benefits may remain registered while no premium is due.

## Preparing the statement {#usage}

1. Compute and confirm the month's payroll using its real calendar/absence
   sources. An API create does not execute the form's onchange: API callers
   must supply the native worked-day rows, as the form or batch wizard does.
2. Open **Payroll Declarations → SK dávka514 (health)**, select the period
   and **Published514 text (2023+)**, and review the statement inputs.
3. Choose **Generate**. The common declaration workflow stores the generated
   file as an attachment and checks its field limits, dates, precision,
   record framing and totals.
4. Upload through the insurer's authorised channel. **Mark Submitted** records
   a filing fact locally; it does not send or prove acceptance by the insurer.
5. For a full replacement, prepare a **Corrective** filing for the same
   employer, period and insurer after the original was marked submitted.
   **Reset to Draft** allows a new generation; the exact filed bytes remain
   in the common archive.

Excluded pension-agreement income must not contain health premiums. This is
checked before the agreement is filtered out. Historical insurer/profile
facts use retained evidence where available; editing today's employee card
does not reclassify that source.

## What the statement contains {#output}

The published text uses UTF8, CRLF records, decimal commas, `|` separators
including a final separator on each line, and a filename such as
`N5142606.001` or `O5142606.002`. Its three header records have10,13 and20
fields; each employee record has17 fields.

Both disability groups have separate employer totals. The employee premium
in a body row excludes the minimum top-up; its total includes employer,
employee and top-up. The corresponding employee header total includes the
top-up. OP income, other income, OP and employee assessment base are distinct.
The employee sheet displays the same base and calendar days as the text.

## Limitations {#limitations}

Reviewed [health calendars](module:l10n_sk_hr_payroll_base#health-calendar)
supply actual insured days and minimum exceptions through payroll evidence.
A superseded or newly added calendar requires review of payroll corrections
before generating a new statement. Original filed attachments remain available.
Calendar review does not register an employee or submit a 601 notice.

- Original **N** and full corrective **O** generation are supported. The codec
  can represent signed additive values, but automatic **A** differences need
  a separate reviewed correction source; the form does not offer that flow.
- The text adapter currently requires one consolidated payroll source per
  employee within the calendar month. Multiple/irregular correction sources
  need their own consolidation adapter rather than a silent double count.
  Separate HR cards sharing one insured-person identifier are also refused
  until their sources are consolidated; changing the HR record ID does not
  create another insured person.
- A legacy payslip without retained evidence needs a controlled review of
  original sources. No evidence is fabricated during module installation.
- Registered counts remain reviewed statement inputs. This module does not
  create the insurer's registrations or submit declarations over the network.
- A text writer does not establish every payroll profile's statutory
  correctness. Mid-month insurance changes, other minimum exemptions and
  additional-income allocation require the corresponding payroll adapters.
- Legacy XML retains its previous calculation path and structural check.
  Use the published text adapter for the new retained-assessment workflow.
