---
title: Kontrolný výkaz DPH / kontrolní hlášení CZ/SK
summary: Obrazovky a výpočet spoločné pre slovenský kontrolný výkaz DPH a české kontrolní hlášení — oddiely z zaúčtovaných dokladov, kontroly pred exportom, XML overené voči XSD a záznam o podaní.
verified: 19.0.2.4.0
---

## Na čo slúži {#purpose}

Na Slovensku aj v Česku podáva platiteľ popri daňovom priznaní aj prehľad
jednotlivých faktúr: slovenský **kontrolný výkaz DPH** (KV DPH) a české
**kontrolní hlášení** (KH). Tlačivá sú iné, práca je rovnaká — zaradiť každý
zaúčtovaný doklad s DPH do správneho oddielu, skontrolovať ho, vytvoriť
úradné XML a uschovať podanú kópiu.

Tento modul je spoločná časť: ponuka a formulár *Kontrolný výkaz DPH*,
priradenie oddielu každej položke denníka, prechod na zdrojové doklady,
export a záznam o podaní. Sám nič nepodáva. Oddiely, pravidlá zaradenia a
úradné XML dodáva modul krajiny:

- [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph) — slovenský KV DPH,
- [module:l10n_cz_kh](module:l10n_cz_kh) — české kontrolní hlášení.

Právny rámec, verzie tlačiva a pravidlá jednotlivých oddielov sú opísané na
ich stránkach. Modul nepoužíva výkazový engine Odoo Enterprise, takže v
edícii Community aj Enterprise funguje rovnako.

## Nastavenie {#setup}

Nainštalujte modul krajiny; tento sa nainštaluje s ním. Potom skontrolujte:

- **IČ DPH spoločnosti** je vyplnené. Každý export ho uvádza ako
  identifikáciu platiteľa a bez neho sa nespustí.
- **Dane s prenesením daňovej povinnosti sú rozpoznané.** Pravidlá zaradenia
  rozhodujú podľa príznaku dane *Prenos daňovej povinnosti*. Modul krajiny ho
  nastaví na daniach s prenesením daňovej povinnosti zo slovenskej alebo
  českej účtovej osnovy Odoo — pri inštalácii, pri každom načítaní osnovy pre
  novú spoločnosť a pri aktualizácii. Pri dani s prenesením, ktorú si
  vytvoríte sami, zaškrtnite **Prenos daňovej povinnosti** vo formulári dane
  (*Rozšírené možnosti*); pole sa zobrazuje pri slovenských a českých daniach.
- **Denník pre jeden oddiel.** Denník môže poslať všetky svoje riadky s DPH do
  jedného oddielu bez ohľadu na pravidlá: karta *Rozšírené nastavenia*
  denníka, blok *Kontrolný výkaz*, pole **Prepis sekcie kontrolného
  výkazu** — kód oddielu tak, ako ho uvádza tlačivo, napr. `D.1` pre denník
  pokladnice eKasa. Pri bežných denníkoch ho nechajte prázdne.
- **Partneri majú vyplnené IČ DPH.** Väčšina podrobných oddielov
  identifikuje druhú stranu podľa IČ DPH a export vymenuje každý doklad,
  ktorého partnerovi chýba tam, kde ho tlačivo vyžaduje.

V *Účtovníctvo → Konfigurácia → CZ/SK lokalizácia* sú dva zoznamy:

| Ponuka | Čo obsahuje |
|---|---|
| Verzie kontrolného výkazu | Jeden záznam na každú úradnú štruktúru tlačiva: platnosť, oddiely, XML šablónu a koreňový element, úradnú XSD, voči ktorej sa export overuje, a hranicu, ktorá oddeľuje podrobné riadky od súhrnných. Dodávajú ich moduly krajín; spravidla netreba nič meniť. |
| Typy kontrolného výkazu | Druhy podania podľa krajiny (slovenský *riadny / opravný / dodatočný*, český *řádné / opravné / následné / následné/opravné*) a kód, ktorý každý zapíše do XML. |

## Ako sa doklad dostane do oddielu {#sections}

Každá zaúčtovaná položka denníka s daňou dostane pri zaúčtovaní oddiel
kontrolného výkazu. O tom, ktorý, rozhodujú pravidlá modulu krajiny;
spoločné je toto:

- **Faktúry a dobropisy** majú smer (dodanie alebo prijatie) daný typom
  dokladu. **Interný doklad** s DPH sa zaradí podľa svojich daní, ak všetky
  smerujú rovnako (všetko predajné alebo všetko nákupné dane); zmiešaný
  doklad sa vynechá.
- **Prenesenie daňovej povinnosti sa testuje ako prvé**, takže samozdanené
  plnenie nikdy nepropadne do bežných oddielov.
- **Dane na základe platby** (*Daňová spôsobilosť: Na základe platby*) sa
  vykazujú, keď ich platba urobí splatnými, nie pri zaúčtovaní faktúry.
  Riadok opisuje faktúru — partnera a číslo —, ale nesie dátum a sumu platby,
  jeden riadok za každú platbu. Platba, ktorej spárovanie sa v tom istom
  období zruší, sa vynuluje.
- **Ktoré obdobie.** Uskutočnené plnenia sa vykazujú v období podľa
  *Dátumu zdaniteľného plnenia*, a ak chýba, podľa dátumu účtovania. Prijaté
  doklady sa vykazujú v období, v ktorom sa uplatňuje odpočet: podľa dátumu
  účtovania alebo podľa neskoršieho obdobia zapísaného na doklade
  (*Deklarované obdobie DPH*). Rovnaké pravidlo používajú moduly daňového
  priznania, takže sa zhodujú v tom, čo do obdobia patrí.
- **Dobropisy.** Dobropis vytvorený z faktúry je s ňou prepojený a výkaz
  z tohto prepojenia uvedie číslo pôvodnej faktúry. Pri dobropise vytvorenom
  ručne zadajte číslo opravovaného dokladu do poľa *Original document number*
  (karta *Ďalšie info*; popisok je v tejto verzii anglicky). Pole sa zobrazuje
  len na dobropisoch slovenskej alebo českej spoločnosti, ktoré nie sú
  prepojené s faktúrou.
- **Interné doklady s DPH** môžu uviesť, čo ich typ povedať nevie: na karte
  *Ďalšie info* **Smer DPH** (dodané alebo prijaté plnenie) a **Oprava DPH**
  (či ide o opravný doklad). Ak je *Oprava DPH* nastavená na opravu, zobrazí sa
  aj *Original document number*. Na faktúrach ich nechajte prázdne.
- **Po riadkoch** má zoznam položiek denníka dokladu dva voliteľné stĺpce:
  **Sekcia kontrolného výkazu** (uložený oddiel) a **IČ DPH pre kontrolný výkaz**,
  ktoré pre jeden riadok nahradí IČ DPH partnera (zahraničná pobočka
  s vlastným číslom).

Oddiel je uložený na položke denníka. Ak sa zmení niečo, čo pravidlá
nevidia — napríklad daňová krajina spoločnosti —, musí uložené oddiely
prepočítať správca; prepočet samotného výkazu nestačí.

## Príprava a podanie výkazu {#usage}

*Účtovníctvo → Výkazy → Zákonné výkazy → Kontrolný výkaz DPH*, potom *Nové*.

1. Vyplňte **spoločnosť**, **obdobie** (*Dátum od*, *Dátum do*) a **typ
   obdobia** (mesačne alebo štvrťročne); potom zvoľte **verziu** (ponúknu sa
   len verzie platné pre obdobie) a **typ výkazu**. Obdobie, ktoré verzia
   nepripúšťa (jej *Povoliť mesačné* / *Povoliť štvrťročné*), sa odmietne.
2. Kliknite na **Vypočítať**. Oddiely sa naplnia zo zaúčtovaných dokladov
   obdobia a výkaz prejde do stavu *Náhľad*. Každý oddiel má vlastnú kartu.
   Kým je výkaz v návrhu alebo náhľade, môžete počítať znova, koľkokrát
   treba; každý výpočet zostaví oddiely nanovo z účtovníctva.
3. **Kontrola.** Stĺpec ✓ ukazuje, či položky denníka za riadkom dávajú
   dokopy jeho základ a daň. Tlačidlo **Documents** na riadku otvorí tieto
   položky zoskupené podľa dokladov, so základom, sadzbou, DPH a odpočítanou
   DPH každej z nich — posledné dve sa líšia tam, kde je odpočítateľná len
   časť dane, napríklad pohonné hmoty na 50 %. Súhrnné riadky ukážu všetky
   doklady, ktoré sumarizujú. Chybný riadok opravte na doklade a počítajte znova.
   Kde to modul krajiny ponúka (slovenské oddiely okrem D.2), možno riadok
   opraviť aj vo výkaze: zaškrtnite **Prepísať** a upravte sumy; oprava
   prepočet prežije a znova sa použije na riadok s rovnakou identitou, a tá,
   ktorej riadok zmizol, sa oznámi v chatteri.
4. Kliknite na **Exportovať XML**. Pred vytvorením súboru export overí:
   - IČ DPH spoločnosti a kmeňové údaje, ktoré úradné tlačivo vyžaduje (modul
     krajiny vymenuje chybné doklady);
   - vecné pravidlá: podrobný riadok, ktorého daň nezodpovedá základu ×
     sadzbe, export zastaví, ak sa líši dvojnásobne a viac, a zdaniteľný
     riadok so základom bez dane ho zastaví vždy. Menšie rozdiely
     (zaokrúhlenie) a ostatné upozornenia ho nezastavia: zobrazia sa v žltom
     pruhu navrchu výkazu a v chatteri až do ďalšieho exportu.

   XML sa potom overí voči úradnej XSD uloženej na verzii a priloží sa k
   výkazu (*XML príloha*). Výkaz je v stave *Exportované*. Po novom výpočte
   môžete exportovať znova.
5. **Podajte XML** finančnej správe a kliknite na **Označiť ako podané**.
   Podaná kópia sa zmrazí (*Podané XML*, *Dátum podania*), pridá sa do
   histórie podaní a výkaz sa zamkne proti prepočtu aj exportu.
6. Označením ako podané sa zároveň otvorí záznam o **doručení**, ktorý drží
   priebeh doručenia a potvrdenky úradu (pozri
   [module:l10n_cssk_submission_base](module:l10n_cssk_submission_base)).
   Tlačidlo **Podať** otvorí nový a nechá zvoliť kanál: ručný kanál portálu
   zaznamená, že výkaz bol podaný ručne; s modulom
   [module:l10n_cz_epo](module:l10n_cz_epo) možno české podanie podpísať a
   odoslať priamo na EPO. Odznak v hlavičke ukazuje stav doručenia (popisy
   stavov sú v tejto verzii anglicky).

Výkaz označený ako podaný sa nedá vymazať. Tlačidlo *Porovnania* sa objaví,
keď bol výkaz porovnaný s účtovníctvom alebo s iným podaním.

## Opravy {#amendments}

- **Vrátiť do návrhu** znovu otvorí exportovaný alebo podaný výkaz. Smie to
  len administrátor účtovníctva. Už podané kópie zostávajú v histórii podaní.
- **Dodatočný / opravný** (slovenský výkaz) alebo **Opravné / následné**
  (české hlásenie) na podanom výkaze vytvorí nový návrh prepojený s ním
  (*Opravuje*). Zvoľte typ opravného podania, opravte účtovníctvo a potom
  počítajte a exportujte ako zvyčajne. Ako sa oprava vypočíta, závisí od
  krajiny: slovenský *dodatočný* kontrolný výkaz obsahuje len zmenené
  riadky, české *následné* kontrolní hlášení opakuje celé obdobie. Pozri
  stránky krajín.

**Historické podania** — výkazy prenesené z predchádzajúceho systému ako
záznam toho, čo sa podalo — majú stav *Historické podanie*. Nedajú sa
prepočítať, exportovať ani podať.

## Obmedzenia {#limitations}

- Tento modul sám nič nepodáva; podáva sa ručne na portáli alebo cez modul
  kanála podania.
- Oddiel položky denníka je uložený. Po zmene daňovej krajiny alebo po zmene
  samotných pravidiel ich musí správca prepočítať skôr, než sa výkazy
  počítajú znova.
- České karty oddielov *Prepísať* neponúkajú: české riadky vykazujú stĺpce
  podľa sadzieb, ktoré prepis nenesie. Opravte doklad.
- Pravidlá zaradenia sú najlepším možným odhadom a stránky krajín uvádzajú, čo
  treba ešte potvrdiť s účtovníkom. Každý výkaz pred podaním skontrolujte.
