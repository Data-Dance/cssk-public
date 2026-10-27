---
title: Debit Notes — Data Dance refinements
summary: Titles a printed customer debit note as a corrective tax document, hides the Credit Note button and lists customer debit notes with credit notes. Posting is left to Odoo.
verified: 19.0.1.0.1
---

## What it is for {#purpose}

Odoo's *Debit Notes* module (`account_debit_note`) adds a **Debit Note**
button to posted invoices and bills: it creates a new invoice linked to the
original, for an amount that **increases** what was invoiced. That is the
Czech *opravný daňový doklad* raising the tax base and the Slovak
*ťarchopis*.

This module adjusts three things around it:

1. the title printed on a customer debit note;
2. the **Credit Note** button on invoices, which it hides;
3. the customer *Credit Notes* list, which it makes show customer debit notes
   too.

It does not change how anything is posted — see [Posting](#posting).

## Legal background {#legal}

A later increase of the price is a correction of the tax base in both
countries, and the document that records it is itself a tax document:

- **Slovakia.** The tax base is corrected when the price is increased —
  [§ 25 ods. 1 písm. c)](law:sk/2004/222#paragraf-25.odsek-1) of the VAT Act.
  A document that changes the original invoice and refers to it specifically
  and unambiguously is an invoice under
  [§ 71 ods. 2](law:sk/2004/222#paragraf-71.odsek-2), and per
  [§ 74 ods. 3 písm. c)](law:sk/2004/222#paragraf-74.odsek-3.pismeno-c) it
  must carry the number of the original invoice and the data that change.
- **Czech Republic.** The base is corrected under § 42 of the
  [VAT Act](law:cz/2004/235), and the corrective document must carry the
  particulars listed in § 45 odst. 1 — among them the number of the original
  tax document, the reason for the correction, and the difference in the tax
  base and in the tax.

Odoo's debit-note wizard writes the original number and the reason you enter
into the new document's *Reference*, which the invoice prints; the lines of
the debit note are the difference itself. This module does not add any
further particulars.

## The printed debit note {#report}

A customer debit note is printed with the title **Debit Note**, **Draft Debit
Note** or **Cancelled Debit Note** followed by its number. In Czech the
titles read *Opravný daňový doklad*, *Návrh opravného daňového dokladu* and
*Zrušený opravný daňový doklad*; in Slovak *Ťarchopis*, *Návrh ťarchopisu*
and *Zrušený ťarchopis*.

## Credit notes and the Credit Note button {#credit-notes}

- The **Credit Note** button on posted customer invoices and vendor bills is
  hidden. A credit note can still be created from the list of invoices or
  bills: select the document and use *Action → Reverse*.
- *Accounting → Customers → Credit Notes* lists customer credit notes **and
  customer debit notes** — Odoo's own list shows invoices and credit notes
  with a filter on credit notes. Vendor debit notes are not in it.

## Posting {#posting}

The module does not touch posting: invoices, bills, credit notes, debit notes
and journal entries are posted by Odoo with all of Odoo's checks, and with
whatever other installed modules add to posting.

A debit note therefore cannot be posted with a **negative total**, like any
other invoice: a reduction of the price is a credit note.

Up to version 19.0.1.0.0 the module replaced Odoo's posting with an old copy
of it that skipped several checks — a negative total, an untrusted company
bank account, an account that does not fit the journal or belongs to another
company, an archived analytic account — for every entry in the database, and
that left out the posting additions of other modules. Version 19.0.1.0.1
removed it.

## Limitations {#limitations}

- The module adds no particulars of a corrective document beyond what
  Odoo's debit note already carries.
