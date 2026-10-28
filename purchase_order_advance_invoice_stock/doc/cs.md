---
title: Přijaté zálohové faktury — Sklad
summary: Přijatá zálohová faktura nikdy nevytvoří příjemku; zboží se přijímá na objednávce, na které bylo objednáno.
verified: 19.0.1.0.0
family: purchase_order_advance_invoice#register
---

Přijatá zálohová faktura modulu
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
je samostatná nákupní objednávka a její úhrada ji potvrdí. S nainstalovaným
Skladem by Odoo pak vytvořilo příjemku na její skladované produkty a totéž
zboží by se očekávalo dvakrát: na záloze i na objednávce, na které bylo
objednáno.

S tímto doplňkem záloha nikdy nevytvoří příjemku — ani při úhradě, ani při
ručním potvrzení, ani když se později přidá řádek nebo zvýší množství. Zboží
přijměte jako obvykle na **nadřazené objednávce**. Běžných nákupních
objednávek se to netýká.

Nainstaluje se sám, jsou-li nainstalovány
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
i Sklad (`purchase_stock`). Nic se nenastavuje.
