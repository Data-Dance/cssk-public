---
title: SK Deferrals and Accruals (časové rozlíšenie)
summary: Points Odoo's deferral tools at the Slovak accounts 381, 383, 384 and 385 — the OCA cut-offs on Community, Odoo's own deferrals on Enterprise.
verified: 19.0.1.0.3
---

## What it is for {#purpose}

*Časové rozlíšenie* moves a cost or revenue into the period it belongs to
when the invoice falls into another one: insurance paid in advance for next
year, rent received in advance, a service of December invoiced in January.
The Slovak chart keeps four accounts for it:

| Account | Slovak term | Gloss | Typical case |
|---|---|---|---|
| 381 | Náklady budúcich období | prepaid expense | insurance or rent paid in advance |
| 383 | Výdavky budúcich období | accrued expense | rent paid in arrears |
| 384 | Výnosy budúcich období | deferred revenue | rent or a subscription received in advance |
| 385 | Príjmy budúcich období | accrued revenue | rent received in arrears |

Odoo has two different engines for this, depending on the edition. Neither
knows the Slovak accounts. Two small modules connect them:

- **This module** ([module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff))
  fills the default accounts of the **OCA cut-offs**
  (`account_cutoff_start_end_dates`), which run on Community and Enterprise —
  see [Cut-offs](#cutoffs).
- [module:l10n_sk_account_deferred](module:l10n_sk_account_deferred) fills
  the accounts of **Odoo Enterprise's own deferrals** — see
  [Enterprise deferrals](#enterprise).

Both install themselves when their engine and the Slovak chart (`l10n_sk`)
are present. Neither posts anything on its own: they only make the engine
post to the right accounts.

Items whose amount is **not yet known** at the period end are not
*časové rozlíšenie*; for those see
[module:l10n_cssk_accrual](module:l10n_cssk_accrual).

## Legal background {#legal}

- The [Accounting Act](law:sk/2002/431) requires items to be booked and
  reported in the period they relate to in time and substance —
  [§ 3 ods. 1](law:sk/2002/431#paragraf-3.odsek-1).
- [Opatrenie 740/2002 Z. z.](law:sk/2002/740) names the accounts:
  costs and expenditure relating to future periods are deferred on 381 and
  382, or 383 ([§ 5 ods. 3](law:sk/2002/740#paragraf-5.odsek-3)); revenue
  and income on 384 or 385 ([§ 5 ods. 4](law:sk/2002/740#paragraf-5.odsek-4)).
  [§ 56](law:sk/2002/740#paragraf-56) describes each account — prepaid rent
  and subscriptions on 381, rent paid in arrears on 383, rent received in
  advance on 384, rent received in arrears on 385 — and lists costs that are
  **not** deferred, such as advertising, training and market research,
  unless the service itself is paid in advance (§ 56 ods. 6).

Account 382 *Komplexné náklady budúcich období* is not mapped by either
module.

## Cut-offs (OCA engine) {#cutoffs}

### What the module sets {#cutoffs-setup}

On a company with the Slovak chart — when the chart is loaded, or on install
for a company that already has it — the module fills, only where empty:

| Setting (*Accounting → Configuration → Settings*, block *Cut-offs*) | Account |
|---|---|
| Default Account for Prepaid Expense | 381000 |
| Default Account for Accrued Expenses | 383000 |
| Default Account for Prepaid Revenue | 384000 |
| Default Account for Accrued Revenues | 385000 |
| Default Cut-off Journal | the company's first *Miscellaneous* journal |

It also switches **Accrual On Taxes** off. The OCA engine has it on by
default and then accrues the VAT of the source lines as well, on a *Default
Tax Account for Accrued Expense / Revenue* the Slovak chart does not have, so
every cut-off over taxed lines stopped with *Missing 'Accrued Expense Tax
Account'*. Nor would it be right: input VAT cannot be deducted before the
invoice is in hand ([§ 51 ods. 1 písm. a) of the VAT Act](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a)),
so an accrual on 383 / 385 is the amount without VAT. On install and upgrade
the option is switched off only where no accrued-tax account is configured, on the
company or on a tax; if your accountant set one up, it stays on.

You can change any of them there. Review two more settings of the same
block, which this module leaves alone:

- **Post Cut-off Journal Entry** is off: the cut-off entry is created as a draft for you to check
  and post.
- **Partner on Journal Items by Default** controls whether the entry keeps
  the partner on each line.

### Entering the dates {#cutoffs-dates}

The cut-off engine works from **start and end dates on invoice and bill
lines** (*Start Date*, *End Date*). Enter them on every line
whose cost or revenue covers a period — for example 1. 7. 2026 – 30. 6. 2027
on an annual insurance bill. To make the dates compulsory for a product,
tick *Must Have Start/End Dates* on it.

### Running a cut-off {#cutoffs-usage}

At the period end: *Accounting → Accounting → Cut-offs*, then the type,
then *New*:

| Menu | Account | Lines it picks up |
|---|---|---|
| Prepaid Expense | 381 | bill lines dated on or before the cut-off date whose end date is after it; the part after the cut-off date is deferred |
| Prepaid Revenue | 384 | the same for invoice lines |
| Accrued Expense | 383 | bill lines dated **after** the cut-off date whose start date is on or before it; the part up to the cut-off date is brought back |
| Accrued Revenue | 385 | the same for invoice lines |

The amount is split by days. Enter the cut-off date and check the source
journals, then click **Re-Generate Lines**, review the lines and click
**Create Journal Entry**. The entry is dated on the cut-off date.

Two practical consequences:

- 383 and 385 work only with invoices **already booked** with a later date —
  run them when the January invoices for December services are in, before
  the books are closed.
- The cut-off entry is **not reversed automatically**. Reverse it yourself
  as of the first day of the next period (*Reverse Entry* on the entry), so the
  original invoice lines carry the cost again in the period they belong to.

Only one cut-off per type and date can exist in a company.

## Enterprise deferrals {#enterprise}

Odoo Enterprise (`account_accountant`) has its own deferrals: on a bill or
invoice line you set the period in the **Deferred Date** column, and Odoo spreads the amount through a deferral
account by month or by day.

[module:l10n_sk_account_deferred](module:l10n_sk_account_deferred) installs
itself with `account_accountant` on a database with the Slovak chart and
sets, in *Accounting → Configuration → Settings*:

| Setting | Value |
|---|---|
| Deferred expense entries → Deferred expense | 381000 |
| Deferred revenue entries → Deferred revenue | 384000 |
| *Journal* of both blocks | the company's first *Miscellaneous* journal, if empty |

Without it Enterprise fills the two accounts with the first current-asset
and the first current-liability account of the chart, whatever they are. On
install the module sets both accounts on every Slovak company where they are
empty or still on that generic choice; an account you had set by hand is
kept. Later, only new companies are touched.

Whether entries are generated when the bill is posted (*On bill
validation*) or in one batch (*Manually & Grouped*), and
whether the amount is split by months or days, are Enterprise's own settings
in the same blocks. The deferral reports are under *Accounting → Review → Regularization
Entries → Deferred Expenses / Deferred Revenues* (in Slovak the middle
menu reads *Regulatívne požiadavky*, a mistranslation).

Enterprise deferrals cover only the in-advance cases, 381 and 384. Accrued
items on 383 and 385 need the cut-offs above or a manual entry.

## Limitations {#limitations}

- Both modules only set default accounts and journals. They neither compute
  nor post anything themselves.
- Accrued items are booked without VAT. For a company that is not a VAT
  payer, whose VAT is a cost, add the VAT to the accrual by hand.
- Cut-off entries are not reversed automatically.
- Odoo's Slovak chart names account 385000 *Náklady budúcich období
  (krátkodobé)* and 383000 *Výdaje budúcich období*; the opatrenie calls them
  *Príjmy budúcich období* and *Výdavky budúcich období*. The accounts are the
  right ones; only the names shipped by Odoo are off. Rename them in the chart
  of accounts if they confuse your users.
- On Enterprise both engines can be installed at the same time, and an
  invoice line then shows both sets of dates. Use one engine for a given
  line: dates entered in both would defer the amount twice.
- Neither module checks whether a cost may be deferred at all (§ 56 ods. 6
  of the opatrenie).
