---
title: SK účtovná závierka — závierkové účty 701 / 702 / 710
summary: Uzavretie účtovných kníh na konci roka cez závierkové účty 710, 702 a 701 — a predovšetkým to, aby sa na tieto účty vôbec dalo účtovať.
verified: 19.0.1.0.2
---

## Na čo slúži {#purpose}

V podvojnom účtovníctve sa účtovné knihy na konci roka uzatvárajú cez tri
**závierkové účty**, ktoré štandardné Odoo nepozná:

| Účet | Názov | Úloha |
|---|---|---|
| 710 | Účet ziskov a strát | prevezme konečné stavy účtov triedy 5 (náklady) a triedy 6 (výnosy); jeho zostatok je výsledok hospodárenia |
| 702 | Konečný účet súvahový | prevezme konečné zostatky všetkých súvahových účtov (triedy 0 – 4) a výsledok hospodárenia z účtu 710 |
| 701 | Začiatočný účet súvahový | cez neho sa súvahové účty k prvému dňu nového roka znova otvoria |

Modul robí dve veci:

1. **Umožní účtovať na 701, 702 a 710.** Slovenská účtová osnova v Odoo ich
   dodáva ako podsúvahové účty a Odoo odmietne každý účtovný doklad, ktorý
   podsúvahový účet kombinuje s bežným. Uzávierkový zápis je presne taká
   kombinácia, takže bez tohto modulu by sa závierka nedala zaúčtovať vôbec
   (pozri [Zmena typu účtov](#retype)).
2. **Dodá šablónu uzávierky** pre modul OCA *Fiscal year closing*
   (`account_fiscal_year_closing`), ktorý z hlavnej knihy vytvorí tri
   uzávierkové a otváracie zápisy.

Nainštaluje sa sám, keď je nainštalovaná slovenská účtová osnova (`l10n_sk`)
aj `account_fiscal_year_closing`.

## Právny rámec {#legal}

- **Kedy sa knihy uzatvárajú a otvárajú.** Účtovná jednotka, ktorá je
  právnickou osobou, uzavrie účtovné knihy vždy k poslednému dňu účtovného
  obdobia —
  [§ 16 ods. 4 písm. b) zákona o účtovníctve](law:sk/2002/431#paragraf-16.odsek-4.pismeno-b)
  — a otvorí ich k prvému dňu účtovného obdobia —
  [§ 16 ods. 1 písm. b)](law:sk/2002/431#paragraf-16.odsek-1.pismeno-b).
  Ak uzavrie knihy k poslednému dňu účtovného obdobia, zostavuje účtovnú
  závierku ako riadnu —
  [§ 17 ods. 6](law:sk/2002/431#paragraf-17.odsek-6).
- **Ako sa knihy uzatvárajú.** Opatrenie MF SR č. 23054/2002-92, ktorým sa
  ustanovujú podrobnosti o postupoch účtovania a rámcovej účtovej osnove pre
  podnikateľov účtujúcich v sústave podvojného účtovníctva (oznámenie
  [č. 740/2002 Z. z.](law:sk/2002/740)), určuje v
  [§ 8 ods. 2](law:sk/2002/740#paragraf-8.odsek-2) poradie: najprv sa zistí
  výsledok hospodárenia pred zdanením a zaúčtuje sa daň z príjmov (písm. c),
  potom sa konečné stavy účtov nákladov a výnosov zaúčtujú na účet 710
  (písm. d), konečné zostatky účtov majetku, záväzkov a vlastného imania na
  účet 702 (písm. e) a nakoniec sa výsledok hospodárenia preúčtuje z účtu 710
  na účet 702 (písm. f).
- **Ako sa knihy otvárajú.** Začiatočné stavy súvahových účtov sa účtujú
  proti účtu 701 — [§ 7 ods. 2](law:sk/2002/740#paragraf-7.odsek-2). Výsledok
  hospodárenia bezprostredne predchádzajúceho účtovného obdobia sa pri
  otvorení účtov zaúčtuje na účet **431 – Výsledok hospodárenia v
  schvaľovaní** — [§ 7 ods. 3](law:sk/2002/740#paragraf-7.odsek-3) — a z
  neho sa podľa rozhodnutia príslušného orgánu preúčtuje ďalej —
  [§ 7 ods. 4](law:sk/2002/740#paragraf-7.odsek-4).
- **Verejná obchodná spoločnosť.** V v. o. s. (a vo vzťahu ku komplementárom
  komanditnej spoločnosti) sa výsledok na účet 702 nepreúčtuje, ale účtuje sa
  o nároku spoločníkov cez účet 596 —
  [§ 8 ods. 4](law:sk/2002/740#paragraf-8.odsek-4). Šablóna tento prípad
  nerieši.

## Zmena typu účtov {#retype}

Slovenská účtová osnova v Odoo dáva účtom 701000, 702000 a 710000 typ účtu
*Off-Balance Sheet* (v slovenskom preklade Odoo *Podsúvaha*). Odoo má pevné
pravidlo, že účtovný doklad s podsúvahovým účtom nesmie obsahovať žiadny iný
druh účtu. Uzavretie triedy 5 na 710 alebo súvahového účtu na 702 toto
pravidlo porušuje a Odoo zápis odmietne.

Modul preto týmto trom účtom zmení typ na *Equity* (v slovenskom preklade
Odoo „Vlastný imanie“):

- pri každej spoločnosti, ktorá už slovenskú osnovu má, jednorazovo pri
  inštalácii modulu — a len ak je účet ešte stále podsúvahový; typ, ktorý ste
  nastavili sami, ostane;
- pri spoločnostiach, ktoré slovenskú osnovu načítajú neskôr, cez šablónu
  účtovej osnovy.

Čo to pre vás znamená:

- Uzávierkové a otváracie zápisy, aj začiatočné stavy zaúčtované proti 701,
  sa dajú zaúčtovať.
- Štatutárnych výkazov sa zmena nedotkne: riadky priraďujú podľa **čísla**
  účtu, nie podľa typu, a triedu 7 vynechávajú úplne.
- Všeobecná súvaha Odoo teraz tieto tri účty ukazuje vo vlastnom imaní. Po
  spárovanom uzavretí a otvorení sú nulové, no v období s uzavretím a ešte
  bez otvorenia (alebo naopak) na nich zostatok vidno.
- Účet 711 – Začiatočný účet nákladov a výnosov sa nemení a ostáva
  podsúvahový; šablóna ho nepoužíva.

## Nastavenie {#setup}

Šablóna je v *Účtovníctvo → Konfigurácia → Fiscal Year Closing → Closing
templates* pod názvom **Účtovná závierka (SK) — 701 / 702 / 710** (obrazovky
samotného modulu uzávierky sú v angličtine). Má tri kroky:

| Krok | Kód | Zápis | Dátum |
|---|---|---|---|
| Uzavretie nákladov a výnosov (710) | SK_PL | trieda 5 a trieda 6 → 710000 | posledný deň roka |
| Uzavretie súvahových účtov (702) | SK_CLOSING | triedy 0 – 4 a 710 → 702000 | posledný deň roka |
| Otvorenie súvahových účtov (701) | SK_OPENING | opak kroku SK_CLOSING, proti 701000; výsledok na 431000 | dátum otvorenia |

Účty pohľadávok a záväzkov sa uzatvárajú **po partneroch** (*Un-reconciled*),
takže zostatok každého partnera sa prenesie do nového roka; ostatné účty sa
uzatvárajú zostatkom.

Pred prvou uzávierkou:

- **Založte denník pre uzávierku**, napríklad *UZAV* typu *Rôzne*, a nastavte
  ho ako *Journal* každého kroku — v šablóne alebo priamo v uzávierke. Bez
  neho modul použije denník s kódom `MISC` alebo prvý denník typu *Rôzne*.
- **Zaraďte tento denník medzi denníky koncoročnej uzávierky spoločnosti**
  (pole *Denníky koncoročnej uzávierky*, ktoré pridáva
  [module:l10n_cssk_core](module:l10n_cssk_core)). Štatutárna účtovná
  závierka aj daňové priznanie k dani z príjmov zápisy v týchto denníkoch
  vynechávajú a [module:l10n_cssk_account_financial_report](module:l10n_cssk_account_financial_report)
  to vie urobiť aj v účtovných zostavách. Inak sa uzávierkové zápisy počítajú
  ako bežné účtovné prípady a k poslednému dňu roka je každý uzavretý účet
  nulový. V tejto verzii pole nie je na žiadnom formulári; nastaví ho
  administrátor, napríklad importom do zoznamu spoločností.
- **Šablónu si prejdite s účtovníkom.** Do každej uzávierky sa skopíruje,
  takže úpravy v uzávierke platia len pre ňu.

## Uzavretie roka {#usage}

1. Zaúčtujte všetko za rok **vrátane dane z príjmov** (591 / 341), ktorú
   § 8 ods. 2 písm. c) opatrenia vyžaduje pred uzavretím účtov.
2. *Účtovníctvo → Účtovníctvo → Fiscal year closings*, potom *Nový*. Zadajte
   rok (pri hospodárskom roku cez dva kalendárne roky ten neskorší) a
   skontrolujte *From date*, *To date* a *Opening date*. Vyberte šablónu
   uzávierky; jej kroky sa skopírujú do *Moves configuration*, kde ešte môžete
   zmeniť denníky, dátumy aj priradenie účtov.
3. *Check draft moves* je predvolene zapnuté: výpočet sa zastaví, ak je v roku
   akýkoľvek nezaúčtovaný doklad.
4. Kliknite na **Calculate**. Tri zápisy vzniknú v stave *Návrh*. Skontrolujte
   ich cez **Show moves** / **Show move lines**. Ak niektorý nie je
   vyrovnaný, Odoo namiesto neho ukáže nevyrovnané riadky.
5. Kliknite na **Confirm and post moves**. *Cancel* uzávierkové zápisy opäť odstráni, *Recalculate* ich
   zmaže a vytvorí znova.

Čo modul pri slovenských spoločnostiach mení oproti všeobecnému modulu:

- **Na účte 702 je protizápis ku každému účtu.** Všeobecný modul by zaúčtoval
  jediný riadok s rozdielom všetkých zdrojových účtov — pri úplnej súvahe je
  nulový, takže 702 by sa v zápise vôbec neobjavil. Tu má každý uzatváraný
  účet svoj protiriadok na 702 (v prvom kroku na 710) a 702 je nulový vďaka
  bilančnej rovnosti.
- **Otvorenie ide cez 701.** Všeobecný modul otvára rok stornom uzávierkového zápisu, pri
  ktorom by na oboch stranách ostal účet 702. Modul protiúčet otváracieho
  zápisu zmení na 701000.
- **Výsledok hospodárenia sa otvorí na 431.** Storno by výsledok vrátilo aj
  na účet 710; modul tento riadok presunie na 431000 (pozri nižšie).

### Výsledok hospodárenia v otváracom zápise {#result-431}

Uzávierka prenesie výsledok hospodárenia z účtu 710 na 702. V otváracom
zápise ho modul zaúčtuje na **431000** *Výsledok hospodárenia v
schvaľovaní*, ako vyžaduje § 7 ods. 3 opatrenia: zisk na ťarchu 701 a v
prospech 431, stratu na ťarchu 431 a v prospech 701. Účet 710 sa v
otváracom zápise neobjaví. Ak spoločnosť účet 431000 nemá, riadok ostane na
710 a server to zapíše do logu; pred zaúčtovaním ho zmeňte na váš účet 431.

Otváracie zápisy zaúčtované vo verzii 19.0.1.0.1 alebo staršej otvorili
výsledok na účte 710. Ak taký máte, zaúčtujte k jeho dátumu otvorenia doklad,
ktorý zostatok preúčtuje z 710 na 431.

Rozhodnutie valného zhromaždenia (alebo iného príslušného orgánu) o výsledku
hospodárenia je samostatný doklad, ktorý sa účtuje neskôr: modul
[module:l10n_sk_account_move_template](module:l10n_sk_account_move_template)
naň má predkontácie *Preúčtovanie schváleného zisku (431 na 428)* a
*Preúčtovanie schválenej straty (431 na 429)*.

## Obmedzenia {#limitations}

- Uzávierka daň z príjmov nevypočíta ani nezaúčtuje.
- Verejnú obchodnú spoločnosť (§ 8 ods. 4 opatrenia, účet 596) šablóna
  nerieši.
- Zostatky sa berú zo zápisov s dátumom od *From date* do *To date*. Súvahový
  účet, ktorého začiatočný stav je zaúčtovaný pred začiatkom roka (napríklad
  pri migrácii dát so starším dátumom), sa uzavrie len o pohyb roka. Každý
  rok otvárajte zápisom k jeho prvému dňu.
- Uzávierkové a otváracie riadky na účtoch pohľadávok a záväzkov sa
  nespárujú s faktúrami, ktoré prenášajú. Po partneroch sa vzájomne rušia, no
  objavujú sa v zoznamoch otvorených položiek a vo vekovej štruktúre.
- Protizápisy po účtoch, otvorenie cez 701 a výsledok na 431 platia len pre slovenské
  spoločnosti (šablóna osnovy `sk`); ostatné spoločnosti majú všeobecné
  správanie modulu.
- Postupy pri závierke sa medzi účtovníkmi líšia, najmä v tom, ako sa
  výsledok hospodárenia dostane na 702. Šablóna je východisko a pred
  prvou ostrou závierkou ju má odsúhlasiť váš účtovník.
