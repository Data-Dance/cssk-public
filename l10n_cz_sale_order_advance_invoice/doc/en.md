---
title: Advance Invoices — Czech Accounts
summary: Wires the advance-invoice settings to the Czech chart of accounts.
verified: 19.0.1.1.0
family: sale_order_advance_invoice#localization
---

Fills in the advance-invoice settings for every company with the Czech chart of accounts: it creates the reconcilable clearing account 324001 *Přijaté zálohy – zúčtování (daňový doklad)*, uses 324000 *Přijaté provozní zálohy* for short-term and 475000 *Dlouhodobé přijaté zálohy* for long-term received advances, and names the TDADV journal *Daňové doklady k přijatým platbám*.

Install it together with the advance invoices module on a Czech company. It runs at installation and again whenever the Czech chart is loaded later, for example for a new company, and fills only settings that are still empty.
