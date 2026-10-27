---
title: SK Virtual Cash Register (VRP2) — Connection
summary: The connection to Finančná správa's virtual cash register (VRP 2) shared by the invoice-payment and Point of Sale modules.
verified: 19.0.2.4.0
family: l10n_sk_vrp2_account#connection
---

Connects Odoo to the Slovak virtual cash register (VRP 2): the login of the company's own register in *Accounting → Configuration → Settings*, block **VRP2 - Slovak Virtual Cash Register**, with *Login* / *Logout*, the register's details as VRP reports them (DKP, business name, DIČ, IČO, IČ DPH) and the *Round to 0.05 €* setting. Each Point of Sale till uses the same mechanism with its own login.

It does nothing on its own. It is installed by [module:l10n_sk_vrp2_account](module:l10n_sk_vrp2_account) (invoice payments) and [module:pos_vrp2](module:pos_vrp2) (sales at the till), whose guides describe how to use it.
