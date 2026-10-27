---
title: CZ/SK Internal Document (interní / interný doklad)
summary: Prints a journal entry as the internal accounting document — interní doklad in Czech, interný doklad in Slovak — with the particulars the accounting acts require.
verified: 19.0.1.0.1
---

## What it is for {#purpose}

Every accounting entry needs an accounting document behind it. For an invoice
or a bank statement that is the external document itself; for an entry that
has nothing external behind it — an accrual, depreciation, a revaluation, a
closing entry, a manual correction — the accountant writes an **internal
document** (*interní doklad* in Czech, *interný doklad* in Slovak).

Odoo has no such printout. This module adds one: any journal entry prints as an
internal document carrying the particulars the law asks of an accounting
document, with a line for each signature.

It depends only on Odoo's `account` and does not need the rest of the
Czech/Slovak localization.

## Legal background {#legal}

- **Czech Republic.** [§ 11 odst. 1 of the Accounting Act No. 563/1991 Sb.](law:cz/1991/563)
  requires an accounting document (*účetní doklad*) to contain its
  designation, the content of the accounting case and its participants, the
  amount, the moment the document was prepared, the moment the case occurred
  if that differs, and the signature record of the person responsible for the
  case **and** of the person responsible for booking it.
- **Slovakia.** [§ 10 ods. 1 of the Accounting Act No. 431/2002 Z. z.](law:sk/2002/431#paragraf-10.odsek-1)
  requires the same particulars except the second signature: only the
  signature record of the person responsible for the accounting case, and that
  only where the case is not verified by electronic data interchange or an
  internal control system (§ 32 ods. 3 písm. b) and c)).

The printout follows the Czech list, which is the longer one, so it satisfies
both. On a Slovak document the second signature line is simply more than the
law asks for.

## How to print it {#usage}

Open a journal entry (*Accounting → Accounting → Journal Entries*, or any
invoice, bill or entry) and choose *Print → Interní / interný doklad*. You can
also select several entries in the list and print them together; each gets its
own page. The file is named after the document, e.g.
`Interní doklad - MISC-2026-10-0007.pdf`.

There is nothing to set up.

## What the document shows {#content}

| On the printout (CZ / SK) | Taken from |
|---|---|
| Označení dokladu / Označenie dokladu | the entry number |
| Účetní jednotka / Účtovná jednotka | the company, with its company registry number (IČO) when filled in |
| Deník / Denník | the journal |
| Obsah účetního případu / Obsah účtovného prípadu | the entry's *Reference*; if empty, its internal note; if that is empty too, the labels of its lines |
| Účastníci účetního případu / Účastníci účtovného prípadu | the company, then every partner on the entry and its lines |
| Peněžní částka / Peňažná suma | the entry total (sum of debits), in company currency |
| Datum vyhotovení / Dátum vyhotovenia | the day the entry was **created** in Odoo |
| Datum uskutečnění účetního případu / Dátum uskutočnenia účtovného prípadu | the accounting date |
| Lines | account, label, partner, analytic distribution with shares (e.g. `Warehouse (60 %)`), Má dáti / Má dať, Dal, and totals |
| Signature records | on the left the user who **created** the entry, as responsible for the accounting case; on the right whoever **posted** it, as responsible for booking it; each with a line to sign on |

A draft entry prints with **NEZAÚČTOVÁNO** / **NEZAÚČTOVANÉ** (not booked)
under the title, and without a name on the booking signature.

## Language {#language}

The wording is the statute's own and is **not translated**: it follows the
company's fiscal country. A Slovak company prints the Slovak terms; every other
company prints the Czech ones. The user's language does not matter.

## Limitations {#limitations}

- *Datum vyhotovení* is the day the record was created in Odoo, not a date you
  choose. If the document was prepared on another day, the printout does not
  show it.
- The person who posted the entry is read from the entry's history (the last
  change of status). If the entry was posted by the scheduled auto-posting,
  that is the user the automation runs as; if the history was deleted, the
  name stays empty.
- The printed names are the Odoo users who created and posted the entry, not
  necessarily the persons your internal rules make responsible. The signature
  lines are for an actual signature; the module does not sign anything
  electronically.
- Quantities and unit prices are not printed; the amount is the entry total.
- Every entry can be printed this way, including invoices and bills, although
  they already have an external document.
