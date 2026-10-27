---
title: Exchange Rates for Slovakia (ECB/NBS, VÚB, Tatra banka)
summary: Downloads the ECB reference rate a Slovak company values foreign currency at, sets the provider up for you, fills weekends and holidays, and adds the VÚB and Tatra banka rate lists.
verified: 19.0.1.1.2
---

## What it is for {#purpose}

A Slovak company keeps its books in euro and converts every foreign-currency
invoice, payment and balance at the **reference exchange rate** (*referenčný
výmenný kurz*) set by the European Central Bank and published by Národná banka
Slovenska. Odoo needs that rate for every day on which a document is dated.

This module builds on the OCA rate-update framework
([module:currency_rate_update](module:currency_rate_update)), which already
knows how to download the ECB rates. It adds what a Slovak company needs on
top:

- **the provider is created for you** when the module is installed, so the
  rates start arriving without anybody filling in a form;
- **weekends and public holidays get a rate**, carried forward from the last
  day on which one was published;
- **two commercial rate lists**, VÚB banka and Tatra banka, for when you want
  to see what a bank actually charged rather than the statutory rate.

It works on Community and Enterprise alike; it does not need Odoo Enterprise's
own automatic rates.

## Legal background {#legal}

- **Accounting.** Assets and liabilities in a foreign currency are converted to
  euro at the reference rate set and announced by the ECB or by Národná banka
  Slovenska *"v deň predchádzajúci dňu uskutočnenia účtovného prípadu"* — on
  the day **before** the transaction — and at the balance-sheet date at the
  rate of that day:
  [§ 24 ods. 2 of the Accounting Act](law:sk/2002/431#paragraf-24.odsek-2).
  A purchase of foreign currency for euro may instead be valued at the rate it
  was actually bought at ([§ 24 ods. 3](law:sk/2002/431#paragraf-24.odsek-3)).
- **VAT.** A taxable amount invoiced in a foreign currency is converted at the
  same ECB/NBS reference rate announced on the day before the tax liability
  arises, unless the company has notified the tax office that it uses the
  customs rate for the whole calendar year:
  [§ 26 ods. 1 of the VAT Act](law:sk/2004/222#paragraf-26.odsek-1).

So the statutory source is the ECB service. The VÚB and Tatra banka lists are
commercial rates; they are not the reference rate. The module applies the
**preceding-day** rule to a Slovak company's documents — see
[Which day's rate a document takes](#rate-date).

## What installation sets up {#setup}

On installation, every company whose country (or fiscal country) is Slovakia
gets an **ECB** provider, provided the database already has at least one active
foreign currency the ECB publishes. The provider:

- quotes **the currencies already active** in the database that the ECB
  publishes, never the company's own currency — it does not activate new ones;
- runs **daily**;
- has *Fill non-publishing days* switched on.

A company that already has an ECB provider, even an archived one, is left
alone: archiving it counts as a decision. A company with no active foreign
currency gets no provider, because there would be nothing to download.

The providers are listed in *Accounting → Configuration → Currency Rates
Providers* — on Community without full accounting the root menu reads
*Invoicing*. The screen and its labels come from the OCA module and are in
English.

If you activate a currency **after** installing the module and the list is
still empty, create the provider yourself: *New*, *Provider* = **European
Central Bank**, pick the *Currencies*, leave the interval at 1 day, save. The
list also has a button for this, **Create the Slovak default provider**, shown
even when the list is empty; it creates only what is missing and needs Settings
rights (anyone else gets a message saying so). With the Czech module also
installed, the list shows only one of the two buttons; the other stays in the
*Actions* menu of a selected row. To add a
currency to an existing provider, edit its *Currencies* field — the action
never changes a provider that exists.

Automatic downloads also need *Automatic Currency Rates (OCA)* to be ticked in
*Accounting → Configuration → Settings*, block *Currencies*. It is ticked by
default.

## Day to day {#usage}

Once a day the rates for the provider's currencies are downloaded and stored as
the currency's rates (*Accounting → Configuration → Currencies*), each under
the day the ECB announced it. Which of them a document takes is described in
[Which day's rate a document takes](#rate-date).

To load rates for past dates — a history import, a late invoice — open the
provider and click **Update Rates Now**, choose the *Start Date* and
*End Date*, and confirm. The ECB service supplies its full history.

When a download fails, the error is posted in the provider's chatter and the
next scheduled run tries again.

## Which day's rate a document takes {#rate-date}

In a company whose country or fiscal country is Slovakia, a document takes
the reference rate announced on the **day before** the day that decides it
— the newest rate dated before that day:

| Document | Deciding day | Example: rate used |
|---|---|---|
| Invoice, vendor bill, credit note, receipt | the *taxable supply date* (*dátum dodania*) when filled in, otherwise the invoice date | dated Friday 6 March → the rate of Thursday 5 March |
| Payment, bank-statement line | its date | dated Monday 9 March → the rate of Friday 6 March |
| Other journal entry with a foreign-currency line | its accounting date | dated Sunday 8 March → the rate of Friday 6 March |

After a weekend or a holiday the "day before" has no rate of its own, so the
last rate announced before it applies — the same rate *Fill non-publishing
days* copies onto those days, so the result does not depend on that option.

The **year-end revaluation is not shifted**: balances are valued at the rate
of the balance-sheet day itself (§ 24 ods. 2 písm. b)), which is what the
revaluation reads.

The rate of a draft invoice is recalculated when its date changes; a posted
document keeps the rate it was posted with. A company outside Slovakia keeps Odoo's own rule
(the rate of the document's date).

## Weekends and holidays {#fill}

Neither the ECB nor the banks publish rates on weekends and holidays. With
**Fill non-publishing days** ticked on the provider (the default), after every
download each calendar day in the downloaded range that has no rate gets a copy
of the last rate before it. A day that already has a rate is never overwritten
by the fill, and a filled day is overwritten as soon as a rate for that date is
actually published.

The fill only carries a rate forward. If the range starts before the first rate
the database has, those first days stay empty.

The option is available on every provider, not only the Slovak ones, and is
also picked up by the Czech
[module:currency_rate_update_cz](module:currency_rate_update_cz) when both are
installed.

## Commercial bank rates (VÚB, Tatra banka) {#bank-rates}

Two further services appear in the provider's *Provider* field:

| Service | What is downloaded | Currencies | History |
|---|---|---|---|
| VÚB banka | the bank's daily rate list (*kurzový lístok*), middle rate for transfers (*Devíza stred*) | AUD, BGN, CAD, CNY, CZK, DKK, GBP, HUF, CHF, JPY, NOK, PLN, RON, SEK, TRY, USD | today's list only |
| Tatra banka | the bank's published exchange-rate feed | CZK, GBP, HUF, PLN, SEK, CHF, USD | about the last 30 days |

Use them to see what a conversion at that bank would cost. They are **not** the
statutory reference rate, so do not let them value your documents: a company's
rate table holds one rate per currency and day, and two providers quoting the
same currency for the same company overwrite each other's rates. Put a
commercial provider in a separate company, or quote currencies the ECB
provider does not.

The download and parsing of both feeds live in
[module:currency_rate_sk_base](module:currency_rate_sk_base), installed
automatically.

## Limitations {#limitations}

- The election under § 26 ods. 1 of the VAT Act to use the customs rate for
  a whole calendar year is not supported; such a company has to enter the
  rate on its invoices by hand.
- The preceding-day rule covers invoices, bills, payments, bank-statement
  lines and journal entries. Purchase and sales orders, and other places
  where Odoo shows a converted amount for information, still use the rate
  of their own date.
- The ECB publishes rates for about thirty currencies. Národná banka Slovenska
  also announces rates for some currencies the ECB does not; those are not
  downloaded.
- The VÚB and Tatra banka feeds are web pages run by the banks, not documented
  interfaces. A change on the bank's side stops the download until the module
  is updated.
- A provider is created automatically only on installation and by the action
  described above. Currencies activated later are not added to an existing
  provider.
