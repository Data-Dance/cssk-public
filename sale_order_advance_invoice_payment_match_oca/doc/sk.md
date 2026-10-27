---
title: Zálohové faktúry — párovanie výpisov (OCA)
summary: Spúšťa párovanie zálohových faktúr v automatickom párovaní párovacieho widgetu OCA.
verified: 19.0.1.0.1
family: sale_order_advance_invoice_payment_match#bank-reconciliation
---

Spustí párovanie zálohových faktúr pred automatickým párovaním widgetu OCA (`account_reconcile_oca`), ešte pred jeho modelmi párovania a párovaním faktúr. Pohyb, ktorý uhrádza preddavok, sa spáruje, zaeviduje ako platba a vyrovná ako prvý a vo widgete sa potom zobrazí ako spárovaný. Spúšťa sa len vtedy, keď widget skutočne páruje, nie keď iba počíta návrh.

Nainštaluje sa sám, keď je nainštalované párovanie výpisov k zálohovým faktúram aj `account_reconcile_oca`. Vlastné nastavenia nemá: funguje len pre spoločnosti so zapnutým automatickým párovaním (*Auto-match bank statements*).
