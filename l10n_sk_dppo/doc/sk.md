---
title: SK daňové priznanie k dani z príjmov PO (DPPO)
summary: Slovenské daňové priznanie k dani z príjmov právnických osôb — všetky vzory od roku 2013, výsledok hospodárenia z účtovníctva, výpočet dane so sadzbou a minimálnou daňou daného roka a XML overené proti schéme finančnej správy.
verified: 19.0.1.11.1
---

## Na čo slúži {#purpose}

Každá slovenská obchodná spoločnosť podáva raz ročne daňové priznanie k
dani z príjmov právnických osôb (DPPO). Tento modul dodáva tlačivo na
obrazovku daňového priznania z modulu
[module:l10n_cssk_income_tax_base](module:l10n_cssk_income_tax_base), ktorého
návod opisuje spoločný postup — vytvorenie priznania, výpočet, prepis
riadkov, export, označenie ako podané a zaúčtovanie dane. Táto stránka
opisuje to, čo je slovenské:

- riadky každého vzoru tlačiva od roku 2013 do roku 2025 so schémou (XSD)
  finančnej správy ku každému;
- **r. 100**, výsledok hospodárenia pred zdanením, vypočítaný z účtovníctva;
- **výpočet dane** od r. 100 po daň na úhradu, so sadzbou a minimálnou daňou
  daného roka, pri vzoroch, pri ktorých ho modul počíta;
- riadky dodatočného daňového priznania;
- s modulom [module:l10n_sk_fs](module:l10n_sk_fs) aj kontrolu, či r. 100
  súhlasí s účtovnou závierkou (pozri [nižšie](#zavierka)).

Samotné daňové úpravy — ktoré náklady sú daňovo neuznateľné, ktoré výnosy
sú oslobodené, odpočet daňovej straty — zadáva účtovník.

## Právny rámec {#legal}

Odkazy sú na [zákon o dani z príjmov](law:sk/2003/595).

- **Východisko.** Daňovník účtujúci v sústave podvojného účtovníctva
  vychádza z výsledku hospodárenia —
  [§ 17 ods. 1 písm. b)](law:sk/2003/595#paragraf-17.odsek-1.pismeno-b). To
  je r. 100.
- **Sadzba.** Pri právnickej osobe je sadzba dane zo základu dane zníženého
  o daňovú stratu podľa
  [§ 15 písm. b) bodu 1](law:sk/2003/595#paragraf-15.pismeno-b.bod-1)
  **10 %**, ak daňovník dosiahol zdaniteľné príjmy (výnosy) neprevyšujúce
  100 000 eur, **24 %**, ak prevyšujú 5 000 000 eur, inak **21 %**. Podľa
  [§ 52zzzb ods. 4](law:sk/2003/595#paragraf-52zzzb.odsek-4) sa tieto
  sadzby prvýkrát použijú za zdaňovacie obdobie, ktoré sa začína najskôr
  1. 1. 2025. Za rok 2024 platilo 15 % do 60 000 eur a 21 % nad túto sumu.
- **Minimálna daň.**
  [§ 46b ods. 2](law:sk/2003/595#paragraf-46b.odsek-2) ju určuje podľa
  zdaniteľných príjmov: 340 eur do 50 000 eur, 960 eur do 250 000 eur,
  1 920 eur do 500 000 eur a 3 840 eur nad túto sumu. Znižuje sa na
  polovicu pri daňovníkovi s dostatočným podielom zamestnancov so
  zdravotným postihnutím ([ods. 3](law:sk/2003/595#paragraf-46b.odsek-3)),
  za zdaňovacie obdobie kratšie ako 12 mesiacov sa počíta ako 1/12 za každý
  kalendárny mesiac ([ods. 6](law:sk/2003/595#paragraf-46b.odsek-6)) a
  neplatí sa v prípadoch podľa
  [ods. 7](law:sk/2003/595#paragraf-46b.odsek-7), napríklad za prvé
  zdaňovacie obdobie novej spoločnosti. Kladný rozdiel medzi minimálnou daňou
  a vypočítanou daňou možno započítať najviac v troch nasledujúcich
  obdobiach ([ods. 5](law:sk/2003/595#paragraf-46b.odsek-5)). Za
  zdaňovacie obdobie, ktoré začína najskôr 1. 1. 2026, pribudlo piate
  pásmo: 11 520 eur nad 5 000 000 eur
  ([§ 52zzzj ods. 5](law:sk/2003/595#paragraf-52zzzj.odsek-5)).
- **Daňová licencia.** Do roku 2017 určoval § 46b daňovú licenciu 480,
  960 alebo 2 880 eur podľa postavenia platiteľa DPH a obratu. Podľa
  [§ 52zk](law:sk/2003/595#paragraf-52zk) sa naposledy uplatnila za
  zdaňovacie obdobie končiace 31. 12. 2017, a pri hospodárskom roku za
  obdobie končiace v priebehu roka 2018.
- **Daňová strata.** Odpočítať ju možno počas najviac piatich bezprostredne
  nasledujúcich zdaňovacích období, najviac do 50 % základu dane, u
  mikrodaňovníka do výšky celého základu —
  [§ 30 ods. 1](law:sk/2003/595#paragraf-30.odsek-1). Riadok 410.
- **Malé sumy.** Daň na úhradu vypočítaná v daňovom priznaní sa neplatí, ak
  nepresiahne 5 eur — [§ 46](law:sk/2003/595#paragraf-46).
- **Lehota.** Daňové priznanie sa podáva a daň sa platí do troch
  kalendárnych mesiacov po uplynutí zdaňovacieho obdobia —
  [§ 49 ods. 2](law:sk/2003/595#paragraf-49.odsek-2); oznámením správcovi
  dane ju možno predĺžiť podľa
  [§ 49 ods. 3](law:sk/2003/595#paragraf-49.odsek-3).

## Nastavenie {#setup}

Modul nemá nastavenia. Pred prvým priznaním skontrolujte údaje spoločnosti
(*Nastavenia → Užívatelia & spoločnosti → Spoločnosti*), lebo z nich sa
vypĺňa hlavička XML:

| Pole spoločnosti | Kam ide |
|---|---|
| DIČ (z modulu [module:l10n_sk_base](module:l10n_sk_base)), ak je prázdne, tak *IČ DPH* bez „SK“ | DIČ |
| *IČO* | IČO |
| Názov spoločnosti | obchodné meno (prvých 75 znakov) |
| Ulica / PSČ / Mesto / Krajina | sídlo — číslo je číslo na konci poľa *Ulica* (*Hlavná 1141/11*); *Ulica2* sa použije, len ak obsahuje iba číslo |
| Kód NACE kontaktu spoločnosti ([module:partner_nace](module:partner_nace)) | SK NACE (0, ak je prázdny) |
| *Právna forma* kontaktu spoločnosti (`l10n_sk_trade_registry`) | právna forma |

Voliteľné moduly, ktoré priznanie dopĺňajú:

- **`account_asset_tax`** (daňové odpisy). Tabuľka B sa potom vyplní
  z daňovej evidencie majetku a riadky **r. 150** (účtovné odpisy vyššie
  ako daňové — pripočítateľná položka) a **r. 250** (daňové odpisy vyššie
  ako účtovné — odpočítateľná položka) sa z nej odvodia — pozri
  [Tabuľky A a B](#tables). Bez neho zostane tabuľka B prázdna, pokiaľ ju
  nezadáte.
- **[module:l10n_sk_vat_registration](module:l10n_sk_vat_registration).**
  Daňová licencia závisela od toho, či bola spoločnosť k poslednému dňu
  zdaňovacieho obdobia platiteľom DPH. S týmto modulom rozhoduje dátum
  registrácie, a ak nie je vyplnený, kategória registrácie; bez neho, alebo
  ak nie je vyplnené ani jedno, sa za platiteľa považuje každá spoločnosť s
  vyplneným *IČ DPH*.

## Vzory tlačiva {#versions}

Pri vytváraní priznania zvoľte **Verziu** pre obdobie. Ponúkne sa každý vzor,
ktorého platnosť sa s obdobím prekrýva, takže pri hospodárskom roku cez dva
kalendárne roky sa ponúknu dva — zvoľte ten, ktorý pre dané obdobie určuje
finančná správa. Čo modul vypočíta, závisí od vzoru:

| Verzia | Obdobia | Modul vypočíta |
|---|---|---|
| DPPO 2013, DPPO 2014 | 2013; 2014 | len r. 100 a tabuľky A/B (r. 130, 150, 250) |
| DPPO 2015 | 2015 – 2016 | výpočet dane, sadzba 22 %, daňová licencia |
| DPPO 2017, 2018, 2019 | po jednom roku | výpočet dane, sadzba 21 %, daňová licencia, kde ju § 52zk ešte uplatňuje (pozri nižšie) |
| DPPO 2020, 2021, 2022 | 2020; 2021; 2022 – 2023 | len r. 100 a tabuľky A/B (r. 130, 150, 250) |
| DPPO 2024 | 2024 | výpočet dane, 15 % / 21 %, minimálna daň |
| DPPO 2025 | 2025 | výpočet dane, 10 % / 21 % / 24 %, minimálna daň |

Pri vzoroch „len r. 100“ zadávate všetky ostatné riadky sami, vrátane dane.

Pri vzoroch 2018 a 2019 je r. 810 nulový, ak nejde o hospodársky rok
končiaci v roku 2018: [§ 52zk](law:sk/2003/595#paragraf-52zk) daňovú
licenciu pre každé neskoršie obdobie zrušil. Riadky na tlačivách ostali,
lebo licenciu zaplatenú za roky 2015 – 2017 možno ďalej započítať podľa
§ 46b ods. 5; tento zápočet zadajte sami.

Publikovaný vzor **MF/014309/2026-721** už má natívny výpočtový register.
Jeho zákonná platnosť sa riadi lehotou na podanie; elektronická schéma je
samostatný publikačný krok (pozri [publikovaný vzor](#published-2026)).

Sadzby a sumy minimálnej dane sú uložené pri každom vzore, nie v programe.
Vzor, ktorému chýba sadzba, výpočet odmietne a sadzbu si nedomýšľa.

## Výpočet priznania {#usage}

**r. 100 — výsledok hospodárenia pred zdanením.** Zostatok účtových tried 5
a 6 za obdobie bez dane z príjmov (591, 592, 595) a bez prevodu podielov na
výsledku hospodárenia spoločníkom (596). Počítajú sa len zaúčtované doklady.

**Riadky, ktoré zadávate** (zaškrtnite *Prepis*, zadajte sumu, znova
vypočítajte):

- pripočítateľné položky r. 110 – 180 a odpočítateľné položky r. 210 – 290,
  okrem r. 130, 150 a 250, ktoré vychádzajú z [tabuliek A a B](#tables);
- r. 302 – 308, r. 320, r. 330 (ďalšie úpravy základu dane) a **r. 410**,
  odpočet daňovej straty;
- r. 501 – 503, r. 610 (úľava na dani), r. 710 (zápočet dane zaplatenej v
  zahraničí), r. 1040 (zaplatené preddavky), r. 1060 – 1071 (daň z
  osobitných základov);
- **r. 560**, zdaniteľné príjmy (výnosy). Predvyplní sa zostatkom triedy 6,
  ktorý zahŕňa aj výnosy, ktoré nie sú zdaniteľné; ak sa líši, opravte ho,
  lebo podľa neho sa určuje sadzba aj minimálna daň.

**Riadky, ktoré modul vypočíta** pri vzoroch s výpočtom dane:

| Riadok | Výpočet |
|---|---|
| r. 200 | r. 110 + 130 + 140 + 150 + 170 + 180 |
| r. 300 | r. 210 + 220 + … + 290 |
| r. 301 | r. 100 + r. 200 − r. 300 |
| r. 310 | r. 301 + 302 + … + 306 − r. 307 + r. 308 |
| r. 400 | r. 310 − r. 320 − r. 330 |
| r. 500 | r. 400 − r. 410, najmenej 0 |
| r. 510 | r. 500 − r. 501 − r. 502 − r. 503 |
| r. 550 | sadzba podľa r. 560 |
| r. 600 | r. 510 × r. 550, ak je r. 510 kladný |
| r. 700, r. 800 | r. 600 − r. 610, potom − r. 710 |
| r. 810 | minimálna daň (alebo daňová licencia) podľa r. 560, pri kratšom období 1/12 za mesiac |
| r. 820, r. 830 | kladný rozdiel medzi r. 810 a r. 800, na riadku, ktorý naň vzor používa |
| r. 900 | r. 810, ak minimálna daň prevyšuje daň |
| r. 1050 | vyššia z hodnôt r. 800 a r. 810 |
| r. 1080 | r. 1050 + 1060 + 1070 + 1071 |
| r. 1100 / r. 1101 | r. 1080 − r. 1040: daň na úhradu, ak presahuje 5 eur, alebo preplatok ako záporná suma |

Sumy sa zaokrúhľujú matematicky na centy. Prepísaný riadok sa nikdy
neprepočíta, takže ktorýkoľvek z nich môžete prevziať — polovičnú minimálnu
daň podľa § 46b ods. 3 alebo oslobodenie podľa ods. 7 zadáte prepisom
r. 810. Zápočet minimálnej dane zaplatenej v minulých rokoch (tabuľka
r. 830 a riadky za ňou až po r. 1000) modul nepočíta.

Zaúčtovanie dane opísané v
[návode k spoločnému modulu](module:l10n_cssk_income_tax_base#provision)
účtuje r. 1050; je dostupné len pri vzoroch 2024 a 2025.

## Tabuľky A a B {#tables}

III. časť tlačiva rozpisuje dva riadky tela: **tabuľka A** (*Položky, ktoré
nie sú daňovými výdavkami*) je rozpis r. 130, **tabuľka B** (*Odpisy
hmotného majetku*) zdôvodňuje r. 150 a 250. Každý riadok oboch tabuliek je
riadkom priznania označeným tabuľkou a číslom riadka: `a06` je riadok 6
tabuľky A, `b02` riadok 2 tabuľky B.

| Riadok | Obsah (vzory od roku 2015) | Výpočet |
|---|---|---|
| a01 – a16 | položky tabuľky A; a16 = ostatné položky | zadávate |
| a17 | úhrn | a01 + … + a16 |
| b01 | účtovné odpisy hmotného majetku | z evidencie majetku alebo zadávate |
| b02 | daňové odpisy pred b04, bez b05 | z evidencie majetku alebo zadávate |
| b03 | neuplatnená časť ročného odpisu prenajatého majetku (§ 19 ods. 3 písm. a)) | zadávate |
| b04 | odpisy nezahrnuté pre prerušenie odpisovania (§ 22 ods. 9) | z evidencie majetku alebo zadávate |
| b05 | pomerná časť ročného odpisu pri predaji (§ 22 ods. 12) | z evidencie majetku alebo zadávate |
| b06 | odpisy zahrnuté do základu dane | b02 − b03 − b04 + b05, najmenej 0 |
| **r. 130** | | a17 |
| **r. 150** | | b01 − b06, ak je kladný |
| **r. 250** | | b06 − b01, ak je kladný |

Vzory 2013 a 2014 majú kratšiu tabuľku A (a15 je úhrn a01 – a14)
a štvorriadkovú tabuľku B s daňovými odpismi v b01 a účtovnými v b02; tam
r. 150 = b02 − b01 a r. 250 = b01 − b02, ak sú kladné.

S modulom [module:account_asset_tax](module:account_asset_tax) sa b01, b02,
b04 a b05 načítajú z daňovej evidencie za majetok na účte hmotného majetku
(akýkoľvek okrem 01x). b04 je odpis, ktorý by pripadol na rok prerušenia,
b05 celé mesiace evidencie v roku predaja pri majetku označenom podľa § 22
ods. 12. b03 zadávate vždy sami. Pri b03 rovnom 0 sú r. 150 a 250 rozdielom
účtovných a daňových odpisov za celú spoločnosť ako doteraz.

Každý z týchto riadkov sa dá prepísať, aj odvodené. Ak tabuľka obsahuje
nejakú hodnotu, prepísaný r. 130, 150, 250, a17 alebo b06 s ňou musí
súhlasiť: export priznanie s rozdielom odmietne, rovnako ako tlačivo
finančnej správy. Priznanie, ktoré má r. 150 zadaný priamo v tele
a tabuľku B prázdnu, sa exportuje ako doteraz.

Riadok tabuľky, ktorý nikto nevyplnil, zostane v súbore XML prázdny.

## Dodatočné daňové priznanie {#amendments}

Vytvorí sa tlačidlom **Dodatočné / opravné** z podaného priznania (pozri
[návod k spoločnému modulu](module:l10n_cssk_income_tax_base#amendments)).
*Typ výkazu* nastavte na *Dodatočné*. Pri výpočte sa riadky poslednej známej
dane vyplnia z predchádzajúceho priznania a riadky rozdielu ako *toto
priznanie mínus predchádzajúce*:

| Posledná známa | Rozdiel | Zdroj |
|---|---|---|
| r. 1120 | r. 1130 | r. 1050, daň alebo minimálna daň |
| r. 1140 | r. 1150 | r. 400, daňová strata |
| r. 1160 | r. 1170 | r. 1060, daň podľa § 17f |
| r. 1180 | r. 1190 | r. 1070, daň podľa § 51e |
| r. 1191 | r. 1192 | r. 1071, daň podľa § 51ea |

Funguje to aj pri viacerých dodatočných priznaniach za sebou, lebo každé
uvádza priznanie v plnom rozsahu.

## Súbor XML {#xml}

**Exportovať XML** vytvorí *dokument* zvoleného vzoru a overí ho proti XSD
tohto vzoru zverejnenej finančnou správou. Obsahuje hlavičku — DIČ, IČO,
obchodné meno, sídlo, zdaňovacie obdobie a druh priznania (riadne /
opravné / dodatočné) — a všetky riadky tela. **Neobsahuje** a pred podaním
musíte doplniť:

- telefón a e-mail; kód SK NACE a právnu formu, ak ich spoločnosť nemá
  (pozri [Nastavenie](#setup));
- vyhlásenia v hlavičke (napr. mikrodaňovník, polovičná alebo neplatená
  minimálna daň, zápočet minimálnej dane), všetky zapísané ako „nie“;
- tabuľky tlačiva okrem A a B (C až K), poukázanie podielu zaplatenej dane (§ 50),
  oprávnenú osobu, počet príloh a žiadosť o vrátenie preplatku.

Dátum vyhlásenia je deň exportu. Prijímateľ podielu podľa § 50, oprávnená
osoba a stála prevádzkareň zostávajú prázdne — skoršie verzie ich vypĺňali
vlastným IČO, názvom a adresou spoločnosti.

Schéma súbor s týmito časťami prázdnymi prijme; správca dane priznanie bez
častí, ktoré sa vás týkajú, neprijme.

## Porovnanie s účtovnou závierkou {#zavierka}

Ak je nainštalovaný tento modul, modul
[module:l10n_sk_fs](module:l10n_sk_fs) a slovenský balík
[module:l10n_sk_datadance](module:l10n_sk_datadance), nainštaluje sa
automaticky prepojovací modul
[module:l10n_sk_dppo_fs](module:l10n_sk_dppo_fs) a do vypočítaného priznania
pridá tlačidlo **Porovnať s účtovnou závierkou**. To nájde účtovnú závierku
spoločnosti (*Účtovná závierka UZPODv 14 (SK)*), ktorá pokrýva obdobie
priznania — prednostne tú s rovnakými dátumami — a porovná r. 100 s
riadkom 56 výkazu ziskov a strát (výsledok hospodárenia za účtovné obdobie
pred zdanením). Obe čísla sú ten istý výsledok hospodárenia, takže sa musia
zhodovať s odchýlkou najviac 0,50 eura; rozdiel znamená, že sa obe podania
nezhodujú, najčastejšie pre prepísaný r. 100 alebo iné obdobie.

Výsledok sa uloží pri priznaní ako porovnanie — otvorí ho tlačidlo
*Porovnania* — oddelene od ostatných porovnaní toho istého priznania. Ak
účtovná závierka za obdobie neexistuje, tlačidlo to oznámi a nič neporovná.

## Obmedzenia {#limitations}

- **XML adaptér nového publikovaného vzoru čaká na doplnenie.** Natívny
  výpočet už obsahuje pásmo 11.520; nenahrádzajte nový vzor starým 2025 XML.
- **Vzory 2013, 2014 a 2020 – 2023** počítajú len r. 100 a tabuľky A/B; daň je na vás.
- Obsah riadkov 3 a 4 tabuľky B vzorov 2013 a 2014 poučenie neuvádza;
  vyplňte ich podľa tlačiva.
- r. 560 sa predvypĺňa celou triedou 6; pri vzoroch 2015 – 2019, ktoré
  r. 560 nemajú, sa podľa triedy 6 určuje aj pásmo daňovej licencie.
- Tabuľky a vyhlásenia uvedené v časti [Súbor XML](#xml) sa nevytvárajú.
- Väčšina riadkov tela je označená len číslom; čítajte ich podľa
  oficiálneho tlačiva a poučenia na jeho vyplnenie.
- Definície riadkov a výpočet dane by mal pred prvým podaním skontrolovať
  váš účtovník.

## Publikovaný vzor MF/014309/2026-721 {#published-2026}

Zoznam verzií vychádza z príslušnej **zákonnej lehoty na podanie** vrátane
účinného predĺženia zadaného v poli *Príslušná zákonná lehota na podanie*.
Pri bežnej trojmesačnej lehote nechajte pole prázdne. Obdobie júl 2025–jún 2026
bežne používa starší vzor; pri účinnom predĺžení do marca 2027 už nový vzor.
Obdobie december 2025–november 2026 potrebuje nový vzor aj bez predĺženia.
Oneskorený skutočný dátum podania toto pravidlo nemení. Horné pásmo minimálnej
dane naďalej závisí od začiatku zdaňovacieho obdobia.

Natívne priznanie podporuje výpočet nového vzoru pre bežné obdobia od 2026.
Oznámenie sa vzťahuje na posledný deň lehoty na podanie po 31.12.2026, pokiaľ
ho nenahradí neskorší vzor. Zahŕňa teda aj bežný prvý rok 2027 podávaný v 2028.

Riadok 310 je nový účtovníkom posudzovaný vstup podľa § 17k; medzisúčet sa
presunul 315. Nový športový vstup 306 posunul motorové vozidlo, praktické
vyučovanie a kontrolované zahraničné spoločnosti. Minimum 11.520 nad 5 miliónov
platí iba pre obdobia začínajúce od 2026. Oslobodenie alebo polovičnú výšku
podľa § 46b evidujte ako overenú úpravu riadku 810; vstup sa prenesie do
nadväzujúcich súm aj natívneho zaúčtovania dane.

Úradná papierová tlač a poučenie sú publikované. Elektronický adaptér má
samostatný publikačný krok: v overenom katalógu nebola jeho nová schéma.
Výpočet funguje, XML export vysvetlí potrebu nainštalovať aktuálny elektronický
vzor. Nepoužije staré 2025 XML. Zdrojové hashe a platnosť obsahuje
`data/FORM_PUBLICATION.json`.

## Úradný listinný výstup {#official-pdf}

Po výpočte priznania vyplňte **Údaje úradného formulára** a použite tlačidlo
**Úradný formulár PDF**. Identita pochádza zo spoločnosti a zvoleného natívneho
kontaktu. Doplňte kód právnej formy, SK NACE, meno a vzťah oprávnenej osoby,
dátum vyhlásenia a príslušné vyhlásenia. Dodatočné priznanie potrebuje skutočný
dátum zistenia rozdielu dane.

Výstup doplní pôvodný 21-stranový vzor MF/014309/2026-721. Zdroj a SHA256 sú
pripnuté v `static/forms/SOURCES.json`. Telo a tabuľky A/B používajú uložené
riadky natívneho priznania vrátane overených ručných úprav. Po zmene účtovných
podkladov alebo vstupov výpočtu treba priznanie prepočítať. Vyhlásenia
o minimálnej dani sa musia zhodovať s riadkom 810 a sumou pre dané obdobie.
Hodnota presahujúca počet políčok sa výslovne odmietne.

Listinný adaptér podporuje základ, A/B a zadané údaje tabuliek I/D. Nenulové
nároky vyžadujúce ďalšiu tabuľku alebo prílohu potrebujú pred tlačou súvisiace
zadané podklady a adaptér; nikdy sa potichu nevynechajú. Päť pôvodných
priložených strán sa zachová s rovnakým DIČ a uvedie v počte príloh.
Pokračovacie strany tabuľky I sa započítajú navyše.

PDF je nepodpísaná snímka na kontrolu a stiahnutie. Nemení stav priznania,
nevytvára XML a neoznačí priznanie za podané. Rovnaká snímka použije existujúcu
prílohu; zmena identity vytvorí novú a zachová presné pôvodné bajty.
Elektronické podanie naďalej vyžaduje publikovaný XML adaptér.

### Zadané transakcie tabuľky I {#table-i}

V časti **Údaje úradného formulára** zadajte jednotlivé transakcie a úvery
tabuľky I. Zvoľte natívny kontakt závislej osoby a zadajte publikovaný
dvojmiestny kód druhu transakcie (01–37 pre transakcie, 01–05 pre úvery)
a trojmiestny úradný kód štátu daňovej rezidencie protistrany. Zaradenie
a významnosť sú účtovníkom posúdené fakty; referencia je číselník
v publikovanom poučení. Kontroluje sa formát a rozsah kódu bez tichého orezu.

Pri transakcii sa zadáva vplyv so znamienkom, agregácia a prepojenosť podľa
§ 2 písm. r). Vplyv zahŕňa aj účinky v ďalších obdobiach; **nejde o druhý
účtovný zápis ani sumu pripočítavanú k riadku 400**. Úver má najvyššiu
istinu počas obdobia a konečnú istinu, ktorá nesmie prekročiť najvyššiu.
Samostatné vyhlásenie pod zákonnou hranicou sa týka len transakcií, ktoré
už nie sú zahrnuté v agregovanom riadku. Údaje musia zodpovedať vyhláseniu
na prvej strane.

Pôvodné tlačivo má štyri transakcie a päť úverov. Ďalšie riadky vytvoria
výslovne označené pokračovacie kópie pôvodného vzoru tabuľky I s priebežnými
poradovými číslami a číslami príloh. Každá časť má najviac 99 riadkov.
Pri väčšom počte musí účtovník uplatniť poradie z publikovaného poučenia
a zachovať zvyšné údaje v dokumentácii transferového oceňovania; program
žiadny zadaný riadok potichu nevynechá. Údaje sa kopírujú s natívnou opravou,
patria svojej firme a po exporte/podaní ich možno meniť až po natívnom
návrate priznania do návrhu.

### Predchádzajúce daňové straty v tabuľke D {#table-d}

Zadajte úradný stĺpec, pôvodné obdobie a sumu straty, predchádzajúce odpočty
a odpočet uplatňovaný v tomto období. Bežné straty podľa § 30 patria do
stĺpcov 4–8 v časovom poradí. Nová strata aktuálneho obdobia zostáva v riadku
400; v tabuľke D sa objaví až v nasledujúcom priznaní. Voliteľné prepojenie
na natívne pôvodné priznanie kontroluje firmu, obdobie a záporný riadok 400.
Počiatočné údaje možno zadať aj z overených externých podkladov.

Poradie nasledujúceho zdaňovacieho obdobia je overený údaj od 1 do 5 vrátane
krátkych období, nie rozdiel kalendárnych rokov. Bezprostredne nasledujúce
obdobie musí mať číslo 1. Zostatok sa vypočíta z pôvodnej sumy po odpočítaní
predchádzajúcich a aktuálnych odpočtov. Po piatom období nevyužitý zostatok
zanikne a suma pre budúcnosť je nula. Osobitné režimy stĺpcov 1–3 sú zadané
právne kvalifikácie; pri odpočte v stĺpci 1 treba aj vysvetlenie v poli
**Osobitné záznamy úradného formulára**.

Tlačidlo **Preniesť overený odpočet tabuľky D** prenesie súčet do existujúcej
natívnej úpravy riadka 410 a prepočíta priznanie. Pred dokončením skontroluje
aj novo prepočítaný základ. Bežné straty majú publikovaný limit 50 %; aktuálne
oprávnený mikrodaňovník môže pri oprávnených stratách od roku 2021 použiť
celý základ. Ostatné kvalifikácie sú naďalej posúdené fakty; známe rozpory
v mikro vyhláseniach sa odmietnu. Celkový odpočet nesmie prekročiť kladný
riadok 400 ani nevyužitú pôvodnú stratu.

Po zmene údajov D treba odpočet znovu preniesť. PDF aj natívne zaúčtovanie
dane odmietnu nesúlad s riadkom 410. Pred finálnym výstupom skontrolujte
ostatné existujúce ručné vstupy. Účtovným postupom zostáva
natívne zaúčtovanie a storno dane; nevzniká druhá daňová kniha. Všetkých osem
stĺpcov a súčet sa tlačia na pôvodné strany 7–8. Osobitné záznamy sa zalomia
v pôvodnom poli strany 15 a text nad kapacitu sa odmietne bez tichého orezu.

Tento ohraničený adaptér stále slúži na kontrolu a stiahnutie. Ďalšie nenulové
osobitné nároky potrebujú svoje adaptéry pred dokončením
celého listinného podania. Neskoršie publikované formuláre a právne zmeny
podliehajú bežnej aktualizácii; táto verzia nie je zárukou prijatia budúcim
portálom.

### Bežné podvojné účtovníctvo – tabuľky F/L a preddavky {#table-fl}

Tabuľka F číta hospodárske a finančné výnosy a náklady pred daňou z príjmov
z existujúcej zaúčtovanej hlavnej knihy. Používa rovnaké vylúčenie účtov dane
ako natívny riadok 100. Výnosy mínus náklady sa musia rovnať riadku 100.
Pri overených importovaných účtovných údajoch možno výslovne zadať obe sumy
a uchovať zdrojové podklady. Sú to podklady formulára, nevzniká ďalšia kniha.

Tabuľka L začína výnosmi F. Každá úprava má sumu so znamienkom, popis,
súvisiaci trojmiestny riadok priznania a podklady zatriedenia. Čistá úprava
priradená riadku nesmie prekročiť jeho sumu. **Preniesť overené príjmy
tabuľky L** zapíše súčet do existujúceho ručného riadka 560 a prepočíta
priznanie. Zmenené údaje treba znovu preniesť pred PDF či zaúčtovaním dane
používajúcim tieto údaje. Aj bez úprav sa vytlačia L1 a L99. Pôvodný vzor má
26 polí označených 2–21 a 23–28, pričom preskakuje 22. Zachováva sa: označené
pokračovanie doplní chýbajúci riadok 22 a potom 29–98 s číslovaním príloh.
Nad 97 úprav treba skontrolovať kapacitu publikovaného formulára;
žiadna zadaná položka sa potichu nevynechá.

V tejto publikovanej verzii sa riadok 1110 predvolene vypočíta z riadka 500
krát sadzba riadka 550 mínus riadok 610, pred odpočtami 501–503. Výslovné
ručné úpravy účtovníka zostávajú dostupné. Iba pri overenej historickej úľave
podľa § 35/35a zákona č. 366/1999 sa použije osobitný príznak s podkladmi,
kladným riadkom 610 a nulovým riadkom 1110; tlačené pole sa vtedy nevyplní.
Príznak sám neurčuje zákonnú oprávnenosť.

Tabuľka K má súvislé obdĺžniky pre celé eurá. Sumy a súčty nad štyri číslice sa zarovnajú doprava bežným písmom, ak sa zmestia do skutočného poľa. Centy zostávajú v samostatných okienkach; suma širšia než fyzické pole sa odmietne bez orezania.
