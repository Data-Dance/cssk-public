---
title: SK prepočet cudzích mien ku dňu závierky (kurzové rozdiely)
summary: Prepočíta zostatky v cudzej mene referenčným kurzom ku dňu závierky a kurzové rozdiely zaúčtuje na 563 a 663 — sprievodcom OCA v edícii Community a korekčným záznamom Odoo v edícii Enterprise.
verified: 19.0.1.0.1
---

## Na čo slúži {#purpose}

Ku dňu, ku ktorému sa zostavuje účtovná závierka, sa otvorené pohľadávky a
záväzky v cudzej mene, devízové účty a valutová pokladnica prepočítajú
referenčným kurzom tohto dňa; rozdiel oproti účtovnej hodnote je
nerealizovaný kurzový rozdiel. Slovenská osnova ho účtuje na **563**
*Kurzové straty* a **663** *Kurzové zisky*.

Odoo samo účtuje kurzové rozdiely len pri spárovaní platby (na tie isté
účty 563 / 663, ako ich nastavuje slovenská osnova Odoo). Prepočet ku dňu
závierky potrebuje ďalší nástroj a ktorý to je, závisí od edície:

| Edícia | Nástroj | Modul |
|---|---|---|
| Community | sprievodca *Precenenie meny* OCA (`account_multicurrency_revaluation`) | **tento modul**, [module:l10n_sk_currency_revaluation](module:l10n_sk_currency_revaluation) — pozri [Community](#community) |
| Enterprise | výkaz *Nerealizované kurzové zisky/straty* Odoo a jeho korekčný záznam | [module:l10n_sk_currency_revaluation_ee](module:l10n_sk_currency_revaluation_ee) — pozri [Enterprise](#enterprise) |

Oba sa nainštalujú samy, keď je prítomný ich nástroj a slovenská osnova
(`l10n_sk`). Nastavia účty a denník; samotný prepočet urobí nástroj.

## Právny rámec {#legal}

- Majetok a záväzky vyjadrené v cudzej mene sa prepočítavajú na eurá
  **referenčným výmenným kurzom** určeným a vyhláseným Európskou centrálnou
  bankou alebo Národnou bankou Slovenska — pri účtovnom prípade v deň
  predchádzajúci dňu jeho uskutočnenia, pri závierke **v deň, ku ktorému sa
  zostavuje účtovná závierka**
  ([§ 24 ods. 2 zákona o účtovníctve](law:sk/2002/431#paragraf-24.odsek-2)).
- Podľa [§ 24 ods. 4 opatrenia 740/2002](law:sk/2002/740#paragraf-24.odsek-4)
  sa kurzový rozdiel z tohto ocenenia účtuje na ťarchu účtu 563 alebo v
  prospech účtu 663, a to aj pri položkách na účtoch 383 a 385.
- Niektoré položky si ponechávajú kurz pôvodného účtovného prípadu a
  **neprepočítavajú sa**: poskytnuté a prijaté preddavky na účtoch 314, 324
  a 475, obdobné prípady na účte 335, náklady a výnosy budúcich období na
  účtoch 381 a 384 a nevyfaktúrované dodávky na účte 326 do ich
  vyfaktúrovania ([§ 24 ods. 3](law:sk/2002/740#paragraf-24.odsek-3)).

## Community: sprievodca OCA {#community}

### Čo modul nastaví {#setup}

Pri každej spoločnosti so slovenskou osnovou — pri načítaní osnovy alebo
pri inštalácii, ak ju spoločnosť už má:

| Nastavenie | Hodnota |
|---|---|
| Účet kurzových strát | 563000, ak je prázdny |
| Účet kurzových ziskov | 663000, ak je prázdny |
| Predvolený denník kurzových ziskov a strát | denník **KURZ** *Kurzové rozdiely* typu *Rôzne*, ktorý sa založí, ak spoločnosť denník s týmto kódom nemá |

Nájdete ich v *Účtovníctvo → Konfigurácia → Nastavenia*, oddiel *Precenenie
vo viacerých menách*, spolu s voľbou *Automaticky zaúčtovať vytvorené
zápisy* (vypnutá: zápisy vzniknú ako návrh).

### Pred prvým prepočtom {#before}

1. **Prideľte si prístup.** Ponuky OCA vidia len členovia skupiny
   *Zaúčtovanie dodatočných rezervných zápisov*, ktorú predvolene nemá
   nikto. Pridajte ju používateľovi v *Nastavenia → Používatelia*, oddiel
   *Extra Rights*, ktorý sa zobrazí v režime vývojára.
2. **Vyberte účty na prepočet.** Zaškrtnite *Povoliť precenenie meny* pri
   každom účte, ktorého zostatok v cudzej mene sa má prepočítať: devízové
   bankové účty a valutové pokladnice (22x, 21x), pohľadávky (311), záväzky
   (321) a ďalšie, ktoré určí váš účtovník. Pri účtoch podľa § 24 ods. 3 —
   314, 324, 475, 381, 384, 326 — voľbu nechajte **vypnutú**.
3. **Načítajte kurzy.** V Odoo musí byť referenčný kurz ECB práve ku dňu
   závierky.

### Vykonanie prepočtu {#usage}

*Účtovníctvo → Účtovníctvo → Uzávierka → Precenenie meny*:

1. Zadajte *Dátum precenenia* (deň, ku ktorému sa zostavuje závierka).
   **Pole *Začiatok obdobia precenenia* vymažte** alebo ho nastavte
   dostatočne skoro: prepočítajú sa len účtovné položky s dátumom od tohto
   dňa, a predvolenou hodnotou je prvý deň aktuálneho mesiaca — ku koncu
   roka by tak vypadli všetky otvorené položky z predchádzajúcich mesiacov.
   Skontrolujte denník a vzor *Popis zápisu*.
2. Skontrolujte zoznam účtov: na začiatku obsahuje všetky účty s voľbou
   *Povoliť precenenie meny* a pre tento prepočet môžete účty ubrať alebo
   pridať.
3. Kliknite na **Potvrdiť**. Pri účtoch pohľadávok a záväzkov vznikne jeden
   zápis za účet, menu a partnera, pri ostatných účtoch jeden za účet a
   menu. Straty idú na 563000, zisky na 663000.

*Výkaz precenenia meny* v *Účtovníctvo → Výkazy → Uzávierkové zápisy*
ukazuje nerealizované kurzové rozdiely. *Storno precenenia meny* v tej istej
ponuke *Uzávierka* stornuje zápisy prepočtu zo zvoleného obdobia k dátumu,
ktorý zadáte — či na začiatku ďalšieho obdobia stornovať, rozhoduje váš
účtovník.

## Enterprise: korekčný záznam {#enterprise}

[module:l10n_sk_currency_revaluation_ee](module:l10n_sk_currency_revaluation_ee)
sa nainštaluje sám s účtovníctvom Odoo Enterprise a pri každej slovenskej
spoločnosti nastaví:

| Nastavenie korekčného záznamu | Hodnota |
|---|---|
| Účet rezervy na náklady | 563000 |
| Účet rezervy na výnosy | 663000 |
| Denník | KURZ *Kurzové rozdiely*, založený, ak chýba, keď spoločnosť ešte nemá denník na precenenie |

Pri inštalácii sa oba účty **prepíšu**, nech bolo nastavené čokoľvek.
Slovenský preklad Odoo je zavádzajúci: s rezervami tieto účty nesúvisia,
ide o protiúčty pre stratu a pre zisk.

Prepočet: *Účtovníctvo → Kontrola → Regulatívne požiadavky → Kurzové
rozdiely* (prostredná ponuka je nesprávny preklad *Regularization Entries*)
otvorí výkaz *Nerealizované kurzové zisky/straty*. Nastavte jeho dátum na
deň závierky a kliknite na **Korekčný záznam**. Sprievodca navrhne zápis:
každý účet v cudzej mene sa upraví a protizápis ide na 563000 pri strate
alebo na 663000 pri zisku. *Dátum storna* je povinný: Enterprise k nemu
vždy zaúčtuje storno korekcie, zvyčajne k prvému dňu ďalšieho obdobia.

## Obmedzenia {#limitations}

- Moduly nastavujú len účty a denník. V edícii Community sa nič
  neprepočíta, kým účty nemajú voľbu *Povoliť precenenie meny*, a ponuky
  zostanú skryté, kým používateľ nedostane uvedenú skupinu.
- *Začiatok obdobia precenenia* má predvolenú hodnotu prvý deň aktuálneho
  mesiaca a bez upozornenia obmedzí prepočet na položky od tohto dňa.
- Výkaz Enterprise navrhne všetky účty v cudzej mene; nevie, ktoré položky
  vylučuje § 24 ods. 3. Tieto účty vo výkaze vylúčte (presunú sa pod
  *Vylúčené účty*; Odoo si voľbu pamätá pre každý účet a menu) ešte pred
  vytvorením záznamu.
- Enterprise korekciu k dátumu storna vždy stornuje; ponechať ju nemožno.
- Inštalácia založí denník KURZ v každej slovenskej spoločnosti, ktorá nemá
  nastavený denník na precenenie, bez ohľadu na to, či cudzie meny používa.
