---
title: CZ Deferrals and Accruals (časové rozlišení)
summary: Points Odoo's deferral tools at the Czech accounts 381, 383, 384 and 385 — the OCA cut-offs on Community, Odoo's own deferrals on Enterprise.
verified: 19.0.1.0.2
---

## What it is for {#purpose}

*Časové rozlišení* moves a cost or revenue into the period it belongs to
when the invoice falls into another one: insurance paid in advance for next
year, rent received in advance, a service of December invoiced in January.
The Czech chart keeps four accounts for it:

| Account | Czech term | Gloss | Typical case |
|---|---|---|---|
| 381 | Náklady příštích období | prepaid expense | insurance or rent paid in advance |
| 383 | Výdaje příštích období | accrued expense | rent paid in arrears |
| 384 | Výnosy příštích období | deferred revenue | rent or a subscription received in advance |
| 385 | Příjmy příštích období | accrued revenue | rent received in arrears |

Odoo has two different engines for this, depending on the edition. Neither
knows the Czech accounts. Two small modules connect them:

- **This module** ([module:l10n_cz_account_cutoff](module:l10n_cz_account_cutoff))
  fills the default accounts of the **OCA cut-offs**
  (`account_cutoff_start_end_dates`), which run on Community and Enterprise —
  see [Cut-offs](#cutoffs).
- [module:l10n_cz_account_deferred](module:l10n_cz_account_deferred) fills
  the accounts of **Odoo Enterprise's own deferrals** — see
  [Enterprise deferrals](#enterprise).

Both install themselves when their engine and the Czech chart (`l10n_cz`)
are present. Neither posts anything on its own: they only make the engine
post to the right accounts.

Items whose amount is **not yet known** at the period end belong on the
estimated-item accounts 388 and 389 (*dohadné účty*), not here; see
[module:l10n_cssk_accrual](module:l10n_cssk_accrual).

## Legal background {#legal}

- Under [§ 3 odst. 1 of the Accounting Act](law:cz/1991/563) items are
  booked in the period they relate to in time and substance, and all costs
  and revenues regardless of when they are paid or received.
- [Vyhláška 500/2002 Sb.](law:cz/2002/500), § 13 and § 19, describes the
  items: *náklady příštích období* are expenditure relating to costs of
  future periods, *příjmy příštích období* amounts not yet received that
  relate to revenue of the current period and are not booked directly as
  receivables, *výdaje příštích období* costs of the current period not yet
  paid, and *výnosy příštích období* receipts that belong to revenue of
  future periods. Both paragraphs set the test for using these accounts:
  at the time of booking, the purpose, the **amount** and the period must
  all be known. An item whose amount is not known goes on a *dohadný účet*.

## Cut-offs (OCA engine) {#cutoffs}

### What the module sets {#cutoffs-setup}

On a company with the Czech chart — when the chart is loaded, or on install
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
Tax Account for Accrued Expense / Revenue* the Czech chart does not have, so
every cut-off over taxed lines stopped with *Missing 'Accrued Expense Tax
Account'*. Nor would it be right: input VAT cannot be deducted before the
tax document is in hand ([§ 73 odst. 1 písm. a) of the VAT Act](law:cz/2004/235#p73)),
so an accrual on 383 / 385 is the amount without VAT. On install and upgrade
the option is switched off only where no accrued-tax account is configured, on the
company or on a tax; if your accountant set one up, it stays on.

You can change any of them there. Review two more settings of the same
block, which this module leaves alone:

- **Post Cut-off Journal Entry** is off: the cut-off entry is created as a
  draft for you to check and post.
- **Partner on Journal Items by Default** controls whether the entry keeps
  the partner on each line.

### Entering the dates {#cutoffs-dates}

The cut-off engine works from **start and end dates on invoice and bill
lines** (*Start Date*, *End Date*). Enter them on every line whose cost or
revenue covers a period — for example 1. 7. 2026 – 30. 6. 2027 on an annual
insurance bill. To make the dates compulsory for a product, tick *Must Have
Start/End Dates* on it.

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
  as of the first day of the next period (*Reverse Entry* on the entry), so
  the original invoice lines carry the cost again in the period they belong
  to.

Only one cut-off per type and date can exist in a company.

## Enterprise deferrals {#enterprise}

Odoo Enterprise (`account_accountant`) has its own deferrals: on a bill or
invoice line you set the period in the **Deferred Date** column, and Odoo
spreads the amount through a deferral account by month or by day.

[module:l10n_cz_account_deferred](module:l10n_cz_account_deferred) installs
itself with `account_accountant` on a database with the Czech chart and
sets, in *Accounting → Configuration → Settings*:

| Setting | Value |
|---|---|
| Deferred expense entries → Deferred expense | 381000 |
| Deferred revenue entries → Deferred revenue | 384000 |
| *Journal* of both blocks | the company's first *Miscellaneous* journal, if empty |

Without it Enterprise fills the two accounts with the first current-asset
and the first current-liability account of the chart, whatever they are. On
install the module sets both accounts on every Czech company where they are
empty or still on that generic choice; an account you had set by hand is
kept. Later, only new companies are touched.

Whether entries are generated when the bill is posted (*On bill
validation*) or in one batch (*Manually & Grouped*), and whether the amount
is split by months or days, are Enterprise's own settings in the same
blocks. The deferral reports are under *Accounting → Review →
Regularization Entries → Deferred Expenses / Deferred Revenues*.

Enterprise deferrals cover only the in-advance cases, 381 and 384. Accrued
items on 383 and 385 need the cut-offs above or a manual entry.

## Limitations {#limitations}

- Both modules only set default accounts and journals. They neither compute
  nor post anything themselves.
- Accrued items are booked without VAT. For a company that is not a VAT
  payer, whose VAT is a cost, add the VAT to the accrual by hand.
- Cut-off entries are not reversed automatically.
- On Enterprise both engines can be installed at the same time, and an
  invoice line then shows both sets of dates. Use one engine for a given
  line: dates entered in both would defer the amount twice.
- Account 382 *Komplexní náklady příštích období* is not mapped.
- Neither module checks the vyhláška's condition that the amount and period
  are known; an estimate does not belong in a cut-off.
