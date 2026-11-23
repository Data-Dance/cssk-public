---
title: Slovakia — Peppol BIS Billing 3.0 (eFaktúra)
summary: Produces Slovak electronic invoices in Peppol BIS Billing 3.0, identifies Slovak parties on Peppol by their DIČ, and puts the variable symbol where the payer's bank looks for it.
verified: 19.0.3.8.0
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
- it writes the **date of supply** (*dátum dodania*) into the file as the
  VAT point date (*TaxPointDate*, BT-7) and reads it back from received
  invoices; Odoo itself never fills that element from the invoice's taxable
  supply date.

The file itself is plain Peppol BIS Billing 3.0, with no national
extension and no Slovak validation rule on top. What Slovak law asks for
beyond the standard is listed in [What the transposition asks for](#transposition).
The module creates the file; **sending** it over Peppol needs an
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
| On 9950 when its first DIČ is recorded | **moved to 0245 : DIČ** as the DIČ is saved, unless its endpoint was typed by hand |
| Already on 0245 | the endpoint follows the DIČ when you change it |
| On 9950 or another scheme chosen with the DIČ already recorded | **left alone** — the module does not overwrite a scheme somebody may have chosen on purpose |

While a contact has no DIČ, 0245 is impossible, so its 9950 is what Odoo
fell back to rather than a choice: recording the DIČ — by hand or from the
register — moves it. A DIČ written past the form (an import into the
database, an older module version) does not, and for those contacts the
move is a deliberate, repeatable step: select the contacts in *Contacts*
(list or form) and run *Actions → Peppol: use 0245 + DIČ*. It is available to
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
- **TaxPointDate (BT-7)** — the date of supply from the invoice's *Taxable
  Supply Date*, on invoices and credit notes, when it differs from the
  invoice date; a file without it means the two are the same. A received
  invoice carrying the element fills the same field on the vendor bill.
- **CompanyLegalForm (BT-33)** — the seller's legal form and register entry
  (§ 3a of the Commercial Code), when
  [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry) is installed
  and holds them for your company; otherwise the element is left out.
- **Company ID (BT-30 / BT-47)** — the IČO of a Slovak seller or buyer from
  the contact's *Company ID*, under scheme `0158`. The IČ DPH appears only as
  the VAT identifier. A Slovak contact with no IČO gets no legal-entity
  identifier.
- **BillingReference (BT-25 / BT-26)** — on a credit note or debit note
  created from an invoice, the number and issue date of that invoice. On a
  credit note entered by hand, the numbers typed in *Original invoice
  number(s)*, each with its date where it is one of your invoices to that
  customer.
- **Note (BT-22)** — the invoice's terms and conditions. On a credit or debit
  note, the reason typed in the wizard goes first, as "Reason for the
  correction: …" in the customer's language.
- **InvoiceTypeCode** — 380 for an invoice, 383 for a debit note; a credit
  note is a separate document type with code 381.
- **OrderReference (BT-13)** — the invoice's *Customer Reference*. On a
  credit or debit note whose reference only quotes the original invoice, the
  original's reference is used, or the document number.
- The invoice PDF embedded in the file.
- File name `INV_2026_00042_ubl_bis3_sk.xml` (the invoice number with `/`
  replaced).

Before the file is created, the export checks that **your company and the
customer**, where they are Slovak, have a DIČ. If not, it stops with a
message naming the contact and the scheme it is currently published under.
A contact registered under another scheme passes, as long as its DIČ is
recorded.

The same check stops the export when a Slovak supplier or customer has no
street, city or postcode, and when its *Company ID* is filled in but is not
an IČO (up to 8 digits). The message names the contact and what is missing.

To find such contacts before an invoice is stopped, open **Contacts** and
use the filter **E-invoice would be refused**. It lists the Slovak companies
with no DIČ, an incomplete address or a *Company ID* that is not an IČO.

Two things are only pointed out, in a yellow banner on the invoice, and
never stop it:

- **No bank account** on a customer invoice that is not yet paid: the file
  then does not say where to pay. Set *Recipient Bank*, unless the invoice
  is paid in cash or by card.
- **No original invoice** on a credit note entered by hand: fill in
  *Original invoice number(s)*, separated by commas. The field shows on a
  customer credit note that was not created from an invoice.

## What the transposition asks for {#transposition}

Finančná správa publishes *Transpozície štandardu Peppol BIS v podmienkach
Slovenskej legislatívy*, a workbook that marks every term of the standard
as required, conditionally required or not required by Slovak law. It adds
no validation rule of its own. The module was read against version
**1.13 (29 October 2026)**; the file, its checksum and how to re-check a
newer version are in the module's `data/TRANSPOSITION_VERSION`.

| Term | What the transposition says | What the module does |
|---|---|---|
| BT-34, BT-49 electronic address | required, scheme 0245 = DIČ | 0245 + DIČ; export refused without a DIČ |
| BT-35/37/38, BT-50/52/53 address | required (§ 74), though optional in the standard | export refused when street, city or postcode is missing |
| BT-30, BT-47 legal registration | required when an IČO was assigned | IČO under scheme 0158 |
| BT-31, BT-48 VAT identifier | required when an IČ DPH was assigned | IČ DPH from the contact |
| BT-7 date of supply | only when it differs from the issue date and is known | written only then |
| BT-8 VAT point date code | not to be used | never written |
| BT-33 seller's legal form and register entry | conditionally required (§ 3a Commercial Code) | from the trade-registry module when installed |
| BT-25 preceding invoice | not required until 1 July 2030 | written on credit and debit notes made from an invoice, and from the numbers typed on a credit note entered by hand; a warning when there is neither |
| BT-83 payment information | variable symbol, at most 10 digits | variable symbol, last 10 digits |
| BT-84 payment account | the supplier's account number is required | the invoice's bank account when it has one; a **warning** on the invoice when it has none, the export is not refused |
| BT-120 exemption reason text | required when a supply is exempt | from the tax, as Odoo fills it; **not checked** |
| BT-22 invoice note | carries the statutory wordings with no field of their own (for example cash accounting, § 68d) | the invoice's terms and conditions, and the reason on a credit or debit note; the statutory wordings are **not added** automatically |

## Limitations {#limitations}

- An exempt tax with no reason text and a missing statutory wording are not
  checked: the invoice goes out as it is. An invoice with no bank account
  and a credit note that names no original are warned about, not stopped.
- Postcodes are sent as typed, prices with the decimals Odoo holds, and the
  import does not tell a debit note (383) from an invoice.

- The module produces the file only. Transmission over Peppol and the
  reporting of invoice data to Finančná správa are done by the access point.
- It does not decide which invoices must be sent electronically under
  § 85o; it offers the format for every Slovak contact.
- On uninstalling, the format is removed from contacts; their Peppol
  addresses are kept.
