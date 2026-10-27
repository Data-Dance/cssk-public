---
title: Received Advance Invoices — Czech Accounts
summary: Wires the received-advance settings to the Czech chart of accounts.
verified: 19.0.1.0.1
family: purchase_order_advance_invoice#localization
---

Fills in the received-advance settings for every company with the Czech chart of accounts: it creates the reconcilable payable clearing account 314001 *Poskytnuté zálohy – zúčtování (daňový doklad)*, uses 314000 *Poskytnuté provozní zálohy* for paid advances, and creates the purchase journal PDADV *Daňové doklady k odeslaným platbám*. No long-term account is set.

It runs at installation for the companies that already have the Czech chart, and again whenever the chart is loaded later, for example for a new company. It fills only settings that are still empty.
