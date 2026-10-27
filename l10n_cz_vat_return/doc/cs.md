---
title: CZ Přiznání k DPH (DPHDP3)
summary: České přiznání k DPH vypočtené z daňových štítků české účtové osnovy Odoo a exportované jako XML DPHDP3 pro EPO, pro každé období ověřené proti aktuálnímu úřednímu XSD.
verified: 19.0.1.11.0
---

## K čemu slouží {#purpose}

Česká vrstva [společného základu přiznání k DPH](module:l10n_cssk_vat_return_base).
Dodává:

- formulář **DPHDP3** (přiznání k dani z přidané hodnoty): jeho řádky
  napojené na daňové štítky české účtové osnovy Odoo (`l10n_cz`), XML šablonu
  pro EPO (`Pisemnost / DPHDP3`) a úřední schéma;
- větu o subjektu (VetaP) z údajů společnosti pro EPO;
- opravy u nedobytných pohledávek vykazované na ř. 33 a ř. 34;
- úpravy daní české osnovy, bez kterých by několik řádků zůstalo prázdných
  nebo chybných;
- archivované sazby platné před dnešními pro import starších dokladů.

Jak přiznání založit, vypočítat, zkontrolovat, exportovat a podat, popisuje
[stránka společného základu](module:l10n_cssk_vat_return_base#usage); tato
stránka se věnuje tomu, co je české.

## Právní rámec {#legal}

- **Kdo podává.** Daňové přiznání podává plátce a identifikovaná osoba —
  [§ 101 odst. 1 zákona o DPH](law:cz/2004/235) — a plátce je podává i za
  období, v němž mu povinnost přiznat daň nevznikla
  ([§ 101 odst. 3](law:cz/2004/235)).
- **Zdaňovací období.** Kalendářní měsíc ([§ 99](law:cz/2004/235)). Plátce se
  může pro kalendářní rok rozhodnout pro kalendářní čtvrtletí, pokud jeho obrat
  v tuzemsku za bezprostředně předcházející rok nepřesáhl 15 000 000 Kč, není
  nespolehlivým plátcem ani skupinou a změnu oznámí správci daně do konce ledna
  ([§ 99a odst. 1](law:cz/2004/235)).
- **Lhůta.** Je-li zdaňovací období kratší než rok, podává se přiznání **do 25
  dnů po uplynutí zdaňovacího období** a tuto lhůtu nelze prodloužit —
  [§ 136 odst. 4 daňového řádu](law:cz/2009/280).
- **Elektronicky a ve stanovené struktuře.** Plátce je povinen podat daňové
  přiznání i dodatečné daňové přiznání elektronicky
  ([§ 101a odst. 1](law:cz/2004/235)); podání, které nebylo učiněno stanoveným
  způsobem, ve stanoveném formátu nebo struktuře, je neúčinné
  ([§ 101a odst. 4](law:cz/2004/235)).
- **Opravné a dodatečné přiznání.** Před uplynutím lhůty lze přiznání nahradit
  opravným daňovým přiznáním ([§ 138 daňového řádu](law:cz/2009/280)). Zjistí-li
  plátce po lhůtě, že daň má být vyšší než poslední známá daň, podá dodatečné
  daňové přiznání do konce měsíce následujícího po měsíci, ve kterém to
  zjistil ([§ 141 odst. 1](law:cz/2009/280)), a uvede v něm rozdíl oproti
  poslední známé dani a den jeho zjištění ([§ 141 odst. 5](law:cz/2009/280)).
- **Nedobytné pohledávky.** Opravu základu daně u nedobytné pohledávky na
  straně věřitele upravuje [§ 46 a násl. zákona o DPH](law:cz/2004/235),
  odpovídající opravu odpočtu na straně dlužníka [§ 74b](law:cz/2004/235).

## Formulář a jeho struktura {#form}

Finanční správa zveřejňuje **jediné** schéma DPHDP3, `dphdp3_epo2.xsd`, a
přepisuje ho na místě; každé přiznání — za běžné i za staré období — se podává
ve struktuře platné v okamžiku podání. Modul proto obsahuje jedinou verzi bez
konce platnosti, **DPHDP3 (aktuální struktura)**, s tímto schématem a XML s
označením `verzePis="03.01.04"` — struktura 03.01.04 ze dne 11. 8. 2026.
Protože schéma samo neříká, o kterou revizi jde, modul si kontrolní součet
souboru a verzi struktury zapisuje do `data/SCHEMA_VERSION` i s postupem
aktualizace; test selže, pokud se přiložený soubor nebo `verzePis` šablony od
tohoto záznamu odchýlí. Nabízí se pro období od **1. 1. 2016**; toto
datum je opatrná hranice zvolená modulem, ne zákonná, a pro dřívější období
verze není.

Částky se exportují v celých korunách. Datum podání v XML (*d_poddp*) je den
exportu.

## Nastavení {#setup}

Kromě [nastavení společného základu](module:l10n_cssk_vat_return_base#setup)
potřebuje XML na společnosti:

| Kde | Co |
|---|---|
| *DIČ* | DIČ (zapíše se bez `CZ`). |
| *Finanční úřad* | Finanční úřad; jeho kód pro podání jde do *c_ufo*. |
| *Finanční Úřad (CZ)* | Územní pracoviště, *c_pracufo*. |
| *Typ osoby / subjektu* | Rozhoduje, zda je podatel fyzická, nebo právnická osoba. |
| záložka **EPO podání** | U právnické osoby *oprávněná osoba* (jméno a postavení), u fyzické osoby jméno a titul; *Sestavil* a případně *Zástupce*. |
| *NACE (main activity)* | Kód převažující činnosti podle CZ-NACE, *c_okec*; přiznání bez něj EPO hlásí jako závažnou chybu. |
| adresa, telefon, e-mail | Adresa podatele (ulice a číslo se rozdělí), *c_telef*, *email*. |

Typ plátce (*typ_platce*) je vždy **P** (plátce), pokud modul
[module:l10n_cz_vat_status](module:l10n_cz_vat_status) nevede jiný status.

## České přiznání {#usage}

Typy výkazu jsou **Řádné** (B), **Opravné** (O), **Dodatečné** (D) a
**Dodatečné/opravné** (E). Kód řádku je název atributu v XML (`obrat23`,
`dan23`, `odp_tuz23_nar` …) a název řádku uvádí číslo řádku formuláře, např.
*R1 tax_base*.

**Počítají se ze štítků**: řádky 1–13 (základ i daň), 20–26, 30, 32, 33, 34,
základ a odpočet v plné výši na řádcích 40–44 a 47, řádek 50, 51 a 61.

**Počítají se z ostatních řádků**, jak je definuje struktura EPO, po řádcích
výše (každý sčítán v celých korunách tak, jak se exportuje, aby součty
souhlasily):

| Řádek | Vzorec |
|---|---|
| 46 | součet řádků 40–45 v každém sloupci (*v plné výši*, *krácený odpočet*) |
| 62 | řádky 1–13 (daň) − řádek 61 |
| 63 | řádek 46 *v plné výši* + řádek 52 + řádek 53 + řádek 60 |
| 64 | řádek 62 − řádek 63, je-li kladný (vlastní daň) |
| 65 | řádek 63 − řádek 62, je-li kladný (nadměrný odpočet) |
| 66 | řádek 62 − řádek 63, jen u dodatečného přiznání |

**Přepis** na kterémkoli z nich zůstane zachován a promítne se do dalších
řádků. Řádky 64 a 65 se do XML dodatečného přiznání nezapisují, řádek 66 do
žádného jiného. Daň podle § 108 odst. 4 písm. g) a h), kterou formulář
přičítá k řádku 62, ale nemá vlastní řádek, se nemodeluje: kde vznikne,
přičtěte ji k řádku 62 přes **Přepis**.

Řádky 64 a 65 také plní záložku *Vypořádání* (částka k úhradě nebo vrácení
a převod nadměrného odpočtu).

**Ručně** — zadejte je přes **Přepis**, jinak se exportují jako 0:

| Řádek | Obsah |
|---|---|
| 31 | třístranný obchod, prostřední osoba |
| 40–44, 47 (*reduced_claim*) | odpočet v krácené výši |
| 45 | korekce odpočtů |
| 52, 53 | koeficienty a vypořádání odpočtu |
| 60 | úprava odpočtu daně |

**Obsahové kontroly při exportu**: řádky 64 a 65 nesmějí být záporné a
nesmějí být vyplněny oba.

**Dodatečné přiznání** (typ D a E) nelze exportovat bez pole **Důvody
zjištěny dne** (*d_zjist*), které se zobrazí vedle typu výkazu. Je to totéž
datum jako *Den zjištění rozdílu* společného základu (jedno pole, zobrazené
jednou pod českým názvem), takže přiznání vytvořené tlačítkem ho už nese.

**Podání přes EPO.** S modulem [module:l10n_cz_epo](module:l10n_cz_epo)
nabídne **Podat** kanál EPO: přiznání lze ověřit v testovacím režimu EPO a
podat s certifikátem společnosti.

## Úpravy české osnovy {#chart-fixes}

Při instalaci a vždy, když společnost načte českou osnovu, modul upraví daně
osnovy tak, aby je přiznání umělo vykázat:

- **Odpočet daně z přenesené povinnosti (ř. 43 a 44).** `l10n_cz` označuje
  štítkem jen přiznání daně u přenesené daňové povinnosti nebo pořízení z
  jiného členského státu, takže odpočet nešel do žádného řádku. Odpočtové
  větve dostanou nové štítky *VAT 43 Base/Total* a *VAT 44 Base/Total*; sazba
  (základní/snížená) se určí podle řádku, na kterém daň přiznává.
- **Dovoz zboží (ř. 7 a 8).** Tyto daně měly jedinou daňovou větev, takže
  přijatá faktura od dodavatele mimo EU chtěla zaplatit dodavateli i českou
  DPH navíc; doplní se vyrovnávající odpočtová větev. Řádek 9 (nový dopravní
  prostředek) zůstává beze změny.
- **Opravné doklady u přenesené daňové povinnosti z EU.** Čtyři daně měly účet
  daně jen na straně faktury; strana dobropisu dostane stejný účet, takže
  opravný daňový doklad už nenechá DPH na nákladovém účtu.
- **Pořízení z jiného členského státu.** Ve fiskální pozici *Vnitrokomunitární*
  se tuzemské nákupní daně (21 % a 12 %, zboží i služby) mapují na daně
  pořízení z EU, takže přijatá faktura od dodavatele z EU daň samovyměří a
  neponechá českou sazbu. Vazby se jen přidávají; ručně nastavené mapování
  zůstane.

## Opravy u nedobytných pohledávek {#bad-debt}

Doklad označený polem **Oprava u nedobytné pohledávky** (přidává ho
`l10n_cz_statutory`) vypadne ze všech běžných řádků přiznání. Jeho daň jde do
**ř. 33**, je-li to prodejní doklad (oprava věřitele), nebo do **ř. 34**, je-li
to nákupní doklad (oprava dlužníka), navíc k případným záznamům ručně
označeným štítkem *VAT 33* / *VAT 34*.

## Historické sazby {#historic-rates}

Při instalaci a vždy, když společnost načte českou osnovu, se sazby, které už
neplatí, vytvoří jako archivované daně (viz
[stránku společného základu](module:l10n_cssk_vat_return_base#historic-rates)).
Každá se kopíruje z dnešní sazby stejného pásma, protože DPHDP3 odděluje
základní sazbu (ř. 1/2, odpočet ř. 40) od snížené (ř. 3/4, ř. 41):

| Sazba | Platila | Kopíruje se z |
|---|---|---|
| 19 % | 1. 5. 2004 – 31. 12. 2009 | 21 % |
| 20 % | 1. 1. 2010 – 31. 12. 2012 | 21 % |
| 5 % | 1. 5. 2004 – 31. 12. 2007 | 12 % |
| 9 % | 1. 1. 2008 – 31. 12. 2009 | 12 % |
| 10 % | 1. 1. 2010 – 31. 12. 2023 | 12 % |
| 14 % | 1. 1. 2012 – 31. 12. 2012 | 12 % |
| 15 % | 1. 1. 2013 – 31. 12. 2023 | 12 % |

10 % je jedna daň pro obě svá období (2010–2011 a 2015–2023), takže tři roky
mezi nimi její data nevylučují.

## Omezení {#limitations}

- Odpočty v krácené výši a řádky 31, 45, 52, 53 a 60 jsou ruční (viz
  [výše](#usage)), stejně jako část řádku 62 podle § 108 odst. 4 písm. g) a h).
- Obsahové kontroly pokrývají jen řádky 64 a 65; schéma nepozná, zda jsou
  ostatní údaje navzájem konzistentní.
- Pro období před rokem 2016 verze není.
- U dodatečného přiznání jsou řádky přepočtené údaje období a řádek 66 je
  řádek 62 − řádek 63 tohoto přiznání; s opravovaným přiznáním se nesrovnává.
- Záznam v `data/SCHEMA_VERSION` dokládá, že přiložené schéma je to, které
  bylo ověřeno k uvedenému dni, ne že je stále aktuální; aktualizujte ho
  postupem popsaným v tomto souboru.
- Řádky se řídí štítky `l10n_cz`. Daň založená ručně bez správných štítků
  skončí ve špatném řádku nebo v žádném.
