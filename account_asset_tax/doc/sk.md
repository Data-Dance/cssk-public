---
title: Daňové odpisy (CZ/SK)
summary: Druhý, nikdy nezaúčtovaný odpisový plán ku každému majetku pre české a slovenské daňové odpisy popri účtovných, s ročným porovnaním účtovných a daňových odpisov, odloženou daňou a registrom daňových odpisov.
verified: 19.0.1.11.0
---

## Na čo slúži {#purpose}

Slovenské a české spoločnosti odpisujú každý dlhodobý majetok **dvakrát**:

- **Účtovné odpisy** sa riadia vlastným odpisovým plánom účtovnej jednotky a
  účtujú sa do hlavnej knihy (účet 551).
- **Daňové odpisy** sa riadia odpisovými skupinami a metódami zákona o dani z
  príjmov. **Neúčtujú sa** — daňové priznanie ich uplatní namiesto účtovných
  odpisov, takže rozdiel medzi nimi upravuje základ dane.

Registre majetku v Odoo — *Majetok* v Enterprise a register OCA
`account_asset_management` v Community — vedú len prvé z nich. Tento modul
pridáva druhé: daňový odpisový plán pri každom majetku, vypočítaný podľa
zákona, a ročné nástroje, ktoré z oboch plánov pripravia údaje pre daňové
priznanie.

Funguje ako skupina modulov. Nainštalujte:

| Modul | Čo prináša |
|---|---|
| tento modul | výpočet, číselník odpisových skupín, sprievodcov a zostavy |
| **jeden** most k registru majetku: [module:account_asset_tax_oca](module:account_asset_tax_oca) (Community, register OCA) alebo [module:account_asset_tax_ee](module:account_asset_tax_ee) (*Majetok* v Enterprise) | záložku *Daňové odpisy* na karte majetku; pozri [Community](#oca) a [Enterprise](#ee) |
| údaje krajiny: [module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) a/alebo [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax) | zákonné odpisové skupiny s dobou odpisovania, sadzbami a koeficientmi |

Samotný tento modul na majetku nič nezobrazí; potrebuje most.

## Právny rámec {#legal}

**Slovensko** — [zákon č. 595/2003 Z. z. o dani z príjmov](law:sk/2003/595):

- **Odpisové skupiny a doba odpisovania**: sedem skupín, 0 až 6, od 2 do 40
  rokov — [§ 26 ods. 1](law:sk/2003/595#paragraf-26.odsek-1).
- **Spôsob odpisovania.** Rovnomerné odpisovanie vo všetkých skupinách,
  zrýchlené len v skupinách 2 a 3. Spôsob určí daňovník pre každý novoobstaraný
  majetok a *„nemožno ho zmeniť po celú dobu jeho odpisovania“* —
  [§ 26 ods. 3](law:sk/2003/595#paragraf-26.odsek-3).
- **Rovnomerné odpisovanie**: ročný odpis je podiel vstupnej ceny a doby
  odpisovania; v prvom roku len pomerná časť podľa počtu mesiacov od mesiaca
  zaradenia do užívania a neuplatnená časť sa uplatní v roku nasledujúcom po
  uplynutí doby odpisovania —
  [§ 27 ods. 1 a 2](law:sk/2003/595#paragraf-27.odsek-2).
- **Zrýchlené odpisovanie**: koeficienty 6/7/6 (skupina 2) a 8/9/8
  (skupina 3), pomerný prvý rok a zostatková cena pre druhý rok určená, akoby
  sa uplatnil celý odpis prvého roka —
  [§ 28 ods. 1 a 2](law:sk/2003/595#paragraf-28.odsek-2); po technickom
  zhodnotení [§ 28 ods. 3](law:sk/2003/595#paragraf-28.odsek-3).
- **Technické zhodnotenie** a predĺženie doby odpisovania, ktoré prináša —
  [§ 26 ods. 5](law:sk/2003/595#paragraf-26.odsek-5).
- **Prerušenie odpisovania** na celé zdaňovacie obdobia; potom sa pokračuje,
  akoby nebolo prerušené, a doba odpisovania sa predĺži —
  [§ 22 ods. 9](law:sk/2003/595#paragraf-22.odsek-9).
- **Vyradenie.** Ročný odpis možno uplatniť len z majetku účtovaného k
  poslednému dňu zdaňovacieho obdobia —
  [§ 22 ods. 11](law:sk/2003/595#paragraf-22.odsek-11) —, takže v roku
  vyradenia sa daňový odpis neuplatní a daňovým výdavkom je zostatková cena
  podľa [§ 19 ods. 3 písm. b)](law:sk/2003/595#paragraf-19.odsek-3.pismeno-b)
  (pri osobných automobiloch a ďalšom majetku z jeho prvého bodu len do výšky
  príjmov z predaja). Odpis za celé mesiace zostáva len majetku podľa
  [§ 22 ods. 12](law:sk/2003/595#paragraf-22.odsek-12): odpisovanému podľa
  § 26 ods. 6 a 7 a — od roku 2016, ak sa tak daňovník rozhodne — majetku,
  ktorého zostatková cena je výdavkom len do výšky príjmov z predaja.
- **Osobné automobily od 48 000 eur**: základ dane sa zvýši o rozdiel oproti
  rovnomerným odpisom zo vstupnej ceny 48 000 eur, ale len ak je základ dane
  nižší ako stanovená hranica —
  [§ 17 ods. 34](law:sk/2003/595#paragraf-17.odsek-34). Samotné odpisy sa
  neobmedzujú.
- Prepočty sa zaokrúhľujú na eurocenty — [§ 47](law:sk/2003/595#paragraf-47).

**Česká republika** — [zákon č. 586/1992 Sb. o daních z příjmů](law:cz/1992/586):

- **Odpisové skupiny a minimálna doba odpisovania**: šesť skupín, 1 až 6, od
  3 do 50 rokov (§ 30 odst. 1); rovnomerné (§ 31) alebo zrýchlené (§ 32)
  odpisovanie, určené pre každý novoobstaraný majetok a nemenné po celú dobu
  odpisovania (§ 30 odst. 2).
- **Rovnomerné odpisovanie**: sadzba pre prvý rok a pre ďalšie roky, obe zo
  vstupnej ceny, bez pomerného krátenia podľa mesiacov; zvýšené sadzby v prvom
  roku (+10, +15, +20 %) podľa § 31 odst. 1 písm. b) až d) v prípadoch podľa
  § 31 odst. 2 až 4; sadzba pre zvýšenú vstupnú cenu po technickom zhodnotení
  (§ 31 odst. 8).
- **Zrýchlené odpisovanie**: v prvom roku vstupná cena ÷ koeficient, potom
  dvojnásobok zostatkovej ceny ÷ (koeficient − počet rokov odpisovania)
  (§ 32 odst. 2); prvý odpisovateľ môže prvý odpis zvýšiť o 20, 15 alebo 10 %
  vstupnej ceny v tých istých prípadoch ako pri rovnomernom odpisovaní
  (§ 32 odst. 2 písm. a)); po technickom zhodnotení koeficient pre zvýšenú zostatkovú
  cenu (§ 32 odst. 3).
- **Mimoriadne odpisy** bezemisných vozidiel obstaraných od 1. 1. 2024 do
  31. 12. 2028 prvým odpisovateľom: 60 % za prvých 12 mesiacov a 40 % za
  ďalších 12, v celých mesiacoch od mesiaca nasledujúceho po splnení podmienok
  (§ 30a).
- **Vyradenie**: v roku vyradenia len polovica ročného odpisu, a to len pri
  majetku evidovanom na začiatku obdobia (§ 26 odst. 7); majetok zaradený a
  vyradený v tom istom roku nedostane nič.
- **Prerušenie** je možné; pokračuje sa, akoby nebolo prerušené
  (§ 26 odst. 8).
- **Vozidlá kategórie M1**: do výdavkov ide len pomerná časť odpisu podľa
  pomeru 2 000 000 Kč k vstupnej cene (§ 30e).
- Odpisy sa zaokrúhľujú **na celé koruny nahor** (§ 31 odst. 9,
  § 32 odst. 5, § 30a odst. 2).

Účtovné odpisy upravujú osobitne zákony o účtovníctve:
[§ 28 ods. 1 zákona č. 431/2002 Z. z.](law:sk/2002/431#paragraf-28.odsek-1)
a [§ 28 zákona č. 563/1991 Sb.](law:cz/1991/563) — účtovná jednotka odpisuje v
súlade so svojimi účtovnými metódami. Tento plán je odpisový plán registra
majetku a tento modul doň nezasahuje.

## Nastavenie {#setup}

1. Nainštalujte tento modul, most pre svoju edíciu a modul s údajmi krajiny.
   Odpisové skupiny nájdete v *Účtovníctvo → Konfigurácia → Daňové odpisové
   skupiny*.
2. **Nastavenia spoločnosti** na karte spoločnosti (*Nastavenia →
   Spoločnosti*), pri mene — potrebné len pre uvedené funkcie:

   | Pole | Použitie |
   |---|---|
   | Limit daňového odpisu vozidla | Zákonný limit pre vozidlá so začiarknutým *Uplatniť limit odpisu vozidla*, v mene spoločnosti: 48 000 € pri slovenskej spoločnosti, 2 000 000 Kč pri českej. 0 = bez limitu. Čo s ním robí ktorá krajina, pozri pri rovnomennom poli na majetku. |
   | Denník odloženej dane | Interný denník pre zápis odloženej dane z [porovnania](#reconciliation). |
   | Účet odloženej dane (481) | Súvahový účet odloženej dane. Použite účet, na ktorom je len odložená daň z odpisov (napríklad analytický účet 481): porovnanie dorovnáva celý jeho zostatok. |
   | Výsledkový účet odloženej dane (592) | Výsledkový účet odloženej dane. |

3. **Predvolené hodnoty podľa druhu majetku.** *Sledovať daňové odpisy*,
   skupinu, metódu a (CZ) zvýšený odpis v 1. roku nastavte na profile majetku
   (Community) alebo na šablóne majetku (Enterprise); nový majetok vytvorený z
   nich ich prevezme. Pozri časti o mostoch nižšie.

Ponuky tejto skupiny modulov vidia len **správcovia** účtovníctva. Cesty v
ponuke tu začínajú v *Účtovníctvo*; v Community bez účtovníctva Enterprise
sa tá istá hlavná ponuka volá *Fakturácia*.

## Odpisové skupiny {#groups}

*Účtovníctvo → Konfigurácia → Daňové odpisové skupiny* obsahuje zákonné
skupiny nahraté modulmi krajín. Každá skupina má:

- **Krajinu**, číslo **Skupiny**, **Dobu odpisovania (roky)**;
- povolené metódy — *Umožňuje rovnomerné*, *Umožňuje zrýchlené*, *Umožňuje
  mimoriadne (§30a)*;
- české sadzby rovnomerného odpisovania (1. rok, ďalšie roky, zvýšená
  vstupná cena) a koeficienty zrýchleného odpisovania (1. rok, ďalšie roky,
  zvýšená zostatková cena).

Hodnoty pochádzajú zo zákona a pri aktualizácii modulu krajiny sa nahrajú
znova, preto ich neupravujte kvôli jednému majetku. Tabuľky sú na stránkach
modulov [module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax)
a [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax).

Do ktorej skupiny majetok patrí, určuje to, čím majetok je (príloha zákona ho
triedi podľa klasifikácie produkcie), nie účet. Rozhoduje o tom účtovník.

## Nastavenie majetku {#usage}

Otvorte majetok a záložku **Daňové odpisy**:

| Pole | Význam |
|---|---|
| Sledovať daňové odpisy | Viesť pri majetku daňový odpisový plán. |
| Daňová odpisová skupina | Ponúknu sa len skupiny krajiny spoločnosti. |
| Daňová metóda | Rovnomerné, zrýchlené alebo (CZ skupina 2) mimoriadne — prijmú sa len metódy, ktoré skupina povoľuje. |
| Zvýšený odpis v 1. roku | CZ, rovnomerné aj zrýchlené, skupiny 1–3, len prvý odpisovateľ: +10 % pri každom takom majetku, +15 % len pri zariadeniach na čistenie a úpravu vôd a na zhodnocovanie druhotných surovín podľa § 31 odst. 3, +20 % len pri strojoch pre poľnohospodárstvo a lesníctvo poplatníka s prevažne poľnohospodárskou a lesnou výrobou (§ 31 odst. 2); nikdy pri majetku podľa § 31 odst. 5. Podmienky vymenúva nápoveda poľa. Rovnomerné odpisovanie použije tabuľku zvýšených sadzieb, zrýchlené pripočíta percento zo vstupnej ceny k prvému odpisu. Mimo českých skupín 1–3 sa odmietne. |
| Daňová metóda uzamknutá | Začiarkne sa samo po uzavretí prvého roka (pozri [Uzavretie daňového roka](#year-close)); metódu a skupinu potom už zmeniť nemožno. |
| Daňová vstupná cena | Vstupná cena na daňové účely. Pri zapnutí sledovania sa vyplní z účtovnej obstarávacej ceny; zmeňte ju, ak je daňová vstupná cena iná. |
| Uplatniť limit odpisu vozidla | Osobné vozidlo podliehajúce *Limitu daňového odpisu vozidla* spoločnosti. **SK** (§ 17 ods. 34): plán ponechá odpisy v plnej výške a jeho skrytý stĺpec *Pripočítanie za vozidlo (SK § 17 ods. 34)* ukáže za každý rok sumu nad rovnomerným odpisom zo 48 000 € — pozri [Ročné porovnanie](#reconciliation). **CZ** (§ 30e): plán sa počíta z limitu, čo je daňovo uznaná časť každého odpisu. |
| Odpis za celé mesiace v roku vyradenia | Len SK (§ 22 ods. 12): ponechať odpis za celé mesiace, počas ktorých sa majetok v roku vyradenia účtoval. Začiarknite pri majetku odpisovanom podľa § 26 ods. 6 a 7 a podľa vlastného rozhodnutia pri majetku, ktorého zostatková cena je výdavkom len do výšky príjmov z predaja (osobné automobily, člny, lietadlá, motocykle, predané budovy skupiny 6 …). Bez začiarknutia sa v roku vyradenia neodpisuje. |
| Dátum zaradenia (daňové) | Dátum zaradenia do užívania na daňové účely. Prázdne = dátum začiatku účtovného odpisovania. |
| Daňovo odpísané / Daňová zostatková cena | Súčet uzavretých riadkov plánu a súčet riadkov, ktoré ešte uzavreté nie sú. |

Potom kliknite na **Vypočítať daňový odpisový plán**. Plán sa zakaždým
prepočíta z týchto polí; už uzavreté roky zostanú nezmenené.

Ak chcete prepočítať veľa majetku naraz, označte ho v zozname majetku a
zvoľte *Akcia → Vypočítať daňové odpisy*, alebo spustite
*Účtovníctvo → Konfigurácia → Vypočítať daňové odpisy* pre všetok majetok, ktorý
sleduje daňové odpisy. Aj tu zostanú uzavreté roky nezmenené.

## Daňový odpisový plán {#board}

Jeden riadok za každý daňový rok (pri českých mimoriadnych odpisoch za každý
mesiac): odpis roka, kumulatívne odpisy, daňová zostatková cena, poznámka o
spôsobe výpočtu a príznak *Podané*. Ďalšie dva stĺpce k nemu priraďujú účtovné
odpisy toho istého kalendárneho roka: **Účtovný odpis** a **Rozdiel (účtovný −
daňový)**. Rátajú sa v nich všetky účtovné odpisy roka, zaúčtované aj
plánované. Pri mesačnom pláne (§ 30a) sa účtovné sumy roka zobrazia raz, na
poslednom riadku roka.

Ako sa riadky počítajú:

| | Slovensko | Česká republika |
|---|---|---|
| Rovnomerné, prvý rok | ročný odpis × mesiace od mesiaca zaradenia ÷ 12 | celá sadzba pre prvý rok bez ohľadu na mesiac |
| Rovnomerné, ďalšie roky | vstupná cena ÷ doba odpisovania | sadzba pre ďalšie roky |
| Neuplatnená časť prvého roka | samostatný riadok v roku po uplynutí doby odpisovania | — |
| Zrýchlené | § 28: pomerný prvý rok, ďalšie roky zo zostatkovej ceny bez krátenia | § 32: vstupná cena ÷ k₁ (+ zvolených 10/15/20 % vstupnej ceny), potom 2 × ZC ÷ (k − n) |
| Mimoriadne | — | § 30a: 24 mesačných riadkov od mesiaca po zaradení, 60 % a potom 40 % |

Príklady:

- **SK**, stroj, skupina 1 (4 roky), vstupná cena 12 000 €, zaradený v
  októbri: 750 € (3/12), potom tri roky po 3 000 €, v piatom roku 2 250 €.
- **CZ**, stroj, skupina 2, rovnomerne, 300 000 Kč: 33 000 Kč (11 %), potom
  štyri roky po 66 750 Kč (22,25 %).

České odpisy sa zaokrúhľujú na celé koruny nahor a zostatková cena ďalšieho
roka je to, čo zostane po zaokrúhlených odpisoch. Posledný riadok každého
plánu sa upraví tak, aby sa plán presne rovnal odpisovanej cene; pri pláne
podľa § 30a sa aj dvanásty mesiac zastaví na 60 %.

## Technické zhodnotenie, prerušenie, vyradenie {#events}

Udalosti menia plán od určitého dátumu. Zadajte ich tlačidlami pod
**Udalosti životného cyklu** na záložke — *Technické zhodnotenie*,
*Prerušenie odpisovania*, *Vyradenie* — s dátumom (a sumou alebo počtom
rokov). Plán sa hneď prepočíta a udalosť sa uloží, takže každý ďalší výpočet
ju zopakuje.

- **Technické zhodnotenie**: od jeho roka plán pokračuje zo zvýšenej ceny —
  CZ rovnomerne sadzbou pre zvýšenú vstupnú cenu, SK rovnomerne zvýšenou
  cenou ÷ doba odpisovania, zrýchlene koeficientom pre zvýšenú zostatkovú
  cenu. Pole *Daňová vstupná cena* si ponechá pôvodnú cenu; zvýšenie nesie
  udalosť.
- **Prerušenie**: zvolené roky dostanú nulový riadok a zvyšok plánu sa
  posunie o rovnaký počet rokov.
- **Vyradenie**: plán sa ukončí. SK: v roku vyradenia sa neodpisuje, celá
  zvyšná daňová zostatková cena je výdavkom podľa § 19 ods. 3 písm. b); so
  začiarknutým *Odpis za celé mesiace v roku vyradenia* ročný odpis × celé
  mesiace ÷ 12 (mesiac vyradenia sa nezapočíta). CZ: polovica ročného odpisu,
  zaokrúhlená nahor — nič, ak bol majetok v tom istom roku zaradený.
  Vyradenie majetku priamo v
  registri túto udalosť zapíše samo (*Vyradiť* v OCA, *Vyradiť* / *Predať* v
  Enterprise).

Odmietne sa: udalosť s dátumom v poslednom uzavretom roku alebo pred ním,
technické zhodnotenie majetku odpisovaného podľa § 30a (odpisuje sa ako
samostatný majetok, § 30a odst. 3 — vytvorte nový majetok) a prerušenie
odpisovania majetku podľa § 30a.

## Majetok, ktorý sa už odpisuje {#migration}

Pri majetku, ktorého daňové odpisovanie začalo pred Odoo, kliknite na záložke
na **Doplniť (migrácia)**. Zadajte skupinu, metódu, daňovú vstupnú cenu,
dátum zaradenia a **Podané do roku** — posledný rok už uplatnený v podanom
priznaní. Voliteľne zadajte **Očakávanú daňovú ZC** z doterajšej evidencie:
ak sa vypočítaná zostatková cena na konci toho roka líši, nič sa nezapíše a
sprievodca vás na to upozorní. Kontrola prehrá udalosti, ktoré už sú pri
majetku zaznamenané, presne tak, ako ich prehrá plán.

Ak rozdiel spôsobuje technické zhodnotenie alebo prerušenie, ktoré ešte nie je
zaznamenané, zaznamenajte ho ako udalosť a spustite sprievodcu znova. Do roka,
ktorý je už podaný, udalosť zaznamenať nemožno; pri majetku s podanými rokmi
najprv spustite sprievodcu bez očakávanej ZC a s poľom *Podané do roku*
nastaveným na rok pred udalosťou, zaznamenajte udalosť a potom spustite
sprievodcu znova so skutočným podaným rokom a očakávanou ZC.

Sprievodca vypočíta celý zákonný plán, všetky roky do zadaného roka označí
ako podané a uzamkne metódu. Je to aj jediný povolený spôsob, ako opraviť
daňové parametre majetku, ktorého uzavreté roky sú zmrazené.

## Uzavretie daňového roka {#year-close}

Keď je daňové priznanie za rok podané, spustite *Účtovníctvo → Konfigurácia →
Uzavrieť rok daňových odpisov*, zvoľte rok (predvolený je minulý) a kliknite
na **Uzavrieť rok**. Na každom majetku spoločnosti so sledovaním daňových
odpisov sa všetky riadky plánu do zvoleného roka vrátane označia ako
**Podané** a metóda sa uzamkne.

Odvtedy:

- prepočet plánu podaný riadok nikdy nezmení — ak by ho zmenil zmenený
  parameter, výpočet sa odmietne;
- daňovú vstupnú cenu, dátum zaradenia, zvýšený odpis v 1. roku a limit
  vozidla nemožno meniť;
- podané riadky nemožno upravovať.

Uzavreté roky otvorí len sprievodca *Doplniť (migrácia)*.

## Ročné porovnanie a odložená daň {#reconciliation}

*Účtovníctvo → Výkazy → Rekonciliácia daňových odpisov*. Zvoľte obdobie
(predvolený je aktuálny kalendárny rok), skontrolujte **Sadzbu dane z príjmov
(%)** (predvolená 21) a kliknite na **Vypočítať**. Jeden riadok za každý
sledovaný majetok:

| Stĺpec | Obsah |
|---|---|
| Účtovný odpis | zaúčtované účtovné odpisy v období |
| Daňové odpisy | riadky daňového plánu začínajúce v období |
| Pripočet | účtovné − daňové, ak je kladné |
| Odpočet | daňové − účtovné, ak je kladné |
| Účtovná ZC, Daňová ZC (predvolene skryté) | obe zostatkové ceny na konci obdobia |
| Prechodný rozdiel | účtovná ZC − daňová ZC |
| Odložená daň | prechodný rozdiel × sadzba: kladná = záväzok, záporná = pohľadávka |
| Pripočítanie za vozidlo (SK § 17 ods. 34) (predvolene skryté) | pri slovenských automobiloch so začiarknutým *Uplatniť limit odpisu vozidla*: odpisy obdobia nad rovnomerným odpisom zo 48 000 € |

Riadky priznania sa riadia krajinou spoločnosti a zobrazia sa pri súčtoch aj v
hlavičkách PDF a XLSX: **Slovensko** r. 150 (pripočítateľná) a r. 250
(odpočítateľná položka), **Česká republika** ř. 50 (účetní odpisy převyšují
daňové) a ř. 150 (daňové převyšují účetní).

**Pripočítanie za vozidlo** úmyselne nie je v stĺpci pripočtu: § 17 ods. 34 ho
pripočíta k základu dane, len ak je základ nižší ako počet takých automobilov
× ročný rovnomerný odpis zo 48 000 €, a prenajímateľ automobilu prenajatého
bez dohodnutého práva kúpy ho nepripočíta nikdy. Či sa uplatní, rozhoduje sa
v priznaní; sprievodca ukazuje sumu.

V sprievodcovi:

- **Zaúčtovať odloženú daň (návrh)** vytvorí zápis v *Denníku odloženej dane*
  k poslednému dňu obdobia, ktorý dorovná zaúčtovaný zostatok účtu 481 **ku
  koncu obdobia** na vypočítanú odloženú daň, so súvzťažným účtom 592. Zápisy
  s dátumom po konci obdobia sa nezapočítajú. Zostane v stave návrh,
  ak nie je začiarknuté *Zaúčtovať odloženú daň ihneď*.
- **Export XLSX** a **Tlač PDF** dajú tabuľku ako tabuľkový súbor alebo PDF.

Slovenské daňové priznanie právnickej osoby v module
[module:l10n_sk_dppo](module:l10n_sk_dppo) si riadky 150 a 250 načíta z tohto
modulu samo (pripočítanie za vozidlo nie — to zadáte sami, ak sa uplatní).
Berie **súhrn za spoločnosť** — účtovné mínus daňové odpisy za
všetok majetok spolu —, kým sprievodca ukazuje pripočítateľné a odpočítateľné
sumy po jednotlivých majetkoch; ak časť majetku vychádza jedným a časť druhým
smerom, súčty sa líšia. Český modul priznania tieto sumy z tohto modulu nenačítava.

## Register a analýza {#register}

- **Register daňových odpisov** (*Účtovníctvo → Výkazy*): zvoľte rok a
  kliknite na **Tlač registra**. PDF podľa odpisových skupín: vstupná cena,
  počiatočná zostatková cena, odpis roka, oprávky, konečná zostatková cena,
  metóda a účtovný odpis s rozdielom, so súčtami za skupiny a celkovým
  súčtom. Majetok s mesačným plánom (§ 30a) je v ňom raz, so sčítanými
  mesiacmi roka. Hlavičky stĺpcov sú slovensky a anglicky.
- **Účtovné vs. daňové odpisy** (*Účtovníctvo → Výkazy*): kontingenčná
  tabuľka, graf a zoznam účtovných a daňových odpisov podľa majetku, roka a
  skupiny. *Účtovný odpis* počíta všetky účtovné odpisy roka, *Účtovný odpis
  (zaúčtovaný)* len zaúčtované; filter *Podané* ukáže zmrazené roky.

## V Community — register OCA {#oca}

[module:account_asset_tax_oca](module:account_asset_tax_oca) pripája daňový
plán k registru OCA `account_asset_management`:

- záložka **Daňové odpisy** na karte majetku; vstupná cena = obstarávacia
  hodnota majetku, dátum zaradenia = dátum začiatku odpisovania;
- blok **Predvolené nastavenia daňových odpisov** na profile majetku
  (*Sledovať daňové odpisy*, skupina, metóda, zvýšený odpis v 1. roku), ktorý
  sa prenesie na majetok vytvorený s týmto profilom, ak nemá vlastnú skupinu;
- vyradenie majetku sprievodcom *Vyradiť* v registri zapíše daňové vyradenie k
  dátumu vyradenia;
- účtovné odpisy = riadky odpisového plánu registra (zaúčtované = tie s
  účtovným zápisom);
- na karte majetku premenuje pole registra *Number of Years* na *Počet rokov*
  alebo *Počet období* podľa metódy času a vedľa neho zobrazí dĺžku obdobia.

Nadväzuje naň modul
[module:l10n_sk_account_asset_profile](module:l10n_sk_account_asset_profile)
s pripravenými slovenskými profilmi majetku.

## V Enterprise — Majetok Odoo {#ee}

[module:account_asset_tax_ee](module:account_asset_tax_ee) pripája daňový plán
k modulu *Majetok* v Odoo Enterprise:

- záložka **Daňové odpisy** za odpisovým plánom; vstupná cena = pôvodná
  hodnota majetku, dátum zaradenia = dátum prvého odpisu (inak dátum
  obstarania);
- predvolené daňové hodnoty na **šablóne majetku** sa prenesú na majetok
  vytvorený z nej, ak nemá vlastnú skupinu;
- vyradenie alebo predaj majetku zapíše daňové vyradenie k dátumu vyradenia;
- účtovné odpisy = odpisové zápisy majetku (zaúčtované = zaúčtované zápisy;
  zrušené sa ignorujú).

Nainštalovať možno len jeden most, pretože nainštalovaný môže byť len jeden z
oboch registrov majetku.

## Obmedzenia {#limitations}

- **Plány uzavreté pred verziou 19.0.1.10.0 si ponechajú pôvodné sumy.** Do
  tejto verzie plán zaokrúhľoval české odpisy na halier, každému slovenskému
  majetku dal v roku vyradenia pomerný odpis, slovenské automobily od
  48 000 € odpisoval len z tejto sumy a českému majetku vyradenému v prvom
  roku dal polovicu odpisu. Uzavreté roky sú zmrazené, takže prepočet takého
  majetku sa odmietne; ak boli uzavreté sumy nesprávne, opravte ich cez
  *Doplniť (migrácia)*. Neuzavreté roky opraví **Vypočítať daňový odpisový
  plán**.
- **Zaokrúhľovanie podľa § 30a** sa uplatní na každý mesačný odpis (nahor,
  dvanásty mesiac sa zastaví na 60 % v celých korunách). § 30a odst. 2
  nehovorí, či sa zaokrúhľuje po mesiacoch alebo za zdaňovacie obdobie; ročný
  súčet sa môže od zaokrúhlenia za rok líšiť o niekoľko korún.
- *Odpis za celé mesiace v roku vyradenia* sa voči majetku nekontroluje: či
  ide o majetok podľa § 26 ods. 6 a 7 alebo o majetok so zostatkovou cenou
  obmedzenou príjmami z predaja, aj začiatok druhého prípadu v roku 2016,
  overujete vy. Mesiac vyradenia sa nikdy nepočíta ako celý mesiac.
- **Pripočítanie za vozidlo** porovnáva odpisy s rovnomerným odpisom zo
  48 000 € rok po roku v poradí; po technickom zhodnotení, ktoré dobu
  odpisovania predĺži, sa roky navyše pripočítajú celé. Či sa pripočítanie
  vôbec uplatní, sa nevyhodnocuje.
- **Podmienky sa nekontrolujú**: Odoo nevie, či ste prvý odpisovateľ
  (§ 31 odst. 6), ani či ide o majetok, ktorý smie mať +15 % alebo +20 %
  (§ 31 odst. 2 a 3), alebo žiadne zvýšenie (§ 31 odst. 5), preto každý český
  majetok skupín 1–3 ponúka všetky tri zvýšenia; podmienky musíte overiť sami.
  Rovnako podmienky § 30a (bezemisné vozidlo, obstaranie 2024–2028, prvý
  odpisovateľ).
- Technické zhodnotenie dokončené v prvom roku sa spracuje ako udalosť, nie
  ako súčasť vstupnej ceny; ak to účtovník chce inak, zahrňte ho do *Daňovej
  vstupnej ceny*.
- Nie je pokrytý nehmotný majetok, odpisovanie mikrodaňovníka (§ 26 ods. 12),
  majetok odpisovaný podľa určenej doby alebo výkonu (SK § 26 ods. 6 a 7, CZ
  § 30 odst. 4 a 5), nižšie než maximálne české sadzby, povinné prerušenie
  (modul nevie, kedy sa majetok nepoužíval) ani hranice vstupnej ceny
  (1 700 € / 80 000 Kč) — či sa majetok daňovo odpisuje, rozhodujete vy.
- Porovnanie zahŕňa len odpisy. Rozdiel medzi účtovnou a daňovou zostatkovou
  cenou vyradeného majetku sa nepočíta.
- Zápis odloženej dane dorovnáva **celý zaúčtovaný zostatok** účtu 481 ku
  koncu obdobia, a to len na rozdiel z odpisov. Použite ho, len ak na tom
  účte nie je nič iné.
- Roky sú kalendárne: spoločnosť s hospodárskym rokom odlišným od
  kalendárneho dostane plány po kalendárnych rokoch.
- Hlavičky registra sú slovensko-anglické aj pre české spoločnosti.
