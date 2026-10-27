---
title: Mzdové hlásenia CZ/SK
summary: Spoločný základ českých a slovenských mzdových hlásení — ponuka Mzdové hlásenia, postup Generovať / Označiť ako odoslané, opravné hlásenia, verzie tlačív a čítanie výplatných pások z oboch mzdových jadier.
verified: 19.0.1.5.0
---

## Na čo slúži {#purpose}

Každé české a slovenské mzdové hlásenie v tejto lokalizácii — mesačné výkazy
sociálneho a zdravotného poistenia, daňové prehľady, evidenčné listy
dôchodkového poistenia, prihlášky a odhlášky — je samostatný modul. Všetky
fungujú rovnako, lebo stoja na tomto module. Táto stránka opisuje to, čo majú
spoločné; obsah jednotlivých tlačív opisujú ich vlastné stránky.

Modul pridáva ponuku **Mzdové hlásenia**, tabuľku verzií štatutárnych tlačív
a mechanizmus každého hlásenia: obdobie, stavy, export XML s kontrolou voči
schéme, opravné hlásenia a čítanie výplatných pások. Nezávisí ani od Odoo
Enterprise *Mzdy*, ani od OCA aplikácie *payroll*; výplatné pásky číta z tej,
ktorá je nainštalovaná. Nainštaluje sa sám ako závislosť tlačív a samostatne
nerobí nič.

## Tlačivá, ktoré naň nadväzujú {#forms}

| Krajina | Modul | Tlačivo | Komu sa podáva |
|---|---|---|---|
| SK | [module:l10n_sk_hr_payroll_mvp](module:l10n_sk_hr_payroll_mvp) | Mesačný výkaz poistného a príspevkov | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_vpp](module:l10n_sk_hr_payroll_vpp) | Výkaz poistného a príspevkov (nepravidelný príjem) | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_rlfo](module:l10n_sk_hr_payroll_rlfo) | Registračný list fyzickej osoby — prihlásenie a odhlásenie zamestnancov | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_eldp](module:l10n_sk_hr_payroll_eldp) | Evidenčný list dôchodkového poistenia | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_health](module:l10n_sk_hr_payroll_health) | Mesačný výkaz preddavkov na poistné (dávka 514) | zdravotné poisťovne |
| SK | [module:l10n_sk_hr_payroll_monthly_tax_overview](module:l10n_sk_hr_payroll_monthly_tax_overview) | Prehľad o zrazených a odvedených preddavkoch | finančná správa |
| SK | [module:l10n_sk_hr_payroll_annual_tax_report](module:l10n_sk_hr_payroll_annual_tax_report) | Hlásenie o vyúčtovaní dane | finančná správa |
| CZ | [module:l10n_cz_hr_payroll_pvpoj](module:l10n_cz_hr_payroll_pvpoj) | Přehled o výši pojistného (PVPOJ) | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_eldp](module:l10n_cz_hr_payroll_eldp) | Evidenční list důchodového pojištění | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_onz](module:l10n_cz_hr_payroll_onz) | Oznámení o nástupu / skončení zaměstnání | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_health](module:l10n_cz_hr_payroll_health) | Přehled o platbě pojistného zaměstnavatelem (PPPZ) a Hromadné oznámení zaměstnavatele (HOZ) | zdravotné poisťovne |
| CZ | [module:l10n_cz_hr_payroll_annual_tax_settlement](module:l10n_cz_hr_payroll_annual_tax_settlement) | Vyúčtování daně z příjmů fyzických osob ze závislé činnosti | Finanční správa |

Slovenské mzdy ako celok opisuje
[príručka slovenských miezd](module:l10n_sk_hr_payroll_base#declarations).

## Postup {#workflow}

Každé tlačivo má v ponuke *Mzdové hlásenia* vlastnú položku. Jedno hlásenie
patrí jednej spoločnosti a jednému obdobiu:

1. **Nové**, potom vyberte **Rok** a **Mesiac**. Predvolený je aktuálny
   mesiac, preto ho pri hlásení za minulý mesiac zmeňte. Hlásenie zobrazí
   prvý a posledný deň obdobia. *Dátum výplaty* je deň výplaty, ktorý sa
   uvádza tam, kde ho tlačivo vyžaduje (na slovenských tlačivách
   *denVyplaty*); ak ho nevyplníte, použije sa koniec obdobia.
2. Skontrolujte **Verziu** (pozri [Verzie tlačív](#versions)). Výber ponúka
   len verzie pripravovaného tlačiva.
3. Kliknite na **Generovať**. Modul overí kmeňové údaje, ktoré tlačivo
   potrebuje (každé tlačivo pridáva vlastné kontroly — identifikátory
   spoločnosti, rodné čísla, adresy), zozbiera výplatné pásky obdobia, zostaví
   riadok za každého zamestnanca, vytvorí XML, overí ho voči oficiálnej XSD
   schéme a priloží ho. Stav sa zmení na *Vygenerované*.
4. Stiahnite XML a podajte ho na portáli príslušného úradu. Žiadne tlačivo
   z tejto skupiny nič samo neodosiela.
5. Kliknite na **Označiť ako odoslané**. Vygenerované XML sa stane **Podaným
   XML**, pridá sa do **Histórie podaní**, zaznamená sa dátum a hlásenie sa
   uzamkne: nedá sa znova generovať ani vymazať.
6. **Vrátiť do konceptu** ho opäť odomkne. Podaná kópia aj história zostanú
   zachované, takže to, čo sa skutočne podalo, zostane zaznamenané aj vtedy,
   keď sa údaje neskôr pregenerujú.

Pred generovaním výplatné pásky obdobia potvrďte: pásky v koncepte sa
nezapočítajú (pozri [Ktoré výplatné pásky sa započítajú](#payslips)).

Generovanie sa zastaví so správou, ak obdobie nemá žiadne výplatné pásky, ak
neplatí žiadna verzia alebo ak XML neprejde kontrolou voči schéme. Každý krok
sa zapíše do chatteru.

## Opravné hlásenia {#corrections}

Úrady prijímajú opravy už podaných hlásení a každý ich nazýva inak —
*opravné*, *dodatočné*, *storno*. Hlásenie má pole **Typ opravy** s najviac
štyrmi hodnotami, zobrazenými po anglicky:

| Hodnota | Význam |
|---|---|
| Regular | riadne hlásenie za obdobie |
| Corrective | opravné — nahrádza už podané hlásenie |
| Supplementary | dodatočné — dopĺňa už podané hlásenie, ktoré naďalej platí |
| Cancellation | storno — ruší hlásenie, ktoré sa nemalo podať |

Tlačivo ponúka len tie hodnoty, ktoré jeho úrad prijíma a ktoré boli overené
voči pravidlám úradu. V súčasnosti:

| Tlačivo | Ponúkané typy |
|---|---|
| SK Prehľad o zrazených a odvedených preddavkoch | Regular, Corrective |
| SK Hlásenie o vyúčtovaní dane | Regular, Corrective, Supplementary |
| CZ PPPZ | Regular, Corrective |
| všetky ostatné | len Regular — opravy podávajte na portáli |

Pri inom type ako *Regular* odmietne **Generovať** pokračovať, kým nie je
hlásenie toho istého tlačiva za tú istú spoločnosť a obdobie v stave
*Odoslané* — oprava niečoho, čo nebolo podané, by bola odmietnutá. Obdobie sa
porovnáva podľa prvého a posledného dňa, takže pri ročnom tlačive nezáleží
na tom, v ktorom mesiaci bolo hlásenie založené. Ak úrad
potrebuje opravu spárovať s pôvodným hlásením, zadajte jeho označenie do poľa
**Referencia opravy**.

Opravné hlásenie sa zostaví z výplatných pások obdobia v ich aktuálnom stave,
rovnako ako riadne; pozri [Obmedzenia](#limitations).

## Ktoré výplatné pásky sa započítajú {#payslips}

Ak stránka tlačiva neuvádza inak, hlásenie za obdobie započíta každú
výplatnú pásku spoločnosti, ktorá

- **končí** v období — páska patrí do obdobia, do ktorého pripadá jej
  koncový dátum, takže páska presahujúca hranicu mesiaca alebo roka sa
  započíta práve raz, v období, kde končí, a
- je **potvrdená**: v jadre OCA v stave *Hotové* (*Done*), v Enterprise
  *Potvrdené* (*Validated*) alebo *Zaplatené* (*Paid*). Pásky v koncepte
  (a v jadre OCA pásky *Čaká*) sa nezapočítajú, rovnako ako zrušené. Pred
  kliknutím na *Generovať* pásky obdobia potvrďte.

Z týchto pások modul sčíta riadky podľa kódu mzdového pravidla, za každého
zamestnanca aj spolu. Kódy pravidiel sa v jadre Enterprise a OCA mierne líšia
(napríklad slovenský preddavok na daň je v jadre OCA jeden riadok
a v Enterprise jeden riadok za každé daňové pásmo); modul pozná oba zápisy,
takže tlačivo dá v oboch jadrách rovnaký výsledok.

Riadok zamestnanca obsahuje predvolene aj:

| Údaj | Odkiaľ sa berie |
|---|---|
| vymeriavací základ (*Vymeriavací základ*) | **hrubá mzda (GROSS)** zamestnanca za obdobie |
| dni poistenia (*Dni poistenia*) | dni zamestnania v období podľa všetkých verzií zmluvy zamestnanca (začiatok a koniec zmluvy); celé obdobie, ak žiadna verzia nemá dátum začiatku zmluvy |
| odpracované hodiny (*Odpracované hodiny*) | hodiny všetkých riadkov odpracovaných dní, vrátane neprítomností |

Jednotlivé tlačivá tieto hodnoty prevezmú alebo si ich vypočítajú samy;
pozrite stránku tlačiva.

## Verzie tlačív {#versions}

Úrady z času na čas menia tlačivá a schémy. Každý vzor tlačiva je záznam
v *Mzdové hlásenia → Konfigurácia → Verzie hlásenia*: kód hlásenia, krajina,
**Platné od** / **Platné do**, šablóna XML, očakávaný koreňový element a súbor
XSD. Nový vzor sa dodáva ako nový záznam verzie s vlastnou šablónou a schémou;
staré vzory zostávajú k dispozícii.

Nové hlásenie navrhne verziu svojho tlačiva platnú **dnes** v krajine vašej
aktuálnej spoločnosti a pri zmene roka alebo mesiaca ju zmení. Rozhodne
**Generovať**: prepne na verziu tohto tlačiva platnú pre obdobie (ročné
tlačivo sa riadi 1. januárom, tlačivo o udalostiach ich dátumami) a obdobie,
na ktoré sa nevzťahuje žiadna verzia, odmietne. Ak bolo tlačivo zrušené —
verzia s *Platné do* bez nástupcu — správa to uvedie a, ak to tlačivo vie,
povie, čo ho nahradilo. Verzie môže čítať každý
interný používateľ a spravuje ich *Zamestnanci / Správca*; bežne ich
neupravujete.

## Nastavenie spoločnosti {#company}

Formulár českej alebo slovenskej spoločnosti má záložku **Mzdové výkazy**.
Pri českej spoločnosti obsahuje identifikáciu zamestnávateľa, ktorú potrebujú
tlačivá ČSSZ: **Variabilný symbol ČSSZ (VS)** a **Kód OSSZ** miestne
príslušnej okresnej správy sociálneho zabezpečenia. Bez nich tlačivá
odmietnu generovať. Ďalšie moduly pridávajú na rovnakú záložku vlastné
polia.

## Doručenie a potvrdenky {#delivery}

*Označiť ako odoslané* zaznamená, že niekto XML podal. Ako sa dostalo na
úrad, či bolo prijaté a potvrdenky, ktoré to dokazujú, eviduje
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base), ktorý
používa každé mzdové hlásenie. Pozri
[Podanie](module:l10n_cssk_submission_base#usage).

## Obmedzenia {#limitations}

- **Opravy predchádzajúcich mesiacov sa neoddeľujú.** Páska sa započíta do
  mesiaca svojho vlastného obdobia. Doplatok alebo oprava za skorší mesiac
  zadaná na páske tohto mesiaca sa vykáže v tomto mesiaci; nevytvorí opravné
  hlásenie za skorší mesiac ani sa do neho nepresunie. Opravné hlásenie sa
  zostaví z pások opravovaného mesiaca v ich aktuálnom stave, nie ako rozdiel
  oproti podanému, takže dodatočné hlásenie (*Supplementary*) obsahuje celé
  sumy, ak to nerieši šablóna samotného tlačiva. Pred podaním opravu porovnajte
  s podanou kópiou.
- **Rok** možno vybrať od 2020 do budúceho roka.
- **Podanie sa len zaznamenáva, nevykonáva.** Tento modul ani tlačivá na ňom
  postavené nič úradom neodosielajú.
- **Kontrola voči schéme overuje tvar, nie sumy.** Prvé hlásenie každého
  tlačiva odsúhlaste ručne.
