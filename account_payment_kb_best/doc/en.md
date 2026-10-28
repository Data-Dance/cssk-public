---
title: KB BEST Payment Files
summary: Domestic transfers, direct debits and foreign/SEPA payments from a Komerční banka account, exported in KB's BEST format from an OCA payment order.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

**BEST** is Komerční banka's own fixed-width client format for its direct
banking channels — **MojeBanka Business**, **Profibanka** and **Přímý kanál**
(direct channel). This module writes BEST payment files from an OCA
**payment order** (`account_payment_order`), so you pay a batch of bills from
your KB account by uploading one file. It works on Community and Enterprise
alike.

The specification is KB's *Klientský formát BEST podporovaný v KB*, valid from
20 June 2026.

Statements in the same format are imported by
[module:account_statement_import_kb_best](module:account_statement_import_kb_best).

## Payment methods {#methods}

| Payment method | Payment order | BEST record | File |
|---|---|---|---|
| KB BEST (domestic transfer) | outbound (*Payment Orders*) | `01`, domestic transfer | `BEST-DP-<journal>-<date and time>.ikm` |
| KB BEST (domestic direct debit / inkaso) | inbound (*Debit Orders*) | `01` with the direct-debit operation code | `BEST-DP-….ikm` |
| KB BEST (foreign / SEPA transfer) | outbound | `02` with the `03` structured address | `BEST-ZP-<journal>-<date and time>.ikm` |

Files are Windows-1250 with CR LF line ends; domestic records keep Czech
diacritics, foreign records use only the SWIFT character set.

## Setting it up {#setup}

1. **The bank journal** (*Accounting → Configuration → Accounting → Journals*)
   must hold a **KB account** — bank code `0100` — as a `CZ` IBAN or
   `prefix-number/0100`. Any other account is refused. The journal's currency
   (or the company's, if the journal has none) is taken as the currency of the
   KB account.
2. **A payment mode** for each method you use (*Accounting → Configuration →
   Accounting → Payment Modes*), with the KB journal.
3. **Partners**: a bank account for everyone you pay. For a foreign payment
   that is not SEPA also the partner's street, city and country, and the BIC
   of their bank (or the bank's name, city and country).
4. Recommended: [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols)
   so that each bill's symbols reach the payment lines on their own (see
   [module:account_abo](module:account_abo#setup)).

## Making a payment file {#usage}

1. *Accounting → Vendors → Payment Orders* (or *Customers → Debit Orders* for
   direct debits), **New**, choose the KB BEST payment mode, **Create Payment
   Lines from Journal Items**.
2. Check **Variable Symbol**, **Constant Symbol** and **Specific Symbol** on
   the lines; an empty one is taken from a `VS:` / `KS:` / `SS:` token in the
   *Communication*.
3. **Confirm Payments**, **Generate Payment File**.
4. Upload the `.ikm` file in MojeBanka Business, Profibanka or Přímý kanál,
   authorise it there, and mark the order with **File Successfully Uploaded**.

## Rules the file follows {#rules}

These are KB's rules; the module applies them before the bank does and stops
with a message naming the payment:

**Every payment**

- the amount must be positive;
- a due date in the past is moved to today (the bank refuses a past one);
- each payment gets a sequence number derived from its payment line, because
  KB requires the number to be unique for the whole day across all files, not
  only within one file.

**Domestic (record 01)**

- the beneficiary's account must be Czech (IBAN `CZ…` or
  `prefix-number/bank code`);
- a payment in another currency than the KB account's is sent with KB's
  conversion flag; a non-CZK domestic payment may only go to **another KB
  account** — to any other bank it must be in CZK or sent as a foreign payment;
- a direct debit from another bank than KB must be in CZK;
- constant symbols KB refuses in a batch are refused here too: `???5`
  (corrective settlement), `??51` (enforcement), `0006` and `0007`;
- the *Communication* becomes up to four lines of 35 characters of message for
  the beneficiary, and its first 30 characters your own description;
- your own VS and SS are sent empty: the bank replaces them with the
  beneficiary's anyway.

**Foreign (record 02)**

- a payment goes as **SEPA** when it is in EUR, to an IBAN in a SEPA country,
  with shared charges; everything else is a standard foreign payment;
- into the EEA only **shared charges (SHA)** are allowed;
- a EUR payment into the EEA needs the beneficiary's IBAN;
- a non-SEPA payment needs the beneficiary's name, street, city and country,
  and the beneficiary bank's BIC or its name, city and country;
- the VS and KS are written into the payment details as `/VS/…` and `/KS/…`,
  where KB reads them back into the transaction history;
- the `03` structured address is added when the partner has a city and a
  country.

## The shared BEST module {#format}

The BEST layouts — both payment records and the statement — live in
[module:account_kb_best_base](module:account_kb_best_base), which this module
and [module:account_statement_import_kb_best](module:account_statement_import_kb_best)
build on. It has no screen of its own.

## Limitations {#limitations}

- A credit note grouped with its invoice on the payment order (the payment
  mode's *Group Transactions in Payment Orders*) becomes **one item of the net
  amount** — the amount of the payment the order books. It carries the
  invoice's variable symbol; when one credit note is netted against several
  invoices their symbols differ and none is sent. Groups without a credit note
  keep one item per invoice. Without grouping, a credit-note line is refused.
- Only from a KB account; this is KB's own format.
- Community payment orders only — there is no Enterprise batch-payment
  variant of this module.
- Urgency and charges are set per payment line: **Priority** (*Urgent* is
  KB's express processing) and **Charge Bearer** (*Shared*, *Payer* = `OUR`,
  *Beneficiary* = `BEN`). They default to normal and shared; into the EEA only
  *Shared* is accepted (see above).
- The order stops at the first payment that breaks a rule; fix it and
  generate again.
- KB's XML format for SEPA payments is a separate module,
  [module:account_payment_kb_sepa](module:account_payment_kb_sepa).
