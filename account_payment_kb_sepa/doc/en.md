---
title: KB XML SEPA Credit Transfer
summary: Adapts the OCA SEPA credit transfer file (pain.001.001.03) to Komerční banka's XML specification when the order is paid from a KB account.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Komerční banka accepts SEPA payments as ISO 20022 **pain.001.001.03** XML,
described in *Klientský formát XML SEPA CT v KB* (valid from 20 June 2026).
The OCA module `account_banking_sepa_credit_transfer` already writes that
file. KB's specification differs from the OCA output in two details, and a
file that ignores them can be refused. This module changes exactly those two
things, and only on payment orders paid **from a KB account** in the
pain.001.001.03 version. Orders from every other bank are left as OCA writes
them.

## What changes for a KB order {#changes}

| | OCA output | For KB |
|---|---|---|
| Postal address of debtor and creditor | country plus free address lines (`AdrLine`) | structured: street (`StrtNm`), building number (`BldgNb`), postcode (`PstCd`), town (`TwnNm`), country (`Ctry`) |
| Missing town or country | address lines written anyway | **no address at all** — KB requires town and country as soon as any address element is given, and the address is optional for SEPA |
| Characters | diacritics kept unless *Convert to ASCII* is ticked on the payment method | always converted to plain ASCII — KB accepts SEPA data only without diacritics |

With the `base_address_extended` module, the street name and the house number
go into their own elements; otherwise the whole street goes into `StrtNm`.

## Setting it up {#setup}

1. The bank journal must hold a **KB account** (bank code `0100`), as a `CZ`
   IBAN or `prefix-number/0100`.
2. Use the OCA payment method **SEPA Credit Transfer to suppliers** with
   *PAIN Version* `pain.001.001.03` (its default), in a payment mode with the
   KB journal (*Accounting → Configuration → Accounting → Payment Modes*).
3. Nothing else: the profile switches on by itself for such orders.

Then pay as with any SEPA payment order — *Accounting → Vendors → Payment
Orders*, **Confirm Payments**, **Generate Payment File** — and upload the XML
in MojeBanka Business, Profibanka or Přímý kanál.

## Limitations {#limitations}

- **SEPA only.** KB's XML carries EUR payments under the SEPA scheme. Payments
  in other currencies, or with `OUR`/`BEN` charges, go through KB's BEST format:
  [module:account_payment_kb_best](module:account_payment_kb_best), method
  *KB BEST (foreign / SEPA transfer)*.
- Other pain versions (for example pain.001.001.09) are not changed.
- KB's rule that identifications and references must not start or end with
  `/` nor contain `//` is not enforced. The end-to-end identifier OCA writes
  satisfies it; payment details you type yourself are passed through.
