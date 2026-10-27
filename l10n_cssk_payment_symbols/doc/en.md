---
title: CZ/SK Payment Symbols (VS/KS/SS)
summary: Variable, constant and specific symbols on invoices, payments and bank statements, and matching incoming payments by them.
verified: 19.0.1.4.1
---

## What it is for {#purpose}

A Czech or Slovak payer identifies what they are paying with numeric **payment
symbols** rather than with a free-text reference:

| Symbol | Slovak / Czech | Length | Typical use |
|---|---|---|---|
| VS | variabilný / variabilní symbol | up to 10 digits | the invoice number — what the customer is asked to quote |
| KS | konštantný / konstantní symbol | up to 4 digits | the kind of payment, e.g. `0008` goods, `0308` services |
| SS | špecifický / specifický symbol | up to 10 digits | an extra identifier some payees ask for (insurers, leasing) |

Odoo itself has only the free-text *Payment Reference*. This module gives the
three symbols their own validated fields, fills them in for you, carries them
into payment QR codes, payments and bank files, reads them back out of bank
statements, and — with one of its add-ons — matches incoming payments to
invoices by the variable symbol.

It depends on Odoo's `account` only, so it works on Community and Enterprise
alike and does not need the rest of the Czech/Slovak localization.

## Legal background {#legal}

The symbols are a **banking convention**, not a statutory requirement for
ordinary commercial payments, in either country:

- **Czech Republic.** The symbols used to be defined by ČNB decree
  No. 62/2004 Sb. That decree was repealed by
  [§ 7 of decree No. 169/2011 Sb.](law:cz/2011/169), which does not define
  them. They live on as the banks' convention and in the payment instructions
  of payees that require them, such as the tax and social-security
  administrations.
- **Slovakia.** In a SEPA credit transfer the symbols travel in the payer's
  reference as `/VS…/SS…/KS…`. Since 18 March 2024, following a
  recommendation of Národná banka Slovenska, banks increasingly prefix a
  question mark: `?/VS…/SS…/KS…` (VS and SS up to 10 digits, KS 4). This
  module reads both forms.

Because a variable symbol is unique only **per issuer** — two suppliers can
both number an invoice 2026001 — the matching below never trusts the symbol
alone when it knows who paid.

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Czech / Slovak Payment
Symbols**:

| Setting | What it does |
|---|---|
| Credit note variable symbol | Whether a customer credit note carries **its own number** (default) or the **variable symbol of the invoice it reverses**. Choose the second if your customers net credit notes against the original invoice. |
| Default constant symbol | Preset on every customer invoice and credit note, e.g. `0308` if you sell services. Leave empty for none. |
| Payment reference = variable symbol | When a customer document is posted, its *Payment Reference* becomes the variable symbol. Odoo's own QR codes, the payment ID in e-invoices (UBL) and the standard bank matching then carry the VS with nothing else to configure. Already-posted documents are not changed. |

## On invoices, credit notes and bills {#invoices}

The three fields sit right after *Payment Reference*: on vendor bills in the
main part of the form, on customer invoices and credit notes in the *Other
Info* tab.

- **Customer invoice.** The variable symbol is filled from the digits of the
  document number, keeping the last 10: `INV/2026/00042` gives `202600042`.
  The constant symbol comes from the company default.
- **Customer credit note.** Its own number, or the original invoice's symbol,
  as set above.
- **Vendor bill.** The variable symbol is taken from the digits of the
  *Bill Reference* — normally the supplier's invoice number, which is also the
  VS they expect. If the supplier asks for a different VS, overwrite it.

Every field stays editable. Anything other than digits, or a value longer than
10 / 4 / 10 digits, is refused when you save.

Customer receipts (*out_receipt*) show no symbols, because Odoo shows them no
*Payment Reference* either.

## Payment QR codes {#qr}

When an invoice prints a payment QR code, its symbols are handed to the QR
generator, so the code the customer scans carries the VS, KS and SS as
separate values. The Czech and Slovak QR formats are provided by
[module:account_qr_code_qr_platba_cz](module:account_qr_code_qr_platba_cz)
(QR Platba),
[module:account_qr_code_pay_by_square_sk](module:account_qr_code_pay_by_square_sk)
(PAY by square) and
[module:account_qr_code_payme_sk](module:account_qr_code_payme_sk)
(payme.sk).

## Payments {#payments}

The *Pay* button (the *Register Payment* wizard) copies the symbols onto the payment it creates when every
document being paid has the same value. A grouped payment over invoices with
different variable symbols gets none — the recipient's bank could not match
it to one invoice anyway. The symbols appear on the payment form after
*Memo*, editable.

## Bank statements {#bank-statements}

When a statement line is created — by a bank connector or a file import — the
symbols are filled in from, in this order:

1. values the bank connector supplies explicitly;
2. the connector's transaction details, under the usual key names
   (`variable_symbol`, `variableSymbol`, `vs`, `variable_code`, and likewise
   for KS and SS);
3. tokens in the label, the reference and the notes: `VS:123`, `VS 123`,
   `/VS123`, `/VS/123`, `?/VS123/SS/KS`. CAMT files often carry the symbols
   only in the reference, which is why that is read too.

A zero symbol (`SS0`) counts as none. The variable symbol is also written at
the front of the label (`123 - original label`, never twice), so Odoo's
standard matching can see it. Lines that existed before the module was
installed are not re-read.

## Matching incoming payments by variable symbol {#bank-matching}

Installing one of two add-ons adds an exact variable-symbol pass to automatic
bank reconciliation. Both install themselves when their engine is present:

- [module:l10n_cssk_payment_symbols_ee](module:l10n_cssk_payment_symbols_ee)
  — for Odoo Enterprise bank reconciliation;
- [module:l10n_cssk_payment_symbols_oca](module:l10n_cssk_payment_symbols_oca)
  — for the OCA reconciliation widget (`account_reconcile_oca`) on Community.

They share one rule. A statement line with a variable symbol is compared with
the open, posted documents of the same company whose symbol is the same,
**ignoring leading zeros** (`0042` = `42`):

- If the bank line already knows the payer (from the account number), only
  that partner's documents are considered.
- If exactly one document carries the symbol, that is the match.
- If several do, the one whose open amount equals the payment is taken — but
  only if exactly one fits, and only in the company currency. Two documents
  with the same symbol and the same amount (two sale journals can both issue
  …00001) are left for you.
- Otherwise nothing is matched and the line is left for you. The pass never
  guesses.

Advance invoices (proformas) are matched by variable symbol in the same pass
when [module:sale_order_advance_invoice_payment_match](module:sale_order_advance_invoice_payment_match#matching)
is installed.

Differences between the two:

| | Enterprise | OCA |
|---|---|---|
| Runs | before Odoo's own matching, which ignores labels of 5 characters or fewer and so can never match a short VS | before OCA's own invoice matching |
| Payment covers the invoice | reconciled | reconciled |
| Partial payment | reconciled, the rest of the invoice stays open | reconciled, the rest of the invoice stays open |
| Overpayment | the invoice is reconciled; the surplus goes on to Odoo's own matching and to you | proposed in the widget, never reconciled automatically |
| Foreign currency | single-document matches only | left to OCA and to you |
| Several lines in one import | — | a line finds only what earlier lines of the same import left open: a second full payment of one invoice is left for you, instalments pay it together, and an overpayment left for you takes nothing from the next line |
| Extra | VS column and VS search on the bank transactions list (KS, SS optional) | — |

## Payment orders {#payment-orders}

With OCA payment orders (`account_payment_order`) installed,
[module:l10n_cssk_payment_symbols_payment_order](module:l10n_cssk_payment_symbols_payment_order)
copies each document's VS, KS and SS onto the payment lines created from it.
The domestic bank-file exporters —
[module:account_abo](module:account_abo) (Czech ABO) and
[module:account_multicash](module:account_multicash) — write them into the
file as structured symbols. It has no screen of its own.

## SEPA / ISO 20022 credit transfers {#iso20022}

With Odoo Enterprise's ISO 20022 export,
[module:l10n_cssk_payment_symbols_iso20022](module:l10n_cssk_payment_symbols_iso20022)
adds a choice to each bank journal, **CZ/SK Symbols in pain.001**:

| Option | What is written into the file |
|---|---|
| Remittance info (default) | `/VS/…/KS/…/SS/…` appended to the unstructured remittance information; `PLATBA/VS/…` when there was none. A structured creditor reference (RF) is left as it is. |
| EndToEndId = variable symbol | the bare variable symbol as the end-to-end identifier |
| Do not export symbols | Odoo's standard file |

**Check with your bank before relying on either.** Banks differ in what they
parse back into symbols, and the Slovak convention described
[above](#legal) writes `?/VS…/SS…/KS…` — letters and digits without a slash
between them, VS–SS–KS order — which neither option produces. Send one test
payment and look at how the payee's statement shows it.

## Limitations {#limitations}

- The variable symbol is derived from the document number. A sequence with a
  year prefix yields symbols like `202600042`; if your customers are used to
  a different form, adjust the sequence or edit the symbol.
- Automatic matching is exact and conservative: no fuzzy matching, no
  foreign-currency multi-document matching, nothing across companies.
- Symbols are read from statement lines when they are created, not later.
