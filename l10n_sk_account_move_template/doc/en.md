---
title: SK Posting Templates for Internal Documents (predkontácie)
summary: Ready-made Slovak debit/credit patterns for internal documents — money in transit via 261 and the transfer of the approved result — that turn one typed amount into a balanced draft entry.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Some entries have no source document for Odoo to derive accounts from:
cash taken from the till to the bank, the profit or loss transferred once
the general meeting has approved the financial statements. The accountant
posts them as an internal document (*interný doklad*), usually from a
memorised pattern.

This module ships such patterns as **journal entry templates** of the OCA
engine `account_move_template`, for companies with the Slovak chart. You pick
a template, type one amount and get a balanced **draft** entry.

**What this is not.** In Slovak accounting programs a *predkontácia* is
usually chosen **on a document** — an invoice, a bank statement, a cash
receipt — and drives how that document is posted. The OCA engine has no link
to any document: it only composes a new manual entry. Invoices, bank and cash
keep getting their accounts from Odoo itself — from the product or product
category, the partner's receivable and payable accounts, the fiscal position,
the tax settings, the journal and the reconciliation models. An existing list
of predkontácie from another program mostly maps onto those, not onto
templates.

## The templates {#templates}

Created in the company's *Miscellaneous* journal (code `general` in the
chart). Line 1 is the amount you type; line 2 copies it.

| Template | Debit (line 1) | Credit (line 2) |
|---|---|---|
| Výber z pokladnice (na peniaze na ceste) | Liquidity Transfer (261…) | the cash journal's account |
| Príjem na bankový účet (z peňazí na ceste) | the bank journal's account | Liquidity Transfer (261…) |
| Výber z bankového účtu (na peniaze na ceste) | Liquidity Transfer (261…) | the bank journal's account |
| Vklad do pokladnice (z peňazí na ceste) | the cash journal's account | Liquidity Transfer (261…) |
| Preúčtovanie schváleného zisku (431 na 428) | 431000 Výsledok hospodárenia v schvaľovaní | 428000 Nerozdelený zisk minulých rokov |
| Preúčtovanie schválenej straty (431 na 429) | 429000 Neuhradená strata minulých rokov | 431000 Výsledok hospodárenia v schvaľovaní |

The four money-in-transit templates make the two halves of a transfer
between cash and bank: the withdrawal on one day, the deposit on another,
with 261 bridging the gap. They use the accounts the company's books
actually post to:

- **Money in transit**: the *Liquidity Transfer* account Odoo creates with
  the chart (a 261 account such as 261001, set as the company's internal
  transfer account), not 261000: in Odoo's Slovak chart 261000 is the bank
  suspense account, where unreconciled statement lines wait.
- **Bank and cash**: the account of the company's first bank journal and
  first cash journal (Odoo gives each journal its own, such as 221001).
  Odoo's Slovak chart creates no cash journal, so until you create one the
  cash templates use the summary account 211000; after creating it, change
  the cash lines to its account.

The two result templates follow the decision on
the profit or loss; the opening of the year that puts the result on 431 is
described in
[module:l10n_sk_fiscal_year_closing](module:l10n_sk_fiscal_year_closing#result-431).

The template names are Slovak in every language: Odoo does not translate
template names.

## Setting it up {#setup}

The templates are created when the Slovak chart is loaded into a company,
and on install for companies that already have it. A company without a
*Miscellaneous* journal from the chart is skipped. Re-installing never
duplicates a template or reverts a change you made to it.

Before the first use, open each template in *Accounting → Configuration →
Accounting → Journal Entry Templates* (in Slovak *Účtovné vzory
(predkontácie)*; the menu needs accounting-administrator rights) and check:

- **The bank and cash accounts.** The templates take the account of the
  first bank and cash journal. With several bank accounts, copy a template
  per bank account and change its line.

Templates are ordinary records: rename them, change accounts, add lines or
create new ones to match your internal rules (*vnútorná smernica*).

## Posting an entry {#usage}

1. *Accounting → Accounting → Create Entry from Template* (in Slovak
   *Vytvoriť zápis podľa vzoru*), or **Generate Journal Entry** on a
   template's form.
2. Pick the template and click **Next** (*Ďalej*).
3. Check the date, journal, reference and partner, and type the amount on
   the line offered.
4. Click **Create Journal Entry** (*Vytvoriť účtovný zápis*).

The entry is created **in draft**; review it and post it as usual.

## Limitations {#limitations}

- Templates create new manual entries only; they cannot be attached to an
  invoice, bank statement or cash document, and they do not change how those
  are posted.
- Templates created before version 19.0.1.1.0 used 221000, 211000 and
  261000; the upgrade moves lines still on those accounts to the accounts
  above and leaves a line you changed alone.
- One bank and one cash account per template; see [Setting it up](#setup).
- The starter set is deliberately small. It does not cover, for example,
  dividends, statutory reserves or the transfer of a result to the
  shareholders' accounts; add those to suit the company.
- The account mapping should be reviewed with your accountant.
