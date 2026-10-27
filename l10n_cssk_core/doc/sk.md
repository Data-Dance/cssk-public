---
title: CZ/SK lokalizácia — spoločné jadro
summary: Spoločný základ českých a slovenských štatutárnych modulov — nastavenia, daňové úrady, kontrola IČO, obdobie DPH dokladu, životný cyklus podania a porovnanie podaného s vypočítaným.
verified: 19.0.1.18.0
---

## Na čo slúži {#purpose}

Na tomto module stavia každý český a slovenský štatutárny modul lokalizácie —
daňové priznanie k DPH, kontrolný výkaz, súhrnný výkaz, účtovná závierka,
daňové priznanie k dani z príjmov. Zámerne ho inštalujete len zriedka:
nainštaluje sa s prvým z nich alebo s kompletnými sadami
[module:l10n_cz_datadance](module:l10n_cz_datadance) a
[module:l10n_sk_datadance](module:l10n_sk_datadance).

Priamo prináša:

- jeden **blok nastavení** pre celú lokalizáciu;
- zoznam **daňových úradov** a **typov subjektov**, ktoré používajú podania;
- **kontrolu IČO** pri českých a slovenských kontaktoch;
- **dátum zdaniteľného plnenia** v zoznamoch faktúr a dátum **Deklarované
  obdobie DPH** na dokladoch, voliteľne s preúčtovaním DPH;
- **výskyt vo výkazoch** pri zaúčtovanom doklade;
- **spoločný životný cyklus štatutárnych podaní** — výpočet, export, označenie
  ako podané, dodatočné podanie — a obrazovky **Podané vs vypočítané**;
- **mapovanie účtov do výkazov** pre účtové rozvrhy, ktoré nepoužívajú kódy
  vzorovej osnovy.

Závisí len od modulov `account` a `mail`, takže funguje v Community aj
Enterprise.

## Nastavenia {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Česká / slovenská
lokalizácia**:

| Nastavenie | Čo robí |
|---|---|
| Rozšírené účtovné menu (Community) | Nainštaluje modul OCA `account_usability` s menu, ktoré má Enterprise (hlavná kniha, denníky, saldá po splatnosti…). Len v Community. |
| Finančné výkazy (Community) | Nainštaluje modul OCA `account_financial_report`: hlavná kniha, obratová súvaha, partnerská kniha, saldá po splatnosti, denník. Len v Community. |
| Predvolený správca dane | Daňový úrad, ktorému sú podania adresované. Ponúkajú sa len úrady krajiny daňovej príslušnosti spoločnosti. |
| DPH priznaná v neskoršom období | Účet na preúčtovanie DPH — pozri [Preúčtovanie DPH](#vat-deferral). Prázdne = vypnuté. |
| Denníky koncoročnej uzávierky | Denníky so zápismi uzavretia a otvorenia účtovného roka (napr. *UZAVIERKA*, *OTVORENIE*). Ich doklady sa nezapočítavajú do účtovnej závierky, daňového priznania k dani z príjmov ani do finančných výkazov, aby uzavretie roka nevynulovalo súvahu a výsledovku. Prázdne, ak sa rok v tejto databáze neuzatvára. |

Kompletné sady pridávajú do tohto bloku vlastné prepínače, jeden na každý
voliteľný modul.

## Vaša spoločnosť {#company}

Vo formulári spoločnosti (*Nastavenia → Spoločnosti*) za poľom *Krajina*:

- **Daňový úrad** — to isté pole ako *Predvolený správca dane* vyššie.
- **Typ subjektu** — právnická alebo fyzická osoba, zo zoznamu
  [typov subjektov](#registries) krajiny spoločnosti; od neho sa odvíjajú
  niektoré tlačivá.

Zápis v obchodnom registri (*Spoločnosť zapísaná v obchodnom registri…*) patrí
do poľa Odoo **Obchodný register** (*Trade Registry*) na spoločnosti, ktoré
slovenská a česká lokalizácia tlačí na faktúru. Tento modul mal predtým
samostatné pole *Registračné údaje*, ktoré netlačil žiadny doklad; z formulára
zmizlo a pri aktualizácii sa jeho hodnota skopíruje do poľa *Obchodný
register*, ak bolo prázdne.

## Kontakty a IČO {#partners}

Pri kontaktoch s krajinou Česko alebo Slovensko:

- Pole registračného čísla sa volá **IČO** a zobrazuje sa aj pri fyzických
  osobách (Odoo ho inak ukazuje len pri spoločnostiach), lebo živnostník, ktorý
  nakúpi cez e-shop, vznikne ako osoba a IČO má.
- IČO sa **kontroluje pri uložení**: musí mať 6 až 8 číslic a platnú
  kontrolnú číslicu (vážený súčet modulo 11, rovnaký v oboch krajinách).
  Chybná hodnota sa odmietne so správou, ktorá menuje spoločnosť — názov firmy,
  IČ DPH či `Test` sa do poľa už zapísať nedajú.
- Platné IČO sa uloží **doplnené nulami na osem číslic**: z `580007` bude
  `00580007`.
- Pred poľom DPH je **Typ subjektu** na zatriedenie partnera v štatutárnych
  výkazoch.

Kontakty iných krajín sa nekontrolujú: nemecké `HRB 12345` sa prijme tak, ako
je.

## Daňové úrady a typy subjektov {#registries}

*Účtovníctvo → Konfigurácia → CZ/SK lokalizácia*:

- **Daňové úrady** — úrady, ktorým sa podania adresujú, každý so stálym kódom,
  kódom zapisovaným do XML (*Kód podania*) a pri českom územnom pracovisku aj
  s nadriadeným regionálnym úradom. Úrady nahrávajú české a slovenské
  štatutárne moduly; vy spravidla len jeden vyberiete. Zobrazujú sa úrady
  krajín daňovej príslušnosti spoločností práve **zvolených** v prepínači
  spoločností: kto pracuje naraz v českej aj slovenskej spoločnosti, vidí
  oboje.
- **Typy osôb / subjektov** — právnická osoba, fyzická osoba a podobne, pre
  každú krajinu, nahrané rovnako.
- **Mapovanie účtov do výkazov** — pozri [nižšie](#account-mapping). Vidia ho
  správcovia účtovníctva.

## Obdobie DPH dokladu {#vat-period}

### Dátum zdaniteľného plnenia

Zoznamy odberateľských a dodávateľských faktúr majú stĺpec **Dátum
zdaniteľného plnenia** (voliteľný, predvolene zobrazený) a vo vyhľadávaní
filter aj zoskupenie podľa neho. Deň dodania určuje obdobie DPH pri predaji.

### Deklarované obdobie DPH {#vat-period-declared}

Na faktúrach, dobropisoch a dodávateľských faktúrach je za dátumom splatnosti
pole **Deklarované obdobie DPH**: obdobie, v ktorom sa DPH vykáže, ak je iné
ako obvykle. V bežnom prípade ho nechajte prázdne.

Štatutárne výkazy zaradia doklad do obdobia takto:

| Doklad | Obdobie |
|---|---|
| Odberateľská faktúra, dobropis odberateľovi | *Deklarované obdobie DPH*, ak je vyplnené; inak dátum zdaniteľného plnenia; inak dátum účtovania |
| Dodávateľská faktúra, dobropis od dodávateľa, iný účtovný doklad | *Deklarované obdobie DPH*, ak je vyplnené; inak dátum účtovania |

Vyplňte ho pri faktúre, z ktorej odpočítavate daň neskôr, než je zaúčtovaná,
pri oprave priznávanej v neskoršom období alebo pri doklade zadanom
oneskorene. Právny základ je v časti [Právny rámec](#legal).

### Preúčtovanie DPH {#vat-deferral}

Keď *Deklarované obdobie DPH* pripadne na neskorší mesiac ako dátum účtovania,
priznanie vykáže daň neskôr, ale účet 343 ju nesie v mesiaci zaúčtovania a s
priznaním sa nezhoduje. Ak v nastavení *DPH priznaná v neskoršom období*
vyberiete účet, pri zaúčtovaní takého dokladu vzniknú aj dva interné doklady v
prvom denníku interných účtovných dokladov:

1. k dátumu účtovania sa daň presunie z účtu DPH na zvolený účet;
2. k deklarovanému dátumu sa vráti späť. Ak je ten dátum ešte v budúcnosti,
   doklad sa zaúčtuje automaticky, keď nastane.

Presúvajú sa len daňové riadky, ktoré vstupujú do uzávierky DPH. Doklady
nenesú dane ani daňové značky, takže ich žiadne priznanie nečíta. Pôvodný
doklad zobrazí **VAT deferral: *n* entries** s odkazom na ne; každý z nich
ukazuje pôvodný doklad v poli *VAT Deferral Of*. Vrátenie dokladu do návrhu,
jeho zrušenie alebo zmena deklarovaného dátumu tieto doklady zruší (a podľa
potreby vytvorí nové).

## Právny rámec {#legal}

*Deklarované obdobie DPH* existuje preto, lebo odpočítanie dane sa môže
uplatniť neskôr ako dodanie:

- **Slovensko** — platiteľ odpočíta daň najskôr v zdaňovacom období, v ktorom
  právo vzniklo, a najneskôr v poslednom zdaňovacom období toho kalendárneho
  roka, ak má faktúru do uplynutia lehoty na podanie priznania; inak v období,
  keď faktúru dostane —
  [§ 51 ods. 2 zákona o DPH](law:sk/2004/222#paragraf-51.odsek-2).
- **Česko** — nárok možno uplatniť najskôr za obdobie, v ktorom sú splnené
  podmienky (najmä daňový doklad), a najneskôr do konca druhého kalendárneho
  roka po roku, v ktorom vznikol —
  [§ 73 odst. 2 a 3 zákona č. 235/2004 Sb.](law:cz/2004/235).

Modul zaznamená obdobie, ktoré zvolíte. Či dodržíte tieto lehoty, nekontroluje.

## Výskyt vo výkazoch {#footprint}

Zaúčtovaná faktúra alebo účtovný doklad má tlačidlo **Výskyt vo výkazoch**
(len pre účtovníkov). Zobrazí riadky štatutárnych výkazov, do ktorých doklad
vstupuje — výkaz, kód riadku a popis — a ak už podanie za obdobie existuje,
aj podanie s odkazom naň. Prázdne podanie znamená, že výkaz za obdobie ešte
nebol vytvorený; riadky ukazujú, kam by doklad vstúpil. Ktoré výkazy sa
zobrazia, závisí od nainštalovaných modulov.

## Štatutárne podania: spoločný životný cyklus {#filings}

Daňové priznanie k DPH, kontrolný výkaz, súhrnný výkaz a ďalšie tlačivá sú
samostatné moduly, ale majú jeden spoločný životný cyklus:

| Krok | Tlačidlo | Čo sa stane |
|---|---|---|
| Návrh → Náhľad | *Vypočítať* | riadky sa vypočítajú z účtovníctva |
| Náhľad → Exportované | *Exportovať XML* | prebehnú kontroly obsahu, vytvorí sa XML, overí sa voči oficiálnej schéme a priloží sa. Chyba v kontrole export zastaví; **upozornenie** nie, ale zobrazí sa v oznámení, zapíše sa do chatu a zostane v poli *Upozornenia exportu* do ďalšieho exportu — prečítajte si ho pred podaním |
| Exportované → Podané | *Označiť ako podané* | exportované XML sa zmrazí ako **podaná kópia** (*Podané XML*), zaznamená sa dátum a podanie sa uzamkne: nedá sa už prepočítať, znova exportovať ani zmazať |
| | *Podať* | otvorí záznam o doručení na potvrdenky úradu — pozri [module:l10n_cssk_submission_base](module:l10n_cssk_submission_base) |
| Podané → Návrh | *Vrátiť do návrhu* | len správcovia účtovníctva; podaná kópia zostane zachovaná |
| | *Dodatočný / opravný* | pri podanom výkaze: vytvorí návrh dodatočného podania prepojený s pôvodným |

Každé XML, ktoré bolo kedy označené ako podané, zostáva v poli **História podaní**,
takže aj po vrátení, prepočte a novom podaní je pôvodne podaná kópia k
dispozícii. Číslo potvrdenky z portálu zapíšte do poľa **Referencia podania**.

**Historické podania.** Podanie prenesené z predchádzajúceho systému je v stave
*Historické podanie*: zaznamenáva, čo bolo skutočne podané, a nedá sa
vypočítať, exportovať ani podať. Dá sa k nemu vytvoriť dodatočné podanie a dá
sa porovnať s tým, čo za rovnaké obdobie vypočíta Odoo (*Porovnať s
vypočítaným*, pozri nižšie).

## Podané vs vypočítané {#comparisons}

*Účtovníctvo → Výkazy → Zákonné výkazy → Podané vs vypočítané*:

- **Porovnania** — jeden riadok za každé podanie a spôsob porovnania, s
  počtom zhodných riadkov, zistení, riadkov na posúdenie a so súčtami.
- **Riadky na posúdenie** — jednotlivé riadky všetkých porovnaní, filtrované
  na tie, ktoré čakajú na odpoveď.

Porovnanie vznikne tlačidlom na podaní. *Porovnať s vypočítaným* pri
historickom podaní ho postaví vedľa toho, čo Odoo vypočíta za rovnaké obdobie;
slovenská sada pridáva porovnanie podania s iným podaním a s účtom 343 (pozri
[module:l10n_sk_datadance](module:l10n_sk_datadance)). Pole **Porovnané voči**
hovorí, čo je v pravom stĺpci:

| Porovnané voči | Pravý stĺpec |
|---|---|
| Podanie, prepočítané | čo Odoo vypočíta za obdobie podania |
| Účtovníctvo | zostatok na účtoch, napr. 343 |
| Iné podanie | iné podanie za rovnaké obdobie |

Každý riadok má **výsledok**:

| Výsledok | Význam |
|---|---|
| Zhoduje sa | rovnaká suma na oboch stranách |
| Suma sa líši | rovnaký riadok, iná suma |
| Rovnaká suma, iný riadok | obe strany majú rovnakú sumu na rôznych riadkoch (zobrazené ako prepojená dvojica) |
| Má to len podanie / Počítame to len my | riadok je len na jednej strane |
| Slovníky nie sú namapované | strany používajú kódy riadkov, ktoré sa nedajú spárovať |
| Rozdiel je očakávaný | štrukturálny rozdiel, napr. kontrolný výkaz obsahuje menej ako priznanie |
| Informatívne, nie kontrola | len na informáciu, nikdy nie zistenie |

Zistenia vybavíte nastavením **stavu** riadku — *Opýtané účtovníka*,
*Podanie bolo správne*, *Podanie bolo nesprávne*, *Chyba je u nás*,
*Vysvetlené, bez zásahu* — a zápisom vyjadrenia účtovníka do **Poznámky**.
Odpoveď aj poznámka prežijú nové spustenie, ktoré aktualizuje len sumy.
Riadok, ktorý už nie je na žiadnej strane, sa nezmaže, ale označí ako *Už sa
neporovnáva*.

Stav porovnania sa odvíja od jeho riadkov — *Všetko sa zhoduje*, *Na
posúdenie*, *Rieši sa*, *Každý rozdiel zodpovedaný* — a ručne sa nastaviť
nedá. Keď porovnanie celé prejdete, kliknite na **Schváliť**; *Odvolať
schválenie* ho zruší. Nové spustenie schválenie nezruší.

## Mapovanie účtov do výkazov {#account-mapping}

Štatutárne výkazy čítajú zostatky podľa **kódu účtu**, podľa kódov vzorovej
účtovej osnovy. Osnova prevzatá z iného systému často používa vlastné
analytické účty — `461001` pre dlhodobý bankový úver, kde súvaha čaká
`461100` — a taký účet nepadne do žiadneho riadku.

*Účtovníctvo → Konfigurácia → CZ/SK lokalizácia → Mapovanie účtov do
výkazov* (správcovia účtovníctva) vám umožní ponechať osnovu a určiť, pod akým
kódom sa účet vykazuje:

| Pole | Význam |
|---|---|
| Účet | váš účet |
| Strana zostatku | *Akýkoľvek zostatok* alebo *Len debetný* / *Len kreditný zostatok* — napr. bankový účet vykázaný ako krátkodobý bankový úver, len keď je v debete banky (prečerpaný) |
| Vykazovaný kód | kód, pod ktorým ho výkaz číta, napr. `461200`; čistý kód bez medzier a operátorov |

Mapovanie podľa strany zostatku platí len pre súvahové zostatky (ku dňu); vo
výsledovke si účet ponechá vlastný kód. Účet môže mať buď jedno mapovanie
*Akýkoľvek zostatok*, alebo debetné a/alebo kreditné, nie oboje. Mapovanie
platí rovnako pre náhľad, XML aj rozpad riadku.

## Obmedzenia {#limitations}

- Kontrola IČO overí, že číslo je správne utvorené, nie že existuje; overenie
  v registri robia iné moduly.
- *Deklarované obdobie DPH* sa nekontroluje voči zákonným lehotám.
- Preúčtovanie DPH ide do prvého denníka interných účtovných dokladov
  spoločnosti; denník sa vybrať nedá. Spoločnosť bez neho dostane pri
  zaúčtovaní chybu.
- *Upozornenia exportu* sa zobrazia v chate podania a v oznámení po exporte;
  formuláre podaní ich zatiaľ neukazujú ako pruh nad formulárom.
