---
title: SK Protokoly o zaradení a vyradení majetku
summary: Protokol o zaradení dlhodobého majetku do používania a protokol o jeho vyradení, tlačené z evidencie majetku v ktorejkoľvek edícii Odoo.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Pri každom dlhodobom majetku vyhotovuje účtovník dva interné doklady:

- **Protokol o zaradení dlhodobého majetku do používania** — inventárne
  číslo, obstarávacia cena, dátum zaradenia, miesto umiestnenia a zodpovedná
  osoba;
- **Protokol o vyradení dlhodobého majetku** — dôvod a spôsob vyradenia a
  hodnoty majetku v tom okamihu.

Modul pridáva údaje, ktoré protokol potrebuje a evidencia majetku ich nemá, a
obe tlačové zostavy. Funguje s tou evidenciou majetku, ktorá je
nainštalovaná:

| Edícia | Evidencia majetku | Prepojenie (nainštaluje sa samo) |
|---|---|---|
| Community | OCA `account_asset_management` | [module:l10n_sk_asset_protocol_oca](module:l10n_sk_asset_protocol_oca) — pozri [Community](#community) |
| Enterprise | Odoo `account_asset` | [module:l10n_sk_asset_protocol_ee](module:l10n_sk_asset_protocol_ee) — pozri [Enterprise](#enterprise) |

Nainštalujte tento modul, príslušné prepojenie sa doinštaluje samo. Bez
evidencie majetku sa modul nainštaluje, ale nič nezobrazí.

## Právny rámec {#legal}

Ani jeden protokol nemá predpísaný vzor. Oba sú internými účtovnými dokladmi
a účtovný doklad musí podľa
[§ 10 ods. 1 zákona o účtovníctve](law:sk/2002/431#paragraf-10.odsek-1)
obsahovať slovné a číselné označenie dokladu, obsah účtovného prípadu a
označenie jeho účastníkov, peňažnú sumu alebo cenu za mernú jednotku a
množstvo, dátum vyhotovenia, dátum uskutočnenia účtovného prípadu, ak sa
líši, a podpisový záznam osoby zodpovednej za účtovný prípad.

Výstupy obsahujú číslo dokladu a dátum vyhotovenia, účtovnú jednotku so
sídlom a IČO, majetok a jeho hodnoty, dátumy a riadky na podpis. Ďalší obsah
protokolov
určuje vnútorná smernica účtovnej jednotky — šablóny berte ako východisko.

## Údaje pre protokoly {#usage}

Otvorte majetok a kartu **Protokoly (SK)**:

| Blok | Pole | Význam |
|---|---|---|
| Zaradenie | Inventárne číslo (*Inventory number*) | Číslo v evidencii majetku. Ak je prázdne, protokoly vytlačia vlastné označenie z evidencie (pozri prepojenia). |
| | Miesto umiestnenia (*Location*) | Kde sa majetok nachádza. |
| | Zodpovedná osoba (*Responsible person*) | Kontakt. |
| | Poznámka k zaradeniu (*Commissioning note*) | Technický stav, príslušenstvo, doklady tvoriace prílohu. |
| | Dátum vyhotovenia protokolu o zaradení (*Commissioning protocol date*) | Kedy bol protokol vyhotovený. Prázdne: protokol uvedie deň tlače; vyplňte ho, aby bola aj neskoršia tlač rovnaká. |
| Vyradenie | Spôsob vyradenia (*Disposal method*) | Predaj, likvidácia, darovanie, manko alebo škoda, vklad do inej spoločnosti, iné. |
| | Dôvod vyradenia (*Disposal reason*) | Voľný text. |
| | Dátum vyhotovenia protokolu o vyradení (*Disposal protocol date*) | Ako pri protokole o zaradení. |

Spôsob vyradenia sa eviduje len pre protokol: majetok nevyradí a nič
nezaúčtuje. Vyradenie vykonajte funkciou samotnej evidencie majetku.

## Tlač {#printing}

Na majetku *Tlač*:

Oba protokoly začínajú číslom dokladu — **ZP-** (zaradenie) alebo **VP-**
(vyradenie) a inventárne číslo — dátumom vyhotovenia a názvom, sídlom a IČO
účtovnej jednotky.

- **Protokol o zaradení majetku** — dátum
  zaradenia, názov majetku, inventárne číslo, obstarávacia cena, odpisový
  plán (profil alebo šablóna majetku), miesto umiestnenia, zodpovedná osoba,
  poznámka a riadky na podpis *Majetok odovzdal* / *Majetok prevzal*.
- **Protokol o vyradení majetku** — dátum
  vyradenia, názov majetku, inventárne číslo, dátum zaradenia, obstarávacia
  cena, oprávky (odpísané), zostatková cena, spôsob a dôvod vyradenia,
  upozornenie, že prílohy dokladujúce spôsob vyradenia sú neoddeliteľnou
  súčasťou protokolu, a riadky na podpis *Vyradenie navrhol* / *Vyradenie
  schválil*.

Hodnoty sa vždy zhodujú: obstarávacia cena − oprávky = zostatková cena, teda
zostatková hodnota vrátane neodpisovateľnej hodnoty. Oprávky sú len zaúčtované
odpisy; v protokole o vyradení vyradeného majetku neobsahujú odpísanú
zostatkovú cenu, tá je v riadku *Zostatková cena*.

Výstupy sú vždy v slovenčine, dátumy vo formáte jazyka používateľa. Oba sa dajú vytlačiť kedykoľvek; protokol o
vyradení majetku, ktorý ešte vyradený nie je, má prázdny dátum vyradenia.

## Community: evidencia majetku OCA {#community}

[module:l10n_sk_asset_protocol_oca](module:l10n_sk_asset_protocol_oca) sa
nainštaluje sám, keď je nainštalovaný tento modul aj OCA
`account_asset_management`. Majetok je v ponuke *Účtovníctvo → Assets →
Assets* (ponuka modulu OCA sa môže zobrazovať anglicky). Protokoly berú:

| V protokole | Z majetku OCA |
|---|---|
| Dátum zaradenia | *Asset Start Date* |
| Obstarávacia cena | *Purchase Value* |
| Oprávky (odpísané) | zaúčtované riadky odpisov (nie riadok vyradenia) |
| Zostatková cena | *Purchase Value* − oprávky (vrátane neodpisovateľnej hodnoty) |
| Odpisový plán | *Asset Profile* |
| Dátum vyradenia | *Asset Removal Date*, ktorý nastaví sprievodca vyradením |
| Inventárne číslo, ak je prázdne | *Reference* |

## Enterprise: evidencia majetku Odoo {#enterprise}

[module:l10n_sk_asset_protocol_ee](module:l10n_sk_asset_protocol_ee) sa
nainštaluje sám, keď je nainštalovaný tento modul aj `account_asset` z Odoo
Enterprise. Majetok je v ponuke *Účtovníctvo → Účtovníctvo → Majetok a
záväzky → Majetok*. Protokoly berú:

| V protokole | Z majetku Enterprise |
|---|---|
| Dátum zaradenia | *Dátum nadobudnutia* |
| Obstarávacia cena | *Pôvodná hodnota* majetku a jeho zvýšení hodnoty (podriadený majetok) |
| Oprávky (odpísané) | zaúčtované odpisy majetku a jeho zvýšení hodnoty vrátane odpisov importovaných ako už vykonané; nie zápis vyradenia ani predaja |
| Zostatková cena | obstarávacia cena − oprávky (vrátane neodpisovateľnej hodnoty) |
| Odpisový plán | *Šablóna majetku* |
| Dátum vyradenia | *Dátum vyradenia*, nastavený pri vyradení alebo predaji |
| Inventárne číslo, ak je prázdne | názov majetku |

Obe prepojenia naraz nainštalovať nemožno, pretože sa obe evidencie majetku
navzájom vylučujú.

## Obmedzenia {#limitations}

- Číslo dokladu sa odvodzuje z inventárneho čísla (alebo z označenia v
  evidencii); jedinečnosť inventárnych čísel Odoo nekontroluje.
- Protokoly neuvádzajú odpisovú skupinu ani daňovú zostatkovú cenu; tie
  vedie [module:account_asset_tax](module:account_asset_tax).
- Zodpovedná osoba je ľubovoľný kontakt, nijako nesúvisí so zamestnancom ani
  s hmotne zodpovednou osobou pri inventarizácii.
