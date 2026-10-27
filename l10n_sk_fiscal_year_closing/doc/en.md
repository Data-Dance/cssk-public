---
title: SK Year-End Closing (accounts 701 / 702 / 710)
summary: Closes the Slovak books at year end through the closing accounts 710, 702 and 701, and makes those accounts postable in the first place.
verified: 19.0.1.0.2
---

## What it is for {#purpose}

Slovak double-entry bookkeeping closes the year through three **closing
accounts** (*závierkové účty*), which standard Odoo does not know:

| Account | Slovak name | Role |
|---|---|---|
| 710 | *Účet ziskov a strát* (profit and loss account) | collects the year-end balances of class 5 (costs) and class 6 (revenues); its balance is the result for the year |
| 702 | *Konečný účet súvahový* (closing balance-sheet account) | collects the closing balances of every balance-sheet account (classes 0–4) and the result from 710 |
| 701 | *Začiatočný účet súvahový* (opening balance-sheet account) | opens the balance-sheet accounts again on the first day of the new year |

The module does two things:

1. **It makes 701, 702 and 710 postable.** Odoo's Slovak chart of accounts
   ships them as off-balance accounts, and Odoo refuses any journal entry that
   mixes an off-balance account with an ordinary one. A closing entry is
   exactly such a mix, so without this module no closing could be posted
   at all (see [Accounts retyped](#retype)).
2. **It ships a closing template** for the OCA *Fiscal year closing* engine
   (`account_fiscal_year_closing`), which produces the three closing and
   opening entries from the ledger.

It installs itself when the Slovak chart of accounts (`l10n_sk`) and
`account_fiscal_year_closing` are both installed.

## Legal background {#legal}

- **When the books are closed and opened.** A legal entity closes its books
  on the last day of the accounting period and opens them on the first day of
  the next one —
  [§ 16 ods. 4 písm. b)](law:sk/2002/431#paragraf-16.odsek-4.pismeno-b) and
  [§ 16 ods. 1 písm. b) of the Accounting Act](law:sk/2002/431#paragraf-16.odsek-1.pismeno-b).
  Closing the books on the last day of the period is what makes the financial
  statements *riadna* (ordinary) —
  [§ 17 ods. 6](law:sk/2002/431#paragraf-17.odsek-6).
- **How the closing is posted.** The Ministry of Finance's *opatrenie* on
  accounting procedures for entrepreneurs in double-entry bookkeeping
  (MF SR No. 23054/2002-92, announced as
  [No. 740/2002 Z. z.](law:sk/2002/740)) prescribes the sequence in
  [§ 8 ods. 2](law:sk/2002/740#paragraf-8.odsek-2): first the income tax is
  computed and booked (letter c); then the closing balances of the cost
  accounts are posted against 710 and those of the revenue accounts likewise
  (letter d); the closing balances of the asset accounts and of the liability
  and equity accounts are posted against 702 (letter e); finally the result
  is transferred from 710 to 702 (letter f).
- **How the books are opened.** Under
  [§ 7 ods. 2](law:sk/2002/740#paragraf-7.odsek-2) the opening balances are
  posted against 701. Under
  [§ 7 ods. 3](law:sk/2002/740#paragraf-7.odsek-3) the result of the previous
  period is opened on **431** *Výsledok hospodárenia v schvaľovaní* (result
  awaiting approval), and under
  [§ 7 ods. 4](law:sk/2002/740#paragraf-7.odsek-4) it leaves 431 when the
  competent body decides how to distribute the profit or settle the loss.
- **General partnerships.** In a *verejná obchodná spoločnosť* (and towards
  the general partners of a *komanditná spoločnosť*) the result is not
  transferred to 702 but booked as the partners' share through 596 —
  [§ 8 ods. 4](law:sk/2002/740#paragraf-8.odsek-4). The template does not
  cover this case.

## Accounts retyped {#retype}

Odoo's Slovak chart gives 701000, 702000 and 710000 the account type
*Off-Balance Sheet* (*Podsúvaha* in the Slovak translation). Odoo has a hard
rule that an entry containing an off-balance account may not contain any
other kind of account. Closing class 5 against 710, or a balance-sheet account
against 702, breaks that rule, and Odoo rejects the entry.

The module therefore changes the type of these three accounts to *Equity*:

- for every company that already has the Slovak chart, once, when the module
  is installed (only where the account is still off-balance — a type you set
  yourself is left alone);
- for companies that load the Slovak chart later, through the chart template.

What this changes for you:

- The closing and opening entries, and any opening balance posted against
  701, can be posted.
- The Slovak statutory statements are not affected: they map rows by account
  **code**, not by type, and leave out class 7 altogether.
- Odoo's own generic balance sheet now shows the three accounts in equity.
  After a matched closing and opening they net to zero, but a period with a
  closing and no opening yet (or the reverse) shows a balance on them.
- Account 711 *Začiatočný účet nákladov a výnosov* is not touched and stays
  off-balance; the template does not use it.

## Setting it up {#setup}

The template appears under *Accounting → Configuration → Fiscal Year Closing →
Closing templates* as **Účtovná závierka (SK) — 701 / 702 / 710** (the engine's
own screens are in English). It has three steps:

| Step | Code | Entry | Date |
|---|---|---|---|
| Uzavretie nákladov a výnosov (710) | SK_PL | class 5 and class 6 → 710000 | last day of the year |
| Uzavretie súvahových účtov (702) | SK_CLOSING | classes 0–4 and 710 → 702000 | last day of the year |
| Otvorenie súvahových účtov (701) | SK_OPENING | reverse of SK_CLOSING, against 701000; the result on 431000 | opening date |

Receivable and payable accounts are closed **per partner** (*Un-reconciled*),
so every partner's balance is carried into the new year; all other accounts
are closed by their balance.

Before the first closing:

- **Create a journal for the closing**, for example *UZAV* of type
  *Miscellaneous*, and set it as the *Journal* of each step — on the template
  or on the closing itself. Without one, the engine uses the journal with
  code `MISC`, or the first miscellaneous journal.
- **Register that journal as a year-end closing journal of the company**
  (field *Year-end closing journals*, *Denníky koncoročnej uzávierky* in
  Slovak, provided by [module:l10n_cssk_core](module:l10n_cssk_core)). The
  statutory financial statements and the income tax return leave entries in
  those journals out, and [module:l10n_cssk_account_financial_report](module:l10n_cssk_account_financial_report)
  can do the same in the ledger reports. Otherwise the closing entries count
  as ordinary activity, and on the last day of the year every closed account
  shows zero. In this version the field is not shown on any form; an
  administrator sets it, for example by importing it into the list of
  companies.
- **Review the template with your accountant.** It is copied into each
  closing, so changes made there apply to that closing only.

## Closing a year {#usage}

1. Book everything for the year, **including the income tax** (591 / 341),
   which § 8 ods. 2 písm. c) requires before the accounts are closed.
2. *Accounting → Accounting → Fiscal year closings*, then *New*. Enter the
   year (for a fiscal year spanning two calendar years, the later one) and
   check *From date*, *To date* and *Opening date*. Choose the closing
   template; its steps are copied into *Moves configuration*, where you can
   still change journals, dates and mappings.
3. *Check draft moves* is on by default: the calculation stops if any draft
   entry is dated within the year.
4. Click **Calculate**. The three entries are created as drafts. Review them
   with **Show moves** / **Show move lines**. If one of them does not
   balance, Odoo shows the unbalanced lines instead.
5. Click **Confirm and post moves**. *Cancel* removes the closing entries again; *Recalculate* deletes
   and recreates them.

What the module changes in the engine for Slovak companies:

- **702 carries a counter-entry for every account.** The generic engine
  would post a single line with the net of all sources — which on a complete
  balance sheet is zero, so 702 would not appear at all. Here each closed
  account has its mirror line on 702 (or on 710 in the first step), and 702
  sums to zero by the balance-sheet equation.
- **The opening runs through 701.** The engine opens the year by reversing
  the closing entry, which would leave 702 on both sides. The module moves
  the counterpart of the opening entry to 701000.
- **The result is reopened on 431.** The reversal would also put the result
  back on 710; the module moves that line to 431000 (see below).

### The result in the opening entry {#result-431}

The closing carries the result from 710 to 702. In the opening entry the
module books it on **431000** *Výsledok hospodárenia v schvaľovaní*, as
§ 7 ods. 3 of the opatrenie requires: a profit as 701 debit / 431 credit, a
loss as 431 debit / 701 credit. 710 does not appear in the opening entry.
If the company has no account 431000, the line stays on 710 and the server
log says so; change it to your 431 account before posting.

Opening entries posted with version 19.0.1.0.1 or earlier reopened the result
on 710. If you have one, post an entry on its opening date moving the balance
from 710 to 431.

The decision of the general meeting (or other competent body) on the result
is a separate entry, posted later: [module:l10n_sk_account_move_template](module:l10n_sk_account_move_template)
provides the templates *Preúčtovanie schváleného zisku (431 na 428)* and
*Preúčtovanie schválenej straty (431 na 429)*.

## Limitations {#limitations}

- Income tax is not computed or booked by the closing.
- General partnerships (§ 8 ods. 4 of the opatrenie, account 596) are not
  covered by the template.
- Balances are taken from entries dated between *From date* and *To date*. A
  balance-sheet account whose opening balance was posted before the start of
  the year (for example by a data migration dated earlier) is closed only for
  the movement of the year. Open each year with an entry dated on its first
  day.
- Closing and opening lines on receivable and payable accounts are not
  reconciled with the invoices they carry forward. They net to zero per
  partner, but appear in open-item lists and ageing reports.
- Only Slovak companies (chart template `sk`) get the per-account mirroring,
  the 701 opening and the result on 431; other companies keep the engine's generic behaviour.
- Closing conventions differ between accountants, notably in how the result
  reaches 702. The template is a starting point and should be signed
  off by your accountant before the first live closing.
