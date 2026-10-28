---
title: Účetní výkazy CZ/SK
summary: Slovenské a české účetní výkazy sestavené z účetnictví řádek po řádku, se srovnatelným obdobím, ručně zadanými údaji tam, kde je účetnictví nedá, kontrolou, zda se každý účet dostal do některého řádku, a evidencí podání.
verified: 19.0.1.10.3
---

## K čemu slouží {#purpose}

Účetní závěrka v Česku i na Slovensku se sestavuje v předepsaném uspořádání:
každý řádek má určený název i obsah. Tento modul je společný mechanismus,
který je vyplňuje z účetních zápisů v Odoo. Funguje stejně v edici Community
i Enterprise a nepoužívá účetní výkazy Odoo Enterprise.

Sám žádný výkaz neobsahuje. Řádky, přiřazení účtů a formát exportu každého
výkazu přináší národní modul:

| Země | Modul | Výkazy |
|---|---|---|
| Česko | [module:l10n_cz_fs](module:l10n_cz_fs) | Rozvaha, výkaz zisku a ztráty, přehled o peněžních tocích, přehled o změnách vlastního kapitálu |
| Slovensko | [module:l10n_sk_fs](module:l10n_sk_fs) | Účtovná závierka Úč POD (súvaha a výkaz ziskov a strát v jednom dokumentu), prehľad peňažných tokov, prehľad zmien vlastného imania, poznámky |
| Slovensko | [module:l10n_sk_single_entry_closing](module:l10n_sk_single_entry_closing) | Účtovná závierka v jednoduchom účtovníctve (Úč FO) |

Tato stránka popisuje, co mají všechny společné: založení výkazu, výpočet,
kontrolu, opravy a evidenci podání. Samotné výkazy a právní rámec popisují
stránky národních modulů.

## Nastavení {#setup}

1. **Nainstalujte národní modul.** Bez něj jsou nabídky níže prázdné.
2. **Zkontrolujte přiřazení účtů.** Řádky čtou účty podle čísla v národní
   účtové osnově. Pokud vaše osnova používá čísla, která výkaz nezná
   (například analytický účet s nestandardním číslem), přiřaďte je v
   *Účetnictví → Konfigurace → CZ/SK lokalizace → Mapování účtů do výkazů*.
   Které účty to potřebují, ukáže [kontrola nepřiřazených účtů](#checks).
3. **Verze výkazů** jsou v *Účetnictví → Konfigurace → CZ/SK lokalizace →
   Verze účetních výkazů* (pro administrátory účetnictví). Každá verze je
   jedno vydání výkazu: jeho řádky, období, na které se vztahuje, XML šablona
   a — pokud ho správce daně zveřejňuje — XSD. Instalují je národní moduly,
   běžně je neupravujete. Archivovanou verzi lze stále vybrat pro období, na
   které se vztahuje.

## Založení a výpočet výkazu {#usage}

*Účetnictví → Výkazy → Zákonné výkazy* a potom druh výkazu: **Rozvaha**,
**Výkaz zisku a ztráty**, **Přehled o peněžních tocích** nebo **Přehled o
změnách vlastního kapitálu**. Klikněte na *Nový*.

- **Období.** *Datum od* a *Datum do* se předvyplní posledním skončeným
  účetním obdobím společnosti, takže i společnost s hospodářským rokem
  dostane správná data.
- **Verze.** Doplní se nejnovější verze daného výkazu platná pro období v
  zemi, ve které je společnost daňově registrována. Pokud žádná verze období
  nepokrývá, pole zůstane prázdné a výkaz nelze uložit.
- **Druh výkazu** ukazuje, o jaký dokument jde. Slovenská Úč POD je jeden
  dokument s rozvahou i výkazem zisku a ztráty, proto se zobrazuje jako
  *Účetní závěrka (rozvaha + výkaz zisku a ztráty)* a je v seznamu pod oběma
  nabídkami; každá nabídka ukáže jen svou část řádků, odjinud se zobrazí
  všechny.

Klikněte na **Vypočítat**. Modul načte zaúčtované zápisy společnosti:

- řádky rozvahy berou **kumulativní zůstatek ke dni Datum do**;
- řádky výkazu zisku a ztráty, přehledu o peněžních tocích a přehledu o
  změnách vlastního kapitálu berou **pohyb za období**; počáteční a konečné
  řádky obou přehledů berou zůstatek den před začátkem období a ke konci
  období;
- sloupec **minulého období** se vypočítá stejně za tytéž dny o rok dříve;
- zápisy v denících závěrky roku se vynechají, protože výkaz zobrazuje činnost
  období, ne uzavírání a otevírání knih (jak se tyto deníky nastavují, viz
  [Omezení](#limitations)).

Výkaz přejde do stavu **Náhled**. Po každé změně v účetnictví jej vypočítejte
znovu; přepočítat jej lze jen ve stavu *Koncept* a *Náhled*.

## Kontrola údajů {#review}

Záložka *Řádky* zobrazuje výkaz jako strom: každý součtový řádek je součtem
řádků pod ním (nahoře *Sbalit vše* / *Rozbalit vše*). Sloupce jsou **Běžné
období** a **Minulé období**.

- **Rozpad na doklady.** Lupa u řádku počítaného z účtů otevře *Zdrojové
  doklady*: účetní zápisy, ze kterých se částka skládá, seskupené podle účtu a
  pak podle dokladu — přesně ty, ze kterých se sečetla.
- **Sloupec ✓** označuje řádky, jejichž zápisy dávají dohromady částku řádku.
  Řádek, který nesouhlasí (zaokrouhlení, ručně zadaná částka), označen není.
- U výkazů ve třech sloupcích — aktiva české rozvahy a slovenská súvaha — má
  každý řádek také **Brutto** a **Korekci** (oprávky a opravné položky) a
  zobrazená částka je netto. Obrazovka ukazuje jen netto; všechny tři sloupce
  jsou v [exportu do XLSX](#xlsx) a v exportovaném XML.

## Ruční zadání částky {#overrides}

Některé údaje účetnictví dát neumí. Klikněte na tužku u částky, zadejte
hodnotu a stiskněte **Vypočítat**, aby se přepočítaly součty nad ní.

- Částka **zůstane zachována při každém přepočtu** a je označena jako zadaná
  ručně. Šipka zpět vrátí řádek na vypočtenou hodnotu při příštím výpočtu.
- **Součtové řádky přepsat nelze** — přepište řádky, ze kterých se skládají.
- **Minulé období** má vlastní přepis. Použijte jej v prvním roce vedení
  účetnictví v Odoo, kdy je loňské účetnictví v jiném systému, aby výkaz
  ukázal loňské údaje tak, jak byly podány.
- Změna částky vrátí výkaz do stavu **Koncept**, takže dokud další výpočet
  nesrovná součty, nelze jej exportovat.

## Kontroly {#checks}

Dvě tlačítka v záhlaví upozorní na to, co i vyrovnaný výkaz může skrývat:

| Tlačítko | Význam | Co udělat |
|---|---|---|
| **Nesouhlasící řádky** (červené) | Řádky, jejichž zápisy nedávají dohromady částku řádku. Pokud takové nejsou, zelené **Řádky souhlasí**. | U ručně zadaných částek je to běžné; jinak otevřete zdrojové doklady řádku. |
| **Nepřiřazené účty** (oranžové) | Účty se zůstatkem ke dni Datum do, které si žádný řádek výkazu nenárokuje. Jejich peníze jsou v účetnictví, ale ne ve výkazu — a výkaz přesto sedí i je vyrovnaný. Zobrazí se 50 největších zůstatků; částky pod 1 se ignorují. | Přiřaďte účet k číslu, které výkaz očekává, v *Mapování účtů do výkazů* a pak znovu *Vypočítat*. Třída 7 (závěrkové a podrozvahové účty) a účty typu podrozvahový se nezobrazují nikdy. Některé účty se zobrazují záměrně — které, uvádějí stránky národních modulů. |

Národní modul může přidat další kontroly, které se spouštějí při exportu
(například slovenská Úč POD kontroluje kontrolní pravidla výkazu).

## Export a evidence podání {#filing}

1. **Exportovat XML** vytvoří soubor ve formátu verze výkazu. Odmítne se,
   dokud je výkaz v konceptu, a také pokud společnost nemá vyplněné *DIČ*,
   které export vyžaduje jako identifikaci předkladatele. Soubor se ověří proti
   XSD verze; verze, u které je uvedeno, že správce daně pro výkaz XSD
   nezveřejňuje, se exportuje bez ověření. Soubor se připojí k výkazu, který
   přejde do stavu **Exportováno**.
2. Soubor podejte sami.
3. **Označit jako podané** to zaznamená: podaná kopie se uchová a výkaz se
   uzamkne — nelze jej přepočítat, znovu exportovat ani smazat.
4. **Podat** otevře záznam o doručení podání. Pokud je nainstalován jen ruční
   kanál, zaznamená, kdo podání na portálu podal, a uchová potvrzení, která
   portál vrátil.

**Opravná závěrka** na podaném výkazu jej zkopíruje do nového konceptu
označeného jako opravný a propojeného s původním. Opravte účetnictví, výkaz
vypočítejte a podejte jako kterýkoli jiný; rozdílové řádky nemá, opravná
závěrka uvádí celé období znovu.

**Vrátit do konceptu** znovu otevře exportovaný nebo podaný výkaz. Smějí to
jen administrátoři účetnictví; podaná kopie zůstane připojena a uvedena v
historii podání.

Výkaz převzatý z předchozího systému jako historické podání se zobrazí ve
stavu **Historické podání** a nelze jej vypočítat, exportovat ani podat. Pokud
se podané a vypočtené údaje porovnávaly, tlačítko **Porovnání** vede k
porovnáním tohoto výkazu.

## Export do Excelu {#xlsx}

S doplňkem [module:l10n_cssk_fs_xlsx](module:l10n_cssk_fs_xlsx) (nainstaluje
se sám, pokud je přítomen modul excelových výkazů `report_xlsx`) přibude u
každého výkazu, který není v konceptu, tlačítko **Export do XLSX**. Tentýž
výstup je v nabídce tisku jako *Výkaz s účty (XLSX)*.

Sešit obsahuje všechny řádky výkazu — označení, název odsazený jako ve
výkazu, brutto, korekci, netto a netto minulého období — a pod každým řádkem
počítaným z účtů účty, ze kterých se skládá, každý s vlastním podílem za
běžné i minulé období. Dokument se dvěma výkazy, například slovenská Úč POD,
má pro každou část samostatný list. Částky řádků jsou uložené částky výkazu,
takže sešit ukazuje přesně to, co se kontrolovalo, včetně ručně zadaných
částek; účty pod přepsaným řádkem ukazují stav účetnictví.

**Upozornění exportu.** Kontroly, které export nezastaví, se zobrazí ve
žlutém pruhu nahoře na formuláři a v chatteru až do dalšího exportu.

## Omezení {#limitations}

- **Deníky závěrky roku nemají pole na obrazovce.** Nastavení na společnosti
  existuje (*Deníky závěrky roku*) a každý výkaz je respektuje, žádný formulář
  je však nezobrazuje, takže je lze nastavit jen technicky. Dokud nastavené
  nejsou, závěrkové a otevírací zápisy se započítají jako kterékoli jiné.
- Obrazovka ukazuje jen netto; brutto a korekce jsou v exportu do XLSX a v XML.
- Výkaz lze založit jen za období, které pokrývá některá verze. Od kdy verze
  národních modulů platí, uvádějí jejich stránky.
- Odsud se nic neodesílá: soubor se vytvoří, ověří a zaeviduje, podáte jej
  sami.
- Přiřazení účtů vychází ze standardní národní účtové osnovy a před prvním
  podáním je třeba je odsouhlasit s účetním.
