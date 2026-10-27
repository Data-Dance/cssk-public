---
title: CZ/SK odsúhlasenie zostatkov a zápočet (saldokonto)
summary: Odsúhlasenie otvorených pohľadávok a záväzkov partnera k dátumu s PDF na podpis a zápočet, ktorý vzájomné pohľadávky a záväzky vyrovná v účtovníctve.
verified: 19.0.1.2.1
---

## Na čo slúži {#purpose}

Dva bežné doklady saldokonta v česko-slovenskom účtovníctve:

1. **Odsúhlasenie zostatkov.** Uložený doklad so zoznamom otvorených
   pohľadávok a záväzkov partnera k zvolenému dátumu, ktorý vytlačíte, pošlete
   partnerovi a označíte ako dohodnutý alebo sporný. Používa sa najmä ku koncu
   roka ako podklad k inventarizácii pohľadávok a záväzkov.
2. **Zápočet.** Dohoda alebo jednostranný prejav, ktorým sa to, čo dlhuje
   partner vám, započíta proti tomu, čo dlhujete vy jemu. Pri zaúčtovaní
   vytvorí zápočtový účtovný zápis a spáruje faktúry.

Modul potrebuje len modul Odoo `account` a
[module:l10n_cssk_core](module:l10n_cssk_core), takže funguje v edícii
Community aj Enterprise. Pracovať s ním môžu používatelia s oprávnením
*Účtovníctvo* (*Show Full Accounting Features*) alebo *Správca* účtovníctva;
mazať doklady môže len správca.

## Právny rámec {#legal}

**Inventarizácia.** Potvrdenie od partnera nevyžaduje ani jeden zákon o
účtovníctve, oba však ukladajú overiť pohľadávky a záväzky k súvahovému dňu a
ich skutočný stav sa zisťuje dokladovou inventúrou:

- **Slovensko:** [§ 29 ods. 1 a 2](law:sk/2002/431#paragraf-29.odsek-1) a
  [§ 30 ods. 1](law:sk/2002/431#paragraf-30.odsek-1) zákona o účtovníctve —
  inventarizáciou účtovná jednotka overuje, či stav v účtovníctve zodpovedá
  skutočnosti, vykonáva ju ku dňu zostavenia účtovnej závierky a pri
  záväzkoch a majetku, pri ktorom nemožno vykonať fyzickú inventúru, sa
  skutočný stav zisťuje dokladovou inventúrou.
- **Česko:** [§ 29 odst. 1 a § 30 odst. 1 písm. b) zákona o
  účetnictví](law:cz/1991/563) — periodická inventarizácia k okamihu
  zostavenia účtovnej závierky, pri záväzkoch a majetku, ktorého existenciu
  nemožno zistiť vizuálne, dokladová inventúra.

Odsúhlasenie zostatkov podpísané partnerom je bežným podkladom tejto
dokladovej inventúry.

**Zápočet.**

- **Slovensko:** podľa [§ 580 Občianskeho zákonníka](law:sk/1964/40#paragraf-580)
  vzájomné pohľadávky rovnakého druhu zaniknú započítaním, pokiaľ sa kryjú, ak
  niektorý z účastníkov urobí prejav smerujúci k započítaniu; zánik nastane
  *„okamihom, keď sa stretli pohľadávky spôsobilé na započítanie“*.
  [§ 581 ods. 2](law:sk/1964/40#paragraf-581.odsek-2) okrem iného vylučuje
  započítanie premlčaných pohľadávok a nesplatnej pohľadávky proti splatnej;
  podľa [§ 581 ods. 3](law:sk/1964/40#paragraf-581.odsek-3) ich možno
  započítať dohodou. Medzi podnikateľmi Obchodný zákonník dopĺňa, že
  započítať možno len pohľadávky uplatniteľné na súde
  ([§ 358](law:sk/1991/513#paragraf-358)), nesplatnú pohľadávku proti
  splatnej len voči dlžníkovi, ktorý nie je schopný plniť svoje peňažné
  záväzky ([§ 359](law:sk/1991/513#paragraf-359)), a pohľadávky v rôznych
  menách len vtedy, ak sú voľne zameniteľné, pričom rozhoduje kurz dňa, keď sa
  stali spôsobilými na započítanie ([§ 362](law:sk/1991/513#paragraf-362)).
- **Česko:** podľa [§ 1982 občianskeho zákonníka](law:cz/2012/89) môže každá
  strana vyhlásiť započítanie vzájomných pohľadávok rovnakého druhu, len čo
  môže požadovať uspokojenie vlastnej pohľadávky a plniť vlastný dlh;
  pohľadávky zanikajú v rozsahu, v akom sa kryjú, k okamihu, keď sa obe stali
  spôsobilými na započítanie. [§ 1987](law:cz/2012/89) pripúšťa len
  pohľadávky uplatniteľné pred súdom, ktoré nie sú neisté ani neurčité, a
  [§ 1991](law:cz/2012/89) dovoľuje stranám dohodnúť započítanie, ktoré by
  jednostranné vyhlásenie nedosiahlo.

Z toho vychádzajú dva režimy modulu: **dvojstranná dohoda** o vzájomnom
započítaní, ktorú podpíšu obe strany, a **jednostranný zápočet**, teda prejav
doručený druhej strane, ktorý možno použiť len pri pohľadávkach spĺňajúcich
zákonné podmienky. Modul tieto podmienky nekontroluje.

## Odsúhlasenie zostatkov {#confirmation}

*Účtovníctvo → Zákazníci → Odsúhlasenia zostatkov*, potom *Nové*:

| Pole | Význam |
|---|---|
| Partner | Spoločnosť (nie kontaktná osoba). Zahrnú sa otvorené položky všetkých jej kontaktov. |
| Kontakt | Osoba, ktorej je odsúhlasenie určené. |
| K dátumu | Dátum, ku ktorému sa zostatok odsúhlasuje, zvyčajne 31. 12. |
| Typ potvrdenia | *Iba pohľadávky*, *Iba záväzky* alebo *Pohľadávky a záväzky*. |

Kliknite na **Vypočítať**. Karta *Otvorené položky* sa naplní všetkými
zaúčtovanými položkami partnera na účtoch pohľadávok a záväzkov, ktoré boli
otvorené **k zvolenému dátumu**: úhrada alebo spárovanie s neskorším dátumom
sa pripočíta späť, takže odsúhlasenie k 31. 12. zostavené vo februári ukáže
aj faktúru uhradenú v januári, a to v plnej sume, ktorá bola otvorená k
31. 12. *Pohľadávky spolu*, *Záväzky spolu* a *Čistý zostatok* (kladný =
partner dlhuje vám) sa počítajú z riadkov.

Riadky sú **snímkou**: majú vlastnú kópiu čísla dokladu, dátumov a sumy, takže
odsúhlasenie zostane také, aké ste odoslali, aj keď sa účtovníctvo neskôr
zmení. Opätovným **Vypočítať** ho zostavíte znova; to ide v stave *Návrh* a
*Odoslané*.

Postup:

1. **Tlač** (zobrazí sa, keď odsúhlasenie nie je návrhom) vytvorí PDF
   *Odsúhlasenie zostatkov (saldokonto)* s oboma spoločnosťami, zoznamom
   položiek, súčtami a dvoma podpisovými riadkami. **Označiť ako odoslané**
   zmení stav na *Odoslané*; e-mail neodošle — PDF pošlite sami, napríklad z
   chatteru.
2. Keď partner odpovie, kliknite na **Dohodnuté** alebo **Sporné**.
3. Ak partner rozporuje jednotlivé položky, označte na týchto riadkoch
   **Blokované**. V PDF zostanú, sivé a s poznámkou *(sporné)*, do súčtov sa
   však nezapočítajú.

**Vytvoriť odsúhlasenia zostatkov** (*Účtovníctvo → Zákazníci*) ich vytvorí
hromadne: zvoľte spoločnosť, dátum, typ a prípadne partnerov — ak ich
nevyberiete, dostane ho každý partner s otvorenou položkou k tomu dňu — a
vypočítané odsúhlasenia sa otvoria v zozname.

PDF je česky alebo slovensky podľa krajiny spoločnosti, s angličtinou, a
strany označuje neutrálne (*Účtovná jednotka* a *Partner*), lebo pri
odsúhlasení záväzkov je vaša spoločnosť dlžníkom.

Dohodnuté alebo sporné odsúhlasenie je zmrazené: riadky sa nedajú meniť a
doklad sa nedá vymazať, len zrušiť. **Nastaviť na návrh** ho uvoľní.
Odsúhlasenia sa číslujú `SALDO/<rok>/0001`.

## Zápočet {#netting}

*Účtovníctvo → Dodávatelia → Dohody o započítaní*, potom *Nové*:

1. Zvoľte **Partnera**, **Dátum dohody**, menu (*Currency*) a **Režim
   zápočtu** — *Dvojstranná dohoda* alebo *Jednostranný zápočet*. Voliteľne
   zvoľte **Zúčtovací denník**; bez neho sa použije prvý denník typu Rôzne
   spoločnosti.
2. Na kartách **Pohľadávky** a **Záväzky** pridajte otvorené účtovné položky,
   ktoré sa majú započítať, a v stĺpci *Suma na zápočet* koľko z každej.
   Započítať možno aj časť položky, nie však viac, než je jej otvorená suma.
   Ponúkajú sa len zaúčtované otvorené pohľadávky a záväzky partnera zo
   zápočtu.
3. Zaúčtovať možno, len keď sa súčet pohľadávok rovná súčtu záväzkov (*Je
   vyrovnané*); táto suma je *Suma zápočtu*.

Položka patrí na stranu podľa toho, kto komu dlhuje, nie podľa účtu: otvorený
dobropis odberateľovi je váš dlh voči partnerovi a patrí medzi záväzky,
dobropis od dodávateľa medzi pohľadávky.

Postup sa líši podľa režimu:

| Režim | Kroky |
|---|---|
| Dvojstranná dohoda | Potvrdiť → Označiť ako odoslané → Odsúhlasené protistranou → Zaúčtovať |
| Jednostranný zápočet | Potvrdiť → Označiť ako odoslané → Zaúčtovať (bez podpisu protistrany) |

**Vytvoriť zápočet** (*Účtovníctvo → Dodávatelia*) zápočet navrhne: zvoľte
partnera, dátum a menu a sprievodca načíta otvorené položky partnera a
rozdelí najvyššiu vyrovnanú sumu, od najstarších položiek.

Riadky sa dajú meniť len v stave *Návrh*. PDF *Započítanie (zápočet)* z ponuky
*Tlač* má podľa režimu nadpis dohody s dvoma podpisovými riadkami alebo
oznámenia o jednostrannom započítaní s jedným.

**Zaúčtovať** najprv overí, či je každá položka stále otvorená aspoň v
dohodnutej sume (medzitým mohla prísť úhrada), potom vytvorí účtovný zápis s
dátumom dohody, ktorý každú pohľadávku zaúčtuje na stranu Dal a každý záväzok
na stranu Má dať v sume na zápočet, a každú položku spáruje s jej vlastným
riadkom zápočtu, takže čiastočné zápočty sa zachovajú presne. Zápočty sa
číslujú `ZAP/<rok>/0001`.

**Cudzia mena.** V mene spoločnosti možno započítať každú otvorenú položku v
jej zaúčtovanej sume. V cudzej mene len položky v tejto mene; sumy sú v nej,
zápočtový zápis sa zaúčtuje kurzom ku dňu dohody a rozdiel oproti kurzu
každej faktúry sa pri spárovaní zaúčtuje ako kurzový rozdiel.

**Zrušiť storno-zápisom** pri zaúčtovanom zápočte zruší spárovanie a
zápočtový zápis stornuje, takže každá položka je znova otvorená presne ako
predtým. Zaúčtovaný zápočet sa nedá vymazať.

## Obmedzenia {#limitations}

- Modul nekontroluje zákonné podmienky jednostranného zápočtu (splatnosť,
  uplatniteľnosť na súde, vylúčenia) ani súhlas partnera; to je na vás.
- Zápočtový zápis má dátum dohody a v cudzej mene kurz toho dňa. Samotné
  pohľadávky zanikajú okamihom, keď sa stali spôsobilými na započítanie
  (§ 580 Občianskeho zákonníka, v Česku § 1982 občanského zákoníku), čo PDF
  uvádza; ak chce účtovník zápis k tomuto dňu, zvoľte ho ako dátum dohody.
- Obe PDF sa riadia krajinou spoločnosti — české znenie a DIČ pre českú
  spoločnosť, inak slovenské znenie a IČ DPH — s angličtinou vedľa. Znenie
  si pred prvým použitím dajte skontrolovať.
- PDF odsúhlasenia ukazuje sumy len v mene spoločnosti.
- *Označiť ako odoslané* len zmení stav; nič sa neodošle e-mailom.
