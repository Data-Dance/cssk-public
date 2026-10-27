---
title: Exchange Rates for the Czech Republic (ČNB)
summary: Downloads the Czech National Bank's daily exchange rate, sets the provider up for you, and supports a fixed monthly rate with the actual daily rates kept for the year-end revaluation.
verified: 19.0.1.3.2
---

## What it is for {#purpose}

A Czech company keeping its books in Czech crowns converts foreign-currency
documents at the **exchange rate announced by Česká národní banka** (ČNB,
*kurz devizového trhu*). Odoo's standard ECB service gives a different number,
so this module adds ČNB as a source to the OCA rate-update framework
([module:currency_rate_update](module:currency_rate_update)) and:

- **creates the ČNB provider for you** when it is installed;
- reads **whole ranges of past dates** correctly, one ČNB yearly file per year;
- supports a **fixed monthly rate** (*pevný kurz*) for companies that use one,
  while keeping the actual daily rates for the balance-sheet revaluation.

It works on Community and Enterprise alike.

## Legal background {#legal}

- **Accounting.** Foreign-currency assets and liabilities are converted at the
  *obecný kurz* — the rate the central bank of the accounting currency (for
  crowns, ČNB) announces for the day of conversion — both when the transaction
  is booked and at the balance-sheet date. For the transaction date a company
  may instead use a **fixed rate**: the rate announced for the first day of a
  period the company chooses in an internal rule, ending at the latest on the
  last day of the accounting period. Banks, insurers and some other regulated
  entities may not use a fixed rate. See § 24c and § 24d of the
  [Accounting Act](law:cz/1991/563).
- **VAT.** A foreign-currency amount is converted at the rate valid for the
  person converting it on the day the tax becomes due — the ČNB rate or the
  ECB reference rate. See § 4 odst. 8 of the [VAT Act](law:cz/2004/235). A
  company on a fixed accounting rate therefore uses that rate for VAT too.

## What installation sets up {#setup}

On installation, every company whose country (or fiscal country) is the Czech
Republic gets a **Česká národní banka** provider, provided the database already
has at least one active foreign currency that ČNB publishes. The provider:

- quotes **the currencies already active** in the database that ČNB publishes,
  never the company's own currency — it does not activate new ones;
- runs **daily**, in *Daily rate* mode;
- has *Fill non-publishing days* switched on when
  [module:currency_rate_update_sk](module:currency_rate_update_sk) is also
  installed (that option belongs to it).

A company that already has a ČNB provider, even an archived one, is left alone.
A company with no active foreign currency gets no provider.

The providers are listed in *Accounting → Configuration → Currency Rates
Providers* — on Community without full accounting the root menu reads
*Invoicing*. The screen comes from the OCA module and, like this module's own
fields, shows in English.

If you activate a currency **after** installation and the list is still
empty, create the provider yourself: *New*, *Provider* = **Česká národní
banka**, pick the *Currencies*, leave the interval at 1 day, save. The list
also has a button, **Create the Czech default provider**, shown even when the
list is empty; it creates only what is missing and needs Settings rights.
(With the Slovak module also installed, the list shows only one of the two
buttons; the other stays in the *Actions* menu of a selected row.)

Automatic downloads also need *Automatic Currency Rates (OCA)* ticked in
*Accounting → Configuration → Settings*, block *Currencies* (ticked by default).

## Daily rate {#daily}

In the default mode, *ČNB rate* = **Daily rate (denní kurz)**, every ČNB
fixing is stored under its own date (*Accounting → Configuration → Currencies*). A
document takes the newest rate dated on or before its date, which on a weekend
or public holiday is the last fixing before it.

To load past rates, open the provider, click **Update Rates Now** and choose
the *Start Date* and *End Date*. A range is read from ČNB's yearly files, so
every fixing day in it is stored, not just the last one. If the range starts on
a weekend or holiday, the last fixing before it is stored too.

ČNB quotes some currencies per 100 units (HUF, JPY and others); the module
converts them, so the stored rate is always per one unit.

## Fixed monthly rate {#fixed-rate}

Set *ČNB rate* = **Fixed monthly rate (pevný kurz)** on the provider if your
internal rule says documents are converted at one rate per month. Then:

- **one rate per month** is stored, dated the 1st, and Odoo applies it to every
  document of that month;
- *Fixed rate taken from* chooses which fixing that is:

| Option | The month's rate is |
|---|---|
| Rate valid on the 1st of the month (default) | the fixing announced for the 1st, or the last one before it if the 1st is not a fixing day |
| Last fixing of the previous month | the last fixing before the 1st |

  The two differ only when the 1st is itself a fixing day. The Accounting Act
  defines the fixed rate as the rate announced for the first day of the
  period, so agree the second option with your accountant before choosing it.

- **the actual daily fixings are kept apart.** They do not appear among the
  currency's rates and no document uses them. They are read only by the
  Czech year-end revaluation,
  [module:l10n_cz_currency_revaluation](module:l10n_cz_currency_revaluation),
  because the balance sheet is revalued at the rate of its own day, not the
  fixed one.

Switching an existing provider to the monthly mode **does not delete** the
daily rates it has already stored. Delete them for the months that should use
the fixed rate, or documents in those months keep taking the daily ones.

## Limitations {#limitations}

- The fixed rate is always monthly. The Act lets a company choose a different
  period in its internal rule; any other period has to be maintained by hand.
- The actual daily rates are used only by
  [module:l10n_cz_currency_revaluation](module:l10n_cz_currency_revaluation)
  (the OCA-based revaluation). Odoo Enterprise's own revaluation and any other
  report see the fixed rate.
- Only the ČNB *kurz devizového trhu* currencies are downloaded (about thirty).
  The rates ČNB announces monthly for other currencies (*kurzy ostatních měn*)
  are not.
- A provider is created automatically only on installation. Currencies
  activated later are not added to an existing provider.
