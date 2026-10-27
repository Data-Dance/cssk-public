---
title: Advance Invoices — Slovak Accounts
summary: Wires the advance-invoice settings to the Slovak chart of accounts.
verified: 19.0.1.1.0
family: sale_order_advance_invoice#localization
---

Fills in the advance-invoice settings for every company with the Slovak chart of accounts: it creates the reconcilable clearing account 324001 *Prijaté preddavky – zúčtovanie (daňový doklad)*, uses 324000 *Prijaté preddavky* for short-term and 475000 *Dlhodobé prijaté preddavky* for long-term received advances, and names the TDADV journal *Faktúry k prijatým platbám*.

Install it together with the advance invoices module on a Slovak company. It runs at installation and again whenever the Slovak chart is loaded later, for example for a new company, and fills only settings that are still empty.
