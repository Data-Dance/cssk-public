---
title: CZ/SK finančné výkazy bez denníkov koncoročnej uzávierky
summary: Predvaha, hlavná kniha, otvorené položky a saldo podľa splatnosti z OCA vynechávajú denníky uzávierky, otvorenia a archívu, rovnako ako výkazy účtovnej závierky.
verified: 19.0.1.0.1
---

## Na čo slúži {#purpose}

Česko-slovenské účtovníctvo každý rok uzavrie účtovné knihy a k prvému
dňu nasledujúceho roka ich znova otvorí. Naša lokalizácia umožňuje
označiť denníky so zápismi uzávierky a otvorenia — a pri agende prevzatej z
iného systému aj archív dokladov spred prechodu — ako **denníky koncoročnej
uzávierky** (nastavenie modulu [module:l10n_cssk_core](module:l10n_cssk_core)).
Výkazy účtovnej závierky aj daňové priznanie k dani z príjmov tieto denníky
vynechávajú.

Výkazy OCA z modulu
[module:account_financial_report](module:account_financial_report) ich
nevynechávali, a preto s účtovnou závierkou nesedeli:

- **predvaha** za rok ukazovala otvárací zápis k 1. 1. ako obrat v roku:
  stĺpec počiatočného stavu bol nulový a celý počiatočný stav bol v stĺpci
  Debet;
- účty, ktoré predchádzajúci systém kedysi prečísloval, si ponechali zostatok
  len z archívu, takže predvaha ukazovala účty, ktoré spoločnosť už nepoužíva;
- **otvorené položky** započítali prevzatý počiatočný stav aj archívne
  doklady, ktoré tento stav sumarizuje.

S týmto modulom štyri výkazy tieto denníky predvolene vynechávajú. Modul sa
nainštaluje sám, keď je nainštalovaný `account_financial_report` aj
[module:l10n_cssk_core](module:l10n_cssk_core).

## Použitie {#usage}

Sprievodcovia v *Účtovníctvo → Výkazy → Účtovné výkazy OCA* dostanú pod
*Cieľové zápisy* políčko **Vylúčiť uzávierkové a archívne denníky**:

| Výkaz | Čo políčko robí |
|---|---|
| Predvaha | Ak filter denníkov necháte prázdny, výkaz sa zostaví zo všetkých ostatných denníkov spoločnosti. Ak denníky zvolíte sami, použijú sa presne tie, vrátane denníkov uzávierky. |
| Hlavná kniha | Výkaz sa zostaví zo všetkých denníkov spoločnosti okrem denníkov uzávierky. |
| Otvorené položky | Položky z denníkov uzávierky sa do otvorených zostatkov nezapočítajú. |
| Saldo podľa splatnosti | Rovnako ako pri otvorených položkách. |

Políčko je predvolene zaškrtnuté, keď má spoločnosť zvolená v sprievodcovi
aspoň jeden denník koncoročnej uzávierky; keď nemá žiadny, je prázdne a nič
nemení. Po zmene spoločnosti sa nastaví znova. Ak ho pri
jednom spustení odškrtnete, dostanete pôvodné správanie OCA.

*Kniha denníka* a *Výkaz DPH* sa nemenia: prvý sa zostavuje po jednotlivých
denníkoch a druhý číta dane, ktoré zápisy uzávierky nemajú.

## Obmedzenia {#limitations}

- **Kým denníky koncoročnej uzávierky nie sú nastavené, modul nič nerobí**, a
  v tejto verzii toto nastavenie spoločnosti (`l10n_cssk_closing_journal_ids`)
  nezobrazuje žiadny formulár. Pomocník poľa odkazuje na nastavenia
  účtovníctva, tam však nie je; nastavenie zverte správcovi.
- Denník, ktorý tam uvediete, z týchto štyroch výkazov úplne zmizne. Ak je v
  takom denníku zaúčtovaný prvý počiatočný stav prevzatej spoločnosti, zmizne
  aj ten; zaúčtujte ho v bežnom denníku.
