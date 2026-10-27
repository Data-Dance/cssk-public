---
title: Odpisový plán majetku — prehľad odpisov
summary: Interaktívny prehľad pohybov dlhodobého majetku a kontingenčná analýza účtovných odpisov pre register majetku v Community (OCA account_asset_management).
verified: 19.0.1.0.2
---

## Na čo slúži {#purpose}

Register majetku v Community, OCA
[module:account_asset_management](module:account_asset_management), vedie
odpisový plán každého majetku zvlášť, ale za celý register ponúka len statický
výkaz v XLSX. Tento modul pridáva dve obrazovky na kontrolu **účtovných
odpisov** za celý majetok:

- **Odpisový plán (dynamický)** — prehľad pohybov dlhodobého majetku za
  ľubovoľné obdobie: obstarávacia cena, oprávky na začiatku, odpisy za obdobie,
  vyradenia, oprávky na konci a zostatková cena, po jednotlivých položkách
  majetku aj po profiloch majetku.
- **Analýza odpisov** — odpisové riadky v kontingenčnej tabuľke a v grafe,
  podľa majetku, profilu a roka.

Obe obrazovky čítajú odpisové plány, nič neúčtujú a nič nemenia. Daňové odpisy
sú samostatný, neúčtovaný odpisový plán s vlastnými výkazmi — pozri
[module:account_asset_tax](module:account_asset_tax).

## Nastavenie {#setup}

Nič sa nenastavuje. Obe obrazovky sú v ponuke *Fakturácia → Majetok*
(*Účtovníctvo → Majetok*, ak je nainštalované Účtovníctvo z Odoo Enterprise) len pre používateľov
so skupinou *Účtovníctvo* (*Show Full Accounting Features*,
`account.group_account_user`, prideľuje sa na karte používateľa); ostatní
používatelia registra majetku ich nevidia.

Čísla sú len také dobré ako odpisové plány za nimi: majetok sa zobrazí, až keď
je potvrdený a jeho odpisový plán vypočítaný.

## Odpisový plán (dynamický) {#schedule}

*Majetok → Odpisový plán (dynamický)*. Hore zvoľte **Od** a **Do**;
predvolene je to aktuálne účtovné obdobie aktívnej spoločnosti. Prehľad sa
prepočíta hneď po zmene dátumu.

Jeden riadok na položku majetku, zoskupené podľa **profilu majetku**, s
medzisúčtom za profil a riadkom **Spolu**. Kliknutím na riadok profilu ho
zbalíte alebo rozbalíte, kliknutím na majetok otvoríte jeho kartu.

| Stĺpec | Obsah |
|---|---|
| Majetok | Referencia a názov majetku. |
| Obstarávacia cena | *Obstarávacia cena* (*Purchase Value*) z karty majetku. |
| Oprávky k začiatku obdobia | Odpisové riadky s dátumom **pred** *Od*. Patria sem aj riadky označené ako *Počiatočný zostatkový zápis* (odpisy prevzaté z predchádzajúceho systému). |
| + Odpisy | Odpisové riadky s dátumom od *Od* do *Do*. |
| Vyradenia / úbytky | Pri majetku vyradenom v období zostatková cena, ktorá z evidencie odišla — obstarávacia cena − oprávky ku koncu obdobia. To je zostatková hodnota odpísaná sprievodcom vyradenia (*Vyradiť*) plus prípadná zostatková hodnota na konci životnosti. |
| Oprávky ku koncu obdobia | Oprávky na začiatku + odpisy za obdobie. |
| Zostatková cena na konci | Obstarávacia cena − oprávky ku koncu obdobia − vyradenia: zostatková cena k dátumu *Do* vrátane zostatkovej hodnoty na konci životnosti; pri majetku vyradenom v období nula. |

**Zaúčtované aj plánované riadky sa počítajú rovnako.** Prehľad ukazuje
odpisový plán, nielen to, čo je v hlavnej knihe: obdobie, ktoré ešte nebolo
zaúčtované, ukazuje plánované odpisy. Čo je skutočne zaúčtované, zistíte v
analýze nižšie s filtrom *Zaúčtované*.

Zahrnutý je majetok v stave *Prebiehajúci*, plne odpísaný (stav, ktorý sa v
slovenskom preklade zobrazuje ako *Zatvoriť*) a vyradený majetok s dátumom
začiatku najneskôr v deň *Do*. Vyradený majetok vypadne, keď je dátum
vyradenia pred *Od*. Majetok v stave *Návrh* sa nezobrazuje. Plne odpísaný
majetok, ktorý spoločnosť stále drží, sa zobrazuje ďalej, bez pohybu v období.

## Analýza odpisov {#analysis}

*Majetok → Analýza odpisov* otvorí odpisové riadky (len riadky typu *Odpis*,
nie riadky obstarania ani vyradenia, a žiadne riadky majetku v stave *Návrh*)
v kontingenčnej tabuľke: majetok v
riadkoch, roky v stĺpcoch, miera *Suma*. Graf zobrazí ročné odpisy ako
skladané stĺpce.

Filtre a zoskupenia vo vyhľadávaní:

- **Zaúčtované** — riadky s účtovným zápisom; **Plánované** — riadky ešte
  nezaúčtované;
- zoskupenie podľa **Majetok**, **Profil majetku** alebo **Rok**.

*Suma* je jediná miera. Pole OCA *Odpis nasledujúceho obdobia*, ktoré
napriek názvu obsahuje zostatkovú hodnotu po danom riadku, je zostatok: jeho
súčet za riadky roka nedával zmysel, preto sa neponúka.

## Obmedzenia {#limitations}

- Prehľad zobrazuje **len aktívnu spoločnosť** v jej mene, aj keď je zvolených
  viac spoločností. Analýza sa riadi bežným výberom spoločností a môže ich
  miešať.
- Prehľad sa nedá vytlačiť ani exportovať; použite export z kontingenčnej
  tabuľky alebo výkaz OCA *Výkaz finančného majetku* v ponuke *Výkazy*.
- Len účtovné odpisy. Daňové odpisy a rozdiel medzi oboma vykazuje
  [module:account_asset_tax](module:account_asset_tax).
- Len pre register majetku v Community. Odoo Enterprise má pre svoj register
  `account_asset` vlastný odpisový prehľad.
