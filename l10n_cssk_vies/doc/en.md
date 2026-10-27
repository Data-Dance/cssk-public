---
title: CZ/SK VIES — direct check and proof of consultation
summary: Checks EU VAT numbers directly against the European Commission's VIES service, without Odoo IAP, and keeps every check with its consultation number as evidence.
verified: 19.0.2.1.0
---

## What it is for {#purpose}

An intra-Community supply of goods is exempt from VAT only if the customer is
registered for VAT in another member state and has given you that VAT
number. Checking the number in **VIES**, the European Commission's VAT
Information Exchange System, is how you show you did.

Odoo checks VAT numbers through its own IAP service and keeps only a yes/no
flag. This module:

- calls the European Commission's VIES service **directly**, with no Odoo
  account or IAP credits;
- makes a **qualified** check — one that names your company as the requester
  — so VIES returns a **consultation number** (*číslo overenia* / *číslo
  ověření*), the identifier of that particular consultation;
- keeps **every check** — date, result, consultation number, the name and
  address VIES holds, who checked and for which company — as a read-only log
  on the contact;
- re-checks contacts daily.

## Legal background {#legal}

The exemption conditions that make the customer's VAT number matter:

- **Slovakia** — [§ 43 ods. 1 zákona o DPH](law:sk/2004/222#paragraf-43.odsek-1):
  the supply is exempt if the acquirer is a taxable person (or a non-taxable
  legal person) identified for VAT in another member state **and has given
  the supplier that identification number**.
- **Czech Republic** — [§ 64 odst. 1 zákona o DPH](law:cz/2004/235): the
  supply to a person registered for VAT in another member state is exempt if
  that person **gave the plátce its VAT identification number**, the goods
  are dispatched to another member state, and the plátce reports the supply
  in the souhrnné hlášení.

Neither act prescribes VIES or the consultation number as the form of proof;
it is the evidence tax authorities customarily ask for when a customer's
number later turns out to have been invalid.

## Setting it up {#setup}

1. Your company must have its own **Tax ID** (IČ DPH / DIČ) filled in. VIES
   issues a consultation number only for a qualified check, which needs the
   requester's VAT number.
2. *Accounting → Configuration → Settings*, block **Taxes**, setting
   **Verify VAT Numbers**: tick **Use direct EU VIES (no IAP)**. This is per
   company.

With the box ticked, Odoo's own VIES check (run when a VAT number is entered,
if *Verify VAT Numbers* is on) goes to the European Commission instead of
IAP, and the daily refresh runs for the company. The **Check now** button
below works whether or not the box is ticked.

## Checking a contact {#usage}

On the contact form, below the *Tax ID*, the **VIES** row shows:

- **Check now** — saves the contact and checks its VAT number in VIES at
  once, as the company you are working in. A notification reports the
  result: *Valid in VIES* with the consultation number, *Not valid in VIES*,
  or *VIES did not answer*.
- a green tick or a red cross — the current verdict; click it to open the
  **VIES** tab. A dash means the company has not checked this contact yet.

The **VIES** tab (shown when the contact has a VAT number):

| Group | Fields |
|---|---|
| Consultation | *VIES Checked On*, *VIES Consultation No.*, *VIES Request Date* (the date VIES gives the consultation), *VIES Last Fault* (only after a check VIES did not answer) |
| As registered in VIES | *VIES Registered Name*, *VIES Registered Address*, *VIES Name Match* (whether the name VIES holds matches the contact's name) |

These fields show **the current company's** latest answered check. Below
them is the full list of checks, by every company you have access to, with
the date, result, consultation number and user. Invalid answers are shown in
red, faults greyed out.

Nobody can edit the log. Only administrators can delete entries.

## Daily refresh {#refresh}

The scheduled action **VIES: Refresh direct checks (CZ/SK)** runs once a day.
For each company with *Use direct EU VIES* ticked it checks top-level
contacts whose VAT number starts with an EU prefix (including `EL` for Greece
and `XI` for Northern Ireland) other than the company's own country, which
are shared or belong to that company, and which that company has not checked
in the last 7 days — at most 200 per company per run, with a short pause between
requests because VIES limits the request rate. Each result is logged and
updates the contact's VIES verdict.

## When VIES does not answer {#faults}

VIES often answers that a national system is unavailable or busy. Such an
answer (`MS_UNAVAILABLE`, `MS_MAX_CONCURRENT_REQ`,
`GLOBAL_MAX_CONCURRENT_REQ`, `SERVICE_UNAVAILABLE`, `TIMEOUT`, `BUSY`) or no
answer at all is logged as **No answer**. It never marks the number invalid
and never replaces the last real proof; the daily refresh tries again after
7 days. Any other negative answer counts as invalid.

## Limitations {#limitations}

- **A contact not yet saved is checked but not logged.** The automatic check
  Odoo runs when you type a VAT number is logged with its consultation number
  like any other — but on a new contact there is nothing to attach it to
  until it is saved. Press *Check now* after saving when you need the proof
  at once.
- **No consultation number without your own VAT number.** Without the
  company's *Tax ID*, VIES answers valid or invalid, but returns no
  consultation number.
- **The daily refresh is not limited to customers.** Every company with
  direct checks enabled checks every shared or own top-level contact with a
  foreign EU VAT number, whether or not it trades with it. Domestic VAT
  numbers and contacts of other companies are left out.
- **The verdict is shared, the proof is not.** The tick or cross is one value
  per contact, whichever company checked last; the consultation number and
  registered data are per company.
- A check proves what VIES answered at that moment. It does not cover the
  other exemption conditions (transport, souhrnné hlášení / súhrnný výkaz).
