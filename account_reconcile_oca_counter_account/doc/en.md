---
title: OCA Reconciliation — Counterparty Account
summary: Shows the counterparty's bank account on the OCA bank reconciliation screen, so a payer who quoted no variable symbol can still be identified.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

The OCA bank reconciliation screen (`account_reconcile_oca`) shows a fixed set
of fields of each statement line, and the **counterparty's bank account** is
not among them — although every statement import of this family (GPC, MT940,
KB BEST, Fio, Tatra banka and others) fills it in. In the Czech Republic and
Slovakia that is often the one thing that tells you who paid: a customer who
forgot the variable symbol is identified by their account number, and matching
by name alone is the guess that books a receivable against the wrong customer.

## What it shows {#usage}

On the reconciliation screen (opened with **Reconcile … Items** on the bank
journal's card in the Accounting dashboard), right after the line's label:

| Field | Content |
|---|---|
| Bank Account Number | the counterparty's account exactly as the bank sent it, e.g. `2600123456/2010` or an IBAN |
| Recipient Bank | the bank account in Odoo that the line was linked to, when a partner's bank account matched |

Both are read-only and appear only when they are filled. Nothing else changes:
no new fields, no new logic, and the ordinary statement line form is untouched.

It installs itself whenever `account_reconcile_oca` is installed.

## Limitations {#limitations}

- It only displays what the statement import stored. Lines from a source that
  does not deliver the counterparty's account (for example a manual entry)
  show nothing.
- It does not match anything by account number by itself; partner matching by
  bank account is done by the statement import when the line is created.
