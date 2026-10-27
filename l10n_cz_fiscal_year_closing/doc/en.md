---
title: CZ Year-End Closing (accounts 701 / 702 / 710)
summary: Makes the Czech closing accounts 701, 702 and 710 postable, so that the year-end closing and the opening balance can be booked at all.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Czech double-entry bookkeeping closes and opens the books through the
closing accounts of class 7:

| Account | Czech name | Role |
|---|---|---|
| 701 | *Počáteční účet rozvažný* (opening balance-sheet account) | counterpart of the opening balances of the balance-sheet accounts |
| 702 | *Konečný účet rozvažný* (closing balance-sheet account) | counterpart of the closing balances of the balance-sheet accounts |
| 710 | *Účet zisků a ztrát* (profit and loss account) | collects the closing balances of the cost and revenue accounts |

Odoo's Czech chart of accounts (`l10n_cz`) ships these three as off-balance
accounts, and Odoo refuses any journal entry that mixes an off-balance account
with an ordinary one. Closing class 5 or 6 against 710, closing balance-sheet
accounts against 702, and posting an opening balance against 701 are all such
mixes, so as shipped **none of them can be posted** — not only at year end,
but also when a company enters its opening balances on going live.

This module fixes exactly that, and nothing more.

## Legal background {#legal}

- An accounting unit closes its books on the last day of the accounting
  period and opens them on the first day of the next —
  [§ 17 odst. 2 písm. b) and odst. 1 písm. b) of the Accounting Act](law:cz/1991/563).
- The opening balances of the balance-sheet accounts must follow on from the
  closing balances with which the previous period was closed —
  [§ 19 odst. 4 of the Accounting Act](law:cz/1991/563).
- The chart of accounts for entrepreneurs places the closing accounts in
  class 7 *Závěrkové a podrozvahové účty*: group 70 *Účty rozvažné* and group
  71 *Účet zisků a ztrát* —
  [annex 4 to Decree No. 500/2002 Sb.](law:cz/2002/500) (*směrná účtová
  osnova*). They are closing accounts, not off-balance ones (those are groups
  75–79).

## What changes {#retype}

The module changes the account type of 701000, 702000 and 710000 from
*Off-Balance Sheet* (*Podrozvahový* in the Czech translation) to *Equity*:

- for every company that already has the Czech chart, once, when the module
  is installed — only where the account is still off-balance; a type you set
  yourself is left alone;
- for companies that load the Czech chart later, through the chart template.

There are no settings and no new screens. What this means for you:

- Closing entries, opening entries and opening balances against 701 can be
  posted.
- The Czech statutory statements are not affected: they map their rows by
  account **code**, not by account type.
- Odoo's own generic balance sheet now shows the three accounts in equity.
  After a matched closing and opening they net to zero, but a period with a
  closing and no opening yet (or the reverse) shows a balance on them.

## Limitations {#limitations}

- The module does **not** produce the closing entries. Post them yourself,
  or with a tool such as the OCA module `account_fiscal_year_closing`, for
  which no Czech closing template is provided (the Slovak module
  [module:l10n_sk_fiscal_year_closing](module:l10n_sk_fiscal_year_closing)
  ships one for the Slovak chart).
- Only companies using the Czech chart (`cz`) are changed. Off-balance
  accounts you add yourself in groups 75–79 keep their type, as they should.
- If you post closing and opening entries, keep them in a dedicated journal
  and register it in the company's *Year-end closing journals*
  ([module:l10n_cssk_core](module:l10n_cssk_core)), so that the statutory
  statements and the income tax return leave them out; otherwise every closed
  account shows zero on the last day of the year. In this version that field
  is not shown on any form; an administrator sets it, for example by
  importing it into the list of companies.
