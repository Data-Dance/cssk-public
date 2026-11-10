---
title: SK kniha jázd a cestovné príkazy
summary: Evidencia jázd vozidla a tuzemské aj zahraničné cestovné príkazy, schválené pred cestou a vyúčtované po nej, s preddavkom, stravným, vreckovým, základnou náhradou a náhradou za pohonné látky podľa zákona 283/2002 Z. z.
verified: 19.0.2.1.0
---

## Na čo slúži {#purpose}

Kniha jázd eviduje každú jazdu vozidla: vodiča, časy, trasu, účel a stav
tachometra. Cestovný príkaz sleduje pracovnú cestu v dvoch krokoch, tak ako
zákon 283/2002 Z. z.: zamestnávateľ pred cestou písomne určí jej podmienky
(§ 3) a zamestnanec po nej predloží vyúčtovanie (§ 36). Príkaz vypočíta stravné
za každý kalendárny deň a pri vlastnom vozidle zamestnanca aj základnú náhradu
a náhradu za pohonné látky.

## Od príkazu po vyúčtovanie {#process}

1. **Návrh.** Zamestnanec, alebo za neho referent výdavkov, vyplní v ponuke
   *Výdavky › Pracovné cesty › Moje cestovné príkazy* účel, miesto odchodu,
   miesto výkonu práce, plánované časy, spôsob dopravy a preddavok, ktorý
   potrebuje.
2. **Na schválenie.** *Odoslať* pošle príkaz schvaľovateľovi: schvaľovateľovi
   výdavkov zamestnanca, inak vedúcemu oddelenia, inak nadriadenému.
   Schvaľovateľ dostane aktivitu a vidí predpokladané stravné.
3. **Schválený.** *Schváliť* zaznamená plánované časy, kto príkaz schválil a
   kedy; to ukazuje vytlačený *Cestovný príkaz*. Z preddavku vznikne schválený
   preddavok zamestnanca, ktorý účtáreň zaúčtuje a vyplatí. Zamestnanec dostane
   aktivitu predložiť vyúčtovanie do 10 pracovných dní od návratu (§ 36 ods. 7).
4. **Vyúčtovanie na schválenie.** Po návrate zamestnanec zadá skutočné časy,
   prechody hraníc, bezplatné jedlá každého dňa, kilometre a na karte *Ostatné
   výdavky* cestovné lístky, ubytovanie a ďalšie výdavky, každý ako výdavok
   s dokladom. *Odoslať vyúčtovanie* prepočíta dni a pošle ho schvaľovateľovi,
   ktorý ho má vyúčtovať do 10 pracovných dní (§ 36 ods. 8). *Vrátiť na
   opravu* ho vráti zamestnancovi.
5. **Vyúčtovaný.** *Schváliť vyúčtovanie* zmení náhrady na jeden schválený
   výdavok a spolu s ním schváli aj ostatné výdavky. Ak bol vyplatený preddavok,
   tieto výdavky ho zúčtujú: účtáreň ich zaúčtuje cez denník zúčtovania,
   zamestnancovi sa vyplatí suma nad preddavok a nevyčerpaný zvyšok sa zaeviduje
   tlačidlom *Vrátiť preddavok* na preddavku. Výsledok ukazuje vytlačené
   *Vyúčtovanie pracovnej cesty*.

*Zrušiť cestu* stiahne príkaz na cestu, ktorá sa neuskutoční. Ak je preddavok
už zaúčtovaný, príkaz namiesto toho vyúčtujte bez dní, aby sa preddavok vrátil.

## Kto čo smie {#access}

- Zamestnanec vidí a zadáva len svoje príkazy a odosiela ich.
- Schvaľovateľ, vedúci oddelenia a nadriadený vidia príkazy svojho tímu a
  schvaľujú alebo zamietajú ich. Nikto neschvaľuje vlastnú cestu, ani manažér
  výdavkov.
- Schvaľovateľa určujú údaje zamestnanca; zamestnanec si ho vybrať nemôže,
  zmeniť ho smie len referent výdavkov.
- Po schválení zostáva príkaz tak, ako bol schválený; cestu, ako prebehla,
  zadáva len zamestnanec alebo referent výdavkov. Odoslaný príkaz ani
  vyúčtovanie sa nedajú meniť, kým nie sú schválené alebo vrátené, a nové
  výdavky sa k nim pridať nedajú.
- Referenti výdavkov vidia všetky príkazy a schválený príkaz môžu vrátiť do
  návrhu, kým preddavok nie je zaúčtovaný.

## Preddavok {#advance}

Preddavok používa modul *Employee Advance and Clearing*
(`hr_expense_advance_clearing`). Inštalácia tohto modulu nastaví jeho produktu
*Employee Advance* účet 335000 *Pohľadávky voči zamestnancom* vo všetkých
spoločnostiach so slovenskou účtovou osnovou a povolí na ňom párovanie;
v spoločnosti pridanej neskôr ho nastavte ručne. Pri zahraničnej ceste je
zamestnávateľ povinný poskytnúť preddavok, ak sa ho zamestnanec nevzdá (§ 36
ods. 1), a formulár na to upozorní.

## Zahraničné cesty {#foreign}

Zahraničný cestovný príkaz má navyše čas odchodu zo Slovenska a návratu naň
(prechod štátnej hranice alebo odlet a prílet lietadla podľa letového poriadku,
§ 16 ods. 2) a krajiny cesty, každú s časom príchodu. Každý kalendárny deň
potom dostane:

- tuzemské stravné za hodiny strávené v ten deň na Slovensku (§ 16 ods. 1 a § 5);
- zahraničné stravné krajiny, v ktorej zamestnanec v ten deň strávil najviac
  hodín, pri rovnosti výhodnejšie (§ 13 ods. 5): 25 % základnej sadzby do 6 hodín
  v zahraničí, 50 % do 12 hodín, nad 12 hodín celú sadzbu (§ 13 ods. 4);
- každé bezplatné jedlo kráti stravné tej časti dňa, kde bolo poskytnuté:
  doma o 25, 40 a 35 % tuzemského stravného nad 18 hodín (§ 5 ods. 6),
  v zahraničí o rovnaké podiely zo základnej sadzby (§ 13 ods. 7). Každé jedlo
  má vlastnú voľbu „v zahraničí“, predvolenú podľa obvyklého času jedla
  (raňajky 8:00, obed 12:00, večera 18:00) voči prechodom hranice; každá časť sa
  kráti najviac na nulu a jedlo doma v deň bez tuzemského stravného nekráti nič;
- vreckové do 40 % zahraničného stravného, ak ho zamestnávateľ poskytuje (§ 14).

Základné sadzby všetkých 193 krajín z opatrenia MF SR č. 401/2012 Z. z. sú
dodané v ponuke Pracovné cesty › Sadzby zahraničného stravného, spolu s osobitnými
sadzbami pre mobilných zamestnancov v cestnej doprave podľa opatrenia
č. 9/2026 Z. z. od 30. 1. 2026; použijú sa, ak je na príkaze označený „Mobilný
zamestnanec v cestnej doprave“. Stravné v cudzej mene sa prepočíta kurzom ECB
alebo NBS platným k prvému dňu mesiaca, v ktorom sa cesta začala (§ 36 ods. 6);
ak kurz chýba, príkaz výpočet odmietne, namiesto toho, aby kurz hádal.

Pri vlastnom vozidle karta **Pohonné látky** rozdelí náhradu na riadky, každý
s kilometrami, jednotkovou cenou a menou (§ 15): doma podľa dokladu zo Slovenska,
v zahraničí podľa dokladu zo zahraničia (možno aj aritmetický priemer viacerých),
v eurozóne v eurách, inde v miestnej mene. Cudzia mena sa prepočíta rovnakým
kurzom k prvému dňu mesiaca. Vzorové príklady ministerstva delia podľa skutočne
spotrebovaného paliva, nádrž po nádrži; v každom prípade majú riadky dať spolu
kilometre cesty a formulár upozorní, ak nedávajú. Bez riadkov platí jedna
jednotková cena pre všetky kilometre.

## Obmedzenia {#limits}

Dni sú slovenské kalendárne dni aj v zahraničí. To, ktorú časť dňa bezplatné
jedlo kráti, vychádza z odbornej literatúry (Mzdové centrum, 2014); text
ministerstva to výslovne neuvádza. Preddavok a vyúčtovanie sú v eurách;
preddavok v cudzej mene (§ 36 ods. 5) sa nespracúva. Spotreba sa zadáva už so
zvýšením podľa § 7 ods. 6. Sadzby sa udržiavajú v ponuke Pracovné cesty; dodaná
sada platí od 1. 1. 2026 a od 1. 12. 2026 so stravným podľa oznámenia
č. 255/2026 Z. z., takže pre skoršie cesty treba najprv zadať ich sadzby.
Lehoty 10 pracovných dní sa riadia pracovným časom zamestnanca: štátne sviatky
sa rátajú ako pracovné dni, ak v ňom nie sú zadané.
