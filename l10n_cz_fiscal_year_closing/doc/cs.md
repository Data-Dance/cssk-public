---
title: CZ účetní závěrka — závěrkové účty 701 / 702 / 710
summary: Uzavře české účetní knihy přes závěrkové účty 710, 702 a 701, otevře nový rok s výsledkem hospodaření na účtu 431 a umožní na tyto účty vůbec účtovat.
verified: 19.0.2.0.0
---

## K čemu slouží {#purpose}

V podvojném účetnictví se účetní knihy uzavírají a otevírají přes závěrkové
účty účtové třídy 7:

| Účet | Název | Úloha |
|---|---|---|
| 701 | Počáteční účet rozvažný | protiúčet počátečních zůstatků rozvahových účtů |
| 702 | Konečný účet rozvažný | protiúčet konečných zůstatků rozvahových účtů |
| 710 | Účet zisků a ztrát | převezme konečné zůstatky nákladových a výnosových účtů |

Česká účtová osnova v Odoo (`l10n_cz`) dodává tyto tři účty jako
podrozvahové a Odoo odmítne každý účetní doklad, který podrozvahový účet
kombinuje s běžným. Uzavření třídy 5 nebo 6 na účet 710, uzavření
rozvahových účtů na účet 702 i zaúčtování počátečních stavů proti účtu 701
jsou přesně takové kombinace, takže v dodaném stavu **nejde zaúčtovat ani
jedno z nich** — a to nejen na konci roku, ale už při zadání počátečních
stavů při přechodu na Odoo.

Modul dělá dvě věci:

1. **Umožní na účty 701, 702 a 710 účtovat** (viz [Co se změní](#retype)).
2. **Dodává šablonu uzávěrky** pro modul OCA *Fiscal year closing*
   (`account_fiscal_year_closing`), který z hlavní knihy vytvoří uzávěrkové
   a otevírací zápisy, a seznam toho, na co se před uzavřením roku podívat.

Nainstaluje se sám, jakmile jsou nainstalovány česká účtová osnova
(`l10n_cz`) i `account_fiscal_year_closing`.

## Právní rámec {#legal}

- Účetní jednotka uzavírá účetní knihy k poslednímu dni účetního období a
  otevírá je k prvnímu dni účetního období —
  [§ 17 odst. 2 písm. b) a odst. 1 písm. b) zákona o účetnictví](law:cz/1991/563).
- Počáteční zůstatky rozvahových účtů musí navazovat na konečné zůstatky,
  jimiž se bezprostředně předcházející období uzavřelo —
  [§ 19 odst. 4 zákona o účetnictví](law:cz/1991/563).
- Směrná účtová osnova pro podnikatele řadí závěrkové účty do účtové třídy 7
  *Závěrkové a podrozvahové účty*: skupina 70 *Účty rozvažné* a skupina 71
  *Účet zisků a ztrát* —
  [příloha č. 4 vyhlášky č. 500/2002 Sb.](law:cz/2002/500). Jsou to účty
  závěrkové, ne podrozvahové (ty tvoří skupiny 75 až 79).

- **Jak se knihy uzavírají.** Český účetní standard č. 002 *Otevírání
  a uzavírání účetních knih* (pro účetní jednotky účtující podle vyhlášky
  č. 500/2002 Sb.): konečné stavy účtů nákladů a výnosů se převedou na účet
  účtové skupiny 71 *Účet zisků a ztrát* (bod 2.2.2), konečné stavy účtů
  aktiv a pasiv a zůstatek účtu zisků a ztrát na konečný účet rozvažný
  účtové skupiny 70 (bod 2.2.3).
- **Jak se knihy otevírají.** Počáteční zůstatky se účtují proti počátečnímu
  účtu rozvažnému (bod 2.1.2). Zisk nebo ztráta zaúčtované na konečný účet
  rozvažný se při otevírání zaúčtují na účet **účtové skupiny 43** *Výsledek
  hospodaření* proti počátečnímu účtu rozvažnému (bod 2.1.3) a účet opustí
  po schválení rozdělení zisku nebo úhrady ztráty příslušným orgánem
  (bod 2.1.5).
- Standard jmenuje jen účtové **skupiny**. 701, 702, 710 a 431 jsou účty
  české osnovy dodávané s Odoo a běžné praxe.
- **Veřejná obchodní a komanditní společnost.** U veřejné obchodní
  společnosti a u komplementářů komanditní společnosti se výsledek
  hospodaření při uzavírání knih rozděluje mezi společníky (body 2.2.4
  a 2.2.5). Šablona tento případ neřeší.

## Co se změní {#retype}

Modul změní typ účtu u 701000, 702000 a 710000 z *Off-Balance Sheet* (v
českém překladu Odoo *Podrozvahový*) na *Equity* (v českém překladu Odoo
„Základní kapitál“):

- u každé společnosti, která už českou osnovu má, jednorázově při instalaci
  modulu — a jen tam, kde je účet stále podrozvahový; typ, který jste
  nastavili sami, zůstane;
- u společností, které českou osnovu načtou později, přes šablonu účtové
  osnovy.

Co to pro vás znamená:

- Uzávěrkové a otevírací zápisy i počáteční stavy proti účtu 701 jde
  zaúčtovat.
- Českých statutárních výkazů se změna nedotkne: řádky přiřazují podle
  **čísla** účtu, ne podle typu účtu.
- Obecná rozvaha Odoo teď tyto tři účty ukazuje ve vlastním kapitálu. Po
  spárovaném uzavření a otevření jsou nulové, ale v období s uzavřením a
  dosud bez otevření (nebo naopak) na nich zůstatek vidět je.

## Šablona uzávěrky {#template}

Šablona *Účetní závěrka (CZ) — 701 / 702 / 710* se nabízí společnostem
s českou účtovou osnovou. Má tři kroky:

| Krok | Kód | Co dělá | Datum |
|---|---|---|---|
| Uzavření nákladů a výnosů (710) | CZ_PL | třída 5 a třída 6 → 710000 | poslední den roku |
| Uzavření rozvahových účtů (702) | CZ_CLOSING | třídy 0–4 a 710 → 702000 | poslední den roku |
| Otevření rozvahových účtů (701) | CZ_OPENING | opak CZ_CLOSING, proti 701000; výsledek hospodaření na 431000 | den otevření |

Účty pohledávek a závazků se uzavírají **po partnerech** (*Un-reconciled*),
takže se zůstatek každého partnera přenese do nového roku; ostatní účty se
uzavírají zůstatkem.

Před první uzávěrkou:

- **Založte pro uzávěrku deník**, například *Uzávěrka roku* typu *Ostatní*,
  a nastavte ho jako *Journal* každého kroku, v šabloně nebo přímo
  v uzávěrce.
  Jinak se použije deník s kódem `MISC`, případně první deník typu Ostatní.
- **Uveďte tento deník v poli *Deníky závěrky roku*** (*Účetnictví →
  Konfigurace → Nastavení*, blok *Česká / slovenská lokalizace*, dodává
  [module:l10n_cssk_core](module:l10n_cssk_core)). Zákonné výkazy, přiznání
  k dani z příjmů a účetní knihy pak jeho zápisy vynechají; jinak je
  k poslednímu dni roku každý uzavřený účet nulový.
- **Projděte šablonu s účetní.** Do každé uzávěrky se kopíruje, takže změny
  provedené v uzávěrce platí jen pro ni.

## Uzavření roku {#usage}

Obrazovky modulu OCA nemají český překlad, proto jsou názvy polí a tlačítek
uvedeny anglicky, jak je uvidíte.

1. Zaúčtujte vše za daný rok včetně daně z příjmů (591 / 341).
2. *Účetnictví → Účetnictví → Fiscal year closings*, pak *Nový*. Zadejte
   rok (u hospodářského roku přes dva kalendářní roky ten pozdější)
   a zkontrolujte *From date*, *To date* a *Opening date*. Vyberte šablonu
   uzávěrky; její kroky se zkopírují do *Moves configuration*, kde lze ještě
   změnit deníky, data i mapování.
3. Přečtěte si rámeček **Před uzavřením roku** nahoře na formuláři (viz
   [níže](#pre-close)).
4. *Check draft moves* je ve výchozím stavu zapnuté: výpočet se zastaví,
   pokud je v roce nějaký nezaúčtovaný záznam.
5. Klikněte na **Calculate**. Tři zápisy se vytvoří jako koncepty;
   prohlédněte si je přes **Show moves** / **Show move lines**.
6. Klikněte na **Confirm and post moves**. *Cancel* uzávěrkové zápisy opět
   odstraní, *Recalculate* je smaže a vytvoří znovu.

Co modul u českých společností mění oproti obecnému chování:

- **Na účtu 702 je protizápis ke každému účtu.** Obecný postup by zaúčtoval
  jediný řádek se saldem všech zdrojů, které je u úplné rozvahy nulové,
  takže by se účet 702 v zápisu vůbec neobjevil. Zde má každý uzavíraný účet
  svůj zrcadlový řádek na účtu 702 (v prvním kroku na účtu 710).
- **Otevírá se přes účet 701.** Obecný postup otevírá rok stornem
  uzávěrkového zápisu, takže by na obou stranách zůstal účet 702. Modul
  protiúčet otevíracího zápisu převede na 701000.
- **Výsledek hospodaření se otevírá na účtu 431.** Storno by výsledek
  vrátilo na účet 710; modul tento řádek převede na 431000 *Výsledek
  hospodaření ve schvalovacím řízení*: zisk MD 701 / D 431, ztráta MD 431 /
  D 701. Pokud společnost účet 431000 nemá, řádek zůstane na účtu 710
  a záznam o tom je v logu serveru; před zaúčtováním ho změňte na svůj účet
  skupiny 43.

Rozhodnutí o výsledku hospodaření (431 na 428, 429, fondy nebo společníky)
je samostatný zápis, účtovaný až po rozhodnutí valné hromady nebo jiného
příslušného orgánu.

## Před uzavřením roku {#pre-close}

Formulář uzávěrky vypíše, na co se nejdřív podívat: nezaúčtované záznamy,
mezery v číslování dokladů, zůstatky na účtech 431 (o loňském výsledku se
ještě nerozhodlo), 395 a 261, nepotvrzené výplatní pásky, nezaúčtované
odpisy a nepodané přiznání k DPH za poslední období. Seznam je jen
upozornění a zobrazuje se společnostem, jejichž fiskální zemí je Česká
republika.

## Omezení {#limitations}

- Uzávěrka nepočítá ani neúčtuje daň z příjmů.
- Šablona neřeší veřejné obchodní a komanditní společnosti (ČÚS 002 body
  2.2.4 a 2.2.5) ani individuální podnikatele vedoucí účetnictví (výsledek
  jde na skupinu 49, bod 2.1.5 písm. b)).
- Rozdíly ze změn způsobů oceňování, které se účtují v prvním měsíci nového
  období na skupinu 42 (bod 2.1.4), se negenerují.
- Zůstatky se berou ze zápisů s datem mezi *From date* a *To date*.
  Rozvahový účet, jehož počáteční stav byl zaúčtován před začátkem roku
  (například migrací dat s dřívějším datem), se uzavře jen o pohyb roku.
  Každý rok otevírejte zápisem k jeho prvnímu dni.
- Uzávěrkové a otevírací řádky na účtech pohledávek a závazků se nepárují
  s fakturami, které přenášejí. Po partnerech dávají nulu, ale objeví se
  v seznamech otevřených položek a ve věkové struktuře.
- Přetypované účty, zrcadlení po účtech, otevření přes 701 a výsledek na
  431 se týkají jen společností s českou osnovou (`cz`). Podrozvahové účty,
  které si sami založíte ve skupinách 75 až 79, svůj typ ponechají.
- Instalace nebo aktualizace na tuto verzi nainstaluje modul OCA
  `account_fiscal_year_closing`, který šablona potřebuje.
- Zvyklosti při uzávěrce se mezi účetními liší. Šablona je výchozí bod
  a před první ostrou uzávěrkou by ji měla odsouhlasit vaše účetní.
