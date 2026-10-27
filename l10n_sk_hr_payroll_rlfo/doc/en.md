---
title: SK Social Insurance Registration of Employees (RLFO)
summary: Registrations (prihláška) and de-registrations (odhláška) of employees with the Sociálna poisťovňa, entered as a batch of events and exported as XML checked against the official schema.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

Before an employee starts work, the employer registers them with the
**Sociálna poisťovňa**, and it de-registers them when the insurance ends. The
form is the *Registračný list fyzickej osoby* (**RLFO**); this module produces
its electronic batch for employees (the *RLZEC* schema), one file with any
number of registrations and de-registrations.

Unlike the contribution statements, the RLFO is **not built from payslips**.
You enter the events yourself; the module fills in the relationship type and
the employee's personal data, renders the XML and validates it. It uses
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
only for the export, validation and filed-copy handling, so it does not need a
payroll engine — but the relationship type is only proposed correctly when one
of the Slovak payroll modules is installed (see
[the Slovak payroll guide](module:l10n_sk_hr_payroll_base#employees)).

## Legal background {#legal}

References are to the [Social Insurance Act](law:sk/2003/461).

- **Registration and de-registration.** Under
  [§ 231 ods. 1 písm. b)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-b) the
  employer registers an employee for sickness, pension and unemployment
  insurance (an irregular-income employee under § 4 ods. 2 for pension
  insurance only) **before the insurance arises, at the latest before the
  employee starts work**, and de-registers them **within eight days** of the
  insurance ending. A registration for an insurance relationship that never
  arose must be cancelled (*zrušiť prihlásenie*).
- **Interruption.** An interruption of the insurance is reported within eight
  days — [§ 231 ods. 1 písm. d)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-d).
  This module does not produce that event.
- The form and the way of sending it are set by the Sociálna poisťovňa —
  [§ 231 ods. 2](law:sk/2003/461#paragraf-231.odsek-2).

## Setting it up {#setup}

- *Company ID* (IČO), 8 to 12 digits, on the company form.
- *Sociálna poisťovňa variable symbol*, exactly 10 digits — fill it in on the
  RLFO form itself. It is stored on the company and shared with the MVP, VPP
  and ELDP modules, so it is entered once. Changing it needs the right to edit
  companies.
- Per employee: the **birth number** in *Identification No* (9 or 10 digits)
  and the date of birth (*Birthday*). The surname and first name are taken
  from the employee's name: the **last word is the surname** and everything
  before it the first name — write employee names as *First name(s)
  Surname*. With `hr_employee_firstname` installed, its separate first and
  last name fields are used instead.

## Preparing a batch {#usage}

*Payroll Declarations → SK RLFO (registrations)*, then *New*. *Year* and
*Month* only name the batch; they do not limit the events.

Add one line per event under *Registration events*:

| Column | What to enter |
|---|---|
| *Employee* | the employee |
| *Event type* | *Registration* (prihláška, `PA`) or *De-registration* (odhláška, `OD`) |
| *Relationship type (typZec)* | proposed from the employee's contract, editable — see below |
| *Insurance start (datVznikPoist)* | required for both event types |
| *Insurance end (datZaniku)* | required for a de-registration |

The relationship type is proposed from the contract's *Agreement Type* and
*Regular monthly income*:

| Contract | Regular income | Irregular income |
|---|---|---|
| employment (pracovný pomer) | ZEC | ZEC |
| DoVP | ZECD1 | ZECD1N |
| DoPČ | ZECD2 | ZECD2N |
| DoBPŠ | ZECD3 | ZECD3N |

*ZECN* (employee with an irregular income) can be chosen by hand. All
agreement codes, the DoBPŠ ones included, are de-registered through the
agreement branch of the schema.

Then **Generate**. The XML is validated against `RLZEC-v2026.xsd` and attached;
upload it to the Sociálna poisťovňa portal and click **Mark Submitted**. A
de-registration is written in the branch that matches its relationship type
(agreement, irregular income, or regular employment).

Generation stops if the batch has no events, if an employee lacks a valid
birth number, or if a date required for the event is missing.

## Limitations {#limitations}

- **Two event types only:** registration and de-registration. A change
  (*zmena*), an interruption (*prerušenie*) or a cancelled registration
  (*zrušenie prihlásenia*) must be filed through the portal.
- **Nothing is filled in from the contracts but the relationship type.** The
  dates are entered by hand and are not checked against the contract or the
  employee's hire and departure dates, and no event is created when an
  employee is hired or leaves — keeping to the deadlines is up to you.
- The relationship type is proposed when the employee is chosen and is not
  re-checked later against the insurance actually owed.
- Without separate name fields only the last word is taken as the surname:
  check a two-word surname such as *Anna Mária Nová Kováčová* in the XML.
- Contact data in the file are the company's phone and e-mail and the name of
  the user who generates the batch.
- Only the RLZEC 2026 vintage is shipped. Schema validation checks the shape
  of the file, not the data.
