---
title: Daň z finančných transakcií
summary: Natívne účtovné zdroje, overené zaradenie transakcií a oznámenie OZNDFTv26.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Pripraviť vlastné oznámenie právnickej osoby zo zaúčtovaných položiek a dokladov
o skutočných transakciách/úhradách. Modul používa spoločný rámec exportu,
archivácie a evidencie doručenia. Nededí dividendový formulár a nevytvára
náhradnú účtovnú knihu.

## Bežný prípad {#common-case}

1. Vyberte mesiac, zaúčtovaný kredit zahraničného bankového účtu, skutočný deň
   a podklad dôvodu c. Overte vypočítanú lehotu.
2. Overte zdroje a zaúčtujte daň natívnym zápisom 538/345 bez duplicity.
3. Exportujte XML; uchová sa spoločná snímka údajov a presné bajty prílohy.
4. Zaevidujte skutočné podanie a potvrdenku v spoločnej evidencii doručenia.
   Tlačidlo súbor neposiela ani nepotvrdzuje jeho prijatie úradom.

Zmena telefónu, adresy alebo účtovných zdrojov po exporte upozorní na potrebu
overiť opravu. Nezmení pôvodné XML ani nezablokuje evidenciu jeho skutočného
podania. Záväzok už podaného oznámenia sa účtuje z uchovaných podaných údajov.

Bankovým zdrojom je kredit predvoleného platobného účtu bankového denníka;
pokladňa nie je bankový prevod. Stornovaný zdroj ani jeho reverz nie sú novou
platbou alebo daňovým kreditom. Vlastná rezerva nie je zaplatená daň. Existujúce
natívne storno rezervy sa prevezme bez ďalšieho storna.

Pri bankovej dávke označte všetky časti, zadajte sumu a jedinečný identifikátor
každej skutočnej platby a overte ich. Súčet musí pokryť celý bankový riadok.
Limit aj minimum potom platia na platbu: desať platieb po 5 000 € dáva daň 200 €,
nie jeden limit 40 €. Neúplná dávka sa odmietne; čerpanie v inom podanom mesiaci
nesmie presiahnuť skutočnú bankovú sumu.

## Zdroje {#sources}

Prevod a výber hotovosti používajú skutočný kredit bankového účtu. Základ
rezidenta tvorí celý bankový debit, nekráti sa percentom daňových výdavkov.
Skutočný dátum sa overuje nezávisle od neskoršieho účtovného dátumu. Pri cudzej
mene treba zachovať sumu, menu a oficiálny kurz ECB/NBS platný v deň transakcie.
Výpočet používa nezaokrúhlený prepočítaný základ; XML ho zobrazuje v centoch.
Účtovný kurz môže byť odlišný.

Preúčtované náklady odkazujú na skutočné vysporiadanie záväzku vrátane
započítania. Každá pôvodná transakcia tretej osoby má samostatný identifikátor;
jedna úhrada môže vysporiadať viac pôvodných transakcií. Zníženia a korekcie
potrebujú vlastný zaúčtovaný zdroj a overený podklad právneho priradenia.
Samotné zaúčtovanie záväzku nepreukazuje zaplatenie dane.

Právne zaradenie c/d/e, vylúčenia a výber dane bankou sa overujú osobitne,
neodvodzujú sa iba z IBAN. Podklady o vylúčených/bankou zdanených operáciách
zostanú zachované bez druhej dane. Ročné použitie karty sa identifikuje
stabilným označením, nikdy celým číslom karty.

## Postup {#workflow}

Bežný účtovník vyberie firmu/mesiac, vyhotovenie a plánované/skutočné podanie,
skutočnú podávajúcu osobu. Zákonná lehota sa vypočíta; odkaz na daňový kalendár je voliteľný. Na potvrdenky
používa existujúcu rolu prípravy podaní. Opravné oznámenie patrí do lehoty;
po nej dodatočné so skutočným dňom zistenia a poslednou známou daňou.

Kontrola zdrojov vytvorí snímku. Zaúčtovanie dane vytvorí natívny zápis 538/345,
pri zápornom výsledku 345/538; úhrada ani vratka sa tým nevymýšľajú. Opakované
stlačenie nevytvorí druhý zápis. Nepodanú daň možno natívne stornovať. Oprava
podanej dane účtuje iba rozdiel oproti skutočným zápisom a stornám v reťazci.
Export overuje pôvodný XSD. Evidencia podania uchová XML a zdroje a otvorí
evidenciu doručenia, súbor tým nie je odoslaný ani prijatý úradom.

Reset uchová podania aj účtovnú históriu. Zmena podaného obsahu potrebuje
samostatnú opravu. Historické stiahnutie neprepočítava dnešné údaje. Migrácia
úložiska s rovnakými bajtmi zostáva funkčná.

## Hranice aktuálneho overenia {#limits}

XML validácia overuje štruktúru formulára, nie prijatie úradom.
Identifikované pôvodné transakcie zdieľajú limit 40 € cez čiastočné úhrady
a skoršie účinné podané obdobia. Zmena skoršieho priradenia potrebuje overenú
opravu neskoršieho oznámenia. Tlačidlo Overiť skoršie preúčtované transakcie
odhalí túto závislosť bez prepisovania podaného XML. Vylúčené preúčtované
transakcie uchovajú overené právne zaradenie.

Účtovník zadáva vlastný overený podiel na dani už zaplatenej pôvodným platiteľom
a uchová doklad a výpočet podielu v odkaze zdroja. Natívnym účtovným zdrojom je
vlastný podiel firmy; program neodvodzuje právny podiel z celého cudzieho dokladu.
Rovnaký zdroj sa v účinných podaných obdobiach nedá použiť nad zostávajúcu sumu.

Presné dátumy neúplného mesiaca zostávajú vo vykazovanom mesiaci. Zverejnený
formulár vyžaduje začiatok pred koncom; jednodňové obdobie vyžaduje osobitné
vyriešenie formulára s úradom a program ho potichu nerozšíri. Vratka na zahraničný
účet bez IBAN používa firemný účet, SWIFT/BIC a skutočný názov, mesto a krajinu
banky/pobočky; krajina pobočky sa neodvodzuje z BIC.
Spoločná uzávierka a ročník 2027 zostávajú otvorené.
Zákonná lehota sa vypočíta ako koniec nasledujúceho mesiaca s posunom na
pracovný deň podľa § 27 ods. 4 daňového poriadku. Ručne zadaný dátum zákonnú
lehotu nepredĺži. Oneskorené riadne podanie varuje; typ opravy určuje vypočítaná lehota.


## Rozsah {#scope}

Neskorší zápis podania nepreukazuje, že bolo skutočne podané neskoro. Ak uchovaný
export uvádza podanie v lehote, no evidujete ho až po nej, Odoo zapíše upozornenie
s oboma dátumami a žiada overenie potvrdenky. Uchovajte skutočnú potvrdenku
portálu. Ak bolo opravné oznámenie skutočne podané po lehote, pripravte dodatočné
oznámenie podľa § 16 daňového poriadku. Upozornenie zachováva oprávnenú spätnú
evidenciu a pôvodné XML; neosvedčuje zadaný dátum ani prijatie úradom.

Slovenský účet pri samotnom dôvode zahraničného poskytovateľa tiež upozorňuje:
overte, či daň už nezrazila domáca banka. Legitímny domáci osobitný účet zostáva
možný; upozornenie nemení vypočítanú daň.

OZNDFTv26 podporuje obdobia od januára 2026. Apríl–december 2025, ich opravy
a daň za karty roku 2025 podaná v januári 2026 potrebujú OZNDFTv25 a nie sú
podporované týmto modulom. Ohlásené zrušenie od roku 2027 sa nepovažuje za účinný
zákon; pred budúcim obdobím overte účinný predpis a formulár.

Podklady: [formulár FS](https://pfseform.financnasprava.sk/Formulare/eFormVzor/DP/form.629.html),
[FAQ FS](https://www.financnasprava.sk/sk/aktualne-dan-clo/faq/dan-financne-transakcie)
a pôvodný XSD zaznamenaný v `data/SCHEMA_VERSION`.
