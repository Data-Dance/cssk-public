---
title: SK virtuálna registračná pokladnica (VRP2) — pripojenie
summary: Pripojenie k virtuálnej registračnej pokladnici finančnej správy (VRP 2), spoločné pre evidenciu úhrad faktúr a modul Miesto predaja.
verified: 19.0.2.4.0
family: l10n_sk_vrp2_account#connection
---

Pripája Odoo k virtuálnej registračnej pokladnici (VRP 2): prihlásenie pokladnice spoločnosti v *Účtovníctvo → Konfigurácia → Nastavenia*, blok **VRP2 — slovenská virtuálna registračná pokladnica**, s tlačidlami *Prihlásenie* / *Odhlásiť*, údajmi o pokladnici tak, ako ich hlási VRP (DKP, obchodné meno, DIČ, IČO, IČ DPH), a nastavením *Zaokrúhľovať na 0,05 €*. Každá pokladnica v module Miesto predaja používa ten istý mechanizmus s vlastným prihlásením.

Sám osebe nerobí nič. Inštalujú ho moduly [module:l10n_sk_vrp2_account](module:l10n_sk_vrp2_account) (úhrady faktúr) a [module:pos_vrp2](module:pos_vrp2) (predaj na pokladni), ktorých návody opisujú, ako sa používa.
