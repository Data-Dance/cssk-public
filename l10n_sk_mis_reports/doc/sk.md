---
title: SK manažérska výsledovka (MIS Builder)
summary: Manažérska výsledovka na slovenskej účtovej osnove ako upraviteľná šablóna MIS Builder pre Odoo Community.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Odoo Enterprise má vlastné manažérske výkazy, Community žiadne. Tento modul
dáva databáze Community **manažérsku výsledovku** pre spoločnosti, ktoré
účtujú podľa slovenskej účtovej osnovy Odoo. Je to šablóna pre modul OCA
[module:mis_builder](module:mis_builder), takže obdobia, porovnania, rozpočty,
export do PDF a XLSX zabezpečuje tento modul a šablónu si môže kontrolór sám
upraviť.

Ide o manažérsky pohľad, **nie** o *Výkaz ziskov a strát* do účtovnej
závierky. Výkazy účtovnej závierky zostavuje modul
[module:l10n_sk_fs](module:l10n_sk_fs). Zoskupenia tu sú zvolené kvôli
prehľadnosti a nezodpovedajú riadkom tlačiva, preto tieto dva výkazy
neporovnávajte riadok po riadku.

## Čo výkaz obsahuje {#lines}

Šablóna sa volá **Manažérska výsledovka (SK)**. Číta účty tried 5 a 6 podľa
začiatku čísla účtu, takže nepotrebuje žiadne značky účtov:

| Riadok | Účty | Znamienko |
|---|---|---|
| Tržby za tovar | 604 | výnos |
| Tržby za vlastné výrobky a služby | 601, 602, 606, 607 | výnos |
| Ostatné výnosy z hospodárskej činnosti | 61, 62, 64, 65 | výnos |
| **Výnosy spolu** | súčet troch riadkov vyššie | |
| Predaný tovar | 504 | náklad |
| Predané nehnuteľnosti na predaj | 507 | náklad |
| Spotreba materiálu a energie | 501, 502, 503, 505 | náklad |
| Služby | 51 | náklad |
| Osobné náklady | 52 | náklad |
| Dane a poplatky | 53 | náklad |
| Odpisy dlhodobého majetku | 551 | náklad |
| (pomocný riadok) trieda 54 a 55 vrátane odpisov | 54, 55 | náklad |
| Ostatné náklady na hospodársku činnosť | 54 a 55 bez 551 | náklad |
| **Náklady spolu** | súčet nákladových riadkov (pomocný riadok sa nezapočítava) | |
| **Prevádzkový výsledok hospodárenia** | výnosy spolu − náklady spolu | |
| Finančné výnosy | 66 | výnos |
| Finančné náklady | 56 | náklad |
| **Výsledok hospodárenia pred zdanením** | prevádzkový výsledok + finančné výnosy − finančné náklady | |
| Daň z príjmov | 591, 592, 595 | náklad |
| Prevod podielov na výsledku hospodárenia spoločníkom | 596 | náklad |
| **Výsledok hospodárenia po zdanení** | výsledok pred zdanením − daň z príjmov − prevod podielov | |

Každá suma je **obrat za obdobie**, nie kumulovaný zostatok. Výnosy sa
otáčajú, aby sa zobrazovali kladne, rovnako ako náklady, a medzisúčty sedia
tak, ako to čitateľ čaká. Účtová skupina 61 (zmena stavu vnútroorganizačných
zásob) je výnosom, keď má stranu Dal; pri úbytku zásob je preto táto časť
*Ostatných výnosov* záporná.

Pomocný riadok *(pomocný riadok) trieda 54 a 55 vrátane odpisov* je tam len na
to, aby sa odpisy nezapočítali dvakrát — účet 551 patrí do skupiny 55. Jeho
štýl (*SK — pomocný (skrytý)*) ho vo výkaze skrýva.

## Spustenie výkazu {#usage}

1. Nainštalujte modul. Potrebuje slovenskú účtovú osnovu a modul
   [module:mis_builder](module:mis_builder).
2. Otvorte *Účtovníctvo → Výkazy → MIS Reporting → MIS Reports* (ponuky
   MIS Builder sú v angličtine) a kliknite na *Nové*.
3. Zvoľte šablónu (*Template*) **Manažérska výsledovka (SK)** a spoločnosť.
4. Zvoľte jedno obdobie, alebo zapnite porovnávací režim (*Comparison Mode*)
   a na karte *Columns* pridajte stĺpce — napríklad mesiace roka alebo tento
   rok oproti minulému.
5. Kliknite na **Preview**, **Print** (PDF) alebo **Export** (XLSX). Z každej
   sumy sa dá prejsť na účtovné položky, z ktorých vznikla.

Predvolene sa započítavajú len zaúčtované zápisy (*Target Moves: All Posted
Entries*).

## Úprava šablóny {#adjusting}

Šablóna je v *Účtovníctvo → Konfigurácia → MIS Reporting → MIS Report
Templates*. Ktoré účty patria do ktorého riadku, je manažérske rozhodnutie a
treba ho odsúhlasiť s účtovníkom — najmä čo patrí do *Ostatných nákladov* a čo
do prevádzkových skupín. Výrazy upravíte priamo tam.

Šablóna a jej štýly sa nahrajú len raz: vaše úpravy prežijú aktualizáciu
modulu. Oprava z novšej verzie modulu sa pri aktualizácii použije len na
riadok, ktorý ste nemenili.

Pri pridávaní riadkov pozor na jednu pascu: technický názov riadku nesmie
začínať predponou účtovného výrazu, napríklad `bal`, `balp`, `crd` alebo
`deb`. MIS Builder tieto reťazce prepisuje ako text a každý výraz, ktorý sa
na taký riadok odvoláva, potom ukáže `#ERR`. Preto sa pomocný riadok volá
`trieda_54_55`.

## Obmedzenia {#limitations}

- Účty sa vyberajú podľa začiatku čísla. Účty s inými číslami, ktoré do osnovy
  doplníte, výkaz nezachytí, kým ich nepridáte do šablóny.
- Nie je to prehľad peňažných tokov ani ich plán. Plán peňažných tokov dáva
  modul OCA [module:mis_builder_cash_flow](module:mis_builder_cash_flow), *Prehľad peňažných tokov* do účtovnej
  závierky modul [module:l10n_sk_fs](module:l10n_sk_fs).
