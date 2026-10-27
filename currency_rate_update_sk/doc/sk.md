---
title: Kurzy mien pre Slovensko (ECB/NBS, VÚB, Tatra banka)
summary: Sťahuje referenčný výmenný kurz ECB, ktorým slovenská účtovná jednotka prepočítava cudziu menu, sám založí poskytovateľa, doplní kurzy na víkendy a sviatky a pridá kurzové lístky VÚB a Tatra banky.
verified: 19.0.1.1.2
---

## Na čo slúži {#purpose}

Slovenská účtovná jednotka účtuje v eurách a každú faktúru, platbu a zostatok
v cudzej mene prepočítava **referenčným výmenným kurzom**, ktorý určuje
Európska centrálna banka a vyhlasuje Národná banka Slovenska. Odoo potrebuje
tento kurz pre každý deň, ku ktorému je datovaný nejaký doklad.

Modul stavia na module OCA na aktualizáciu kurzov
([module:currency_rate_update](module:currency_rate_update)), ktorý už vie
kurzy ECB sťahovať. Pridáva to, čo slovenská firma potrebuje navyše:

- **poskytovateľa kurzov založí sám** pri inštalácii, takže kurzy začnú
  prichádzať bez toho, aby ktokoľvek vypĺňal formulár;
- **víkendy a sviatky dostanú kurz** prenesený z posledného dňa, v ktorý bol
  vyhlásený;
- **dva kurzové lístky komerčných bánk**, VÚB banky a Tatra banky, ak chcete
  vidieť, za koľko by menu skutočne previedla banka, a nie zákonný kurz.

Funguje v edícii Community aj Enterprise; nepotrebuje automatické kurzy
Odoo Enterprise.

## Právny rámec {#legal}

- **Účtovníctvo.** Majetok a záväzky v cudzej mene sa prepočítavajú na eurá
  referenčným výmenným kurzom určeným a vyhláseným ECB alebo Národnou bankou
  Slovenska *„v deň predchádzajúci dňu uskutočnenia účtovného prípadu“* a ku
  dňu, ku ktorému sa zostavuje účtovná závierka, kurzom toho dňa —
  [§ 24 ods. 2 zákona o účtovníctve](law:sk/2002/431#paragraf-24.odsek-2).
  Prírastok cudzej meny nakúpenej za eurá možno oceniť aj kurzom, za ktorý
  bola nakúpená ([§ 24 ods. 3](law:sk/2002/431#paragraf-24.odsek-3)).
- **DPH.** Základ dane fakturovaný v cudzej mene sa prepočíta tým istým
  referenčným kurzom ECB alebo NBS vyhláseným v deň predchádzajúci dňu vzniku
  daňovej povinnosti; inak len vtedy, ak platiteľ písomne oznámil daňovému
  úradu, že počas celého kalendárneho roka používa kurz podľa colných
  predpisov — [§ 26 ods. 1 zákona o DPH](law:sk/2004/222#paragraf-26.odsek-1).

Zákonným zdrojom je teda služba ECB. Kurzové lístky VÚB a Tatra banky sú
komerčné kurzy, nie referenčný kurz. Modul pri dokladoch slovenskej
spoločnosti uplatňuje pravidlo **predchádzajúceho dňa** — pozri
[Kurz ktorého dňa doklad dostane](#rate-date).

## Čo nastaví inštalácia {#setup}

Pri inštalácii dostane každá spoločnosť, ktorej krajinou (alebo daňovou
krajinou) je Slovensko, poskytovateľa **ECB** — ak už má databáza aspoň jednu
aktívnu cudziu menu, ktorú ECB vyhlasuje. Poskytovateľ:

- kótuje **meny, ktoré sú v databáze už aktívne** a ktoré ECB vyhlasuje, nikdy
  nie vlastnú menu spoločnosti — nové meny neaktivuje;
- sťahuje kurzy **denne**;
- má zapnuté *Fill non-publishing days* (dopĺňanie dní bez kurzu).

Spoločnosť, ktorá už poskytovateľa ECB má, hoci aj archivovaného, modul
nechá tak: archivácia je rozhodnutie. Spoločnosť bez aktívnej cudzej meny
poskytovateľa nedostane, lebo by nebolo čo sťahovať.

Poskytovatelia sú v *Účtovníctvo → Konfigurácia → Currency Rates Providers*
— v edícii Community bez plného účtovníctva sa koreňová ponuka volá
*Fakturácia*. Obrazovka aj popisy polí pochádzajú z modulu OCA a sú po
anglicky.

Ak menu aktivujete **až po inštalácii** modulu a zoznam je stále prázdny,
založte poskytovateľa sami: *Nové*, *Provider* = **European Central Bank**,
vyberte *Currencies*, interval nechajte 1 deň a uložte. Zoznam má na to aj tlačidlo
**Create the Slovak default provider**, zobrazené aj v prázdnom zozname;
založí len to, čo chýba, a vyžaduje práva na Nastavenia (ostatní dostanú
správu, kto to môže urobiť). Ak je nainštalovaný aj český modul, zoznam ukáže
len jedno z oboch tlačidiel; druhé zostane v ponuke *Actions* označeného
riadka. Ak chcete existujúcemu poskytovateľovi
pridať menu, upravte jeho pole *Currencies* — akcia existujúceho
poskytovateľa nikdy nemení.

Automatické sťahovanie vyžaduje aj zaškrtnuté *Automatic Currency Rates (OCA)*
v *Účtovníctvo → Konfigurácia → Nastavenia*, blok *Meny*. Predvolene je
zaškrtnuté.

## Bežná prevádzka {#usage}

Raz denne sa stiahnu kurzy mien poskytovateľa a uložia sa ako kurzy meny
(*Účtovníctvo → Konfigurácia → Meny*), každý s dňom, keď ho ECB vyhlásila.
Ktorý z nich doklad dostane, opisuje
[Kurz ktorého dňa doklad dostane](#rate-date).

Kurzy za minulé obdobie — pri prenose histórie alebo neskoro zaúčtovanej
faktúre — načítate tak, že otvoríte poskytovateľa, kliknete na **Update Rates
Now**, zvolíte *Start Date* a *End Date* a potvrdíte. Služba ECB poskytuje
celú históriu.

Ak sťahovanie zlyhá, chyba sa zapíše do komunikácie (chatter) poskytovateľa a
najbližšie plánované spustenie to skúsi znova.

## Kurz ktorého dňa doklad dostane {#rate-date}

V spoločnosti, ktorej krajinou alebo daňovou krajinou je Slovensko, dostane
doklad referenčný kurz vyhlásený v deň **predchádzajúci** rozhodujúcemu dňu —
najnovší kurz s dátumom pred týmto dňom:

| Doklad | Rozhodujúci deň | Príklad: použitý kurz |
|---|---|---|
| Faktúra, prijatá faktúra, dobropis, pokladničný doklad | *dátum dodania*, ak je vyplnený, inak dátum faktúry | z piatka 6. marca → kurz zo štvrtka 5. marca |
| Platba, riadok bankového výpisu | jej dátum | z pondelka 9. marca → kurz z piatka 6. marca |
| Iný účtovný zápis s riadkom v cudzej mene | dátum účtovania | z nedele 8. marca → kurz z piatka 6. marca |

Po víkende alebo sviatku „predchádzajúci deň“ vlastný kurz nemá, preto sa
použije posledný kurz vyhlásený pred ním — ten istý, ktorý na tieto dni
skopíruje *Fill non-publishing days*, takže výsledok od tejto voľby nezávisí.

**Precenenie ku koncu roka sa neposúva**: zostatky sa ocenia kurzom samotného
dňa, ku ktorému sa zostavuje účtovná závierka (§ 24 ods. 2 písm. b)), a ten
precenenie aj číta.

Kurz faktúry v koncepte sa prepočíta pri zmene jej dátumu; zaúčtovaný doklad
si ponechá kurz, s ktorým bol zaúčtovaný. Spoločnosť mimo Slovenska sa riadi pravidlom Odoo (kurz dňa
dokladu).

## Víkendy a sviatky {#fill}

ECB ani banky cez víkendy a sviatky kurzy nevyhlasujú. Ak má poskytovateľ
zaškrtnuté **Fill non-publishing days** (predvolené), po každom stiahnutí
dostane každý kalendárny deň stiahnutého obdobia, ktorý kurz nemá, kópiu
posledného kurzu pred ním. Deň, ktorý kurz už má, dopĺňanie nikdy neprepíše,
a doplnený deň sa prepíše, len čo sa preň skutočný kurz vyhlási.

Dopĺňanie kurz len prenáša dopredu. Ak obdobie začína pred prvým kurzom v
databáze, tieto prvé dni zostanú prázdne.

Voľba je na každom poskytovateľovi, nielen na slovenských, a ak sú
nainštalované oba moduly, využije ju aj český
[module:currency_rate_update_cz](module:currency_rate_update_cz).

## Kurzy komerčných bánk (VÚB, Tatra banka) {#bank-rates}

V poli *Provider* poskytovateľa pribudnú dve ďalšie služby:

| Služba | Čo sa sťahuje | Meny | História |
|---|---|---|---|
| VÚB banka | denný kurzový lístok banky, kurz *Devíza stred* | AUD, BGN, CAD, CNY, CZK, DKK, GBP, HUF, CHF, JPY, NOK, PLN, RON, SEK, TRY, USD | len dnešný lístok |
| Tatra banka | kurzy, ktoré banka zverejňuje vo svojom kanáli | CZK, GBP, HUF, PLN, SEK, CHF, USD | približne posledných 30 dní |

Slúžia na porovnanie, za koľko by menu previedla banka. **Nie sú** zákonným
referenčným kurzom, preto nimi nenechajte oceňovať doklady: tabuľka kurzov
spoločnosti má pre každú menu a deň jeden kurz a dvaja poskytovatelia, ktorí
pre tú istú spoločnosť kótujú tú istú menu, si kurzy navzájom prepisujú.
Komerčného poskytovateľa dajte do samostatnej spoločnosti alebo mu nechajte
len meny, ktoré poskytovateľ ECB nekótuje.

Sťahovanie a spracovanie oboch kurzových lístkov zabezpečuje modul
[module:currency_rate_sk_base](module:currency_rate_sk_base), ktorý sa
nainštaluje automaticky.

## Obmedzenia {#limitations}

- Voľba podľa § 26 ods. 1 zákona o DPH používať počas kalendárneho roka kurz
  podľa colných predpisov nie je podporovaná; taká spoločnosť musí kurz na
  faktúrach zadať ručne.
- Pravidlo predchádzajúceho dňa pokrýva faktúry, platby, riadky bankového
  výpisu a účtovné zápisy. Objednávky a ďalšie miesta, kde Odoo prepočítanú
  sumu len zobrazuje, používajú kurz vlastného dňa.
- ECB vyhlasuje kurzy približne tridsiatich mien. Národná banka Slovenska
  vyhlasuje kurzy aj niektorých ďalších mien; tie sa nesťahujú.
- Kurzové lístky VÚB a Tatra banky sú webové stránky bánk, nie
  zdokumentované rozhrania. Zmena na strane banky zastaví sťahovanie, kým sa
  modul neaktualizuje.
- Poskytovateľ sa zakladá automaticky len pri inštalácii a opísanou akciou.
  Meny aktivované neskôr sa do existujúceho poskytovateľa nepridajú.
