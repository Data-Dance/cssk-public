---
title: Daňové priznanie k DPH OSS — úprava pre Úniu (DPOSS_EU)
summary: Slovenské daňové priznanie v osobitnej úprave pre Úniu ako eFormulár Finančnej správy DPOSS_EUv01 v celoeurópskej štruktúre, overené voči úradnej schéme.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Slovenská zdaniteľná osoba, ktorá uplatňuje **osobitnú úpravu pre Úniu**,
podáva štvrťročne daňové priznanie k dani uplatnenej pri predaji tovaru na
diaľku a pri službách spotrebiteľom v iných štátoch EÚ. Tento modul prevedie
priznanie vypočítané modulom
[module:l10n_cssk_oss_base](module:l10n_cssk_oss_base) do eFormulára Finančnej
správy **DPOSS_EUv01** (*Daňové priznanie k DPH — Úprava pre Úniu*) a pred
priložením ho overí voči úradnej schéme.

Všetko o príprave priznania — riadky, opravy, výmenné kurzy a kroky exportu —
opisuje [spoločný návod](module:l10n_cssk_oss_base#usage). Táto stránka
opisuje to, čo je slovenské.

## Právny rámec {#legal}

Odkazy sú na [zákon č. 222/2004 Z. z. o dani z pridanej hodnoty](law:sk/2004/222).

- **Na čo sa úprava vzťahuje.** Na predaj tovaru na diaľku na území EÚ, na
  dodanie služby zdaniteľnou osobou neusadenou v členskom štáte spotreby osobe
  inej ako zdaniteľnej osobe a na určité domáce dodanie tovaru cez elektronické
  rozhranie —
  [§ 68 ods. 1 písm. b)](law:sk/2004/222#paragraf-68.odsek-1.pismeno-b).
- **Registrácia.** Zdaniteľná osoba, ktorá sa rozhodne uplatňovať osobitnú
  úpravu s tuzemskom ako členským štátom identifikácie, oznámi daňovému úradu
  začatie tejto činnosti a potom ju musí uplatňovať na všetky takéto dodania —
  [§ 68b ods. 2](law:sk/2004/222#paragraf-68b.odsek-2) a
  [ods. 6](law:sk/2004/222#paragraf-68b.odsek-6).
- **Elektronické doručovanie.** Písomnosti týkajúce sa osobitnej úpravy sa
  daňovému úradu doručujú elektronickými prostriedkami —
  [§ 68 ods. 3](law:sk/2004/222#paragraf-68.odsek-3).
- **Obdobie a lehota.** Zdaňovacím obdobím je kalendárny štvrťrok; priznanie sa
  podáva aj za štvrťrok bez dodaní, do konca nasledujúceho kalendárneho
  mesiaca, a ak koniec lehoty pripadne na sobotu, nedeľu alebo sviatok,
  posledným dňom lehoty je tento deň —
  [§ 68b ods. 12](law:sk/2004/222#paragraf-68b.odsek-12).
- **Obsah.** Hodnota dodaní bez dane, výška dane pre každú sadzbu, sadzba a
  celková splatná daň v členení podľa členských štátov spotreby — a osobitne
  za tovar odoslaný z iných členských štátov a za služby dodané z prevádzkarní
  v iných štátoch —
  [§ 68b ods. 13 až 16](law:sk/2004/222#paragraf-68b.odsek-13).
- **Eurá.** Sumy sa uvádzajú v eurách; úhrada v inej mene sa prepočíta
  referenčným výmenným kurzom ECB alebo Národnej banky Slovenska platným
  posledný deň zdaňovacieho obdobia alebo nasledujúci deň, ak v posledný deň
  kurz určený nebol —
  [§ 68b ods. 17](law:sk/2004/222#paragraf-68b.odsek-17).
- **Platenie.** Daň sa platí v eurách najneskôr do konca lehoty na podanie
  priznania s odkazom na priznanie —
  [§ 68b ods. 18](law:sk/2004/222#paragraf-68b.odsek-18).
- **Opravy.** Zmena údajov pôvodného priznania sa uvedie v nasledujúcom
  priznaní najneskôr do troch rokov od uplynutia pôvodnej lehoty, s uvedením
  členského štátu spotreby, obdobia a sumy dane, kurzom, ktorý sa mal použiť
  pôvodne — [§ 68b ods. 19](law:sk/2004/222#paragraf-68b.odsek-19).

## Tlačivo {#form}

Modul vytvára **DPOSS_EUv01**, prvý a zatiaľ jediný vzor slovenského priznania
v osobitnej úprave pre Úniu, používaný od začiatku úpravy 1. 7. 2021. Slovenské
tlačivá sa verzujú po vzoroch a za staré obdobie sa použije vzor platný vtedy;
pri tomto priznaní existuje len jeden, preto je tu **jedna verzia tlačiva**,
*DP DPH — úprava pre Úniu (DPOSS_EUv01)*, platná od 1. 7. 2021 bez konca
platnosti. Štvrťroky pred 3. štvrťrokom 2021 sa podávali na priznaní MOSS,
teda na inom tlačive.

XML nie je slovenská štruktúra, ale celoeurópske priznanie OSS
`OSSVATReturnMSCON` podľa schémy `dposs_eu01.xsd`, ktorú Finančná správa
zverejňuje k eFormuláru. Schéma uvádza verziu 1.0 európskej štruktúry, čo nič
nehovorí o revízii súboru, preto ju modul pripína veľkosťou a kontrolným
súčtom a test zlyhá, ak pribalená schéma nesedí.

Čo súbor obsahuje:

| Časť | Obsah |
|---|---|
| `TraderID` | IČ DPH s predponou `SK` |
| `Period` | rok, štvrťrok a dátum začiatku alebo konca, ak sa registrácia začala alebo skončila počas štvrťroka |
| `NilVatReturn` | `1` pri nulovom priznaní, inak `0` |
| `MSIDSupplies` | dodania zo Slovenska: tovar alebo služby, členský štát spotreby (Grécko ako `EL`), sadzba s typom (štandardná alebo znížená), základ dane a DPH |
| `MSESTSupplies` | dodania z prevádzkarne alebo štátu odoslania inde — ručné riadky — s IČ DPH v danom štáte alebo kódom krajiny |
| `Corrections` | za každý opravovaný štvrťrok a členský štát oprava DPH |
| súčty | DPH z dodaní zo Slovenska a odinakiaľ, zvlášť za tovar a služby, a celkový súčet |
| `Balances` | za každý členský štát DPH tohto štvrťroka vrátane opráv |
| `TotalVATAmountDue` | súčet len **kladných** zostatkov, tak ako ho počíta eFormulár; sumu, o ktorú je členský štát po opravách záporný, vracia tento štát sám |

Prvky nesú predponu menného priestoru `vun:`. Je to zámer: nahrávač
eFormulára hľadá prvky podľa tohto mena a súbor bez predpony síce prejde
validáciou, ale do formulára na portáli sa nahrá ako prázdne priznanie.

## Nastavenie {#setup}

- **DIČ** (*Tax ID*) spoločnosti musí byť IČ DPH: `SK` a 10 číslic (číslo
  zadané bez predpony sa prijme a zapíše s ňou). Export čokoľvek iné odmietne.
- Verzia tlačiva sa nainštaluje s modulom. Na každom priznaní zvoľte
  *DP DPH — úprava pre Úniu (DPOSS_EUv01)*.
- Dane OSS v Odoo nastavte podľa
  [spoločného návodu](module:l10n_cssk_oss_base#setup) vrátane slovenskej
  sadzby 5 %.

## Podanie {#usage}

1. Priznanie pripravte a vypočítajte v *Účtovníctvo → Výkazy → Zákonné výkazy
   → Daňové priznania k DPH OSS* a potvrďte kurzy ECB.
2. **Exportovať XML**. Súbor sa overí voči `dposs_eu01.xsd` a priloží.
3. Súbor nahrajte do eFormulára DPOSS_EUv01 na portáli Finančnej správy,
   skontrolujte ho tam a podajte z portálu.
4. **Označiť ako podané**, aby sa uchovala podaná kópia. Záznam podania, ktorý
   otvorí tlačidlo **Podať**, uchová potvrdenie stiahnuté z portálu.

*Splatnú DPH (EUR)* zaplaťte v eurách do konca lehoty na podanie. Modul platbu
nevytvára.

## Obmedzenia {#limitations}

- Len osobitná úprava pre Úniu. Priznania v úprave mimo Únie a pri dovoze nie
  sú vytvorené.
- Modul priznanie Finančnej správe priamo neposiela: súbor sa do eFormulára na
  portáli nahráva ručne.
- Opravu, ktorú treba po uplynutí troch rokov podať priamo členskému štátu
  spotreby, modul nepripravuje.
- Nový vzor alebo tichá revízia schémy si vyžaduje aktualizáciu modulu.
- Kontroly sú tie, ktoré opisuje
  [spoločný návod](module:l10n_cssk_oss_base#limitations); vlastné kontroly
  portálu prebehnú až po nahraní súboru tam.
