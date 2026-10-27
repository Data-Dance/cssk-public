---
title: Fio banka — Connection
summary: The Fio banka API tokens on the bank journal, a connection test, the 30-second call limit and warnings before a token expires.
verified: 19.0.2.2.4
---

## What it is for {#purpose}

Fio banka — in the Czech Republic and through its Slovak branch — lets its
customers connect accounting software to their accounts through the **Fio API**
with a **token** generated in internet banking. This module holds those tokens
on the bank journal and provides what every Fio feature shares: the
connection test, the call limit and the expiry warnings.

On its own it moves no money and imports nothing. The features are:

- [module:account_statement_fio](module:account_statement_fio) — pulls
  transactions and official statements into the journal on a schedule;
- [module:account_payment_fio](module:account_payment_fio) — sends payment
  orders to Fio from an OCA payment order, or with
  [module:account_payment_fio_batch](module:account_payment_fio_batch) from an
  Enterprise batch payment.

## Tokens {#tokens}

A Fio token:

- is generated in Fio internet banking under **Nastavení → API**, authorised
  by SMS or a push notification, and becomes usable **five minutes** later;
- is bound to **one account** — and Fio keeps each currency as a separate
  account, so a CZK and a EUR account need separate tokens and separate
  journals;
- carries one of two rights: *Sledování účtu* (read the account) or *Sledování
  účtu a zadávání platebních a inkasních příkazů* (read and enter payment and
  collection orders);
- expires after at most **180 days**; Fio does not issue a token without an
  expiry date.

Use **two tokens per account**: a read token for the statement pull and a
separate submit token for payment orders. The read token is used every hour,
so it is the one most exposed — and a token that can only read cannot pay
anyone. Each token also has its own call limit (below).

## Setting it up {#setup}

1. Open the bank journal: *Accounting → Configuration → Accounting →
   Journals*. Its bank account must be the Fio account the tokens belong to.
2. In the **Fio banka** section, under the bank account number, fill in the fields in the table below.

| Field | |
|---|---|
| Fio Read Token | the read token (64 characters) |
| Fio Read Token Expires | its expiry date, copied from internet banking |
| Fio Submit Token | the submit token, if you will send payments |
| Fio Submit Token Expires | its expiry date |
| Fio Download Format | *Fio XML* (default) or *Fio JSON*; leave it at XML |

Only users with administrator rights (*Settings*) can see and enter the
tokens. Other users see only whether a token is set.

Then press **Test connection**. Odoo makes one call, stores what Fio reports
about the account (account number, bank code, IBAN, BIC, currency, shown
under *What Fio reports about this account*) and posts a note in the
journal's chatter. A token that belongs to a **different account** than the
journal's IBAN, or an account in a different currency than the journal's, is
refused — importing it would book another account's movements here.

*Accounting → Configuration → Accounting → Fio banka* lists every journal that
has a read token, with both expiry dates; a date already past shows in red.

## Expiring tokens {#expiry}

The Fio API never reports when a token expires, which is why the two expiry
fields are filled in by hand. A daily scheduled action, *Fio: warn about
expiring tokens*, creates a to-do activity on the journal **14 days** before a
recorded expiry date, assigned to an accounting administrator of the company.

**An empty expiry date means no warning** — the statement feed or the payment
upload then simply stops working on the day the token dies.

## The call limit {#rate-limit}

Fio allows **one call per token every 30 seconds**, for reading or writing,
in any format. Odoo keeps track of the last call per token
(*Fio Last Read Call*, *Fio Last Submit Call*) and serialises all Fio calls of
a journal:

- a button pressed too soon (for example *Pull now* right after *Test
  connection*) does not freeze the screen; it says when the next call is
  possible;
- the scheduled actions wait out the remaining seconds;
- if another Fio operation on the same journal is running, you are asked to
  try again shortly.

## Platební titul on partners {#payment-reason}

Fio requires a **platební titul** — the payment reason from the Czech National
Bank's code list — on every foreign payment, and from an account at the Slovak
branch also on a SEPA payment over EUR 50 000. This module adds the field
**Platební titul** to the partner (tab *Sales & Purchase*, under the vendor
payment terms), per company. It is the default for payments to that partner;
see [module:account_payment_fio](module:account_payment_fio#checks).

## The API client {#api}

The protocol itself — the REST calls, the Fio XML and JSON statement formats,
the payment-order XML (`importIB.xsd`) and the bank's answers — lives in
[module:account_fio_base](module:account_fio_base), written against *FIO API
BANKOVNICTVÍ* version 1.9 of 16 October 2025. Fio carries the token in the web
address of each call, so the client removes it from every error message and
log line it produces.

## Limitations {#limitations}

- Fio operates **no test environment**. The connection has been tested against
  recorded bank answers; live behaviour, notably of multi-currency setups and of
  Fio's per-order messages, can only be confirmed on a real account.
- The account check of *Test connection* compares IBANs. A journal whose bank
  account is written as `number/bank code` instead of an IBAN is not compared
  (the currency still is).
- The time of the last call is recorded before the call. If a call fails, that
  record is rolled back, and the next attempt may be refused by Fio as too
  early — with an explanatory message.
- Tokens are stored in the database in plain text, readable to administrators.
