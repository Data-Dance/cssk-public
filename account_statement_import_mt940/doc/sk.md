---
title: Import bankových výpisov — MT940 / MultiCash
summary: Importuje bankové výpisy SWIFT MT940 — súbory *.STA z MultiCash, X-business a Business 24 — so symbolmi VS/KS/SS, účtami protistrany a zostatkami.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

České banky odovzdávajú výpisy účtovným programom vo formáte **SWIFT MT940**:
MultiCash ich zapisuje ako súbory `*.STA` (vo verzii 3.x do priečinka
`MCCWIN`, vo verzii 4.x do `DATA`) a rovnakú štruktúru používajú X-business a
Business 24. Časť SWIFT je všade rovnaká; pole `:86:` („informácia pre
majiteľa účtu“) nie, a práve v ňom sú variabilný, konštantný a špecifický
symbol, účet a názov protistrany a správa k platbe.

Modul takéto súbory importuje cez sprievodcu importom výpisov OCA
(`account_statement_import_file`), v edícii Community aj Enterprise. Je to
výpisová polovica MultiCash; platobnú polovicu rieši modul
[module:account_multicash](module:account_multicash).

## Čo sa načíta {#format}

| Pole | Výsledok |
|---|---|
| `:25:` účet | denník, ku ktorému výpis patrí |
| `:28C:` číslo výpisu | názov výpisu `MT940 <účet>/<číslo>` |
| `:60F:` / `:60M:` počiatočný zostatok | počiatočný zostatok výpisu a jeho mena |
| `:61:` transakcia | riadok výpisu: suma, znamienko (`C` kredit, `D` debet, `RC`/`RD` storná), dátum zaúčtovania (inak dátum valuty), typ transakcie SWIFT, referencia klienta |
| `:86:` podrobnosti | popis, VS/KS/SS, účet a názov protistrany |
| `:62F:` / `:62M:` konečný zostatok | konečný zostatok výpisu |

**Pole `:86:`.** Banky ho zapisujú ako podpolia `?NN` a nezhodnú sa na
číslovaní — Česká sporiteľňa dáva `KS:` do `?20` a `VS:` do `?21`,
Raiffeisenbank `KS` do `?21` a `VS` do `?22`. Modul preto symbol rozpozná
podľa predpony (`VS`, `KS`, `SS`, s dvojbodkou aj bez nej, s úvodnými nulami
aj bez nich), nikdy podľa pozície. Protistrana sa berie z `?30` (kód banky
alebo BIC), `?31` (účet), `?38` (IBAN) a `?32`/`?33` (názov); správa z `?00`,
`?20`–`?29` a `?60`–`?63`. Opakujúci sa šum, napríklad číslo výpisu
Raiffeisenbank a nulové poplatky, sa vynechá. Pole `:86:` bez podpolí sa
ponechá ako voľný text a značky typu `VS:` sa z neho aj tak vyberú.

Na každom riadku výpisu:

- **Popis**: názov protistrany, správa, `VS:…`, `KS:…`, `SS:…`, účet
  protistrany.
- **Partner**: hľadá sa podľa účtu protistrany medzi bankovými účtami v Odoo.
- **Symboly**: ak je nainštalovaný modul
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements),
  aj vo vlastných poliach symbolov riadku.
- Pôvodný text `:61:`/`:86:` ostane uložený pri riadku, referencia klienta
  ide do poľa *Referencia*, typ SWIFT do poľa *Typ transakcie*.

Jeden súbor môže obsahovať viac dní a viac účtov; každý výpis pristane vo
svojom denníku. Výpis rozdelený do viacerých správ (počiatočný zostatok
`:60M:`, rovnaké číslo výpisu, počiatočný zostatok rovný predchádzajúcemu
konečnému) sa spojí do jedného.

Súbor sa číta ako UTF-8, ak je platným UTF-8, inak v kódovej stránke 852 alebo
Windows-1250 podľa toho, ktorá dá viac českých písmen.

## Nastavenie {#setup}

- Každý účet zo súboru potrebuje bankový denník s týmto bankovým účtom
  (*Účtovníctvo → Konfigurácia → Účtovníctvo → Účtovné denníky*) v mene
  výpisu.
- **Účet môže byť zapísaný ľubovoľne.** Česká sporiteľňa zapisuje `:25:` ako
  `0800/192000145399` (najprv kód banky), iné banky ako IBAN. Modul porovnáva
  kód banky, predčíslie a číslo, takže denník s účtom uloženým ako IBAN alebo
  ako `19-2000145399/0800` sa nájde v oboch prípadoch.

## Import výpisu {#usage}

*Účtovníctvo → Účtovníctvo → Importovať výpis* alebo **Import výpisov (OCA)**
na karte bankového denníka na riadiacom paneli Účtovníctva. Vyberte súbor
`.STA` a stlačte **Importovať a zobraziť**.

Opakovaný import toho istého výpisu sa odmietne riadok po riadku: kľúč
importu riadku sa skladá z účtu, čísla výpisu, dátumu valuty, poradia riadku vo
výpise, sumy a referencie banky. Súbor, ktorý sa prekrýva so skorším importom,
prinesie len nové riadky.

## Obmedzenia {#limitations}

- Štruktúra poľa `:86:` bola overená podľa zverejnených opisov Českej
  sporiteľne (*MultiCash 3.2*, platí aj pre Business 24) a Raiffeisenbank
  (MT940 verzie 2–4 pre MultiCash a X-business). MT940 iných bánk sa číta cez
  rovnaké polia SWIFT, ich `:86:` však nebolo porovnané so zverejnenou
  štruktúrou; pri voľnom texte v `:86:` je popisom text tak, ako prišiel.
- Párovanie denníka podľa kódu banky, predčíslia a čísla funguje pre české a
  slovenské účty. Zahraničný účet sa musí zhodovať s účtom denníka tak, ako je
  zapísaný.
- Kľúč importu obsahuje poradie riadku vo výpise. Ak banka vydá výpis znova s
  inak zoradenými riadkami, riadky sa môžu naimportovať dvakrát.
- MT940 má dvojmiestne roky; dátumy sa čítajú v rozsahu 1980–2079.
