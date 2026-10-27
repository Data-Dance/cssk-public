---
title: CZ Foreign-Currency Revaluation (kurzové rozdíly)
summary: Revalues foreign-currency balances at the ČNB rate of the balance-sheet date and books the differences on 563 and 663 — with the OCA wizard on Community and Odoo's adjustment entry on Enterprise.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

At the balance-sheet date, open receivables and payables in a foreign
currency, foreign-currency bank accounts and cash are revalued at the rate
of that day; the difference against their book value is an unrealised
exchange gain or loss (*kurzový rozdíl*). The Czech chart books these on
**563** *Kursové ztráty* and **663** *Kurzové zisky*.

Odoo itself books exchange differences only when a payment is reconciled.
Revaluation at the balance-sheet date needs an extra tool, and which one
depends on the edition:

| Edition | Tool | Module |
|---|---|---|
| Community | OCA *Currency Revaluation* wizard (`account_multicurrency_revaluation`) | **this module**, [module:l10n_cz_currency_revaluation](module:l10n_cz_currency_revaluation) — see [Community](#community) |
| Enterprise | Odoo's *Unrealized Currency Gains/Losses* report and its adjustment entry | [module:l10n_cz_currency_revaluation_ee](module:l10n_cz_currency_revaluation_ee) — see [Enterprise](#enterprise) |

Both install themselves when their tool and the Czech chart (`l10n_cz`) are
present. They set the accounts and the journal; the revaluation itself is
done by the tool.

## Legal background {#legal}

References are to the [Accounting Act](law:cz/1991/563) unless stated
otherwise.

- Assets and liabilities are valued at the moment of the transaction and at
  the end of the balance-sheet day (§ 24 odst. 2). At the balance-sheet day
  only the items listed in § 4 odst. 12 are converted — receivables and
  payables, shares, securities, derivatives, valuables and foreign
  currencies, if expressed in a foreign currency (§ 24c odst. 1 písm. b)).
- The conversion uses the **general rate** (*obecný kurz*): the rate the
  central bank of the accounting currency declares for the day, i.e. the
  ČNB rate for a company keeping its books in CZK; the rate declared for the
  previous day may be used as well (§ 24d odst. 1 and 3).
- A **fixed rate** (*pevný kurz*) may be used only for transactions, not at
  the balance-sheet day (§ 24c odst. 2, § 24d odst. 4).
- The differences go to financial costs or financial revenue; for gradually
  repaid receivables and payables and for movements on groups 21, 22 and 26
  they may be booked at the balance-sheet day only — [§ 60 odst. 1 and 2 of
  vyhláška 500/2002 Sb.](law:cz/2002/500)

## Community: the OCA wizard {#community}

### What the module sets {#setup}

On every company with the Czech chart — when the chart is loaded, or on
install for a company that already has it:

| Setting | Value |
|---|---|
| Revaluation loss account | 563000, if empty |
| Revaluation gain account | 663000, if empty |
| Currency gain & loss Default Journal | a journal **KURZ** *Kurzové rozdíly* of type *Miscellaneous*, created if the company has none with that code |

They are in *Accounting → Configuration → Settings*, section
*Multicurrency revaluation*, together with *Auto Post Created Entries*
(off: the entries are created as drafts).

### Before the first revaluation {#before}

1. **Give yourself access.** The OCA menus are visible only to members of
   the group *Additional provisioning entries posting* (*Zaúčtování
   dodatečných rezervních zápisů*), which nobody has by default. Add it on
   the user in *Settings → Users*, section *Extra Rights*, which appears in
   developer mode.
2. **Choose the accounts to revalue.** Tick *Allow Currency Revaluation* on
   each account whose foreign-currency balance is to be revalued: the
   foreign-currency bank and cash accounts (22x, 21x), receivables (311) and
   payables (321), and others your accountant names. Leave it off on
   accounts that are not revalued, such as advances paid and received,
   whatever your internal rules exclude.
3. **Load the rates.** The ČNB rate for the revaluation date must be in
   Odoo, for example through
   [module:currency_rate_update_cz](module:currency_rate_update_cz).

### Running the revaluation {#usage}

*Accounting → Accounting → Closing → Currency Revaluation* (in Czech
*Uzávěrka → Přecenění měny*):

1. Enter the *Revaluation Date* (the balance-sheet date). **Clear *Start
   Revaluation Period*** or set it early enough: only journal items dated on
   or after it are revalued, and it defaults to the first day of the current
   month, which at year-end would leave out every open item from earlier
   months. Check the journal and the *Entry description* pattern.
2. Check the list of accounts: it starts with every account flagged
   *Allow Currency Revaluation*, and you can remove or add accounts for this
   run.
3. Click **Validate**. For receivable and payable accounts one entry is
   created per account, currency and partner; for other accounts one per
   account and currency. Losses go to 563000, gains to 663000.

The *Currency Revaluation Report* under *Accounting → Reporting → Closing
Entries* lists the unrealised differences. *Reverse Currency Revaluation*,
in the same *Closing* menu, reverses revaluation entries of a chosen
interval as of a date you set — whether to reverse at the start of the next
period is your accountant's choice.

### Companies on a fixed monthly rate {#fixed-rate}

A company that books its documents at a fixed monthly rate keeps that rate
in Odoo's ordinary rate table, and the balance-sheet day still requires the
general rate of the day (see [above](#legal)). When
[module:currency_rate_update_cz](module:currency_rate_update_cz) keeps
ČNB's actual daily rates beside the fixed one, this module makes the
revaluation wizard read the **actual rate** of the revaluation date (or the
latest one before it). A company on daily rates keeps no separate actual
rates, and nothing changes for it.

## Enterprise: the adjustment entry {#enterprise}

[module:l10n_cz_currency_revaluation_ee](module:l10n_cz_currency_revaluation_ee)
installs itself with Odoo Enterprise accounting and sets, on every Czech
company:

| Setting of the adjustment entry | Value |
|---|---|
| Expense Provision Account | 563000 |
| Income Provision Account | 663000 |
| Journal | KURZ *Kurzové rozdíly*, created if missing, when the company has no revaluation journal yet |

On install both accounts are **overwritten**, whatever was set before.

To revalue: *Accounting → Review → Regularization Entries → Unrealized
Currencies* opens the report (*Nezrealizované kurzovní rozdíly*). Set its
date to the balance-sheet date and click **Adjustment Entry** (*Zadání
úpravy*). The wizard proposes the entry: each foreign-currency account is
adjusted, and the counterpart goes to 563000 for a loss or 663000 for a
gain. A **Reversal Date** is required: Enterprise always posts the reversal
of the adjustment on that date, typically the first day of the next period.

Odoo's Czech translation of the two account fields reads *Účet zajišťování
výdajů* and *Účet poskytování příjmů*; these are the expense and income
provision accounts above.

## Limitations {#limitations}

- The modules set accounts and a journal only. On Community nothing is
  revalued until accounts are flagged *Allow Currency Revaluation*, and the
  menus stay hidden until a user is given the group mentioned above.
- The Enterprise report proposes every foreign-currency account. Exclude
  the ones that are not revalued in the report itself (they move under
  *Excluded Accounts*; Odoo remembers the choice per account and currency).
- Enterprise always reverses the adjustment on the reversal date; there is
  no option to keep it.
- *Start Revaluation Period* defaults to the first day of the current
  month and silently limits the revaluation to items dated from then on.
- Neither module checks which accounts are revalued: that, and whether
  advances or other items are excluded, is decided by your accountant.
- The hook creates the journal KURZ on every Czech company that has no
  revaluation journal set, whether or not it uses foreign currencies.
