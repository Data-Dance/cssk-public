---
title: Received Advance Invoices — Slovak Accounts
summary: Wires the received-advance settings to the Slovak chart of accounts.
verified: 19.0.1.0.1
family: purchase_order_advance_invoice#localization
---

Fills in the received-advance settings for every company with the Slovak chart of accounts: it creates the reconcilable payable clearing account 314001 *Poskytnuté preddavky – zúčtovanie (daňový doklad)*, uses 314000 *Poskytnuté preddavky* for paid advances, and creates the purchase journal PDADV *Faktúry k odoslaným platbám*. No long-term account is set.

It runs at installation for the companies that already have the Slovak chart, and again whenever the chart is loaded later, for example for a new company. It fills only settings that are still empty.
