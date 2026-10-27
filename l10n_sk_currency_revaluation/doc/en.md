---
title: SK Foreign-Currency Revaluation (kurzové rozdiely)
summary: Revalues foreign-currency balances at the reference rate of the balance-sheet date and books the differences on 563 and 663 — with the OCA wizard on Community and Odoo's adjustment entry on Enterprise.
verified: 19.0.1.0.1
---

## What it is for {#purpose}

At the date the financial statements are prepared for, open receivables and
payables in a foreign currency, foreign-currency bank accounts and cash are
revalued at the reference rate of that day; the difference against their
book value is an unrealised exchange gain or loss (*kurzový rozdiel*). The
Slovak chart books these on **563** *Kurzové straty* and **663** *Kurzové
zisky*.

Odoo itself books exchange differences only when a payment is reconciled
(on the same 563 / 663, as Odoo's Slovak chart sets them). Revaluation at the
balance-sheet date needs an extra tool, and which one depends on the
edition:

| Edition | Tool | Module |
|---|---|---|
| Community | OCA *Currency Revaluation* wizard (`account_multicurrency_revaluation`) | **this module**, [module:l10n_sk_currency_revaluation](module:l10n_sk_currency_revaluation) — see [Community](#community) |
| Enterprise | Odoo's *Unrealized Currency Gains/Losses* report and its adjustment entry | [module:l10n_sk_currency_revaluation_ee](module:l10n_sk_currency_revaluation_ee) — see [Enterprise](#enterprise) |

Both install themselves when their tool and the Slovak chart (`l10n_sk`) are
present. They set the accounts and the journal; the revaluation itself is
done by the tool.

## Legal background {#legal}

- Assets and liabilities in a foreign currency are converted to euro at the
  **reference rate** set by the European Central Bank or Národná banka
  Slovenska — for transactions, on the day before the transaction; at the
  balance-sheet date, **on the day the financial statements are prepared
  for** ([§ 24 ods. 2 of the Accounting Act](law:sk/2002/431#paragraf-24.odsek-2)).
- [§ 24 ods. 4 of opatrenie 740/2002](law:sk/2002/740#paragraf-24.odsek-4)
  books the exchange difference from that valuation on 563 or 663, including
  differences on items carried on 383 and 385.
- Some items keep the rate of the original transaction and are **not**
  revalued: advances paid and received on 314, 324 and 475, similar items on
  335, prepaid costs and deferred revenue on 381 and 384, and unbilled
  supplies on 326 until invoiced
  ([§ 24 ods. 3](law:sk/2002/740#paragraf-24.odsek-3)).

## Community: the OCA wizard {#community}

### What the module sets {#setup}

On every company with the Slovak chart — when the chart is loaded, or on
install for a company that already has it:

| Setting | Value |
|---|---|
| Revaluation loss account | 563000, if empty |
| Revaluation gain account | 663000, if empty |
| Currency gain & loss Default Journal | a journal **KURZ** *Kurzové rozdiely* of type *Miscellaneous*, created if the company has none with that code |

They are in *Accounting → Configuration → Settings*, section
*Multicurrency revaluation*, together with *Auto Post Created Entries*
(off: the entries are created as drafts).

### Before the first revaluation {#before}

1. **Give yourself access.** The OCA menus are visible only to members of
   the group *Additional provisioning entries posting* (*Zaúčtovanie
   dodatočných rezervných zápisov*), which nobody has by default. Add it on
   the user in *Settings → Users*, section *Extra Rights*, which appears in
   developer mode.
2. **Choose the accounts to revalue.** Tick *Allow Currency Revaluation* on
   each account whose foreign-currency balance is to be revalued: the
   foreign-currency bank and cash accounts (22x, 21x), receivables (311),
   payables (321) and others your accountant names. Leave it **off** on the
   accounts of § 24 ods. 3 — 314, 324, 475, 381, 384, 326.
3. **Load the rates.** The ECB reference rate for the balance-sheet date
   itself must be in Odoo.

### Running the revaluation {#usage}

*Accounting → Accounting → Closing → Currency Revaluation* (in Slovak
*Uzávierka → Precenenie meny*):

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

## Enterprise: the adjustment entry {#enterprise}

[module:l10n_sk_currency_revaluation_ee](module:l10n_sk_currency_revaluation_ee)
installs itself with Odoo Enterprise accounting and sets, on every Slovak
company:

| Setting of the adjustment entry | Value |
|---|---|
| Expense Provision Account | 563000 |
| Income Provision Account | 663000 |
| Journal | KURZ *Kurzové rozdiely*, created if missing, when the company has no revaluation journal yet |

On install both accounts are **overwritten**, whatever was set before.
Odoo's Slovak translation calls them *Účet rezervy na náklady* and *Účet
rezervy na výnosy*; they have nothing to do with provisions (*rezervy*) —
they are the counterpart accounts for the loss and the gain.

To revalue: *Accounting → Review → Regularization Entries → Unrealized
Currencies* (in Slovak *Kontrola → Regulatívne požiadavky → Kurzové
rozdiely*) opens the report. Set its date to the balance-sheet date and click
**Adjustment Entry** (*Korekčný záznam*). The wizard proposes the entry:
each foreign-currency account is adjusted, and the counterpart goes to
563000 for a loss or 663000 for a gain. A **Reversal Date** (*Dátum storna*)
is required: Enterprise always posts the reversal of the adjustment on that
date, typically the first day of the next period.

## Limitations {#limitations}

- The modules set accounts and a journal only. On Community nothing is
  revalued until accounts are flagged *Allow Currency Revaluation*, and the
  menus stay hidden until a user is given the group mentioned above.
- *Start Revaluation Period* defaults to the first day of the current month
  and silently limits the revaluation to items dated from then on.
- The Enterprise report proposes every foreign-currency account; it does
  not know which items § 24 ods. 3 excludes. Exclude those accounts in the
  report (they move under *Excluded Accounts*; Odoo remembers the choice per
  account and currency) before creating the entry.
- Enterprise always reverses the adjustment on the reversal date; there is
  no option to keep it.
- The hook creates the journal KURZ on every Slovak company that has no
  revaluation journal set, whether or not it uses foreign currencies.
