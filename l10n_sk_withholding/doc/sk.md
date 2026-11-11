---
title: Oznámenie zrážkovej dane
summary: Rezidentské dividendy a autorské príjmy, skutočné úhrady, OZN4311v26 a príloha A.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Pripraví úplné mesačné oznámenie rezidentskej zrážkovej dane z existujúceho
účtovníctva a skutočných úhrad. Nevytvára druhú dividendu, autorský náklad,
platbu ani daň. Používa spoločný export, uchovanie podania a potvrdeniek.

## Bežný prípad {#common-case}

1. Vyberte firmu, mesiac, skutočné dátumy vyhotovenia a podania, vyhotoviteľa
   a účet 342. Potvrďte, že nechýbajú iné rezidentské zrážkové tituly: riadok 01
   musí obsahovať všetku rezidentskú zrážkovú daň za mesiac.
2. Zadajte príjemcu dividendy, ukončené ziskové obdobie, skutočné rozhodnutie,
   vyplatenie, hrubú sumu a doklady. Vyberte zaúčtované riadky vzniku nároku,
   platby a zrážky. Overte podklad skutočného vyplatenia.
3. Priraďte osobitný skutočný odvod dane: debet 342, sumu, skutočný deň a doklad.
   Samotný zápis alebo príkaz na prevod nie je dôkazom zaplatenia.
4. Overte zdroje a exportujte XML podľa pôvodného XSD. Zaevidujte skutočné
   externé podanie a potvrdenku cez spoločný rámec doručenia. Tlačidlo súbor
   neposiela ani nepotvrdzuje jeho prijatie úradom.

Bežný účtovník používa existujúcu rolu prípravy podaní; nepotrebuje systémové
ani účtovnícke administrátorské práva. Nepodaný návrh môže resetovať. Opätovné
otvorenie podanej histórie zostáva vyhradené spoločnému správcovskému postupu.

## Zdroje a spôsoby úhrady {#sources}

Dividenda používa záväzok 364, autor 321/379, zrážka a odvod 342 vrátane analytík.
Skutočné a účtovné dátumy sa môžu líšiť. Stornované zdroje a reverzy sa odmietnu.
Živé oznámenia rezervujú zdroje aj medzi mesiacmi. Úplná oprava nahrádza
predchodcu; nie je novou platbou. Rozpracovaná oprava neuvoľní ešte účinnú
podanú alokáciu cudziemu oznámeniu. Súbežná zmena vyvolá opakovanie transakcie.

Podporovaná je banka, pokladňa aj natívna account.payment cez jej prechodný účet.
Registrovaná platba stále potrebuje overený doklad skutočnej úhrady; ľubovoľný
kredit obežného aktíva nestačí. Pri zápočte vyberte tento spôsob, uchovajte
právny podklad a spárujte skutočnú pohľadávku voči rovnakému príjemcovi.
Odvod dane má vlastný bankový alebo doložený úradný zápočtový zdroj. Snímka
uchová kredity úhrady a odkazy na natívnu platbu/pohľadávku. Podporovaný je aj
jeden zápis hrubého záväzku, zrážky a čistej úhrady; rovnaké kredity nesmú
preukazovať viac vykázaných platieb než skutočne uhradili.

Nezávislý [príklad FS](https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DP/DPPO/2026/2026.01.15_006_PO_2026_IM_podiel_zisk.pdf)
overuje 650 + 1 050 = 1 700. Sadzba dividendy sa viaže na začiatok ziskového
obdobia: 10 % pre rok 2024, 7 % pre ostatné podporované obdobia. Rezidentský autor
bez vopred písomne dohodnutého nezrážania používa 19 %. Dohoda podľa § 43 ods. 14
patrí do samostatného oznámenia dohody, nie do fiktívnej nulovej zrážky tu.

## Podanie, lehoty a opravy {#filing}

Zahrnú sa iba odvody do skutočného dňa podania. Viac dátumov zostáva zachovaných;
príloha A má jeden tlačený deň odvodu na príjem, jeho zobrazenie treba overiť.

Riadne podanie upozorní po 15. dni nasledujúceho mesiaca s posunom na pracovný
deň. Rešpektuje Veľkú noc aj výnimku septembra 2026. Iná lehota určená správcom
podľa § 43 ods. 11 vyžaduje jeho skutočné rozhodnutie s uchovaným odkazom.

Podkladom podania je presný exportovaný XML a jeho údaje. Neskoršia zmena
účtovníctva alebo adresy príjemcu upozorní na potrebu overiť samostatnú opravu;
nezablokuje evidenciu skutočného podania. Čerpanie alokácií sa znova overí.
Oprava kopíruje úplnú sadu príjmov a uchová predchodcu. Skutočný deň jeho podania
overte potvrdenkou; nenahrádza ho plán ani čas lokálnej evidencie. Vlastníctvo
a identita opravy zostávajú uchované aj po resete.

Pri autorskom príjme je zdaniteľný príjem suma bez DPH znížená iba o skutočne
zrazený príspevok umeleckému fondu podľa
[§ 43 ods. 5 písm. b)](https://www.financnasprava.sk/sk/podnikatelia/dane/dan-z-prijmov/fyzicke-osoby/slobodne-povolania).
Uchovajte pôvodnú odmenu, prípadný skutočný príspevok a účtovné podklady.
Neodpočítavajte domnelý príspevok. Platba autorovi je tento zdaniteľný príjem
znížený o zrazenú daň.

Zaúčtované storno zatiaľ vylučuje pôvodný zdroj aj pri čiastočnom dobropise.
Faktúra na 1 500 s naviazaným dobropisom na 150 tak zatiaľ neposkytne zvyšných 1 350
cez tento adaptér. Ide o známe nepokryté použitie; neodstraňujte väzbu dobropisu
a nemeňte zaúčtované doklady kvôli obídeniu kontroly. Uchované exporty zostávajú
dostupné. Pri evidencii ich skutočného podania neskoršie pracovné návrhy nemajú
prednosť pred už exportovaným nárokom. Nový výpočet naďalej kontroluje všetky
pracovné rezervácie aj uchované nároky ostatných oznámení.

## Identita a rozsah {#scope}

Formálne kontroly rodného čísla overujú dĺžku, dátum, hranicu vyplatenia a mod11.
Deväť číslic patrí narodeniu pred rokom 1954; samotné dvojčíslie neznamená rok
2000. Formát nepreukazuje pridelenie čísla. Nesúlad s § 2 zákona 301/1995 vyžaduje
úradné overenie podľa § 7; náhradné číslo sa nevymýšľa. Dátum narodenia sa použije
len vtedy, keď slovenské rodné číslo nebolo pridelené.

Rozsah: slovenská právnická osoba s účtovníctvom v EUR, rezidentské dividendy FO
zo ziskových období od roku 2017 a rezidentskí autori bez dohody o nezrážaní.
Iné rezidentské tituly potrebujú úplné oznámenie mimo tohto adaptéra; potvrdenie
rozsahu bráni ich tichému vynechaniu. Zahraniční príjemcovia/príloha B, príjemcovia
PO a zdravotné režimy dividend pred rokom 2017 nie sú podporované. OZN4311v26
nepotvrdzuje budúci ročník. [Formulár FS](https://pfseform.financnasprava.sk/Formulare/eFormVzor/DP/form.626.html)
a pôvodné bajty schémy sú pripnuté v data/SCHEMA_VERSION. Podpis a doprava sú
samostatné integrácie.
