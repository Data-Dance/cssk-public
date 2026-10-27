---
title: Párovanie OCA — účet protistrany
summary: Zobrazí bankový účet protistrany na obrazovke párovania bankových výpisov OCA, aby sa dal určiť aj platiteľ, ktorý neuviedol variabilný symbol.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Obrazovka párovania bankových výpisov OCA (`account_reconcile_oca`) zobrazuje
pevný výber polí riadku výpisu a **bankový účet protistrany** medzi nimi nie je
— hoci ho vypĺňa každý import výpisov z tejto rodiny (GPC, MT940, KB BEST, Fio,
Tatra banka a ďalšie). Na Slovensku a v Česku je to často jediný údaj, podľa
ktorého spoznáte, kto platil: odberateľa, ktorý zabudol variabilný symbol,
určíte podľa čísla účtu, a párovanie len podľa mena je práve ten odhad, ktorý
zaúčtuje pohľadávku nesprávnemu odberateľovi.

## Čo zobrazuje {#usage}

Na obrazovke párovania (otvára sa tlačidlom **Reconcile … Items** na karte
bankového denníka na riadiacom paneli Účtovníctva), hneď za popisom riadku:

| Pole | Obsah |
|---|---|
| Číslo bankového účtu | účet protistrany presne tak, ako ho poslala banka, napr. `2600123456/2010` alebo IBAN |
| Banka príjemcu | bankový účet v Odoo, ku ktorému bol riadok priradený, ak sa zhodoval s bankovým účtom partnera |

Obe polia sú len na čítanie a zobrazia sa, len keď sú vyplnené. Nič iné sa
nemení: žiadne nové polia, žiadna nová logika a bežný formulár riadku výpisu
ostáva nedotknutý.

Nainštaluje sa sám vždy, keď je nainštalovaný `account_reconcile_oca`.

## Obmedzenia {#limitations}

- Len zobrazuje to, čo uložil import výpisu. Riadky zo zdroja, ktorý účet
  protistrany nedodáva (napríklad ručne zadané), nezobrazia nič.
- Sám nepáruje nič podľa čísla účtu; partnera podľa bankového účtu priraďuje
  import výpisu pri vzniku riadku.
