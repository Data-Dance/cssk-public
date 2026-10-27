---
title: SK účtovná závierka v jednoduchom účtovníctve (Úč FO)
summary: Účtovná závierka SZČO v jednoduchom účtovníctve — výkaz o príjmoch a výdavkoch z peňažného denníka a výkaz o majetku a záväzkoch z účtovníctva, exportované ako oficiálny súbor UZFOv14.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

SZČO, ktorá vedie **jednoduché účtovníctvo**, uzatvára rok **účtovnou
závierkou** z dvoch výkazov, ktoré sa podávajú ako jeden elektronický dokument
(XML vzor *UZFOv14*):

| Výkaz | Tlačivo | Zdroj údajov |
|---|---|---|
| Výkaz o príjmoch a výdavkoch | Úč FO 1-01, riadky 01 – 12 | peňažný denník |
| Výkaz o majetku a záväzkoch | Úč FO 2-01, riadky 01 – 21, bežné a predchádzajúce obdobie | zostatky účtov ku koncu obdobia |

Modul tento dokument zostavuje na spoločnom mechanizme opísanom v
[module:l10n_cssk_fs_base](module:l10n_cssk_fs_base), takže výpočet, kontroly,
ručné zadanie súm, export aj evidencia podania fungujú rovnako ako pri
ostatných výkazoch. Príjmovú a výdavkovú stranu číta z peňažného denníka
modulu [module:l10n_sk_cash_journal](module:l10n_sk_cash_journal), nie znova z
účtov.

Kto vedie **daňovú evidenciu** alebo uplatňuje paušálne výdavky, nie je
účtovnou jednotkou a závierku nepodáva; tento modul nie je preňho.

## Právny rámec {#legal}

Ak nie je uvedené inak, odkazy sú na [zákon o účtovníctve](law:sk/2002/431).

- **Kto.** Zákon sa vzťahuje na fyzické osoby, ktoré podnikajú a preukazujú
  výdavky na účely zistenia základu dane z príjmov, okrem tých, ktoré vedú
  daňovú evidenciu —
  [§ 1 ods. 1 písm. a) tretí bod](law:sk/2002/431#paragraf-1.odsek-1.pismeno-a.bod-3).
- **Súčasti.** Účtovná závierka v sústave jednoduchého účtovníctva obsahuje
  výkaz o príjmoch a výdavkoch a výkaz o majetku a záväzkoch —
  [§ 17 ods. 4](law:sk/2002/431#paragraf-17.odsek-4).
- **Tlačivo.** Usporiadanie ustanovuje opatrenie MF SR č. MF/27076/2007-74 pre
  účtovné jednotky účtujúce v sústave jednoduchého účtovníctva v znení
  neskorších predpisov; modul vytvára jeho elektronický vzor *UZFOv14*.
  Veľkostné skupiny (mikro, malá, veľká) sa týkajú len účtovných jednotiek v
  podvojnom účtovníctve —
  [§ 2 ods. 5](law:sk/2002/431#paragraf-2.odsek-5) — preto je tlačivo pre
  všetky veľkosti jedno.
- **Uloženie.** Závierka sa ukladá v registri účtovných závierok —
  [§ 23a ods. 3](law:sk/2002/431#paragraf-23a.odsek-3) — prostredníctvom
  portálu finančného riaditeľstva —
  [§ 23b ods. 1](law:sk/2002/431#paragraf-23b.odsek-1).

## Nastavenie {#setup}

1. **Veďte peňažný denník.** Úč FO 1-01 číta kategórie peňažného denníka;
   nastavte ich a vygenerujte denník za rok podľa
   [príručky k peňažnému denníku](module:l10n_cssk_cash_journal_base#usage).
2. **Údaje spoločnosti pre hlavičku**: DIČ (pole *DIČ* z modulu
   [module:l10n_sk_base](module:l10n_sk_base); ak chýba, *Tax ID* bez
   predpony `SK` — bez oboch export neprebehne), *IČO*, meno, adresa — číslo
   domu na konci poľa *Ulica* (*Hlavná 12*) — telefón a e-mail a kód SK NACE,
   ak je nainštalovaný modul [module:partner_nace](module:partner_nace).

## Príprava závierky {#usage}

*Účtovníctvo → Účtovníctvo → Peňažný denník → Účtovná závierka v JÚ (Úč FO)*
a potom *Nový*. Predvyplní sa verzia *Účtovná závierka v jednoduchom
účtovníctve (UZFOv14)*, obdobie sa nastaví na posledný skončený rok.

- **Prvá závierka v JÚ** (*First závierka in JÚ*) nechá stĺpec
  predchádzajúceho obdobia vo výkaze Úč FO 2-01 prázdny. Zaškrtne sa
  automaticky, ak účtovníctvo nemá pred obdobím žiadny zaúčtovaný zápis;
  zaškrtnite ho sami, ak ste v predchádzajúcom období viedli podvojné
  účtovníctvo — to sa z účtovníctva zistiť nedá.

Kliknite na **Vypočítať**.

**Úč FO 1-01 — z peňažného denníka.** Každý riadok sčíta riadky denníka
svojich kategórií za obdobie tak, ako ich kategórie nesú (vrátenie peňazí
zníži vlastnú kategóriu):

| Riadok | Kategórie |
|---|---|
| 01 Predaj tovaru | P1 |
| 02 Predaj výrobkov a služieb | P2 |
| 03 Ostatné príjmy | P3 |
| 05 Zásoby | V1 |
| 06 Služby | V2 |
| 07 Mzdy | V3 |
| 08 Platby poistného a príspevkov | V4, V5 |
| 09 Tvorba sociálneho fondu | V6 |
| 10 Ostatné výdavky | V9, Z1 (odpisy), Z2 (úpravy základu dane) |

Započítajú sa aj odpisy a ostatné nepeňažné riadky peňažného denníka: sú
to jeho uzávierkové účtovné operácie, ktorými sa podľa § 8 ods. 4 písm. a)
opatrenia zvyšujú výdavky, a § 4 ods. 9 zaraďuje odpisy medzi ostatné
výdavky.

Riadky 04, 11 a 12 sú súčty a rozdiel. Príjmy a výdavky, ktoré neovplyvňujú
základ dane (kategórie PN a VN — vklady podnikateľa, splátky úverov, odvod
DPH), v tomto výkaze nie sú; prejavia sa len v zostatkoch Úč FO 2-01.

**Úč FO 2-01 — z účtovníctva.** Zostatky ku koncu obdobia podľa skupín účtov:
dlhodobý majetok (r. 01 – 03), zásoby (04 – 07), pohľadávky (08), krátkodobý
finančný majetok (09 – 13), opravná položka k nadobudnutému majetku (14, 19),
rezervy (16), záväzky (17) a úvery (18). Prečerpaný bankový účet sa vykáže ako
úver. Riadok 21 je rozdiel majetku a záväzkov.

Vklady a úvery s dlhou splatnosťou sa vykážu tam, kam ich zaradí skupina účtu;
presuňte ich ručne zadanou sumou (mechanizmus zaznamená, kto ju zadal).

Výkaz sa zobrazuje aj v zozname *Výkaz ziskov a strát* v ponuke *Zákonné
výkazy*, a to len s riadkami Úč FO 1-01; ponuka Peňažný denník zobrazí celý
dokument.

## Kontroly a export {#export}

- **Nepriradené účty** uvádza len účty majetku a záväzkov, ktoré si žiadny
  riadok nenárokuje. Triedy 5 a 6 (výsledok sa vykazuje z peňažného denníka),
  vlastné imanie (riadok 21 je vlastné imanie podnikateľa), triedy 7 a 9 a
  podsúvahové účty sa zámerne vynechávajú.
- **Exportovať XML** vytvorí dokument UZFOv14 v **celých eurách**, s prázdnym
  prvkom tam, kde suma chýba, a overí ho voči oficiálnej schéme
  `form.300.sk.xsd`. Súbor sa volá *Účtovná závierka v JÚ (Úč FO) — dátum*.
  Podpisový záznam v XML nie je; uvádza sa v listinnej podobe.

Súbor podajte na portáli finančnej správy a zaznamenajte cez **Označiť ako
podané** (pozri [príručku mechanizmu](module:l10n_cssk_fs_base#filing)).

## Obmedzenia {#limitations}

- Druh závierky (*Druh závierky (Úč FO)* na výkaze: riadna, mimoriadna
  alebo priebežná) nastavujete vy; predvolená je riadna. Deň zostavenia je
  deň exportu. Bez kódu NACE sa nepovinný prvok SK NACE vynechá.
- Splatnosť sa z účtov nezisťuje: dlhodobé vklady a úvery treba presunúť
  ručne zadanou sumou.
- Z Odoo sa nič nepodáva.
