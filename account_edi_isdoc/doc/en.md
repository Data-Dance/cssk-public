---
title: ISDOC e-invoices (Czech format)
summary: Sends customer invoices and credit notes as ISDOC 6.0.2 files, embedded in the invoice PDF as well, and turns received ISDOC files into draft vendor bills.
verified: 19.0.1.3.0
---

## What it is for {#purpose}

**ISDOC** (*Information System Document*) is the Czech national format for
electronic invoices, read by most Czech accounting software. This module adds
version **6.0.2** to Odoo's electronic invoicing, next to Peppol BIS 3 and
the other UBL/CII formats:

- **sending** — a customer invoice or credit note for a customer set to
  ISDOC gets an `.isdoc` file, and the ISDOC is also embedded in the invoice
  PDF ([sending](#export));
- **receiving** — an ISDOC file uploaded or emailed into vendor bills becomes
  a draft bill: plain `.isdoc`, an `.isdocx` archive, or a PDF with an
  embedded ISDOC ([receiving](#import)).

It builds on Odoo's `account_edi_ubl_cii`, so it uses the standard *Send*
dialog and the standard bill upload. It needs
[module:l10n_cz_base](module:l10n_cz_base) for Czech bank account numbers.

Three add-ons install themselves when their counterpart is present:

| Add-on | With | Adds |
|---|---|---|
| [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) | Sales | an ISDOC proforma (document type 4) from a sales order — [proformas](#proforma) |
| [module:account_edi_isdoc_sale_advance](module:account_edi_isdoc_sale_advance) | advance invoices (sales) | tax documents for received payments as types 5 and 6, and deducted advances on the final invoice — [advances](#advances) |
| [module:account_edi_isdoc_purchase_advance](module:account_edi_isdoc_purchase_advance) | received advance invoices | imported types 4, 5 and 6 go into the received-advance flow — [received advances](#received-advances) |

## Legal background {#legal}

ISDOC is an industry standard, not a statutory format. What the law
requires is that the customer agrees to an electronic tax document: a tax
document is electronic when it is issued and received electronically, and
the person for whom the supply is made must agree to its use —
[§ 26 odst. 3 of the Czech VAT Act](law:cz/2004/235). An ISDOC file carries
the particulars of [§ 29](law:cz/2004/235), including the date of the
taxable supply (*den uskutečnění plnění*, DUZP), which ISDOC calls
*TaxPointDate*.

ISDOC is not one of the syntaxes of the European standard EN 16931. It does
not meet the Slovak e-invoicing obligation from 1 January 2027, which
requires that structure; for Slovak customers use
[Peppol](module:edi_base_peppol#legal).

## Setting it up {#setup}

1. **Choose ISDOC for the customer.** Contact, tab *Invoicing*, group
   *Customer Invoices*: **eInvoice format** = **Czech Republic (ISDOC)**.
   Odoo shows this field only in **developer mode**. It is **not** chosen
   automatically: for a Czech contact Odoo suggests Peppol BIS 3, so set
   ISDOC on every customer who wants it.
2. **Your company and the customer need** a name, street, city, ZIP, country,
   and an **IČO** (*Company ID*) or a **DIČ** (*Tax ID*). The export lists
   anything missing.
3. **Bank account.** The payment details are written only when the invoice
   has a bank account (*Recipient Bank*); the account is written in the
   domestic form (number and bank code) and as IBAN.
4. **Payment symbols.** With
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols), the
   invoice's variable, constant and specific symbols are written to the file.

## Sending ISDOC {#export}

Send the invoice with Odoo's **Send** dialog as usual. For a customer set to
ISDOC, Odoo generates the file `INV_2026_00042.isdoc`, attaches it to the
invoice and the email, and embeds it in the invoice PDF, which is converted
to PDF/A-3 — the form in which a PDF and its ISDOC travel as one file. If the
PDF/A conversion fails, the ISDOC is still embedded. As with every Odoo
e-invoice, the file is generated once and reused for later sends.

**ISDOCX archive.** On a posted customer invoice or credit note,
**Action → Download ISDOCX** downloads `INV_2026_00042.isdocx`: a ZIP with
the ISDOC, its manifest and the invoice PDF — the third form ISDOC defines.
It is kept as the invoice's attachment and replaced on every download.

What the file contains:

| ISDOC | From Odoo |
|---|---|
| DocumentType | **1** invoice, **2** credit note (5 and 6 with the [advances](#advances) add-on) |
| ID, UUID | the invoice number; a UUID generated on first export and kept, so the document keeps its identity |
| IssueDate, TaxPointDate | the invoice date; the **taxable supply date**, or the invoice date if there is none |
| VATApplicable | whether the invoice carries VAT |
| Supplier and customer | name, IČO, DIČ, address with the house number split off the street, phone, email |
| Invoice lines | description, quantity and unit (`ks` when there is none), unit price and amount without and with VAT, VAT rate, barcode and internal reference of the product |
| OriginalDocumentReference | on a credit note: number, date and UUID of the invoice it corrects |
| TaxTotal, LegalMonetaryTotal | VAT breakdown by rate and totals — the VAT the invoice booked, rounded as on the invoice, so the breakdown adds up to the amount due |
| Deposits | advances deducted on a final invoice, with the amounts already claimed ([advances](#advances)) |
| PaymentMeans | bank transfer: due date, account number, bank code, IBAN, BIC, VS, KS, SS |

The invoice must be in the **company currency**; an invoice in a foreign
currency is refused for ISDOC.

## Receiving ISDOC {#import}

Upload the file into vendor bills, drop it on the list, or send it to the
purchase journal's email alias. Accepted are a plain `.isdoc` file (even when
the sender labels it as a generic file type), an `.isdocx` archive — its PDF
is attached to the bill too — and a PDF with an ISDOC embedded. Files of
older ISDOC versions are read as well.

The draft bill gets:

- the **vendor** — found first by **IČO** (unless the file's DIČ
  contradicts the partner's), then by DIČ, name, email or phone, or created
  when the file has a name and a DIČ; a vendor created this way keeps the
  IČO;
- **Bill Date**, **taxable supply date** (the supplier's DUZP), **Due Date**;
- **Bill Reference** — the supplier's invoice number — and the document's
  UUID;
- the **variable symbol** as payment reference and in the VS field, plus the
  constant and specific symbols, reduced to digits;
- the supplier's **bank account**, converted to IBAN and added to the
  vendor;
- the **lines**, with the product found by name, internal reference or
  barcode, the VAT taxes found by rate, and a discount worked out when the
  line amount differs from price × quantity. A line marked as **local
  reverse charge** (*LocalReverseCharge*, § 92a ZDPH) gets the chart's
  reverse-charge purchase tax at its rate (*21% RC*, *12% RC*), or a tax
  flagged as reverse charge — never the ordinary rate, which would bill VAT
  the supplier never charged. If there is none, the line is left without tax
  and the bill's chatter says so;
- deducted advances as negative lines "Advance payment …", and the
  rounding to whole crowns as a line "Rounding", so the bill total matches
  the amount payable.

Document types 2 and 6 become vendor credit notes; all others become bills.
The [VAT period declared](module:l10n_cssk_core#vat-period-declared) is
deliberately left empty: it is when you claim the deduction, which the
supplier's document cannot know. The bill is a
draft; check it before posting.

## Proformas from sales orders {#proforma}

[module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) can write a
sales order as an ISDOC **proforma**, document type 4 (*zálohová faktura*, a
request for an advance payment): the order number as ID, the order date as
issue date, the order lines, totals, and the company's first bank account
with the order number's digits as variable symbol and the order's expiry
date as due date. On the order, **Action → Download ISDOC Proforma**
downloads it and keeps it as the order's attachment.

A received proforma is read by this module like any ISDOC — as a draft bill
— unless the [received advances](#received-advances) add-on is installed.

## Advance invoices {#advances}

With [module:account_edi_isdoc_sale_advance](module:account_edi_isdoc_sale_advance),
the Czech advance chain of
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) maps
to ISDOC:

| Odoo document | ISDOC |
|---|---|
| tax document for a received payment ([daňový doklad k přijaté platbě](module:sale_order_advance_invoice#tax-document)) | **5**, or **6** for its credit note |
| final invoice with deducted advances ([settling](module:sale_order_advance_invoice#final-invoice)) | **1**; each deduction reported as a taxed (or untaxed) deposit, with the advance's tax document number and variable symbol, and the VAT already claimed shown per rate |

The advance invoice itself is a sales order and is exported as a
[proforma](#proforma). Odoo's own down payments are reported as deposits by
the base module already.

## Received advance invoices {#received-advances}

With [module:account_edi_isdoc_purchase_advance](module:account_edi_isdoc_purchase_advance)
and [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice),
imported advance documents go into the received-advance flow:

- **Type 4 — proforma.** A **received advance** is created for the supplier
  over the document's gross amount, with the supplier's number as vendor
  reference and the product *Advance payment (imported)*, without tax. The
  draft bill created by the import stays, linked to the advance, with a note
  that it **must not be posted**: pay and track the advance, then delete the
  draft. Importing the same proforma again (same supplier and supplier's
  number) creates no second advance; the new draft is linked to the first.
- **Types 5 and 6 — the supplier's tax document for your payment** and its
  credit note. The bill goes to the *Received Advance Tax Documents Journal*,
  takes the taxable supply date from the file, its lines are moved to the
  *Paid Advances Account* (the long-term one for a long-term advance) and
  the payable to the *Paid Advances Clearing Account*. It is linked to the
  open received advance of that supplier found, in this order, by the order
  reference in the file, by the variable symbol, or as the only advance
  waiting for a tax document whose paid amount equals the document total.
  If none or several match, the chatter says so — link it by hand.

See [the supplier's tax document](module:purchase_order_advance_invoice#tax-document)
for what happens next.

## Limitations {#limitations}

- **eInvoice format** is visible only in developer mode, and ISDOC is never
  chosen for a customer automatically.
- Invoices in a foreign currency cannot be exported. On import, the amounts
  in the local currency are used.
- Debit notes (type 3) and simplified tax documents (type 7) are imported as
  ordinary bills.
- The export never writes ISDOC's local reverse-charge element: a
  reverse-charge invoice goes out as a supply without VAT, with no commodity
  code.
- A vendor without a DIČ that is not found by IČO, name, email or phone is
  not created; choose it on the bill.
