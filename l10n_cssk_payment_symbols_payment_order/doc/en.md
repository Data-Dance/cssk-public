---
title: CZ/SK Payment Symbols — Payment Orders
summary: Copies the variable, constant and specific symbol of each document onto OCA payment order lines.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#payment-orders
---

When a line of an OCA payment order (`account_payment_order`) is created from an invoice or bill, this module copies the document's variable, constant and specific symbol onto it, so the domestic bank-file exporters (ABO, Multicash) write them into the file as structured symbols.

It installs itself when both the payment symbols module and `account_payment_order` are installed. It has no screen of its own.
