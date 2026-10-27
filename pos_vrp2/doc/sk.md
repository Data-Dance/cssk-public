---
title: Miesto predaja — SK virtuálna registračná pokladnica (VRP2)
summary: Zaeviduje každú zaplatenú objednávku z Miesta predaja vo virtuálnej registračnej pokladnici finančnej správy (VRP 2) — predaj s položkami a sadzbami DPH, vrátenie tovaru k pôvodnému dokladu, fakturované objednávky ako úhradu faktúry — a vytlačí fiškálne údaje na doklad z pokladne.
verified: 19.0.5.1.1
---

## Na čo slúži {#purpose}

S týmto modulom je každá pokladnica v module Miesto predaja samostatnou
**virtuálnou registračnou pokladnicou** (VRP) finančnej správy. Keď pokladnica
zosynchronizuje zaplatenú objednávku, Odoo vystaví doklad vo VRP 2 a uloží k
objednávke jeho číslo, identifikátory a oficiálne PDF:

- bežný predaj sa zaeviduje ako **doklad s položkami** a sadzbou DPH každej
  položky;
- refundácia sa zaeviduje ako **vrátenie tovaru** k pôvodnému dokladu —
  refundácia celej objednávky je vo VRP stornom predaja;
- vrátený zálohovaný obal sa zaeviduje ako *vrátené obaly*;
- fakturovaná objednávka sa zaeviduje ako **úhrada faktúry**, rovnako ako v
  module [module:l10n_sk_vrp2_account](module:l10n_sk_vrp2_account).

Doklad vytlačený na pokladni nesie číslo dokladu VRP, kód pokladnice,
identifikátor dokladu, OKP a QR kód; oficiálne PDF je na jedno kliknutie.

Produkty a kategórie, ktoré pokladnica predáva, musia existovať aj v katalógu
jej pokladnice VRP; modul ich tam odošle (alebo ich z VRP načíta).

## Právny rámec {#legal}

[Zákon o evidencii tržieb](law:sk/2025/384), účinný od 1. januára 2026:

- Virtuálna registračná pokladnica je jedným z troch druhov pokladnice eKasa
  ([§ 2 písm. b)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-b)): služba
  finančného riaditeľstva poskytovaná výlučne prostredníctvom jeho mobilných
  aplikácií a klientskeho prostredia na jeho webovom sídle
  ([§ 2 písm. e)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-e)).
- Predávajúci musí každú *tržbu* — platbu prijatú na predajnom mieste v
  hotovosti alebo inými prostriedkami, ktoré nahrádzajú hotovosť, vrátane
  platby kartou a poukážkou
  ([§ 2 písm. u)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-u)) — zaevidovať
  bez zbytočného odkladu po jej prijatí
  ([§ 3 ods. 1](law:sk/2025/384#paragraf-3.odsek-1)).
- Pokladničný doklad treba vytlačiť a ihneď odovzdať kupujúcemu; *„iný doklad
  vyhotovený pokladnicou eKasa o prijatí tržby predávajúci nesmie kupujúcemu
  odovzdať“* — [§ 8 ods. 1](law:sk/2025/384#paragraf-8.odsek-1) vymenúva aj
  jeho povinné údaje.
- Pri vrátení platby za vrátený tovar, pri reklamácii či za zálohované palety,
  prepravky a obaly musí predávajúci tiež odovzdať pokladničný doklad; pri
  vrátení zálohovaných obalov bez pôvodného identifikátora dokladu —
  [§ 8 ods. 4](law:sk/2025/384#paragraf-8.odsek-4).
- Doklad o úhrade faktúry obsahuje číslo faktúry a žiadne položky ani DPH —
  [§ 8 ods. 2](law:sk/2025/384#paragraf-8.odsek-2).

**Ktorý doklad odovzdáte zákazníkovi**, je rozhodnutie na vás a vašom
poradcovi. Doklad z pokladne Odoo s fiškálnym blokom preberá identifikačné
údaje dokladu VRP, ale tlačí ho Odoo; oficiálnym dokladom je PDF samotnej VRP,
ktoré modul uloží a otvorí tlačidlom *VRP2 doklad (PDF)*.

## Nastavenie {#setup}

### 1. Priradenie daní (raz za spoločnosť) {#tax-mapping}

*Miesto predaja → Konfigurácia → Nastavenia*, blok **VRP2 – Virtuálna
registračná pokladnica**, **Priradenie daní VRP2**: ku každej sadzbe VRP, ktorú
používate, vyberte predajnú daň v Odoo (*Daň VRP2 0 %*, *5 %*, *19 %*,
*23 %*; polia *10 %* a *20 %* sú pre sadzby, ktoré už neplatia). Ponúkajú sa
len predajné dane aktuálnej spoločnosti.

Priradenie rozhoduje, ktoré produkty sa do VRP odošlú (produkt s nepriradenou
daňou nie) a akú daň dostane produkt načítaný z VRP.

### 2. Platobné metódy {#payment-methods}

Každá platobná metóda má za účtovným denníkom pole **Typ platidla VRP2**:
*Hotovosť*, *Platobná karta*, *Poukážky*, *Stravné poukážky* alebo *Iné*.
Predvyplní sa podľa denníka — pokladničný denník → *Hotovosť*, bankový →
*Platobná karta* —, preto skontrolujte poukážky a iné platidlá. Metóda bez typu
(napríklad na účet zákazníka) nie je platbou do pokladnice: objednávku
zaplatenú takou metódou nemožno zaevidovať a skončí v stave *Chyba VRP2*.

### 3. Pokladnica {#till}

*Miesto predaja → Konfigurácia → Miesta predaja*, otvorte pokladnicu. Blok
**Pokladničné doklady VRP2**:

| Pole | Čo robí |
|---|---|
| Zapnúť VRP2 | Pokladnica eviduje tržby vo VRP. |
| Evidovať automaticky | Doklad sa vystaví hneď, ako pokladnica zosynchronizuje zaplatenú objednávku (predvolené). Bez toho sa objednávky evidujú len ručne. |
| Zaokrúhľovať na 0,05 € | Zodpovedá prepínaču *Zaokrúhľovať na 5 centov* vo webovej aplikácii VRP: hotovostná časť platby sa zaokrúhli na 5 centov. |
| Zaokrúhľovanie hotovosti v Odoo | Zobrazí sa pri zapnutom zaokrúhľovaní; pozri nižšie. |
| Prihlasovacie meno VRP2, Heslo VRP2 | Prihlasovacie údaje **tejto** pokladnice z eKasa zóny na portáli finančnej správy. |

Potom kliknite na **Prihlásiť**. Riadok pod tlačidlami ukáže obchodné meno,
kód pokladnice (DKP) a udelený prístup (*Čítanie* / *Zápis*). Tlačidlo
**Načítať prihlasovacie údaje zo spoločnosti** prenesie do pokladnice
prihlásenie pokladnice spoločnosti (nastavenej podľa
[module:l10n_sk_vrp2_account](module:l10n_sk_vrp2_account#connection)) —
úhrady faktúr aj tržby tejto pokladnice potom pôjdu do tej istej pokladnice
VRP.

Pravidlá, ktoré modul vynucuje:

- **Jedno prihlásenie, jedna pokladnica.** Prihlásenie do VRP je jedna
  pokladnica; nemožno ho zadať pri dvoch pokladniciach v Odoo.
- **Zaokrúhľovanie hotovosti v Odoo sa musí zhodovať s VRP.** Pri zapnutom
  *Zaokrúhľovať na 0,05 €* potrebuje pokladnica zaokrúhľovanie hotovosti v
  Odoo s metódou zaokrúhlenia 0,05 *Nearest* (pridáva riadok zaokrúhlenia),
  použité len na hotovosť; zapnutím VRP2 alebo zaokrúhľovania sa doplní z
  existujúcej metódy 0,05. Pri vypnutom *Zaokrúhľovať na 0,05 €* nesmie Odoo
  zaokrúhľovať vôbec. Inak sa pokladnica neuloží — stav hotovosti by sa nikdy
  nezhodoval s uzávierkou pokladnice VRP (18,48 € v Odoo, 18,50 € vo VRP).

### 4. Katalóg {#catalogue}

VRP tlačí názvy položiek zo svojho katalógu a každá položka dokladu naň
odkazuje kódom služby. Po prihlásení máte pri pokladnici:

- **Odoslať do VRP2** — pošle katalóg tejto pokladne do jej pokladnice VRP:
  kategórie Miesta predaja najvyššej úrovne (pri zapnutom *Obmedziť
  kategórie* len tie, ktoré pokladňa ponúka) a každý produkt spoločnosti
  pokladne, ktorý je *Dostupné v POS*, dá sa predávať, má priradenú daň a patrí
  do niektorej z týchto kategórií, s cenou vrátane DPH, čiarovým kódom,
  internou referenciou a kategóriou. Produkt založený vo VRP dostane **Kód
  služby VRP2**. Odoslanie **odstráni len to, čo samo vytvorilo**: kategóriu
  alebo produkt, ktoré do pokladnice VRP dalo odoslanie z tejto pokladne a
  ktoré už pokladňa neponúka, tam zmaže (kategóriu) alebo deaktivuje
  (produkt). Všetko ostatné v pokladnici VRP — zadané v aplikácii VRP,
  odoslané inou pokladňou alebo inou databázou — zostane nedotknuté. Odoo si
  pre každú pokladňu pamätá, ktorá položka zodpovedá ktorej kategórii či
  produktu, takže dve pokladne majú každá vlastné kódy.
- **Načítať z VRP2** — naopak: z katalógu pokladnice VRP vytvorí alebo upraví
  kategórie a produkty v Odoo (názov, cena prepočítaná bez DPH, DPH, čiarový
  kód, interná referencia) ako služby dostupné v POS.

Na formulári produktu (karta *Miesto predaja*, skupina *VRP2*):

| Pole | Význam |
|---|---|
| Kód služby VRP2, Zosynchronizované s VRP2 | Nastaví prvé odoslanie katalógu. Každá pokladňa predáva pod kódom, ktorý produktu dala jej pokladnica VRP; produkt bez kódu na tejto pokladni sa na nej predať nedá. |
| Zálohovaný obal VRP2 | Zálohovaný obal; jeho vrátenie sa zaeviduje ako *vrátené obaly*. |
| Obľúbené vo VRP2 | Zobraziť medzi obľúbenými vo VRP. |
| Osobitná úprava VRP2 | Slovné označenie pri položkách s 0 % (oslobodené od dane, prenesenie daňovej povinnosti, cestovné kancelárie, umelecké diela, použitý tovar, zberateľské predmety a starožitnosti). Pozri [Obmedzenia](#limitations). |
| Poznámka VRP2 | Interná poznámka pre VRP, netlačí sa. |

Kategória najvyššej úrovne má **Krátky názov VRP2** pre záložky vo VRP; ak je
prázdny, použijú sa prvé dve písmená názvu.

Katalóg odošlite znova vždy, keď premenujete produkt, zmeníte jeho cenu či daň
alebo pridáte nový.

## Na pokladni {#usage}

Predávajte ako zvyčajne. Keď je objednávka zaplatená a zosynchronizovaná:

1. Odoo vystaví doklad vo VRP (pri zapnutom *Evidovať automaticky*).
2. Pred tlačou si pokladnica vyžiada výsledok a vytlačí fiškálny blok:
   **POKLADNIČNÝ DOKLAD č. 0019**, *Kód pokladnice*, *ID dokladu*, *OKP* a QR
   kód identifikátora dokladu.
3. Tlačidlo **VRP2 doklad (PDF)** na obrazovke dokladu otvorí oficiálne PDF z
   VRP.

Ak VRP požiadavku odmietne alebo nie je dostupná, **predaj sa nikdy
nezablokuje**: pokladník dostane upozornenie *Doklad VRP2 NEBOL vystavený*,
na doklade je namiesto fiškálneho bloku text *Doklad nebol zaevidovaný vo
VRP2* a objednávka sa označí ako *Chyba VRP2*. Pokladnica to sama neskúša
znova, lebo po vypršaní časového limitu môže VRP doklad už mať.

### Čo sa odošle {#receipt-content}

| Objednávka | Doklad vo VRP |
|---|---|
| predaj | s položkami: každý riadok s jednotkovou cenou s DPH, zľavou, množstvom, sadzbou DPH a kódom služby |
| refundácia objednávky zaevidovanej vo VRP | položky vrátenia s odkazom na pôvodný doklad a s názvom položky presne tak, ako ho VRP vytlačila; vrátené peniaze ako výdaj |
| vrátený zálohovaný obal bez predaja, na ktorý by sa odkazoval | položka *vrátené obaly* s kódom služby |
| fakturovaná objednávka | úhrada faktúry s číslom faktúry a platbami, bez položiek |

Platby sa vykážu podľa *Typu platidla VRP2* platobnej metódy. Na 5 centov sa
zaokrúhľuje len **hotovostná** časť; doklad, ktorým sa peniaze vracajú, sa
nezaokrúhľuje nikdy. Celkovú sumu dokladu si počíta VRP sama; ak sa od sumy v
Odoo líši zaokrúhlením dane (najviac o 5 centov), rozdiel pohltí najväčšia
bezhotovostná platba.

Objednávka sa odmietne a skončí v stave *Chyba VRP2*, ak:

- produkt nemá kód služby VRP2 (najprv odošlite katalóg);
- riadok má viac daní, daň, ktorá nie je percentuálna, alebo sadzbu DPH,
  ktorú VRP nepozná;
- vracia sa tovar bez odkazu na objednávku, na ktorej bol predaný (refundujte
  ho z tej objednávky v pokladni), alebo tá objednávka ešte nemá doklad VRP;
- vracia sa tovar z **fakturovanej** objednávky (stornujte namiesto toho jej
  doklad o úhrade faktúry), alebo ide o fakturovanú refundáciu;
- platobná metóda nemá typ platidla VRP2;
- bezhotovostné platby prevyšujú sumu objednávky a zároveň sa platilo aj v
  hotovosti.

## Objednávky v administrácii {#orders}

*Miesto predaja → Objednávky → Objednávky*: formulár objednávky má skupinu
**VRP2 Fiscalization** (popis zatiaľ bez prekladu) so *Stavom VRP2*
(*Nezaevidované*, *Zaevidované*, *Chyba*), číslom dokladu, UUID dokladu (to,
čo kóduje QR kód), dátumom, OKP a chybovou správou. **Tlačiť doklad VRP2**
stiahne oficiálne PDF.

**Zaevidovať vo VRP2** (len správcovia Miesta predaja) zaeviduje zaplatenú
objednávku, ktorá ešte zaevidovaná nie je — po chybe alebo pri vypnutej
automatickej evidencii. V zozname objednávok tá istá akcia spracuje viac
objednávok; každé zlyhanie sa zaznamená pri svojej objednávke bez vrátenia
ostatných a oznámenie povie, koľko sa zaevidovalo, zlyhalo a preskočilo.
Filtre **Chyba VRP2** a **Nezaevidované vo VRP2** nájdu objednávky, ktoré
treba riešiť, a *Stav VRP2* a *Číslo dokladu VRP2* si môžete zobraziť ako
stĺpce zoznamu.

**Skôr než po vypršaní časového limitu odošlete objednávku s chybou znova,
skontrolujte zoznam dokladov pokladnice na portáli VRP**: VRP môže doklad už
mať a opätovné odoslanie by tržbu zaevidovalo dvakrát.

## Obmedzenia {#limitations}

- **Osobitná úprava VRP2 sa odošle len pri produkte, ktorého daň VRP je 0 %**,
  tak ako to robí aplikácia VRP; pri inej sadzbe sa ignoruje. Pri oslobodenej
  položke musí doklad uvádzať údaj o oslobodení od dane
  ([§ 8 ods. 1 písm. n)](law:sk/2025/384#paragraf-8.odsek-1.pismeno-n)),
  preto ju pred odoslaním katalógu nastavte na každom produkte s 0 %.
- Položku načítanú z pokladnice VRP alebo odoslanú pred verziou 19.0.5.1.0
  odoslanie aktualizuje, ale nikdy ju nezmaže ani nedeaktivuje; keď sa už
  nepredáva, odstráňte ju v aplikácii VRP.
- Produkty s nulovou cenou sa odošlú bez ceny. Produkty načítané z VRP sa
  zakladajú ako služby; zoznam katalógu sa nestránkuje, takže veľmi veľký
  katalóg VRP sa môže načítať neúplne (upozornenie ide len do logu servera).
- Výmena poukážok za tovar, odpočet preddavkov, cudzia mena a predaj v mene
  iného predávajúceho nie sú podporované.
- Objednávka predaná, keď je pokladnica offline, sa vytlačí bez fiškálneho
  bloku a zaeviduje sa až po synchronizácii.
- Aktualizácia modulu existujúce pokladnice nepreverí: pokladnica so zapnutým
  VRP2 a nezhodným zaokrúhľovaním v Odoo funguje ďalej, kým sa jej nastavenia
  znova neuložia.
- Modul používa to isté rozhranie ako webová aplikácia VRP, ktoré finančná
  správa tretím stranám nezverejňuje. Zmena na jej strane môže modul vyradiť,
  kým sa neupraví.
