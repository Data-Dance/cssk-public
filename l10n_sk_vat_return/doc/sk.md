---
title: SK Daňové priznanie k DPH
summary: Slovenské daňové priznanie k DPH vypočítané z daňových značiek slovenskej účtovej osnovy Odoo, vo vzore platnom pre dané obdobie, exportované ako XML finančnej správy a overené voči jej XSD.
verified: 19.0.1.13.1
---

## Na čo slúži {#purpose}

Slovenská vrstva [spoločného základu daňového priznania](module:l10n_cssk_vat_return_base).
Dodáva:

- každý **vzor** daňového priznania k dani z pridanej hodnoty, ku ktorému
  finančná správa od roku 2012 zverejnila XSD, s jeho riadkami, XML šablónou a
  úradnou schémou;
- definície riadkov napojené na daňové značky slovenskej účtovej osnovy Odoo
  (`l10n_sk`) a slovenské kontrolné pravidlá;
- riadok rozdielu dodatočného daňového priznania doplnený z pôvodného
  priznania;
- nákupné dane pre **služby prijaté z EÚ**, ktoré štandardná osnova nemá;
- sprievodcu **opravou odpočítanej dane podľa § 53b** pri nezaplatených
  faktúrach;
- archivované sadzby spred roka 2025 (20 % a 10 %) na import starších dokladov.

Ako priznanie založiť, vypočítať, skontrolovať, exportovať a podať, opisuje
[stránka spoločného základu](module:l10n_cssk_vat_return_base#usage); táto
stránka sa venuje tomu, čo je slovenské.

## Právny rámec {#legal}

Ak nie je uvedené inak, odkazy sú na [zákon o DPH](law:sk/2004/222).

- **Zdaňovacie obdobie.** Kalendárny mesiac
  ([§ 77 ods. 1](law:sk/2004/222#paragraf-77.odsek-1)). Platiteľ sa môže
  rozhodnúť pre kalendárny štvrťrok, ak uplynulo viac ako 12 kalendárnych
  mesiacov od konca mesiaca, v ktorom sa stal platiteľom, a za 12
  predchádzajúcich po sebe nasledujúcich kalendárnych mesiacov nedosiahol obrat
  100 000 eur ([§ 77 ods. 2](law:sk/2004/222#paragraf-77.odsek-2)).
- **Lehota.** Platiteľ so sídlom, miestom podnikania alebo prevádzkarňou v
  tuzemsku podáva daňové priznanie **do 25 dní po skončení každého
  zdaňovacieho obdobia** a v tej istej lehote platí vlastnú daňovú povinnosť
  ([§ 78 ods. 2 písm. a)](law:sk/2004/222#paragraf-78.odsek-2.pismeno-a));
  vlastná daňová povinnosť je kladný rozdiel medzi splatnou daňou a
  odpočítateľnou daňou ([§ 78 ods. 1](law:sk/2004/222#paragraf-78.odsek-1)).
- **Elektronické podanie.** Platiteľ DPH je povinný doručovať podania
  finančnej správe elektronickými prostriedkami —
  [§ 14 ods. 1 písm. a) daňového poriadku](law:sk/2009/563#paragraf-14.odsek-1.pismeno-a).
- **Nadmerný odpočet.** Nadmerný odpočet platiteľ odpočíta od vlastnej daňovej
  povinnosti v nasledujúcom zdaňovacom období, a ak to nie je možné, daňový
  úrad ho vráti ([§ 79 ods. 1](law:sk/2004/222#paragraf-79.odsek-1));
  mesačný platiteľ, ktorý spĺňa podmienky
  [§ 79 ods. 2](law:sk/2004/222#paragraf-79.odsek-2), dostane nadmerný odpočet
  vrátený hneď a túto skutočnosť vyznačí v priznaní
  ([§ 79 ods. 3](law:sk/2004/222#paragraf-79.odsek-3)).
- **Opravné a dodatočné priznanie.** Pred uplynutím lehoty na podanie môže
  daňový subjekt podať opravné daňové priznanie
  ([§ 16 ods. 1](law:sk/2009/563#paragraf-16.odsek-1)); ak po nej zistí, že
  daň má byť vyššia alebo nadmerný odpočet nižší, je povinný podať dodatočné
  daňové priznanie do konca mesiaca nasledujúceho po tomto zistení
  ([§ 16 ods. 2](law:sk/2009/563#paragraf-16.odsek-2) daňového poriadku).
- **§ 53b.** Platiteľ je povinný opraviť odpočítanú daň v rozsahu, v akom za
  dodanie nezaplatil, v tom zdaňovacom období, v ktorom nastal 101. deň odo dňa
  splatnosti záväzku
  ([§ 53b ods. 1 písm. a)](law:sk/2004/222#paragraf-53b.odsek-1.pismeno-a)), a
  má právo opraviť opravenú odpočítanú daň v období, v ktorom zaplatil
  ([§ 53b ods. 4](law:sk/2004/222#paragraf-53b.odsek-4)).

## Vzory tlačiva {#versions}

Finančná správa zverejňuje pre každý vzor samostatnú XSD schému a staré
ponecháva; za obdobie sa podáva vzor, ktorý preň platil. Modul obsahuje jednu
verziu na každý vzor:

| Verzia (ako sa zobrazuje) | Obdobia | Schéma |
|---|---|---|
| DPH (vzor 1. 1. 2012 – 31. 12. 2017) | 2012 – 2017 | `dph2012.xsd` |
| DPH (vzor 1. 1. 2018 – 31. 12. 2019) | 2018 – 2019 | `dph2018.xsd` |
| DPH (vzor 1. 1. 2020 – 31. 12. 2020) | 2020 | `dph2020.xsd` |
| DPH (vzor do 30. 6. 2025) | 1. 1. 2021 – 30. 6. 2025 | `dph2021.xsd` |
| DPH 2025 | od 1. 7. 2025 | `dph2025.xsd` |

Všetkých päť sú úradné súbory, uložené bajt po bajte, s kontrolnými súčtami
zaznamenanými v module. Na priznaní zoznam *Verzia* ponúkne tú, ktorá pre
obdobie platí.

O vzoroch treba vedieť tri veci:

- **Január až jún 2025 sa podáva na vzore 2021**, hoci sadzby sa zmenili už
  1. 1. 2025. Vzor 2021 má jedinú dvojicu riadkov prenesenia daňovej
  povinnosti `r09`/`r10` a dve tuzemské sadzbové pásma; vzor 2025 ich rozdelil
  podľa sadzby (`r01a`, `r09a`, `r09b`, `r11a` – `r11e`, `r18a`, `r23a` –
  `r23c` …). Verzia 2021 preto do každého svojho riadku zbiera všetky značky,
  na ktoré ho neskorší vzor rozdelil.
- **Schémy 2018 a 2020 sú totožné**, tlačivá nie: riadok 18 je v rokoch
  2018 – 2019 daňová povinnosť pri zrušení registrácie podľa § 81 a v roku
  2020 daň podľa § 48ca, § 48d a § 48e. Sú to dve verzie, aby každé obdobie
  malo svoj význam riadku; overenie voči schéme ich nerozlíši.
- **Vzory 2012 – 2020 číslujú riadky inak** ako vzor 2021 (od riadku 11 o dva)
  a službu od zahraničnej osoby podľa
  [§ 69 ods. 3](law:sk/2004/222#paragraf-69.odsek-3) vykazujú v riadkoch
  `r11`/`r12`, oddelene od ostatného prenesenia daňovej povinnosti v `r09`/`r10`.
  Slovenská osnova má pre obe jedinú rodinu daní, takže modul ich za tieto
  obdobia rozdelí podľa **krajiny dodávateľa**: dodávateľ mimo Slovenska ide do
  `r11`/`r12`, slovenský (alebo bez krajiny) do `r09`/`r10`. Daň používaná
  len pre jeden odsek to môže uviesť v poli **SK § 69 paragraph (pre-2021
  vzory)** na formulári dane (*Rozšírené možnosti*, nákupné dane): osobitná
  daň pre tuzemské stavebné prenesenie je *§ 69 ods. 2 a 9 až 12* bez ohľadu
  na dodávateľa.

Pre obdobia pred rokom 2012 verzia nie je.

## Nastavenie {#setup}

Okrem [nastavenia spoločného základu](module:l10n_cssk_vat_return_base#setup):

- **Údaje spoločnosti v hlavičke XML**: IČ DPH z poľa *DIČ* (ako *DIČ* sa do XML zapíše to isté
  číslo bez `SK`), daňový úrad z poľa **Daňový úrad** (jeho kód pre podanie),
  názov, ulica a číslo, PSČ, obec, telefón a e-mail. *Číslo* je číslo na konci
  poľa **Ulica** („Mlynská 1234/5“ dá *ulica* „Mlynská“ a *číslo* „1234/5“),
  prípadne polia čísla domu, ak sa adresa vedie rozdelená. **Ulica2** sa ako
  číslo podá, len ak obsahuje iba číslo — budova, poschodie či c/o nikdy;
  ulica, ktorá nekončí číslom, sa zapíše celá a *číslo* zostane prázdne.
- **Služby nakupované z EÚ** potrebujú správnu daň dodávateľa, pozri
  [nižšie](#eu-services).

## Slovenské priznanie {#usage}

Typy výkazu sú *Riadny*, *Opravný* a *Dodatočný*. Riadky `r01` až `r29` (vo
vzore 2025 aj s písmenovými variantmi) sa počítajú z daňových značiek
slovenskej osnovy, ktoré sú pomenované podľa riadkov. Okrem toho:

| Riadok | Ako sa vypĺňa |
|---|---|
| r17 (daň celkom) | Súčet riadkov dane. |
| r18, r18a, r19 | Do XML ide **celkové** odpočítanie dane podľa sadzby. Na obrazovke sú to riadky s názvom *(internal) odpočet — …*; riadky s kódom `r18`, `r18a`, `r19` ukazujú len vlastnú značku. |
| r30, r31 | Ručne: odpočet pri registrácii, vrátenie dane cestujúcim. |
| r32 / r33 | Vypočíta sa: vlastná daňová povinnosť alebo nadmerný odpočet podľa výsledku. |
| r34 | Ručne: nadmerný odpočet z predchádzajúceho obdobia, ktorý sa odpočítava. |
| r35 | Vypočíta sa: r32 − r34, nie menej ako nula. |
| r36 | Pri dodatočnom priznaní sa doplní pri **Vypočítať** ako (r32 − r33) tohto priznania mínus (r32 − r33) opravovaného priznania, ak ste ho neprepísali. |
| r37 | Ručne. |

Riadky s názvom *(internal) …* sú pomocné; na tlačive nie sú.

**Kontrolné pravidlá pri exporte.** Export sa zastaví, ak je r32 alebo r33
záporný, ak sú oba kladné, alebo ak je r34 vyšší ako r32. Kontroluje sa aj, či
je každý riadok dane súčinom svojho riadku základu a niektorej sadzby platnej
pre vzor (vo vzore 2025 19, 5 a 23 %); táto kontrola len varuje a varovanie sa
zapíše do serverového logu, na obrazovke sa nezobrazí.

**Dodatočné priznanie** prenesie *Deň zistenia rozdielu* (*datumZisteniaDdp*)
do XML len vtedy, keď je typ *Dodatočný*.

## Prvá strana tlačiva (Hlavička) {#header}

Slovenské priznanie má záložku **Hlavička**, upraviteľnú, kým je priznanie
v stave koncept alebo náhľad:

| Pole | Čo vyplní |
|---|---|
| Postavenie osoby | Kto podáva, ako sa vyznačuje na 1. strane: *Platiteľ dane (§ 4)* (predvolené), *Osoba registrovaná pre daň podľa § 7 alebo § 7a*, *Iná osoba povinná podať priznanie (§ 78 ods. 3, 4 a 9)*, *Zdaniteľná osoba podľa § 3 ods. 5*, *Daňový zástupca podľa § 69a* alebo *§ 69aa* (posledné len za obdobia od 1. 1. 2018). |
| Splnenie podmienok § 79 ods. 2 | Zaškrtnite, ak spĺňate podmienky vrátenia nadmerného odpočtu do 30 dní. Ponúka sa len platiteľovi s mesačným obdobím a exportuje sa ako 1 len vtedy, keď priznanie vykazuje nadmerný odpočet (`r33`). |
| Dátum vyhlásenia | Dátum vyhlásenia; ak je prázdny, použije sa dátum exportu XML. |
| Oprávnená osoba | Meno, telefón a e-mail osoby, ktorá podáva za spoločnosť, napríklad zástupcu podľa § 9 daňového poriadku. Ak spoločnosť podáva sama, nechajte prázdne. |

Podmienky § 79 ods. 2 (12 mesiacov ako platiteľ, nedoplatky najviac 1 000 €)
Odoo overiť nevie; zaškrtnutie je vaše vyhlásenie.

## Služby prijaté z EÚ {#eu-services}

Slovenská osnova Odoo mapuje vo fiškálnej pozícii *Eu intra* každú nákupnú daň
na nadobudnutie **tovaru** (riadky 07/08), takže služba od dodávateľa z EÚ
skončí v zlom riadku. Modul pridáva:

- tuzemské nákupné dane **23% S**, **19% S** a **5% S** (rozsah Služby);
- ich náprotivky pre EÚ **23 % EÚ S**, **19 % EÚ S** a **5 % EÚ S**, ktoré
  daň podľa § 69 ods. 3 samozdania v riadkoch 09b/10b, 09/10 a 09a/10a a
  zároveň ju odpočítajú.

Na produktoch – službách nastavte ako daň dodávateľa daň *S*. Na faktúre od
dodávateľa z EÚ ju fiškálna pozícia nahradí daňou *EÚ S*; tovar si ponechá
svoju daň a ide ďalej do riadkov 07/08. Dane sa doplnia každej slovenskej
spoločnosti pri inštalácii a aktualizácii modulu, len ak chýbajú.

## Oprava odpočítanej dane podľa § 53b {#par53b}

*Účtovníctvo → Účtovníctvo → Oprava odpočítanej dane (§ 53b)* otvorí
sprievodcu:

| Pole | Význam |
|---|---|
| Ku dňu | Deň, ku ktorému sa meria lehota po splatnosti; opravné zápisy dostanú tento dátum. |
| Dní po splatnosti | Predvolene 100. |
| Denník opráv | Všeobecný denník pre zápisy. |
| Protiúčet (náklad) | Účet, na ktorý sa opravená daň preúčtuje, zvyčajne 548. |

Sprievodca zobrazí zaúčtované prijaté faktúry nezaplatené alebo čiastočne
zaplatené, ktorých splatnosť je aspoň o daný počet dní skôr ako zvolený deň,
ktoré si uplatnili odpočet a ešte neboli opravené. **Vygenerovať opravy**
zaúčtuje za každú faktúru jeden zápis: odpočítanú daň vynásobenú nezaplateným
podielom, v prospech účtu dane na vstupe so značkou riadku 29 a na ťarchu
zvoleného účtu. Riadok `r29` priznania ju prevezme.

Keď je opravená faktúra zaplatená (celá alebo sčasti), zobrazí tlačidlo
**Znovu uplatniť odpočet (§ 53b ods. 4)**: zaúčtuje zrkadlový zápis za
zaplatený podiel s dnešným dátumom, nikdy viac, než sa opravilo. Záložka
*Ďalšie informácie* faktúry ukazuje jej *Stav § 53b* a zápisy opráv.

## Historické sadzby {#historic-rates}

Pri inštalácii a vždy, keď spoločnosť načíta slovenskú osnovu, modul vytvorí
sadzby, ktoré už neplatia, ako archivované dane (pozri
[stránku spoločného základu](module:l10n_cssk_vat_return_base#historic-rates)):

| Sadzba | Platila | Kopíruje sa z |
|---|---|---|
| 20 % | 1. 1. 2011 – 31. 12. 2024 | dnešných daní 23 %; ich značky prenesenia daňovej povinnosti sa presunú z 09b/10b späť na 09/10, riadky, ktoré vtedy existovali |
| 10 % | 1. 1. 2007 – 31. 12. 2024 | dnešných daní 19 % |

Základná sadzba 19 % z rokov 2004 – 2010 sa nevytvára: dnešné dane 19 % sú
znížená sadzba a druhá rodina s rovnakým názvom by s nimi kolidovala.

## Obmedzenia {#limitations}

- Postavenie osoby nastavuje len políčko na 1. strane. Riadky sa počítajú
  rovnako pre každého: osoba registrovaná podľa § 7 alebo § 7a nemá nárok na
  odpočet, preto skontrolujte, že jej priznanie žiadny nevykazuje.
- Podmienky § 79 ods. 2 vyhlasujete vy, Odoo ich neoveruje.
- Záložka *Vysporiadanie* sleduje prenos nadmerného odpočtu pre sumu na
  úhradu, ale `r34` nevypĺňa: odpočítavanú sumu zadajte do `r34` cez
  **Prepis**. Ručné sú aj riadky r30, r31 a r37.
- Sprievodca § 53b datuje zápisy dňom, ktorý zvolíte; spúšťajte ho za obdobie,
  v ktorom nastal 101. deň.
- Priradenie riadkov zníženej sadzby vo vzore 2021 (r01/r02 zbiera 19 % aj
  5 %) je odvodené zo štruktúry tlačív, nie z podaného priznania; pred importom
  histórie so zníženou sadzbou ho dajte potvrdiť účtovníkovi.
- Odtiaľto sa nič nepodáva: XML exportujte, podajte na portáli finančnej správy
  a priznanie potom označte ako podané.
