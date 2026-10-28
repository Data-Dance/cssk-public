---
title: Daňové priznanie k dani z príjmov PO (CZ/SK)
summary: Obrazovka, na ktorej sa pripravuje daňové priznanie k dani z príjmov právnických osôb (DPPO) — výsledok hospodárenia z účtovníctva, úpravy účtovníka, výpočet dane, XML overené proti schéme a zaúčtovanie splatnej dane.
verified: 19.0.1.5.8
---

## Na čo slúži {#purpose}

Daňové priznanie právnickej osoby vychádza z výsledku hospodárenia v
účtovníctve a ten sa potom upravuje na daňový základ: pripočítajú sa náklady,
ktoré zákon neuznáva, odpočítajú sa výnosy, ktoré sa nezdaňujú, odpočíta sa
daňová strata z minulých rokov a až potom sa vypočíta daň. Modul na túto
prácu vytvorí za každé zdaňovacie obdobie jeden záznam — **daňové
priznanie** — a urobí za vás to, čo je číslo a vzorec:

- **výsledok hospodárenia** pred zdanením sčíta zo zaúčtovaných položiek
  denníka za obdobie;
- **úpravy** zadáva účtovník po riadkoch;
- riadky, ktoré sú len výpočtom z iných riadkov, sa prepočítajú;
- priznanie sa exportuje do XML, overí proti oficiálnej schéme tlačiva a
  označí ako podané.

Tento modul je spoločná časť. Vlastné tlačivo nemá: riadky, pravidlá a
štruktúru XML dodáva národný modul —
[module:l10n_sk_dppo](module:l10n_sk_dppo) pre slovenské daňové priznanie k
dani z príjmov právnických osôb a
[module:l10n_cz_dppo](module:l10n_cz_dppo) pre české *přiznání k dani z
příjmů právnických osob* (DPPDP9). Nainštalujte jeden z nich, tento modul sa
nainštaluje s ním. Bez národného modulu ponuka existuje, ale nie je z čoho
vybrať verziu tlačiva.

## Priznanie krok za krokom {#usage}

*Účtovníctvo → Výkazy → Zákonné výkazy → Daň z príjmov (DPPO)*, potom *Nové*.

1. **Hlavička.** Zvoľte obdobie (*Dátum od*, *Dátum do*), potom **Verziu** —
   vzor tlačiva. Ponúknu sa len verzie krajiny, v ktorej je spoločnosť
   daňovo usadená, platné aspoň pre časť obdobia. Potom **Typ výkazu**:
   riadne, opravné alebo dodatočné priznanie, ako ich pomenúva národný modul.
   Uložte. Ak obdobie nepokrýva žiadna verzia — spravidla preto, že správca
   dane vzor pre ten rok ešte nezverejnil — upozornenie to oznámi hneď po
   zadaní dátumov a priznanie sa nedá uložiť.
2. **Vypočítať.** Vyplní kartu *Riadky* a presunie priznanie do stavu
   *Náhľad*. Pri každom riadku je uvedený jeho druh:

   | Druh | Odkiaľ sa hodnota berie |
   |---|---|
   | Výsledok hospodárenia (VZS) | Zostatok uvedených účtov za obdobie, len zo zaúčtovaných dokladov. |
   | Rozdiel účtovných a daňových odpisov majetku | Rozdiel účtovných a daňových odpisov za obdobie z modulu daňových odpisov `account_asset_tax`, ak je nainštalovaný; inak 0. |
   | Súhrn | Vzorec z iných riadkov, prepočíta sa vždy. |
   | Ručné | Zadávate vy. |

3. **Zadajte úpravy.** V riadku zaškrtnite **Prepis** a sumu napíšte do
   stĺpca *Ručná hodnota*. Rovnako opravíte aj vypočítaný riadok. Potom
   znova kliknite na **Vypočítať**: prepísané riadky si vašu sumu ponechajú a
   všetky riadky, ktoré z nich vychádzajú, sa z nej prepočítajú. Ručný riadok
   bez prepisu sa pri každom výpočte vynuluje, preto políčko zaškrtnite vždy.
4. **Skontrolujte čísla.** Pri riadku počítanom z účtov ukáže tlačidlo s
   lupou **Doklady** položky denníka, z ktorých vznikol, zoskupené podľa
   účtov, a stĺpec ✓ hovorí, či sa s riadkom stále zhodujú. Ak nie —
   zvyčajne preto, že sa po poslednom výpočte zaúčtovali ďalšie doklady —
   hlavička ukáže červené tlačidlo **Nesúladné riadky**; keď všetko sedí,
   zelené **Riadky súhlasia**. Stĺpec *Odvodenie* ukazuje vzorec
   vypočítaného riadku alebo *manual input* pri ručnom.
5. **Exportovať XML.** Vytvorí súbor, overí ho proti oficiálnej schéme (XSD)
   uloženej pri verzii tlačiva a priloží ho k priznaniu; stav sa zmení na
   *Exportované*. Ak schéma súbor odmietne alebo spoločnosť nemá vyplnené
   DIČ ani IČ DPH, nič sa nepriloží a hlásenie povie prečo. Verzia bez
   schémy export odmietne vždy.
6. **Podajte priznanie** na portáli finančnej správy a potom kliknite na
   **Označiť ako podané**. Exportovaný súbor sa uloží ako podaný exemplár,
   zaznamená sa dátum a stav sa zmení na *Podané*. Tlačidlo **Podať** otvorí
   záznam o doručení podania, kde sa uchová potvrdenie o podaní; pri označení
   ako podané sa takýto záznam otvorí automaticky.

Podané priznanie sa nedá vymazať. **Vrátiť do konceptu** ho znova otvorí —
smie to len používateľ s právom *Účtovníctvo / Správca* — a všetky podané exempláre zostanú
zachované: každý podaný súbor ostane pri priznaní, aj keď ho nahradí nový.

## Opravné a dodatočné priznanie {#amendments}

Pri podanom priznaní vytvorí tlačidlo **Dodatočné / opravné** nové priznanie
v koncepte, prepojené s pôvodným (*Opravuje*), so skopírovanými riadkami a
vašimi prepismi ako východiskom. Zmeňte mu *Typ výkazu* na opravné alebo
dodatočné, opravte, čo sa zmenilo, a znova ho vypočítajte. Riadky, ktoré
porovnávajú obe priznania, vyplní národný modul, ak ich jeho tlačivo má (v
slovenskom priznaní poslednú známu daň a riadky rozdielu).

## Zaúčtovanie splatnej dane {#provision}

Po výpočte priznania ukáže blok **Splatná daň z príjmov (591/341)** daň z
riadku, ktorý verzia tlačiva určuje ako daň na zaúčtovanie (v slovenskom
priznaní r. 1050, v českom ř. 340), a tlačidlo **Zaúčtovať splatnú daň**
ju zaúčtuje:

- na ťarchu účtu splatnej dane z príjmov (prvý účet, ktorého kód začína na
  **591**) a v prospech účtu dane z príjmov (prvý začínajúci na **341**);
- k poslednému dňu obdobia, v denníku zvolenom v bloku, inak v prvom
  denníku typu *Rôzne*. Účty možno v bloku zvoliť aj ručne (*Účet daňového
  nákladu*, *Účet daňového záväzku*), ak ich osnova pod 591 a 341 nemá.

Nejde o rezervu, ale o splatnú daň z príjmov, ktorou sa uzatvára výkaz
ziskov a strát a súvaha za rok. **Stornovať splatnú daň** ju
zruší opačným zápisom. Tlačidlo sa zobrazí, len ak je daň vyššia ako nula a
len pri verziách tlačiva, ktoré riadok dane určujú.

**Upozornenia exportu.** Kontroly, ktoré export nezastavia, sa zobrazia v
žltom pruhu navrchu formulára a v chatteri až do ďalšieho exportu.

## Obmedzenia {#limitations}

- **Daňové úpravy sú na vás.** Modul vypočíta výsledok hospodárenia a
  aritmetiku; nerozhoduje, ktoré náklady sú daňovo neuznateľné ani ktoré
  výnosy sú oslobodené.
- Výsledok hospodárenia počíta len **zaúčtované** doklady. Po zaúčtovaní
  posledných uzávierkových zápisov priznanie prepočítajte.
- Zaúčtuje sa **celá** daň z priznania. Pri dodatočnom priznaní zaúčtujte
  rozdiel sami: ďalšie zaúčtovanie by daň započítalo dvakrát.
- Účty pre zaúčtovanie dane sa hľadajú podľa začiatku kódu (591, 341). Ak
  ich účtová osnova nemá, zvoľte ich v bloku splatnej dane.
- Verzie tlačiva, ich riadky ani sadzby nemajú vlastnú obrazovku. Zmeniť ich
  môže len správca s technickým prístupom.
- Samotné podanie prebieha na portáli finančnej správy; *Označiť ako podané*
  ho len zaznamená.
