---
title: SK dávka514 — mesačný výkaz preddavkov na zdravotné poistenie
summary: Publikovaný textový formát514 od roku2023 z uchovaných zdravotných podkladov OCA pások, riadne a opravné podanie a spoločný archív. Starší XML formát zostáva pre existujúcich klientov.
verified: 19.0.1.3.0
---

## Na čo slúži {#purpose}

Mesačný výkaz pre VšZP (25), Dôveru (24) alebo Union (27). Menu ponúkne
**Publikovaný text514 (2023+)**. Výkaz používa podklady uchované pri výpočte
OCA pásky: skutočný zamestnanecký základ, OP, obe sadzby, zdravotné
postihnutie, doplatok do minima, kalendárne dni, rodné číslo a poisťovňu.
Sadzba sa neodvodzuje delením zaokrúhleného poistného hrubým príjmom.

Existujúcim API klientom zostáva predvolený **Starší XML formát**. Kontroluje
sa jeho štruktúra; prijateľnosť podľa overenej schémy autority nie je
preukázaná. Nový adaptér uchovaných podkladov poskytuje
[module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca). Iné mzdové
jadro potrebuje vlastný zodpovedajúci adaptér pre publikovaný TXT.

## Právny rámec {#legal}

[Zákon o zdravotnom poistení](law:sk/2004/580) upravuje mesačný výkaz (§20),
splatnosť (§17), OP (§16 ods.16–18) a minimálny preddavok (§16a).
Textový formát vychádza z [rozhrania zverejneného VšZP](https://www.vszp.sk/files/platitelia/tlaciva-platitelov/vykaz-preddavkov-zamestnavatela/struktura-vykazu-1.rtf).
SHA256 zdroja je pri serializéri. Nenahrádza sa lokálne upraveným XSD.
Správnosť formátu a skutočné prijatie poisťovňou sú odlišné výsledky.

Príjem oprávnený na OP a ostatný príjem majú samostatné polia, aj keď si
zamestnanec mesačnú OP neuplatnil. Písomné neuplatnenie doplatku pri súbehu
zamestnaní podľa §16a ods.5 je samostatná skutočnosť. Neoznačujte ho len
preto, že ide o dôchodcu, osobu so zdravotným postihnutím alebo poistenca štátu.

## Nastavenie {#setup}

Na zamestnávateľovi zadajte IČO, DIČ a predvolenú poisťovňu. Zamestnancovi
nastavte skutočné rodné číslo a poisťovňu **pred výpočtom pásky**. Zdravotné
postihnutie a nárok na OP patria na dátumovanú verziu pracovného vzťahu.
Neuplatnenie doplatku pri súbehu potrebuje aj odkaz na uchované písomné
oznámenie zamestnanca.

Na výkaze vyberte poisťovňu, zadajte číslo platiteľa pridelené touto
poisťovňou, bankový účet zamestnávateľa, dátum výplaty a odoslania, poradie
dávky a právnu formu. Vybraný účet musí patriť zamestnávateľovi; samotný
platný IBAN cudzej osoby nestačí.

Zadajte overený počet prihlásených osôb v tejto poisťovni a spolu vo všetkých
poisťovniach. Počet sa neodvodzuje od kladného poistného: aj osoba počas
celomesačnej PN môže zostať prihlásená pri nulovom poistnom.

## Zostavenie výkazu {#usage}

1. Vypočítajte a potvrďte mzdy podľa skutočného kalendára a schválených
   absencií. Priamy API create nevykonáva formulárové onchange; API klient
   musí naplniť natívne riadky dochádzky rovnako ako formulár alebo dávka miezd.
2. Otvorte **Mzdové výkazy → SK dávka514**, vyberte obdobie,
   **Publikovaný text514 (2023+)** a skontrolujte vstupy výkazu.
3. **Generovať** uloží prílohu v spoločnom výkazovom postupe a overí polia,
   dátumy, presnosť, členenie viet a súčty.
4. Súbor odošlite oprávneným kanálom poisťovne. **Označiť ako podané** iba
   eviduje túto skutočnosť; samo osebe nič neodosiela ani nepreukazuje prijatie.
5. Po evidencii pôvodného podania možno pripraviť úplný **Opravný** výkaz
   rovnakej firmy, obdobia a poisťovne. **Vrátiť do návrhu** umožní nové
   generovanie; presné pôvodné podané bajty zostanú v spoločnom archíve.

Vylúčený príjem z dôchodkovej dohody nesmie obsahovať zdravotné odvody.
Kontrola prebehne ešte pred vyradením pásky. Pri dostupnom uchovanom
podklade sa používa vtedajší profil a poisťovňa; dnešná úprava karty ich nemení.

## Obsah výkazu {#output}

Text používa UTF8, CRLF, desatinnú čiarku a oddeľovač `|` aj na konci každej
vety. Názov má napríklad `N5142606.001` alebo `O5142606.002`. Tri hlavičkové
vety majú10,13 a20 polí; každá veta poistenca má17 polí.

Obe skupiny zdravotného postihnutia sa sumarizujú samostatne. Zamestnanecké
poistné v riadku nezahŕňa doplatok; celková suma riadka zahŕňa zamestnávateľa,
zamestnanca aj doplatok. Zamestnanecký súčet v hlavičke už doplatok obsahuje.
Príjem pre OP, ostatný príjem, OP a zamestnanecký základ zostávajú oddelené.
Tabuľka zamestnancov zobrazuje rovnaký základ a dni ako text.

## Obmedzenia {#limitations}

Skontrolované [poistné kalendáre](module:l10n_sk_hr_payroll_base#health-calendar)
poskytujú skutočné poistné dni a výnimky minima cez uchovaný mzdový podklad.
Nahradený alebo dodatočne doplnený kalendár vyžaduje pred novým výkazom kontrolu
opravy mzdy. Pôvodné podané prílohy zostávajú dostupné. Kontrola kalendára
neprihlasuje zamestnanca ani neodosiela oznámenie601.

- Podporované je riadne **N** a úplné opravné **O**. Knižnica vie podpísané
  rozdielové hodnoty, no automatické **A** potrebuje osobitný overený opravný
  zdroj; formulár tento postup neponúka.
- Aktuálny TXT adaptér potrebuje jediný konsolidovaný zdroj za zamestnanca
  v kalendárnom mesiaci. Viaceré a nepravidelné opravné zdroje potrebujú
  príslušnú konsolidáciu, aby sa nezapočítali dvakrát.
  To platí aj pre samostatné HR karty s rovnakým identifikátorom poistenca;
  iné ID zamestnaneckého záznamu nevytvára ďalšieho poistenca.
- Staršia páska bez uchovaného podkladu potrebuje kontrolované prevzatie
  pôvodných údajov. Inštalácia dôkaz nevymýšľa.
- Počty prihlásených zostávajú overovanými vstupmi výkazu. Modul nevytvára
  registrácie v poisťovni ani sieťovo neodosiela podania.
- Samotný textový formát nepotvrdzuje správnosť všetkých poistných profilov.
  Zmeny počas mesiaca, ďalšie výnimky z minima a dodatočné príjmy potrebujú
  zodpovedajúce mzdové adaptéry.
- Starší XML používa pôvodnú výpočtovú cestu a kontrolu štruktúry. Pre nový
  postup s uchovanými zdravotnými podkladmi používajte publikovaný TXT.
