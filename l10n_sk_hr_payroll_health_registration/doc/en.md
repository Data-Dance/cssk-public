---
title: SK Health Insurance Registration Notices (601)
summary: Reviewed HR events in the published XML and Latin2 text601 interfaces, using the common declaration and filed-copy archive.
verified: 19.0.1.0.0
---

## Purpose {#purpose}

Prepare employer registration/change notices for VšZP25, Dôvera24 and Union27.
The source is a reviewed HR event, not a payslip or a second payroll ledger.
The module installs without either payroll engine. It uses the existing
declaration workflow, sending vintage and submission tracking.

## Sources and interfaces {#sources}

The implementation follows MU12/14/2014, updated10December2025, in the
[ÚDZS Bulletin1/2026](https://www.udzs-sk.sk/wp-content/uploads/2026/01/VE_1_2026_sv.pdf).
The schema README documents its extraction and hashes. The XSD was derived
from the published PDF; it is not represented as an independently downloaded
authority XSD. XML uses UTF8; text601 uses ISO8859-2, CRLF, trailing separators
and10/25/9 fields. Change dates use YYYYMMDD, also confirmed by the
[insurer interface guide](https://www.dovera.sk/najcastejsie-otazky/elektronicka-pobocka/e-pobocka-platitel).

## Workflow {#workflow}

An HR manager opens Payroll Declarations / SK health registration601, selects
the insurer, sending date/serial, payer identity, company bank and contact.
Add the employee, reviewed code, Z(start)/K(end)/X(cancel row), actual change
date and retained source reference. Employee onchange prefills the identity;
BIČ must be an identifier actually assigned by the authority.

Confirm separately that the employer must report the event. A factual ePN or
state-insured interval does not imply another employer notice. Optional linked
health calendars must be reviewed and match the employee/company. Z/K endpoints
must agree with the unioned coverage run; a monthly clipped calendar alone
does not establish a new employment start or end every month. Cancellation may
refer to a superseded calendar. Same-employer employment suppresses2D notices.
When the country payroll module is installed, its dated health-exemption fact
blocks a2D start; K and X remain available. HR-only installations require
manual eligibility review; the module does not invent missing payroll facts.

Generate checks the interface and retains the exact attachment and source.
Record as submitted records an external action; it does not send the file or
claim insurer acceptance. Reset preserves filed copies. A filed batch retains
its company, insurer, period, serial and correction identity even after reset
or removal of working event rows. Use a separate record for a genuinely new
filing/correction. An explicit full O
batch references a filed batch of the same company and insurer. The operator
must review the correction contents and insurer response; cancellations are
not inferred or automatically propagated into coverage/payroll calendars.

## Boundaries and validation {#limits}

The published XML pattern contains trailing spaces after2S (strike). The
negative control first validates an otherwise identical baseline. For2S use
text601 when names are representable in Latin2; Unicode names are not silently
transliterated. Ordinary XML supports Unicode. A provider-confirmed XML schema
or portal entry is needed when both limitations apply.

This module does not infer actual agreement work/rest days, irregular-income
allocation, external ePN notifications, or authority identifiers. These must
come from reviewed source records. Generating a structurally valid file is
separate from verifying the legal event and obtaining an authority receipt.
The native corporate form supports a payer with IČO; non-IČO natural-person
payer onboarding is outside this form's verified scope. Future published
interface changes require another vintage review.

Tests cover XML/text records, pinned derived XSD, required fields, same-day
start/end, historical events with current sending vintage, HR-manager access,
company isolation, correction retention, source/calendar checks and immutable
file content with same-content storage migration. Authority acceptance has
not been tested with synthetic identities.
