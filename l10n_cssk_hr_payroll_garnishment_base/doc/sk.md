---
title: Zrážky zo mzdy CZ/SK
summary: Evidencia českých a slovenských exekučných príkazov na zrážky zo mzdy, zákonné poradie uspokojovania všetkých príkazov zamestnanca na výplatnej páske, oznámenia platiteľa mzdy exekútorovi či súdu a poukázanie zrážok príjemcovi.
verified: 19.0.1.3.0
---

## Na čo slúži {#purpose}

Keď súdny exekútor, súd alebo úrad nariadi zrážať časť mzdy zamestnanca —
slovenská *exekúcia zrážkami zo mzdy*, česká *exekuce srážkami ze mzdy* —
zamestnávateľ sa stáva **platiteľom mzdy**. Musí zoradiť príkazy podľa
poradia, nechať zamestnancovi nepostihnuteľnú časť mzdy, zvyšok rozdeliť
medzi oprávnených v poradí, ktoré určuje zákon, zrazené sumy poukázať a
vyúčtovať ich.

Tento modul je na to **evidencia**:

- jeden záznam za každý doručený príkaz, s poradím, druhom pohľadávky a
  zostatkom dlhu;
- výpočet, ktorý berie **všetky** prebiehajúce príkazy zamestnanca naraz a
  určí, koľko z mesačnej čistej mzdy pripadne na každý z nich — podľa
  slovenských alebo českých predpisov, podľa krajiny spoločnosti;
- jedna **zrážka** za každý príkaz a výplatnú pásku, s údajom, z ktorej
  tretiny suma pochádza;
- **oznámenia** platiteľa mzdy a **vyúčtovanie zrážok** na tlač.

Závisí len od modulu `hr` Odoo, vlastné mzdy teda nemá. Výplatnú pásku
napája doplnok opísaný v časti [Mzdové jadrá](#engines) a platbu exekútorovi
doplnok v časti [Poukázanie príjemcovi](#accounting). Skupina modulov:

| Modul | Čo robí |
|---|---|
| [module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base) (tento modul) | Evidencia, výpočet, oznámenia. |
| [module:l10n_cssk_hr_payroll_garnishment_ee](module:l10n_cssk_hr_payroll_garnishment_ee) | Napojenie na Mzdy Odoo Enterprise. |
| [module:l10n_cssk_hr_payroll_garnishment_oca](module:l10n_cssk_hr_payroll_garnishment_oca) | Napojenie na mzdovú aplikáciu OCA. |
| [module:l10n_cssk_hr_payroll_garnishment_account](module:l10n_cssk_hr_payroll_garnishment_account) | Zo zrážok vytvorí záväzky voči exekútorovi. |

Samotnú zrážku počíta mzdové pravidlo národných miezd:
[module:l10n_sk_hr_payroll_ee](module:l10n_sk_hr_payroll_ee),
[module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca),
[module:l10n_cz_hr_payroll_ee](module:l10n_cz_hr_payroll_ee) alebo
[module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca).

## Právny rámec {#legal}

Overené voči úplným zneniam platným v októbri 2026.

**Slovensko** — [Exekučný poriadok](law:sk/1995/233) (§ 66 až 92) a
[nariadenie vlády č. 268/2006 Z. z.](law:sk/2006/268) o rozsahu zrážok zo
mzdy pri výkone rozhodnutia.

- Zráža sa z **čistej mzdy**: mzda po odpočítaní preddavku na daň, poistného
  na zdravotné a sociálne poistenie a príspevku na starobné dôchodkové
  sporenie ([§ 69 ods. 1](law:sk/1995/233#paragraf-69.odsek-1)).
- **Základná suma**, ktorá sa nesmie zraziť, závisí od vymáhanej pohľadávky:
  140 % životného minima na plnoletú fyzickú osobu pri neprednostnej
  pohľadávke ([§ 1 ods. 1 nariadenia](law:sk/2006/268#paragraf-1.odsek-1)),
  100 % pri prednostnej pohľadávke
  ([§ 2 ods. 2](law:sk/2006/268#paragraf-2.odsek-2)) a 70 % zo 60 % pri
  výživnom pre maloleté dieťa
  ([§ 2 ods. 1](law:sk/2006/268#paragraf-2.odsek-1) v spojení s
  [§ 70 ods. 2 Exekučného poriadku](law:sk/1995/233#paragraf-70.odsek-2)).
  Použije sa životné minimum platné **v mesiaci, za ktorý** sa zrážky
  vykonávajú.
- Na každú osobu, ktorej povinný poskytuje výživné, sa pripočíta 25 % — zo
  základnej sumy pri neprednostnej pohľadávke, pri prednostnej zo 100 %
  základu ([§ 1 ods. 2](law:sk/2006/268#paragraf-1.odsek-2),
  [§ 2 ods. 3](law:sk/2006/268#paragraf-2.odsek-3)). Na rozdiel od Česka sa
  započítava aj manžel so samostatným príjmom. U poberateľa dôchodkových
  dávok je to 50 % ([§ 2a](law:sk/2006/268#paragraf-2a)).
- Zvyšok čistej mzdy nad **trojnásobok** základnej sumy podľa § 1 ods. 1 sa
  zráža bez obmedzenia ([§ 3 ods. 1](law:sk/2006/268#paragraf-3.odsek-1)).
  Sumy sa zaokrúhľujú na eurocenty nadol ([§ 4](law:sk/2006/268#paragraf-4)).
- Zvyšok čistej mzdy sa zaokrúhli nadol na sumu deliteľnú troma; na
  neprednostnú pohľadávku sa zráža jedna tretina, na prednostnú dve.
  Prednostné pohľadávky sa uspokojujú najprv z druhej tretiny
  ([§ 71 ods. 1 a 2](law:sk/1995/233#paragraf-71.odsek-1)). Z prvej tretiny
  sa uspokojujú všetky podľa poradia, z druhej najprv výživné bez ohľadu na
  poradie ([§ 72](law:sk/1995/233#paragraf-72.odsek-2)). Poradie určuje deň
  doručenia príkazu na začatie exekúcie platiteľovi mzdy
  ([§ 72 ods. 3](law:sk/1995/233#paragraf-72.odsek-3)) a zrážky sa vykonávajú
  odo dňa doručenia ([§ 66 ods. 1](law:sk/1995/233#paragraf-66.odsek-1)).
  Zrazené sumy sa vyplácajú **exekútorovi**
  ([§ 81 ods. 1](law:sk/1995/233#paragraf-81.odsek-1)).
- Nový zamestnávateľ, ktorý zistí vydaný príkaz, to bezodkladne oznámi
  exekútorovi ([§ 84 ods. 2](law:sk/1995/233#paragraf-84.odsek-2)). Keď
  povinný prestane pracovať, platiteľ mzdy to do týždňa oznámi exekútorovi a
  zašle mu vyúčtovanie zrážok
  ([§ 85 ods. 2](law:sk/1995/233#paragraf-85.odsek-2)).

**Česko** — [občiansky súdny poriadok (občanský soudní řád), § 276 až 302](law:cz/1963/99)
a [nariadenie vlády č. 595/2006 Sb.](law:cz/2006/595) (*nařízení o
nezabavitelných částkách*). Rovnako postupuje *soudní exekutor*.

- Nezabaviteľná suma (*nezabavitelná částka*) je 85 % súčtu životného minima
  jednotlivca, normatívneho nájomného (*normativní nájemné*) jednočlennej
  domácnosti v obci s aspoň 70 000 obyvateľmi a energetického paušálu, plus
  štvrtina tejto sumy na každú vyživovanú osobu; manžel sa nezapočítava
  (okrem prípadov podľa § 1 odst. 2). Zaokrúhľuje sa na celé koruny nahor a
  použijú sa sumy k **1. januáru roka, v ktorom sa mzda vypláca** (§ 3 a 4
  nariadenia).
- Nad **1,9-násobok** tohto súčtu sa zvyšok čistej mzdy zráža bez obmedzenia
  (§ 2 nariadenia); táto časť sa pripočíta k druhej tretine v rozsahu
  potrebnom pre prednostné pohľadávky, zvyšok k prvej (§ 279 odst. 3).
- Tretiny, prednostné pohľadávky a poradie fungujú ako na Slovensku, v celých
  korunách (§ 279, § 280). Platiteľ mzdy však začína zrážať **od prvého dňa
  mesiaca nasledujúceho po doručení** (§ 282a).
- Ak sú na mzdu súčasne nariadené **aspoň štyri výkony rozhodnutia** na
  peňažné pohľadávky, zrážajú sa dve tretiny: prednostné pohľadávky sa aj
  naďalej uspokojujú najprv z druhej tretiny, ale čo nevyčerpajú, pripadne
  k prvej tretine a neostáva povinnému (§ 279 odst. 4 a 6). Neplatí to, ak
  povinný preukáže starobný dôchod, invalidný dôchod druhého alebo tretieho
  stupňa alebo sirotský dôchod **a** zároveň je jedna tretina nižšia ako
  mesačná odmena a hotové výdavky insolvenčného správcu (§ 279 odst. 5).
- Nástup povinného oznamuje nový zamestnávateľ súdu bez odkladu (§ 294
  odst. 2), odchod do týždňa spolu s vyúčtovaním zrážok (§ 295 odst. 2).
  Na dopyty súdu odpovedá podľa § 128 o. s. ř., exekútora podľa § 33
  odst. 5 exekučního řádu.

## Nastavenie {#setup}

1. Krajina spoločnosti musí byť Slovensko alebo Česko. V inej spoločnosti
   mzdy príkazy ignorujú.
2. Skontrolujte zákonné sumy v *Zamestnanci → Konfigurácia → Garnishment
   Rates* (len správca personalistiky). Dodané hodnoty sú v časti
   [Zákonné sumy](#rates). Keď sa suma zmení, pridajte nový záznam s dátumom
   platnosti (*Date From*).
3. Pri zamestnancovi, voči ktorému je príkaz, na karte *Nastavenia* v skupine
   **Wage Garnishment**:

   | Pole | Čo robí |
   |---|---|
   | Maintained Persons (vyživované osoby) | Osoby, ktorým zamestnanec poskytuje výživné. Každá zvyšuje nepostihnuteľnú sumu. Kto sa započítava, posúďte sami: manžela každá krajina posudzuje inak (pozri [Právny rámec](#legal)) a nezapočítava sa osoba, v ktorej prospech trvá exekúcia na výživné. |
   | Pension Recipient (poberateľ dôchodkových dávok) | Slovensko: na každú vyživovanú osobu sa pripočíta 50 % namiesto 25 %. Česko: zamestnanec preukázal starobný dôchod, invalidný dôchod druhého alebo tretieho stupňa alebo sirotský dôchod; pravidlo dvoch tretín pri štyroch a viac exekúciách sa potom neuplatní, kým je jedna tretina nižšia ako mesačná suma insolvenčného správcu (§ 279 odst. 5 o. s. ř.). |

   Národné mzdové moduly majú na zmluve vlastné pole *Garnishment
   Dependents* pre staršie pravidlo s jednou pohľadávkou. Ak je *Maintained
   Persons* ponechané na 0, evidencia použije toto pole zo zmluvy (platnej ku
   koncu obdobia); číslo zadané tu má vždy prednosť.

Prístup: personalisti so skupinou *Officer: Manage all employees* vidia a
upravujú príkazy a zrážky, mazať môže len *Správca* personalistiky. Záznamy patria spoločnosti a výplatná páska
použije vždy len príkazy svojej spoločnosti.

## Evidencia príkazu {#orders}

*Zamestnanci → Garnishments → Orders*, *Nové*.

| Pole | Význam |
|---|---|
| Case Number (spisová značka) | Napr. `EX 123/2026`. |
| Employee | Povinný. |
| Garnishment Type | *Court execution* (exekúcia), *Insolvency* (oddlženie), *Agreement* (dohoda o zrážkach zo mzdy) alebo *Administrative enforcement* (správna exekúcia). Pri českej spoločnosti rozhoduje, či sa príkaz započíta do štyroch výkonov podľa § 279 odst. 4 o. s. ř.: *Court execution* a *Administrative enforcement* áno, *Agreement* a *Insolvency* nie. Inak výpočet nemení. |
| Claim Class (druh pohľadávky) | **Podľa neho sa počíta.** *Maintenance* (výživné), *Priority* (prednostná), *Administrative fine* (pokuta za priestupok) alebo *Ordinary* (neprednostná). Prevezmite ho z príkazu. |
| Delivered On | Deň, keď bol príkaz doručený **vám**. Určuje poradie. |
| Date Start / Date End | Obdobie, na ktoré sa príkaz vzťahuje. *Date Start* sa pri slovenskej spoločnosti predvyplní dňom doručenia, čo zodpovedá zákonu; pri českej prvým dňom mesiaca nasledujúceho po doručení (§ 282a o. s. ř.). Dá sa zmeniť; ručná hodnota ostane, kým sa nezmení *Delivered On*. |
| Total Claim | Istina, trovy a úroky podľa príkazu. Pri bežnom výživnom bez konečnej sumy nechajte 0. |
| Monthly Maintenance | Bežné mesačné výživné. Bez celkovej sumy je príkaz neukončený a sám sa nikdy neuzavrie. |
| Arrears | Dlžné výživné, ktoré sa zráža popri bežnom (zobrazí sa len pri výživnom). |
| Creditor, Bailiff | Oprávnený a súdny exekútor. Ak je exekútor vyplnený, peniaze idú jemu. |
| Payee, Payee Bank Account | Príjemca (počíta sa) a jeho účet. Účet iného subjektu sa nedá uložiť. |
| Variable Symbol | Číslice spisovej značky, posledných 10; dá sa prepísať. Špecifický a konštantný symbol podľa príkazu. |

Príkaz musí mať celkovú sumu alebo mesačné výživné. Samotný príkaz priložte
na karte *Document*.

**Stavy.** Príkaz v stave *Draft* mzdy ignorujú. **Start** ho prepne do
stavu *Running* — zrážajú sa len prebiehajúce príkazy. **Suspend** ho
pozastaví (napr. pri odklade exekúcie), **Mark Settled** uzavrie,
**Cancel** zruší, **Reset to Draft** vráti pozastavený alebo zrušený príkaz
do konceptu. Príkaz, ktorého celková suma bola zrazená, sa uzavrie sám, keď
sa potvrdí výplatná páska, ktorá ho doplatila; zrušenie alebo vrátenie tejto
pásky do konceptu ho znova otvorí.

Na formulári zamestnanca je tlačidlo **Garnishments** s počtom
prebiehajúcich príkazov.

## Na výplatnej páske {#payslip}

Pravidlo národných miezd **Wage Garnishment** (`GARNISHMENT`) beží po dani a
odvodoch. Ak má zamestnanec prebiehajúci príkaz spoločnosti výplatnej pásky,
evidencia vypočíta zrážku z čistej mzdy pásky cez všetky prebiehajúce
príkazy, ktorých obdobie sa s páskou prekrýva, a pravidlo zrazí celkovú
sumu.

Kým je páska koncept, do príkazov sa nezapisuje nič, nech sa prepočíta
koľkokrát chce. Keď pásku **potvrdíte** (*Potvrdiť*), zaznamená sa z tej istej
čistej mzdy jedna zrážka za každý príkaz a páska ich ukáže na karte
**Garnishments**. Všetky nájdete v *Zamestnanci → Garnishments →
Deductions*.

- **Zrušiť** alebo **Nastaviť na koncept** na páske vymaže jej zrážky, ktoré
  ešte neboli poukázané.
- Pásku, ktorej zrážka už bola **poukázaná**, nemožno zrušiť ani vrátiť do
  konceptu; najprv stornujte poukázanie.
- Zamestnanci bez zaevidovaného príkazu ostávajú na staršom pravidle národných
  miezd so vstupmi, takže na evidenciu môžete prechádzať po jednom
  zamestnancovi.

## Ako sa zrážka počíta {#calculation}

**Slovensko**, v centoch: nepostihnuteľný základ závisí od druhu pohľadávky
(140 %, 100 %, 70 % × 60 % alebo 50 % životného minima plus suma na
vyživované osoby). Modul vypočíta tretiny osobitne pre každý druh pohľadávky,
ktorý sa u zamestnanca vyskytuje; prednostné pohľadávky čerpajú svoju druhú
tretinu a časť nad hranicou, neuspokojený zvyšok súťaží v prvej tretine
podľa poradia, pri rovnakom poradí pomerne. Výživné má v druhej tretine
prednosť bez ohľadu na poradie a pri nedostatku sa delí podľa bežného
výživného. Dve poistky držia výpočet na bezpečnej strane: žiadny príkaz
nedostane viac, ako by mu dovolil jeho vlastný druh samostatne, a
zamestnancovi vždy ostane aspoň najnižší základ spomedzi príkazov, z ktorých
sa skutočne zrážalo. Čo poistky odrežú, ostáva zamestnancovi.

Príklad (od 1. 7. 2026): čistá mzda 1 000 €, jedno dieťa, jedna
neprednostná pohľadávka. Základ 413,30 € + 103,32 € = 516,62 € (sumy
zaokrúhlené nadol podľa § 4). Zvyšok 483,38 €, zaokrúhlený nadol na násobok
troch 483,36 €, tretina **161,12 €**.

**Česko**, v celých korunách: nezabaviteľná suma 85 % × (životné minimum +
normatívne nájomné + energetický paušál) × (1 + ¼ × vyživované osoby),
zaokrúhlená nahor; zvyšok do hranice zaokrúhlený nadol na násobok troch a
rozdelený na tretiny, nad hranicou zrážaný celý. Druhá tretina: najprv
výživné, potom ostatné prednostné podľa poradia; čo prednostné nevyčerpajú,
ostáva zamestnancovi. Prvá tretina: všetko neuhradené podľa poradia. Ak sú
aspoň štyri prebiehajúce príkazy zamestnanca typu *Court execution* alebo
*Administrative enforcement* (§ 279 odst. 4 až 6), to, čo prednostné
pohľadávky z druhej tretiny nevyčerpajú, sa pripočíta k prvej tretine pre
všetky pohľadávky podľa poradia — okrem prípadu, keď je zamestnanec označený
ako *Pension Recipient* a jedna tretina je nižšia ako *Insolvency trustee
monthly amount* (§ 279 odst. 5).

## Zákonné sumy {#rates}

| Krajina | Platí od | Sumy |
|---|---|---|
| SK | 1. 7. 2024 | životné minimum 273,99 € |
| SK | 1. 7. 2025 | životné minimum 284,13 € |
| SK | 1. 7. 2026 | životné minimum 295,22 € |
| CZ | 1. 1. 2026 | životné minimum 4 860 Kč, normatívne nájomné 9 430 Kč, energetický paušál 2 300 Kč (súčet 16 590 Kč); 85 %; ¼ na osobu; bez obmedzenia nad 31 521 Kč (1,9 × 16 590); mesačná suma insolvenčného správcu (*Insolvency trustee monthly amount*) 1 089 Kč ((750 + 150) × 1,21, vyhl. 313/2007 Sb.) |

Slovenské koeficienty sú vo všetkých záznamoch rovnaké: neprednostná 140 %,
prednostná 100 %, výživné pre maloleté dieťa 70 % × 60 %, pokuta 50 %, 25 %
na osobu (50 % u poberateľa dôchodkových dávok), bez obmedzenia nad
trojnásobkom základnej sumy podľa § 1 ods. 1.

Český záznam pred rokom 2026 sa nedodáva, lebo reforma 2026 zmenila samotný
vzorec. Od 1. 10. 2026 je české životné minimum jednotlivca 5 500 Kč, no
podľa § 4 nariadenia sa na mzdy vyplácané v roku 2026 použije suma
k 1. januáru; pred výpočtom miezd vyplácaných v roku 2027 pridajte záznam
na rok 2027.

## Oznámenia a vyúčtovanie zrážok {#notices}

*Zamestnanci → Garnishments → Statutory Notices* vytlačí pre jedného
zamestnanca a niektoré alebo všetky jeho príkazy:

| Notice Type | Obsah |
|---|---|
| Notice of employment start (oznámenie o nástupe) | povinný nastúpil dňa *Event Date*; príkazy v evidencii |
| Notice of employment end (oznámenie o skončení) | povinný odišiel dňa *Event Date*; stav každého príkazu |
| Answer to an enquiry (odpoveď na dopyt) | príkazy v poradí s pohľadávkou, zrazenou sumou a zostatkom |
| Account of deductions (vyúčtovanie zrážok) | príkazy a všetky zrážky obdobia rozdelené na druhú a prvú tretinu, s údajom o poukázaní |

Adresát (*Addressee*) sa predvyplní príjemcom prvého vybraného príkazu.
Tlačivá sú v angličtine s českým nadpisom a podpisujú sa ručne. Pod
nadpisom oznámenie cituje ustanovenie podľa krajiny spoločnosti:

| Notice Type | Slovenská spoločnosť | Česká spoločnosť |
|---|---|---|
| Notice of employment start | § 84 ods. 2 Exekučného poriadku | § 294 odst. 2 o. s. ř. |
| Notice of employment end | § 85 ods. 2 Exekučného poriadku | § 295 odst. 2 o. s. ř. |
| Answer to an enquiry | *Odpoveď na žiadosť exekútora* (bez paragrafu) | § 128 o. s. ř. / § 33 odst. 5 exekučního řádu |

## Mzdové jadrá {#engines}

Evidenciu s mzdovou aplikáciou spájajú dva mostíky. Každý sa nainštaluje
sám, keď je nainštalované jeho jadro aj tento modul:

| | Enterprise | OCA |
|---|---|---|
| Modul | [module:l10n_cssk_hr_payroll_garnishment_ee](module:l10n_cssk_hr_payroll_garnishment_ee) | [module:l10n_cssk_hr_payroll_garnishment_oca](module:l10n_cssk_hr_payroll_garnishment_oca) |
| Mzdová aplikácia | *Mzdy* Odoo Enterprise (`hr_payroll`) | OCA `payroll` |

Robia to isté: zaznamenajú zrážky pri potvrdení pásky, vymažú ich pri jej
zrušení alebo vrátení do konceptu, odmietnu zrušiť alebo vrátiť do konceptu
pásku, ktorej zrážka už bola poukázaná, a pridajú na pásku kartu *Garnishments*. Suma na
páske potrebuje len tento modul a národné mzdové pravidlo; bez mostíka by sa
však nič nezaznamenalo k príkazom a príkazy by sa nikdy neuzavreli.

## Poukázanie príjemcovi {#accounting}

[module:l10n_cssk_hr_payroll_garnishment_account](module:l10n_cssk_hr_payroll_garnishment_account)
sa nainštaluje sám spolu s `account` a
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols).

Mzdový doklad účtuje všetky zrážky v prospech jedného súhrnného záväzku
(napr. 379). Poukázanie presunie podiel každého príkazu na príjemcu:

    MD  súhrnný záväzok zo zrážok
        D  záväzok voči exekútorovi alebo oprávnenému (s partnerom)

jeden zaúčtovaný doklad za každý príkaz, so symbolmi a bankovým účtom
príjemcu z príkazu. Otvorený záväzok sa potom uhradí ako ktorýkoľvek
dodávateľ — platobným príkazom a bankovým súborom alebo spárovaním s
výpisom.

1. *Účtovníctvo → Konfigurácia → Nastavenia* (v Community bez plného
   účtovníctva *Fakturácia → Konfigurácia → Nastavenia*), blok
   **Wage Garnishments**: zvoľte **Garnishment Remittance Journal** (denník
   typu Rôzne) a **Garnishment Liability Account** — ten istý účet, na ktorý
   mzdové účtovanie zaúčtuje zrážky.
2. Príjemca musí mať vyplnený účet záväzkov.
3. Buď *Zamestnanci → Garnishments → Remit to Payees*: zvoľte *Up To* a
   prípadne *Only This Payee*, skontrolujte zoznam a kliknite na **Remit**;
   alebo v *Deductions* označte zrážky a kliknite na **Remit to Payee**.

Doklad má dátum posledného konca obdobia, ktoré pokrýva. Poukázané zrážky sú
v stave *Remitted* a nedajú sa vymazať. Ponuku a tlačidlo vidí
*Administrátor* účtovníctva a používatelia v skupine *Show Full Accounting
Features*; ponuka je pod *Zamestnanci*, takže treba aj rolu
v personalistike. Účtovník na zrážke nezmení nič okrem údajov o poukázaní.

## Obmedzenia {#limitations}

- **Slovenské zaokrúhľovanie** sa riadi [§ 4 nariadenia](law:sk/2006/268#paragraf-4):
  nepostihnuteľné sumy aj hranica zrážok bez obmedzenia sa zaokrúhľujú nadol
  na eurocenty. Suma na povinného a suma na osobu sa zaokrúhľujú osobitne
  (od 1. 7. 2026 413,30 € + 103,32 € na osobu), ako ich odseky vymedzujú;
  zaokrúhlenie len ich súčtu by mohlo chrániť o cent viac.
- **Pokuty.** Druh *Administrative fine* používa 50 % životného minima plus
  25 % na osobu. Tento základ ([§ 2b nariadenia](law:sk/2006/268#paragraf-2b))
  sa týka pokút vymáhaných z dávok, ktoré inak exekúcii nepodliehajú, a nič na
  osobu nepripočítava; pred použitím na mzdu to preverte.
- **Kombinácia rôznych druhov pohľadávok** na Slovensku je modelové riešenie
  tam, kde zákon mlčí; výsledok pri príkazoch rôznych druhov dajte
  skontrolovať.
- **Oznámenia.** Tlačivá sú v angličtine s českým nadpisom aj pre slovenské
  spoločnosti. Potvrdenie pre odchádzajúceho zamestnanca
  ([§ 84 ods. 1](law:sk/1995/233#paragraf-84.odsek-1)) sa netlačí; oznámenia
  exekútorovi o práceneschopnosti nad desať dní a o materskej či rodičovskej
  dovolenke ([§ 67 ods. 4 a 5](law:sk/1995/233#paragraf-67.odsek-4)) sa
  nevytvárajú.
- **Česko**: príkazy zaevidované pred verziou 19.0.1.2.2 si ponechajú vtedy
  uložený *Date Start* (deň doručenia); sumy sa berú k 1. januáru roka
  výplaty, ktorý sa bez dátumu platby z pásky odhadne ako mesiac po období;
  paušálna náhrada nákladov platiteľa mzdy (50 Kč mesačne, § 279 odst. 1
  o. s. ř. a § 4d až 4e vyhlášky č. 485/2000 Sb.) sa nepočíta ani nezráža —
  platiteľ mzdy sa jej môže vzdať; ak ju uplatňujete, zrazte ju mimo
  evidencie.
- **Len mzda.** Nemocenské, dôchodky a iné príjmy vyplácané tretími osobami
  modul nerieši, rovnako ani nižšie zrážky dohodnuté podľa
  [§ 77](law:sk/1995/233#paragraf-77.odsek-1) či mzdu vyplatenú naraz za viac mesiacov
  (každý mesiac treba počítať osobitne).
- Podiel zrážky z časti nad hranicou (*From Unlimited Part*) sa nesleduje;
  započíta sa do tretín.
