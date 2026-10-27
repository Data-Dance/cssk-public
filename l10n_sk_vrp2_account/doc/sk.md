---
title: SK virtuálna registračná pokladnica (VRP2) — úhrady faktúr
summary: Zaeviduje úhradu odberateľskej faktúry v hotovosti alebo kartou vo virtuálnej registračnej pokladnici finančnej správy (VRP 2) ako pokladničný doklad o úhrade faktúry, uchová oficiálny doklad v Odoo a v prípade potreby ho stornuje.
verified: 19.0.2.4.0
---

## Na čo slúži {#purpose}

Kto prijme úhradu vystavenej faktúry v hotovosti alebo platobnou kartou na
predajnom mieste, musí ju zaevidovať v pokladnici eKasa ako *pokladničný
doklad — úhrada faktúry*. Mnohí menší podnikatelia na to namiesto hardvérovej
pokladnice používajú bezplatnú **virtuálnu registračnú pokladnicu** (VRP)
finančnej správy.

Modul prepája Odoo s VRP 2, takže úhrady faktúr netreba prepisovať do webovej
aplikácie VRP:

- tlačidlo **Fiscalize in VRP2** na zaúčtovanej odberateľskej faktúre
  zaeviduje úhradu a stiahne oficiálny doklad vo formáte PDF;
- tá istá akcia v zozname faktúr to urobí pre viac faktúr naraz a vráti jeden
  PDF súbor;
- voliteľne doklad vystaví aj sprievodca *Platba* pri registrácii platby;
- tlačidlo **Storno (VRP2)** vydaný doklad stornuje;
- každý doklad zostane v Odoo s číslom, identifikátormi, oficiálnym PDF a
  údajmi vymenenými s VRP.

Modul iba eviduje úhradu vo finančnej správe. Zaznamenanie platby v Odoo
zostáva na vašom bežnom postupe a v účtovaní faktúry sa nič nemení.

Samotné pripojenie (prihlásenie, pokladnica spoločnosti) zabezpečuje modul
[module:l10n_sk_vrp2_base](module:l10n_sk_vrp2_base), ktorý sa nainštaluje
spolu s týmto modulom a je opísaný [nižšie](#connection). Predaj na pokladni
v predajni rieši modul [module:pos_vrp2](module:pos_vrp2).

Tlačidlá na formulári faktúry a akcia v zozname sa v tejto verzii zobrazujú po
anglicky (chýba ich preklad), ostatné popisy sú po slovensky.

## Právny rámec {#legal}

[Zákon o evidencii tržieb](law:sk/2025/384), účinný od 1. januára 2026:

- **Virtuálna registračná pokladnica** je služba zriadená finančným
  riaditeľstvom, poskytovaná výlučne prostredníctvom jeho mobilných aplikácií
  a klientskeho prostredia na jeho webovom sídle —
  [§ 2 písm. e)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-e). Je jedným z
  troch druhov pokladnice eKasa
  ([§ 2 písm. b)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-b)).
- **Čo treba evidovať.** *Tržbou* je platba prijatá na predajnom mieste v
  hotovosti alebo inými platobnými prostriedkami, ktoré nahrádzajú hotovosť,
  vrátane platby kartou; tržbou je aj preddavok alebo doplatok —
  [§ 2 písm. u)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-u). Predávajúci ju
  musí zaevidovať bez zbytočného odkladu po prijatí —
  [§ 3 ods. 1](law:sk/2025/384#paragraf-3.odsek-1).
- **Pokladničný doklad o úhrade faktúry** obsahuje číslo faktúry a **nesmie**
  obsahovať označenie tovaru či služby, základ dane, sadzby ani výšku DPH —
  [§ 8 ods. 2](law:sk/2025/384#paragraf-8.odsek-2). DPH je na faktúre. Preto
  majú doklady vystavené týmto modulom jediný riadok *Úhrada faktúry: &lt;číslo
  faktúry&gt;* a žiadnu rekapituláciu DPH.
- **Hotovosť sa zaokrúhľuje na 5 centov.** Doklad obsahuje zaokrúhlenie ceny
  — [§ 8 ods. 1 písm. p)](law:sk/2025/384#paragraf-8.odsek-1.pismeno-p) —,
  ktoré zákon o cenách (zákon č. 18/1996 Z. z., § 3 ods. 4) predpisuje len pre
  cenu platenú v hotovosti: zvyšok pod 2,5 centa nadol, od 2,5 centa nahor a
  cenu 1 alebo 2 centy na 5 centov. Platba kartou sa nezaokrúhľuje nikdy.
- **Odovzdanie dokladu.** Predávajúci musí kupujúcemu odovzdať pokladničný
  doklad ihneď po vytlačení; elektronicky ho môže zaslať, ak s tým kupujúci
  súhlasí a požiada o to pred vytlačením —
  [§ 8 ods. 1](law:sk/2025/384#paragraf-8.odsek-1). PDF, ktoré modul stiahne,
  je doklad samotnej VRP; vytlačte ho alebo ho so súhlasom kupujúceho pošlite
  tlačidlom *Odoslať doklad e-mailom*.

Či je konkrétna platba tržbou (bankový prevod napríklad nie je), posúdite vy a
váš účtovník; modul zaeviduje to, čo mu zadáte.

## Pripojenie pokladnice spoločnosti {#connection}

Jedno prihlásenie do VRP 2 patrí práve jednej pokladnici (s vlastným *kódom
pokladnice*, DKP). Úhrady faktúr sa evidujú na pokladnici **spoločnosti**,
ktorú nastavíte v *Účtovníctvo → Konfigurácia → Nastavenia* (v edícii
Community bez plného účtovníctva *Fakturácia → Konfigurácia → Nastavenia*),
blok **VRP2 — slovenská virtuálna registračná pokladnica**:

1. **Pripojenie VRP2** — zadajte *Prihlasovacie meno VRP2* a *Heslo VRP2*
   pokladnice z eKasa zóny na portáli finančnej správy a kliknite na
   **Prihlásenie**. Stav VRP2 sa zmení na *Pripojené*.
2. **Údaje o pokladnici VRP2** potom ukážu, čo o pokladnici hlási VRP: kód
   pokladnice (DKP), obchodné meno, DIČ, IČO a IČ DPH. Skontrolujte ich —
   presne tieto údaje ponesú doklady.
3. **Zaokrúhľovať na 0,05 €** — zodpovedá prepínaču *Zaokrúhľovať na 5
   centov* vo webovej aplikácii VRP. Ak je zapnutý, platba **v hotovosti** sa
   na doklade zaokrúhli na 5 centov a rozdiel sa vykáže ako zaokrúhlenie. VRP
   Odoo neoznámi, ako ho máte nastavený vo webovej aplikácii, preto ho tu
   nastavte rovnako. Predvolene zapnutý.
4. **Fiskalizovať úhrady faktúr** — sprievodca *Platba* ponúkne evidenciu vo
   VRP (pozri [nižšie](#on-payment)). Pod ním **Zaokrúhlenie hotovosti VRP2**
   určuje zaokrúhlenie hotovosti (*Účtovníctvo → Konfigurácia → Zaokrúhlenie
   hotovosti*), na ktorého účty výnosov a nákladov sa zaúčtuje 5-centový
   rozdiel zaokrúhlenej hotovostnej platby.

Relácia sa po vypršaní obnoví sama; tlačidlo **Odhlásiť** ju ukončí. Heslo a
token relácie vidia len administrátori. Oznámenie po prihlásení ukáže aj
prístup, ktorý VRP prihláseniu udelila (*Rola VRP2*: *Čítanie* alebo
*Zápis*); na vystavovanie dokladov treba prístup na zápis.

Pokladnice v module Miesto predaja majú **vlastné** pokladnice VRP a vlastné
prihlásenia, nastavené pri každej pokladni; pozri
[module:pos_vrp2](module:pos_vrp2#setup).

## Evidencia úhrady faktúry {#usage}

### Z faktúry {#from-invoice}

Na **zaúčtovanej odberateľskej faktúre** bez platného dokladu VRP kliknite na
**Fiscalize in VRP2**, zvoľte, ako zákazník zaplatil — **Hotovosť** alebo
**Karta**, nič nie je predvolené — a kliknite na **Fiskalizovať**. Modul
vystaví doklad a stiahne oficiálne PDF.

- Doklad je na **celú sumu faktúry**. Čiastočnú úhradu evidujte
  [cez sprievodcu Platba](#on-payment).
- Platba sa tým v Odoo nezaregistruje. Zaregistrujte ju ako zvyčajne — pri
  zaokrúhlenej hotovostnej platbe v zaokrúhlenej sume s odpisom rozdielu.

### Viac faktúr naraz {#mass}

V *Účtovníctvo → Zákazníci → Faktúry* označte faktúry a zvoľte *Akcie →
Fiscalize in VRP2* a pre všetky zvoľte *Hotovosť* alebo *Karta*. Dobropisy vo
výbere sa preskočia. Každá faktúra dostane vlastný doklad (celá suma) a vy
jedno PDF so všetkými.

Pred odoslaním sa skontrolujú všetky faktúry: ak niektorá nie je zaúčtovaná,
nie je odberateľskou faktúrou alebo už doklad má, neodošle sa nič. Ak VRP
odmietne niektorú faktúru až potom, čo ostatné už boli zaevidované,
zaevidované zostanú a zlyhanie sa zaznamená pri tej faktúre (doklad v stave
*Chyba* a správa v histórii), aby ste ju mohli zaevidovať znova.

### Pri registrácii platby {#on-payment}

Ak je zapnuté **Fiskalizovať úhrady faktúr** a spoločnosť je prihlásená,
sprievodca *Platba* na odberateľských faktúrach zobrazí za poľom *Poznámka*
dve ďalšie polia:

| Pole | Význam |
|---|---|
| Fiskalizovať vo VRP2 | Vystaviť doklad k registrovanej platbe. Predvolene zaškrtnuté. |
| Typ platby VRP2 | *Hotovosť* alebo *Karta*. Na 5 centov sa zaokrúhľuje len hotovosť. |

Doklad je na **sumu platby**, takže pri čiastočnej úhrade sa zaeviduje
zaplatená časť. Jedna faktúra, jeden doklad: pri viacerých faktúrach vypnite
*Zoskupiť platby*, inak sprievodca platbu odmietne.

Platba **v hotovosti** so zapnutým *Zaokrúhľovať na 0,05 €* sa zaúčtuje v sume,
ktorú zákazník skutočne odovzdá:

- Pri úhrade celej faktúry na 18,48 € v hotovosti sa platba zaregistruje na
  18,50 € a 0,02 € sa odpíše na účet výnosov *Zaokrúhlenia hotovosti VRP2*
  (pri zaokrúhlení nadol na jeho účet nákladov). Doklad uvedie 18,48 € ako
  cenu, 0,02 € ako zaokrúhlenie a 18,50 € ako zaplatenú sumu. Ak zaokrúhlenie
  hotovosti VRP2 nie je nastavené, sprievodca platbu odmietne skôr, než sa
  čokoľvek odošle.
- Čiastočná platba v hotovosti už musí byť násobkom 0,05 €, inak ju sprievodca
  odmietne.
- Viac faktúr naraz v hotovosti sprievodca prijme, len ak žiadnu netreba
  zaokrúhliť; inak ich zaplaťte po jednej. Ak zlyhá prvý doklad,
neuloží sa nič — ani platba, ani doklad. Ak zlyhá niektorý ďalší, platby
zostanú, zlyhanie sa zaznamená pri jeho faktúre a doklad vystavíte znova z
faktúry.

## Storno dokladu {#storno}

Tlačidlo **Storno (VRP2)** na faktúre s platným dokladom vystaví vo VRP
storno: nový doklad s jedným záporným opravným riadkom, ktorý odkazuje na
pôvodný doklad, a výdajom z pokladnice. Storno vráti presne sumu, ktorú
zaevidoval pôvodný doklad, vrátane prípadného zaokrúhlenia na 5 centov.
Pôvodný doklad sa označí ako *Zrušené* a faktúru možno zaevidovať znova.

Storno sa nedotkne faktúry ani žiadnej platby v Odoo. Dobropis nemožno
zaevidovať ako úhradu faktúry; stornujte namiesto toho pôvodný doklad.

## Doklady {#receipts}

*Účtovníctvo → Zákazníci → Doklady VRP2* obsahuje všetky doklady a faktúra ich
ukáže cez tlačidlo **Doklady VRP2**. V zozname faktúr si môžete zobraziť
skrytý stĺpec *Fiskalizované vo VRP2*.

Na doklade:

- **Typ dokladu**: *Úhrada faktúry* alebo *Storno*; stav: *Potvrdené*,
  *Chyba* alebo *Zrušené* (stornovaný).
- **Číslo dokladu**, **UUID dokladu** (identifikátor dokladu vo VRP, `V-…` —
  práve ten kóduje QR kód na oficiálnom doklade), **OKP** a *Fiskalizované
  dňa*.
- **Tlačiť oficiálny doklad** stiahne PDF z VRP; **Odoslať doklad e-mailom**
  požiada VRP, aby doklad poslala na e-mailovú adresu odberateľa.
- Odoslané a prijaté údaje sa na kontrolu uchovávajú na technickej karte.

Zostava *VRP2 Receipt* vytlačí prehľad z Odoo (*Pokladničný doklad — úhrada
faktúry*) s identifikáciou pokladnice a QR kódom identifikátora dokladu.
Kupujúcemu sa odovzdáva PDF samotnej VRP.

## Obmedzenia {#limitations}

- Evidencia z faktúry alebo zo zoznamu vždy zaeviduje **celú sumu faktúry**;
  samotnú platbu a odpis prípadného zaokrúhlenia hotovosti zaregistrujete
  sami.
- Tlačidlo *Fiscalize in VRP2* sa zobrazuje na každej zaúčtovanej
  odberateľskej faktúre, aj keď spoločnosť nie je k VRP pripojená; chyba sa
  ukáže až po kliknutí.
- Len odberateľské faktúry. Preddavky, poukážky, platby v cudzej mene a
  vklady či výbery hotovosti modul nerieši.
- Po vypršaní časového limitu môže VRP doklad už mať, hoci ho Odoo zaznamenalo
  ako neúspešný. Pred opätovným vystavením skontrolujte zoznam dokladov
  pokladnice na portáli VRP.
- Modul používa to isté rozhranie ako webová aplikácia VRP, ktoré finančná
  správa tretím stranám nezverejňuje. Zmena na jej strane môže modul vyradiť,
  kým sa neupraví.
