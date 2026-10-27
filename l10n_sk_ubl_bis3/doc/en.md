---
title: Slovakia — Peppol BIS Billing 3.0 (eFaktúra)
summary: Produces Slovak electronic invoices in Peppol BIS Billing 3.0, identifies Slovak parties on Peppol by their DIČ, and puts the variable symbol where the payer's bank looks for it.
verified: 19.0.3.2.0
---

## What it is for {#purpose}

Odoo can write an invoice as a Peppol BIS Billing 3.0 file (UBL 2.1,
EN 16931), but out of the box it neither offers that format for Slovak
customers nor identifies Slovak parties on the Peppol network correctly.
This module fills those gaps:

- it adds the format **Slovakia (Peppol BIS 3.0)** and makes it the default
  for every Slovak contact;
- it identifies a Slovak party on Peppol by scheme **0245 with its DIČ**, not
  by its IČ DPH (scheme 9950) as Odoo does, and not by the IČO, which Odoo
  puts under 0245;
- it **refuses to export** an invoice when your company or a Slovak customer
  has no DIČ recorded, naming the contact to fix;
- it writes the **variable symbol** into the payment identifier of the file
  (*PaymentID*, BT-83), which is what the payer's bank uses to match the
  payment.

The file itself is plain Peppol BIS Billing 3.0, with no national
extension. The module creates the file; **sending** it over Peppol needs an
access point, for example Odoo's own Peppol service or
[module:edi_base_peppol](module:edi_base_peppol) with a provider such as
[module:edi_epostak_peppol](module:edi_epostak_peppol). Reporting the
invoice data to Finančná správa is the access point's job, not this module's.

The module installs itself once the Slovak chart of accounts and Odoo's
UBL/CII module are both installed.

## Legal background {#legal}

Electronic invoicing becomes mandatory for domestic supplies in Slovakia on
**1 January 2027**, by
[§ 85o of the VAT Act](law:sk/2004/222#paragraf-85o) in the wording effective
from that date (the consolidated text in force today contains only the parts
of § 85o already effective):

- **Who and what (§ 85o ods. 2).** A VAT payer that, from 1 January 2027,
  supplies goods or services with the place of supply in Slovakia to a
  taxable person established in Slovakia — or to a non-taxable legal person
  established there — or receives a payment before such a supply, must issue
  an electronic invoice. Supplies exempt under § 28 to § 43 and § 47 and
  simplified invoices are excluded. Issuing an electronic invoice does not
  need the recipient's consent; sending it other than through a delivery
  service does.
- **What counts as an electronic invoice (§ 85o ods. 4).** A document with
  the particulars of § 74 ods. 1, issued, sent and received in a format that
  allows automated processing and in a data structure that follows the
  European standard for electronic invoicing and its list of syntaxes.
- **Corrections (§ 85o ods. 5).** A document changing such an invoice must
  be an electronic invoice too, carry the number of the original invoice and
  the data that change, and go the same way.

Whether a particular invoice falls under the mandate is a question of the
law, not of the format: the module offers the format for every Slovak
contact and leaves the choice of what to send to you.

## Setting it up {#setup}

1. **Record the DIČ** on your company and on your Slovak contacts: the field
   **DIČ** from [module:l10n_sk_base](module:l10n_sk_base). It is never
   derived from the IČ DPH — the module used to do that and stopped, because
   a wrong derivation produces a valid-looking identifier that belongs to
   somebody else.
2. **Check the contact's Peppol address.** *Invoicing* tab of the contact
   (*Fakturácia*), group *Customer Invoices*: **Peppol e-address (EAS)**
   should read *SK Tax identification number (DIČ)* (code 0245) with the DIČ
   next to it. The format field, **eInvoice format**, is shown only in
   developer mode and is filled automatically.
3. **Your company's bank account** should be the IBAN the customer is to pay
   to; it goes into the file as usual.
4. **Variable symbol.** With
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols)
   installed, its variable symbol is used — see
   [payment symbols on invoices](module:l10n_cssk_payment_symbols#invoices).

## The Peppol identifier: 0245 + DIČ {#participant}

How a Slovak contact (one whose country, or VAT prefix, is Slovakia) gets
its Peppol address:

| Contact | Peppol address |
|---|---|
| New, with a DIČ | **0245** : DIČ — also for a company created on the company form with its DIČ filled in |
| New, without a DIČ | what Odoo computes — 9950 : IČ DPH for a VAT payer — until a DIČ is recorded; the export is refused meanwhile |
| Already on 0245 | the endpoint follows the DIČ when you change it |
| Already on 9950 or another scheme chosen earlier | **left alone** — the module does not overwrite a scheme somebody may have chosen on purpose |

The last row matters for contacts that existed before their DIČ was
recorded: they keep 9950 even after you fill in the DIČ, and because the DIČ
is now present the export no longer stops them. Moving them is a
deliberate, repeatable step: select the contacts in *Contacts* (list or
form) and run *Actions → Peppol: use 0245 + DIČ*. It is available to
accounting administrators (*Accounting / Administrator*). It moves every
selected Slovak contact that has a DIČ and whose endpoint is either empty or
exactly what Odoo derived from the VAT number; a hand-typed endpoint and a
contact without a DIČ are left as they are. The same move ran once
automatically when the module was upgraded to version 19.0.2.0.0, before
most DIČs had been recorded, so run it after recording missing DIČs (for
example with
[module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk)).
It is also how to fix a company that was created on 9950 before version
19.0.3.2.0: run it on the company's contact.

When a company is created, the module applies the same move to the contact
Odoo creates for it, so a company saved with its DIČ lands on 0245 at once.
A company created for an existing contact keeps that contact's scheme.

## What the file contains {#export}

- The standard Peppol BIS Billing 3.0 content Odoo produces: parties, IČ DPH,
  lines, VAT breakdown, IBAN, reverse charge where it applies.
- **PaymentID (BT-83)** — the variable symbol: the invoice's variable symbol
  when the payment-symbols module is installed, otherwise its payment
  reference, otherwise the invoice number; reduced to digits and the last
  10 kept.
- The invoice PDF embedded in the file.
- File name `INV_2026_00042_ubl_bis3_sk.xml` (the invoice number with `/`
  replaced).

Before the file is created, the export checks that **your company and the
customer**, where they are Slovak, have a DIČ. If not, it stops with a
message naming the contact and the scheme it is currently published under.
A contact registered under another scheme passes, as long as its DIČ is
recorded.

## Limitations {#limitations}

- The module produces the file only. Transmission over Peppol and the
  reporting of invoice data to Finančná správa are done by the access point.
- Contacts that were on 9950 before their DIČ was recorded stay there until
  somebody runs *Peppol: use 0245 + DIČ* on them; nothing runs it
  automatically when a DIČ is filled in later.
- It does not decide which invoices must be sent electronically under
  § 85o; it offers the format for every Slovak contact.
- On uninstalling, the format is removed from contacts; their Peppol
  addresses are kept.
