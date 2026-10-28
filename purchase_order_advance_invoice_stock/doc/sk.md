---
title: Prijaté zálohové faktúry — Sklad
summary: Prijatá zálohová faktúra nikdy nevytvorí príjemku; tovar sa prijíma na objednávke, na ktorej bol objednaný.
verified: 19.0.1.0.0
family: purchase_order_advance_invoice#register
---

Prijatá zálohová faktúra modulu
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
je samostatná nákupná objednávka a jej úhrada ju potvrdí. S nainštalovaným
Skladom by Odoo potom vytvorilo príjemku na jej skladované produkty a ten istý
tovar by sa očakával dvakrát: na preddavku aj na objednávke, na ktorej bol
objednaný.

S týmto doplnkom preddavok nikdy nevytvorí príjemku — ani pri úhrade, ani pri
ručnom potvrdení, ani keď sa neskôr pridá riadok alebo zvýši množstvo. Tovar
prijmite ako obvykle na **nadradenej objednávke**. Bežných nákupných
objednávok sa to netýka.

Nainštaluje sa sám, keď sú nainštalované
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
aj Sklad (`purchase_stock`). Nič sa nenastavuje.
