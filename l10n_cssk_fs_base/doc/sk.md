---
title: Účtovné výkazy CZ/SK
summary: Slovenské a české účtovné výkazy zostavené z účtovníctva riadok po riadku, s porovnateľným obdobím, ručne zadanými údajmi tam, kde ich účtovníctvo nedá, kontrolou, či sa každý účet dostal do niektorého riadku, a evidenciou podania.
verified: 19.0.1.10.3
---

## Na čo slúži {#purpose}

Účtovná závierka na Slovensku aj v Česku sa zostavuje na predpísaných
tlačivách: každý riadok má určený názov aj obsah. Tento modul je spoločný
mechanizmus, ktorý ich vypĺňa z účtovných zápisov v Odoo. Funguje rovnako v
edícii Community aj Enterprise a nepoužíva účtovné výkazy Odoo Enterprise.

Sám žiadny výkaz neobsahuje. Riadky, priradenie účtov a formát exportu
každého tlačiva prináša národný modul:

| Krajina | Modul | Výkazy |
|---|---|---|
| Slovensko | [module:l10n_sk_fs](module:l10n_sk_fs) | Účtovná závierka Úč POD (súvaha a výkaz ziskov a strát v jednom dokumente), prehľad peňažných tokov, prehľad zmien vlastného imania, poznámky |
| Slovensko | [module:l10n_sk_single_entry_closing](module:l10n_sk_single_entry_closing) | Účtovná závierka v jednoduchom účtovníctve (Úč FO) |
| Česko | [module:l10n_cz_fs](module:l10n_cz_fs) | Rozvaha, výkaz zisku a ztráty, přehled o peněžních tocích, přehled o změnách vlastního kapitálu |

Táto stránka opisuje, čo majú všetky spoločné: vytvorenie výkazu, výpočet,
kontrolu, opravy a evidenciu podania. Samotné tlačivá a právny rámec opisujú
stránky národných modulov.

## Nastavenie {#setup}

1. **Nainštalujte národný modul.** Bez neho sú ponuky nižšie prázdne.
2. **Skontrolujte priradenie účtov.** Riadky čítajú účty podľa čísla v
   národnej účtovej osnove. Ak vaša osnova používa čísla, ktoré tlačivo
   nepozná (napríklad analytický účet s neštandardným číslom), priraďte ich v
   *Účtovníctvo → Konfigurácia → CZ/SK lokalizácia → Mapovanie účtov do
   výkazov*. Ktoré účty to potrebujú, ukáže
   [kontrola nepriradených účtov](#checks).
3. **Verzie výkazov** sú v *Účtovníctvo → Konfigurácia → CZ/SK lokalizácia →
   Verzie účtovných výkazov* (pre administrátorov účtovníctva). Každá verzia je
   jedno vydanie tlačiva: jeho riadky, obdobie, na ktoré sa vzťahuje, XML
   šablóna a — ak ho správca dane zverejňuje — XSD. Inštalujú ich národné
   moduly, bežne ich neupravujete. Archivovanú verziu možno stále vybrať pre
   obdobie, na ktoré sa vzťahuje.

## Vytvorenie a výpočet výkazu {#usage}

*Účtovníctvo → Výkazy → Zákonné výkazy* a potom druh výkazu: **Súvaha**,
**Výkaz ziskov a strát**, **Prehľad peňažných tokov** alebo **Prehľad zmien
vlastného imania**. Kliknite na *Nový*.

- **Obdobie.** *Dátum od* a *Dátum do* sa predvyplnia posledným skončeným
  účtovným obdobím spoločnosti, takže aj spoločnosť s hospodárskym rokom
  dostane správne dátumy.
- **Verzia.** Doplní sa najnovšia verzia daného výkazu platná pre obdobie v
  krajine, v ktorej je spoločnosť daňovo registrovaná. Ak žiadna verzia
  obdobie nepokrýva, pole zostane prázdne a výkaz nemožno uložiť.
- **Druh výkazu** ukazuje, o aký dokument ide. Slovenská Úč POD je jeden
  dokument so súvahou aj výkazom ziskov a strát, preto sa zobrazuje ako
  *Účtovná závierka (súvaha + výkaz ziskov a strát)* a je v zozname pod oboma
  ponukami; každá ponuka ukáže len svoju časť riadkov, z iného miesta sa
  zobrazia všetky.

Kliknite na **Vypočítať**. Modul načíta zaúčtované zápisy spoločnosti:

- riadky súvahy berú **kumulatívny zostatok ku dňu Dátum do**;
- riadky výkazu ziskov a strát, prehľadu peňažných tokov a prehľadu zmien
  vlastného imania berú **pohyb za obdobie**; začiatočné a konečné riadky
  dvoch posledných berú zostatok deň pred začiatkom obdobia a ku koncu obdobia;
- stĺpec **minulého obdobia** sa vypočíta rovnako za tie isté dni o rok skôr;
- zápisy v denníkoch koncoročnej uzávierky spoločnosti sa vynechajú, lebo
  výkaz zobrazuje činnosť obdobia, nie uzatváranie a otváranie kníh (ako sa
  tieto denníky nastavujú, pozri [Obmedzenia](#limitations)).

Výkaz prejde do stavu **Náhľad**. Po každej zmene v účtovníctve ho vypočítajte
znova; prepočítať ho možno len v stave *Návrh* a *Náhľad*.

## Kontrola údajov {#review}

Karta *Riadky* zobrazuje tlačivo ako strom: každý súčtový riadok je súčtom
riadkov pod ním (hore *Zbaliť všetko* / *Rozbaliť všetko*). Stĺpce sú
**Bežné obdobie** a **Minulé obdobie**.

- **Rozpad na doklady.** Lupa pri riadku počítanom z účtov otvorí *Zdrojové
  doklady*: účtovné zápisy, z ktorých sa suma skladá, zoskupené podľa účtu a
  potom podľa dokladu — presne tie, z ktorých sa sčítala.
- **Stĺpec ✓** označuje riadky, ktorých zápisy dávajú spolu sumu riadku.
  Riadok, ktorý nesúhlasí (zaokrúhlenie, ručne zadaná suma), označený nie je.
- Pri tlačivách v troch stĺpcoch — slovenská súvaha a aktíva českej rozvahy —
  má každý riadok aj **Brutto** a **Korekciu** (oprávky a opravné položky) a
  zobrazená suma je netto. Obrazovka ukazuje len netto; všetky tri stĺpce sú v
  [exporte do XLSX](#xlsx) a v exportovanom XML.

## Ručné zadanie sumy {#overrides}

Niektoré údaje účtovníctvo dať nevie. Kliknite na ceruzku pri sume, zadajte
hodnotu a stlačte **Vypočítať**, aby sa prepočítali súčty nad ňou.

- Suma **zostane zachovaná pri každom prepočte** a je označená ako zadaná
  ručne. Šípka späť vráti riadok na vypočítanú hodnotu pri ďalšom výpočte.
- **Súčtové riadky prepísať nemožno** — prepíšte riadky, z ktorých sa skladajú.
- **Minulé obdobie** má vlastný prepis. Použite ho v prvom roku vedenia
  účtovníctva v Odoo, keď je minuloročné účtovníctvo v inom systéme, aby
  výkaz ukázal minuloročné údaje tak, ako boli podané.
- Zmena sumy vráti výkaz do stavu **Návrh**, takže kým ďalší výpočet nezosúladí
  súčty, nemožno ho exportovať.

## Kontroly {#checks}

Dve tlačidlá v hlavičke upozornia na to, čo aj vyrovnaný výkaz môže skrývať:

| Tlačidlo | Význam | Čo urobiť |
|---|---|---|
| **Nesúladné riadky** (červené) | Riadky, ktorých zápisy nedávajú spolu sumu riadku. Ak také nie sú, zelené **Riadky súhlasia**. | Pri ručne zadaných sumách je to bežné; inak otvorte zdrojové doklady riadku. |
| **Nepriradené účty** (oranžové) | Účty so zostatkom ku dňu Dátum do, ktoré si žiadny riadok výkazu nenárokuje. Ich peniaze sú v účtovníctve, ale nie vo výkaze — a výkaz napriek tomu sedí aj je vyrovnaný. Zobrazí sa 50 najväčších zostatkov; sumy pod 1 sa ignorujú. | Priraďte účet k číslu, ktoré tlačivo očakáva, v *Mapovanie účtov do výkazov* a potom znova *Vypočítať*. Trieda 7 (závierkové a podsúvahové účty) a účty typu podsúvahový sa nezobrazujú nikdy. Niektoré účty sa zobrazujú zámerne — ktoré, uvádzajú stránky národných modulov. |

Národný modul môže pridať ďalšie kontroly, ktoré sa spúšťajú pri exporte
(napríklad slovenská Úč POD kontroluje kontrolné pravidlá tlačiva).

## Export a evidencia podania {#filing}

1. **Exportovať XML** vytvorí súbor vo formáte verzie výkazu. Odmietne sa, kým
   je výkaz v stave Návrh, a tiež ak spoločnosť nemá vyplnené ani DIČ (pole
   *DIČ*), ani *Tax ID*: identifikáciou predkladateľa je DIČ, takže účtovná
   jednotka, ktorá nie je platiteľom DPH, exportuje so samotným DIČ. Súbor sa overí voči XSD
   verzie; verzia, pri ktorej je uvedené, že správca dane pre tlačivo XSD
   nezverejňuje, sa exportuje bez overenia. Súbor sa priloží k výkazu, ktorý
   prejde do stavu **Exportované**.
2. Súbor podajte na portáli finančnej správy sami.
3. **Označiť ako podané** to zaznamená: podaná kópia sa uchová a výkaz sa
   uzamkne — nemožno ho prepočítať, znova exportovať ani vymazať.
4. **Podať** otvorí záznam o doručení podania. Ak je nainštalovaný len ručný
   kanál, zaznamená, kto podanie na portáli podal, a uchová potvrdenia, ktoré
   portál vrátil.

**Opravná závierka** na podanom výkaze ho skopíruje do nového návrhu
označeného ako opravný a prepojeného s pôvodným. Opravte účtovníctvo, výkaz
vypočítajte a podajte ako ktorýkoľvek iný; rozdielové riadky nemá, opravná
závierka uvádza celé obdobie znova.

**Vrátiť do návrhu** znova otvorí exportovaný alebo podaný výkaz. Smú to len
administrátori účtovníctva; podaná kópia zostane priložená a uvedená v
histórii podaní.

Výkaz prenesený z predchádzajúceho systému ako historické podanie sa zobrazí
v stave **Historické podanie** a nemožno ho vypočítať, exportovať ani podať. Ak
sa podané a vypočítané údaje porovnávali, tlačidlo **Porovnania** vedie k
porovnaniam tohto výkazu.

## Export do Excelu {#xlsx}

S doplnkom [module:l10n_cssk_fs_xlsx](module:l10n_cssk_fs_xlsx) (nainštaluje sa
sám, ak je prítomný modul excelových výkazov `report_xlsx`) pribudne na každom
výkaze, ktorý nie je v stave Návrh, tlačidlo **Export do XLSX**. Ten istý
výstup je v ponuke tlače ako *Výkaz s účtami (XLSX)*.

Zošit obsahuje všetky riadky výkazu — označenie, názov odsadený ako na
tlačive, brutto, korekciu, netto a netto predchádzajúceho obdobia — a pod
každým riadkom počítaným z účtov účty, z ktorých sa skladá, každý s vlastným
podielom za bežné aj minulé obdobie. Dokument s dvoma výkazmi, napríklad
slovenská Úč POD, má pre každú časť samostatný hárok. Sumy riadkov sú uložené
sumy výkazu, takže zošit ukazuje presne to, čo sa kontrolovalo, vrátane ručne
zadaných súm; účty pod prepísaným riadkom ukazujú stav účtovníctva.

**Upozornenia exportu.** Kontroly, ktoré export nezastavia, sa zobrazia v
žltom pruhu navrchu formulára a v chatteri až do ďalšieho exportu.

## Obmedzenia {#limitations}

- **Denníky koncoročnej uzávierky nemajú pole na obrazovke.** Nastavenie na
  spoločnosti existuje (*Denníky koncoročnej uzávierky*) a každý výkaz ho
  rešpektuje, žiadny formulár ho však nezobrazuje, takže ho možno nastaviť len
  technicky. Kým nie je nastavené, uzávierkové a otváracie zápisy sa
  započítajú ako ktorékoľvek iné.
- Obrazovka ukazuje len netto; brutto a korekcia sú v exporte do XLSX a v XML.
- Výkaz možno vytvoriť len za obdobie, ktoré pokrýva niektorá verzia. Od kedy
  verzie národných modulov platia, uvádzajú ich stránky.
- Odtiaľto sa nič neodosiela: súbor sa vytvorí, overí a zaeviduje, podáte ho
  sami.
- Priradenie účtov vychádza zo štandardnej národnej účtovej osnovy a pred prvým
  podaním ho treba odsúhlasiť s účtovníkom.
