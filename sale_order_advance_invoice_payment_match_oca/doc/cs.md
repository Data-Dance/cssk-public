---
title: Zálohové faktury — párování výpisů (OCA)
summary: Spouští párování zálohových faktur v automatickém párování párovacího widgetu OCA.
verified: 19.0.1.0.1
family: sale_order_advance_invoice_payment_match#bank-reconciliation
---

Spustí párování zálohových faktur před automatickým párováním widgetu OCA (`account_reconcile_oca`), ještě před jeho modely párování a párováním faktur. Pohyb, který hradí zálohu, se spáruje, zaeviduje jako platba a vyrovná jako první a ve widgetu se pak zobrazí jako spárovaný. Spouští se jen tehdy, když widget skutečně páruje, ne když pouze počítá návrh.

Nainstaluje se sám, je-li nainstalováno párování výpisů k zálohovým fakturám i `account_reconcile_oca`. Vlastní nastavení nemá: funguje jen pro společnosti se zapnutým automatickým párováním (*Auto-match bank statements*).
