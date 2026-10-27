---
title: INTRASTAT-SK — štatistické hlásenie o obchode s tovarom v rámci EÚ
summary: Mesačné hlásenie INTRASTAT-SK o tovare dovezenom z iných členských štátov a vyvezenom do nich, zostavené z faktúr ako súbor INSTAT XML na import do portálu finančnej správy — v edícii Community na module OCA, v Enterprise na vlastnom výkaze Intrastat od Odoo.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

Podnik, ktorého obchod s tovarom s inými členskými štátmi EÚ prekročí prah
oslobodenia, každý mesiac predkladá **hlásenie INTRASTAT-SK**: jedno za tovar
dovezený z iných členských štátov a jedno za tovar do nich vyvezený. Každá
položka obsahuje kód tovaru, partnerský členský štát, krajinu pôvodu, druh
obchodu, vlastnú hmotnosť, množstvo v doplnkových merných jednotkách,
fakturovanú hodnotu, druh dopravy a dodacie podmienky.

Odoo vie tieto údaje zozbierať z faktúr, slovenské hlásenie však nevyhotoví
ani jedna edícia: Community Intrastat vôbec nemá a výkaz Intrastat v Odoo
Enterprise pozná hlásenia iných štátov, no nie Slovenska. Táto skupina modulov
to dopĺňa. Vyhotoví oficiálnu **správu INSTAT XML** (schéma `instat62.xsd`),
ešte pred stiahnutím ju overí voči schéme a vy súbor naimportujete do portálu
INTRASTAT-SK.

Cesty sú dve, pre každú edíciu jedna, a z tých istých dokladov vytvoria ten
istý súbor:

| Edícia | Modul | Odkiaľ sa berú údaje |
|---|---|---|
| Community | tento modul | modul OCA `intrastat_product` (hlásenia v ponuke *Účtovníctvo → Výkazy → Intrastat*) |
| Enterprise | [module:l10n_sk_intrastat_ee](module:l10n_sk_intrastat_ee) | výkaz *Intrastat (Tovar)* a zúčtovanie daní od Odoo — pozri [Enterprise](#enterprise) |

Obe používajú ten istý generátor súboru,
[module:l10n_cssk_intrastat_base](module:l10n_cssk_intrastat_base) (pozri
[Spoločný generátor](#engine)).

## Právny rámec {#legal}

- **Rámec EÚ.** Intrastat je súčasťou európskych podnikových štatistík podľa
  [nariadenia (EÚ) 2019/2152](law:eu/reg/2019/2152). Jeho článok 13 ods. 1
  vymenúva, čo členský štát vývozu odovzdáva o každom vývoze tovaru v rámci
  EÚ, a to vrátane **identifikačného čísla pre DPH partnera** v členskom štáte
  dovozu a **krajiny pôvodu**. Preto položka vývozu nesie IČ DPH odberateľa a
  každá položka krajinu pôvodu.
- **Kto vykazuje a odkedy.** Spravodajskú povinnosť určuje Štatistický úrad
  SR, hlásenia sa podávajú cez portál finančnej správy
  `intrastat.financnasprava.sk`. Podľa *Príručky pre spravodajské jednotky,
  vydanie 2026*:
  - **prah oslobodenia** na rok 2026 je **1 000 000 eur**, sleduje sa zvlášť
    pre dovoz a zvlášť pre vývoz tovaru v rámci EÚ; subjekty s hlavnou
    činnosťou v SK NACE 01 – 03 alebo 10 – 12 majú nižšie prahy 200 000 eur
    (dovoz) a 400 000 eur (vývoz);
  - povinnosť na rok 2026 sa určuje podľa obchodu za obdobie od 1. októbra
    2024 do 30. septembra 2025, prípadne vzniká v mesiaci, v ktorom
    kumulatívna hodnota obchodu v roku 2026 prah prekročí;
  - hlásenie sa predkladá **do 15. kalendárneho dňa** po skončení
    sledovaného mesiaca, a ak pripadne na sobotu, nedeľu alebo sviatok, do
    najbližšieho pracovného dňa;
  - štvrťročný platiteľ DPH predkladá hlásenia **mesačne**.
- **Terminológia.** Štatistický úrad dnes hovorí o *dovoze tovaru v rámci
  EÚ* a *vývoze tovaru v rámci EÚ* namiesto pôvodného *prijatia* a
  *odoslania*. Obrazovky modulu OCA ešte používajú *Prijatie* a *Odoslanie*;
  ide o tie isté dva toky.

Modul nerozhoduje, či ste povinní vykazovať — prahy nesleduje. Toky nastavte
podľa svojej spravodajskej povinnosti.

## Nastavenie (Community) {#setup}

1. *Účtovníctvo → Konfigurácia → Nastavenia*, blok **Intrastat**: pre každý
   tok, ktorý vykazujete, nastavte **Prijatie** a **Odoslanie** na
   *Štandardná* alebo *Rozšírená*, pre tok bez povinnosti na *Exempt*
   (oslobodené; v slovenčine zatiaľ nepreložené). Voliteľne nastavte
   **Predvolený druh dopravy**. V Community bez plného účtovníctva sa
   koreňová ponuka volá *Fakturácia*.
2. Raz načítajte kódy tovaru: *Účtovníctvo → Konfigurácia → Intrastat →
   Load Intrastat Codes* (sprievodca OCA nainštalovaný s týmto modulom,
   ponúkne sa aj hneď po inštalácii) načíta kombinovanú nomenklatúru.
3. Na každom skladovom produkte vyplňte **Kód tovaru (KN)**, **Krajina
   pôvodu** a **hmotnosť** v kg. Produkt, ktorého kód tovaru má doplnkovú
   mernú jednotku (kusy, litre…), sa vykazuje aj v nej.
4. Spoločnosť musí mať vyplnené **IČ DPH**, inak sa súbor nevytvorí.
5. Na samotných faktúrach do a z EÚ pridáva modul OCA polia Intrastatu
   (transakcia, druh dopravy, krajina); skontrolujte ich pred zaúčtovaním.

## Mesačné hlásenie (Community) {#usage}

*Účtovníctvo → Výkazy → Intrastat → Hlásenie produktov Intrastat*, potom
*Nový*:

1. Zvoľte **rok**, **mesiac** a **typ** — *Prijatie* alebo *Odoslanie*. Každý
   tok je samostatné hlásenie.
2. **Generovať riadky z faktúr** zozbiera zaúčtované faktúry a dobropisy
   mesiaca. Okno s výsledkom vymenuje partnerov, produkty, jednotky a
   faktúry, ktoré nebolo možné použiť, a prečo. Ak sa nenájde nič, pole
   **Akcia** sa nastaví na *Nulové*.
3. Skontrolujte záložku **Transakcie** (riadok za každý riadok faktúry),
   opravte faktúry alebo produkty a riadky vygenerujte znova.
4. **Potvrdiť** zoskupí transakcie do riadkov hlásenia — jeden riadok za
   každú kombináciu vykazovaných údajov.
5. **Generovať XML súbor** vytvorí správu INSTAT XML, overí ju voči
   `instat62.xsd`, priloží ju k hláseniu a označí ho ako *Dokončené*. Súbor,
   ktorý schémou neprejde, sa odmietne s chybovým hlásením schémy.
6. Súbor stiahnite, naimportujte do portálu INTRASTAT-SK
   (`intrastat.financnasprava.sk`), skontrolujte a odošlite.

Čo súbor obsahuje:

- **Jedno hlásenie v súbore** pri prvom hlásení, tok `A` (dovoz) alebo `D`
  (vývoz), sledované obdobie `RRRR-MM`, typ hlásenia `1` (úplné), kód funkcie
  `O` (štandardné) — alebo `N` (nulové, bez položiek), keď je **Akcia**
  hlásenia *Nulové*.
- Spravodajskou jednotkou je vaša spoločnosť (IČ DPH, názov, ulica, PSČ,
  obec). Poradové číslo hlásenia (*declarationId*) je **Revízia** hlásenia,
  teda poradové číslo hlásenia za daný tok v sledovanom mesiaci.
- Za každú položku: kód tovaru (bez medzier), kód a množstvo doplnkovej
  mernej jednotky, partnerský členský štát, krajina pôvodu, vlastná
  hmotnosť, fakturovaná hodnota v mene spoločnosti, druh obchodu rozdelený
  na **kód A a kód B** (`11` sa vykáže ako A = 1, B = 1), druh dopravy,
  dodacie podmienky (Incoterm) a — len pri vývoze — IČ DPH partnera.
  Hmotnosť, množstvo a hodnota sa zaokrúhlia na celé čísla, ako to schéma
  vyžaduje.
- Doplnkové merné jednotky sa vykazujú oficiálnym kódom (`p/st`,
  `1 000 kWh`, `l alc. 100 %`…), nie názvom jednotky v module OCA.

Tlačidlo **Export do Excelu** na hlásení dá tie isté riadky ako tabuľku na
kontrolu.

### Opravy {#corrections}

Odoslané hlásenie sa opraví **revíziou**: hlásenie duplikujte (dostane
ďalšiu **Revíziu**), nastavte jeho **Akciu**, vygenerujte riadky a súbor
znova. INTRASTAT-SK čísluje hlásenia za mesiac pre každý tok 1, 2, 3 … a
ďalší súbor s ďalším číslom sa k mesiacu *pripočíta* (Príručka pre
spravodajské jednotky 2026, ods. 221–222), preto o obsahu súboru rozhoduje
akcia:

| Akcia | Čo súbor obsahuje |
|---|---|
| *Nahradiť* | zrušenie (kód funkcie `D`, bez položiek) každého hlásenia, ktoré za mesiac a tok ešte platí — podaných od poslednej skoršej revízie *Nahradiť* alebo *Nulové* — a za ním správne položky pod číslom revízie. Takto Príručka nahrádza hlásenie (ods. 229–230, príklad 19 b). |
| *Pripojiť* | revíziu ako ďalšie čiastkové hlásenie pod jej číslom, nič sa neruší. Musí obsahovať **len doplňované transakcie**: ostatné z revízie pred potvrdením odstráňte. |
| *Nulové* | zrušenia ako pri *Nahradiť* a potom nulové hlásenie (kód funkcie `N`). |

Zrušenie hlásenia nesie poradové číslo opravného hlásenia 1 — každé sa ruší
raz.

## Enterprise {#enterprise}

V Odoo Enterprise plní rovnakú úlohu
[module:l10n_sk_intrastat_ee](module:l10n_sk_intrastat_ee), postavený na
module `account_intrastat` od Odoo. Údaje berie z polí Intrastatu na
produktoch a faktúrach v Odoo; z modulu OCA nepoužíva nič.

- **Tlačidlo XML vo výkaze.** *Účtovníctvo → Výkazy → Dane a fiškálna
  oblasť → Intrastat (Tovar)* má pre slovenskú spoločnosť export **XML**.
  Zvoľte **jeden kalendárny mesiac** — dlhšie obdobie sa odmietne. Jeden
  súbor obsahuje dovoz aj vývoz ako dve hlásenia v jednej obálke (každý tok
  sa čísluje samostatne, obe sú teda hlásením číslo 1 za mesiac); tok, ktorý vo voľbách
  výkazu odznačíte, sa vynechá. Mesiac bez údajov sa odmietne, nepodá sa
  prázdny.
- **Zoskupenie.** Výkaz Odoo vracia riadok za každý riadok faktúry; modul
  sčíta riadky, ktoré sa zhodujú vo všetkých vykazovaných údajoch, do jednej
  položky, ako to INSTAT očakáva. Pri vývoze zostávajú riadky s rôznym IČ DPH
  odberateľa samostatnými položkami.
- **Zúčtovanie Intrastatu.** Modul pridá mesačné slovenské zúčtovanie
  *Intrastat* so splatnosťou 15 dní po skončení mesiaca, v ponuke
  *Účtovníctvo → Účtovníctvo → Závierka → Zúčtovanie daní*. Krok **Odoslať**
  otvorí okno s tlačidlom *Download XML* (stiahnuť XML) a postupom na
  portáli; potvrdením sa zúčtovanie označí ako dokončené. Pri uzamknutí
  zúčtovania sa XML priloží k nemu.
- Spoločnosť musí mať IČ DPH; ak chýba, otvorí sa formulár spoločnosti.
  Export spúšťajte so slovenskou spoločnosťou ako aktívnou.

Inštaluje sa len v edícii Enterprise a tento modul nepotrebuje.

## Výskyt vo výkazoch {#footprint}

Ak je spolu s modulom OCA nainštalovaný
[module:l10n_cssk_core](module:l10n_cssk_core), nainštaluje sa sám
[module:l10n_cssk_intrastat_footprint](module:l10n_cssk_intrastat_footprint)
a doplní Intrastat do **výskytu vo výkazoch** zaúčtovaného dokladu (pozri
[výskyt vo výkazoch](module:l10n_cssk_core#footprint)). Za každé hlásenie
Intrastat, ktoré prevzalo niektorý riadok dokladu, uvedie formulár
*Intrastat*, obdobie (`RRRR-MM`), tok a stav hlásenia (*Koncept*,
*Potvrdené*, *Dokončené*) s odkazom naň. Riadok vykázaný v pôvodnom aj v
opravenom hlásení uvedie obe.

Výskyt číta väzbu, ktorú si hlásenie uložilo pri generovaní riadkov.
Nerozhoduje, či by sa riadok vykazovať mal, preto **mesiac, za ktorý ešte
hlásenie nebolo vygenerované, neukáže nič**. Funguje pre slovenské aj české
hlásenia modulu OCA; výkaz Intrastat v Odoo Enterprise nečíta.

Odoo takýto prepájací modul nainštaluje len vtedy, keď sa inštaluje niektorá
z jeho závislostí. V databáze, kde boli oba moduly nainštalované skôr, než
prepájací modul vznikol, ho treba raz nainštalovať ručne.

## Spoločný generátor {#engine}

[module:l10n_cssk_intrastat_base](module:l10n_cssk_intrastat_base) obsahuje
kód spoločný pre obe edície a vlastné obrazovky nemá:

- generátor **INSTAT XML** pre Slovensko — jedno hlásenie v súbore pre
  Community, alebo jedna obálka s viacerými hláseniami pre Enterprise — s
  overením voči priloženej schéme `instat62.xsd`;
- generátor súboru **InstatOnline CSV** pre Česko, ktorý používa
  [module:l10n_cz_intrastat_oca](module:l10n_cz_intrastat_oca).

Závisí len od modulu `base`, takže sa nainštaluje automaticky s tým
modulom, ktorý ho potrebuje.

## Obmedzenia {#limitations}

- **Opravy jednotlivých položiek sa nevyhotovujú.** Revízia nahrádza celé
  hlásenia (zrušenie a nové podanie, pozri [Opravy](#corrections)); opravné
  hlásenie len so zmenenými položkami pod ich pôvodnými poradovými číslami
  (kód funkcie `M`) modul nevyhotoví. Oba postupy uvádza Príručka.
- Zrušenia predpokladajú, že každá skoršia revízia za mesiac bola podaná.
  Revízia, ktorá sa nikdy neodoslala, sa zruší rovnako; radšej ju vymažte,
  než by zostala v poradí.
- Vyhotoví sa len **úplné hlásenie** (typ `1`), aj keď je spoločnosť
  nastavená na *Štandardná*. Zjednodušený postup vykazovania nie je
  podporovaný.
- **Región** sa vykáže len vtedy, keď ho modul OCA dodá; slovenské kódy
  regiónov sa nedodávajú.
- Prahy oslobodenia sa nekontrolujú: modul podá to, čo mu zadáte.
- V Enterprise je každý export štandardným hlásením číslo 1 za každý tok;
  revízie neexistujú. Dva exporty za ten istý mesiac sú dva súbory
  s rovnakými číslami — opravy odoslaného hlásenia z Enterprise robte na
  portáli.
- Výsledkom je súbor na import do portálu; samotné podanie a jeho potvrdenie
  prebieha na portáli, mimo Odoo.
