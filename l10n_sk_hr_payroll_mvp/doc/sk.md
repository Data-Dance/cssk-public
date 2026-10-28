---
title: SK MVP — mesačný výkaz poistného a príspevkov
summary: Mesačný výkaz poistného a príspevkov pre Sociálnu poisťovňu zostavený z výplatných pások mesiaca — sumy za fondy a príloha po zamestnancoch, export do XML overený voči oficiálnej schéme.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

Zamestnávateľ každý mesiac vykazuje **Sociálnej poisťovni** poistné
a príspevky na starobné dôchodkové sporenie, ktoré za mesiac odvádza:
*Mesačný výkaz poistného a príspevkov* (**MVP**, elektronicky *MVPP*). Výkaz
obsahuje za každý fond sumu za zamestnávateľa a za zamestnanca a prílohu
s riadkom za každého zamestnanca.

Modul výkaz zostaví z výplatných pások mesiaca a vyexportuje ho do súboru XML,
ktorý nahráte na portál Sociálnej poisťovne. Výplatné pásky číta cez spoločný
modul
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
takže funguje s oboma mzdovými jadrami — pozri
[príručku slovenských miezd](module:l10n_sk_hr_payroll_base#declarations).

Dohody s nepravidelným príjmom sa vykazujú na inom výkaze, VPP — pozri
[module:l10n_sk_hr_payroll_vpp](module:l10n_sk_hr_payroll_vpp).

## Právny rámec {#legal}

Odkazy sú na [zákon o sociálnom poistení](law:sk/2003/461).

- **Povinnosť predložiť výkaz.** Podľa
  [§ 231 ods. 1 písm. g)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-g)
  zamestnávateľ predkladá pobočke *výkaz poistného a príspevkov na starobné
  dôchodkové sporenie* za príslušný kalendárny mesiac **v lehote splatnosti
  ním odvádzaného poistného**, s uvedením dňa určeného na výplatu príjmov,
  ktoré sú vymeriavacím základom zamestnanca, v členení na jednotlivých
  zamestnancov a na jednotlivé fondy, a s určením fyzickej osoby, ktorá plní
  povinnosti voči Sociálnej poisťovni. Nesprávne údaje opravuje *opravným
  výkazom* (druhý bod toho istého písmena).
- **Splatnosť.** Poistné, ktoré platí a odvádza zamestnávateľ, je splatné
  v deň určený na výplatu príjmov; ak taký deň nie je určený, v posledný deň
  nasledujúceho kalendárneho mesiaca —
  [§ 143 ods. 2](law:sk/2003/461#paragraf-143.odsek-2).
- Obsah a spôsob zasielania tlačiva určuje podľa
  [§ 231 ods. 2](law:sk/2003/461#paragraf-231.odsek-2) Sociálna poisťovňa;
  ona zverejňuje aj schému XML, voči ktorej modul výkaz overuje.

## Nastavenie {#setup}

Pred prvým výkazom treba na spoločnosti vyplniť dva údaje:

| Údaj | Kde | Použije sa ako |
|---|---|---|
| *IČO*, 8 až 12 číslic | formulár spoločnosti | `<identifikator>` |
| *Variabilný symbol Sociálnej poisťovne*, presne 10 číslic | pozri nižšie | `<variabilnySymbol>` — číslo, ktoré zamestnávateľovi pridelila Sociálna poisťovňa |

*Variabilný symbol Sociálnej poisťovne* vyplňte priamo vo formulári MVP.
Ukladá sa na spoločnosti a je spoločný s modulmi VPP, ELDP a RLFO, takže sa
zadáva raz; na jeho zmenu treba právo upravovať spoločnosti.

Každý zamestnanec vo výkaze musí mať **rodné číslo** (9 alebo 10 číslic;
lomka a medzery sa ignorujú) v poli *Identifikačné č*.

Telefón a e-mail kontaktnej osoby sa berú zo spoločnosti, meno kontaktnej
osoby je meno užívateľa, ktorý výkaz generuje.

## Zostavenie výkazu {#usage}

*Mzdové hlásenia → SK MVP (sociálne poistenie)*, potom *Nové*.

1. Zvoľte **Rok** a **Mesiac**. *Dátum výplaty* je deň výplaty uvedený
   v `<denVyplaty>`; ak ho nevyplníte, použije sa posledný deň mesiaca.
2. Kliknite na **Generovať**. Modul zoberie výplatné pásky spoločnosti, ktorých
   obdobie leží v danom mesiaci, vytvorí riadok za každého zamestnanca,
   vygeneruje XML a overí ho voči priloženej schéme `MVPP-v2026.xsd`. XML sa
   priloží k záznamu (*Príloha XML*) a záznam prejde do stavu *Vygenerované*.
3. XML stiahnite, nahrajte na portál Sociálnej poisťovne a kliknite na
   **Označiť ako odoslané**. Podaná kópia sa uchová; odoslaný výkaz nemožno
   znova vygenerovať ani zmazať, kým ho nevrátite do konceptu.

**Vrátiť do konceptu** výkaz znova otvorí — napríklad po oprave výplatnej
pásky — a *Generovať* ho potom zostaví nanovo.

Generovanie sa zastaví s hlásením, ak spoločnosti chýba IČO alebo platný
variabilný symbol, ak zamestnanec nemá platné rodné číslo alebo ak za mesiac
neexistuje žiadna výplatná páska.

## Obsah výkazu {#output}

Každý fond sa berie z riadkov výplatných pások s pevným kódom mzdového
pravidla:

| Fond (element) | Zamestnávateľ | Zamestnanec |
|---|---|---|
| nemocenské poistenie (`np`) | SICKEMPLOYER | SICK |
| starobné poistenie (`sp`) | PENSIONEMPLOYER | PENSION |
| invalidné poistenie (`ip`) | DISABILITYEMPLOYER | DISABILITY |
| poistenie v nezamestnanosti (`pvn`) | UNEMPLOYMENTEMPLOYER | UNEMPLOYMENT |
| úrazové poistenie (`up`) | ACCIDENT | — |
| garančné poistenie (`gp`) | GUARANTEEEMPLOYER | — |
| rezervný fond solidarity (`rfs`) | RESERVEFUNDEMPLOYER | — |
| podpora v čase skrátenej práce (`pfp`) | SHORTTIMEEMPLOYER | — |

Úhrn (`spoluPoistne`) je súčet týchto riadkov. Zdravotné poistenie v ňom nie
je — vykazuje sa zdravotnej poisťovni v dávke 514
([module:l10n_sk_hr_payroll_health](module:l10n_sk_hr_payroll_health)).

Riadok prílohy obsahuje rodné číslo, vymeriavací základ (*GROSS* zamestnanca
za mesiac), počet dní, počet hodín z odpracovaných dní na výplatných páskach
a sumy zamestnanca za jednotlivé fondy.

## Obmedzenia {#limitations}

- **Len riadny výkaz** (`typVykazu` R). Opravný výkaz modul nevytvorí; opravy
  podajte cez portál.
- **Započíta sa každá výplatná páska mesiaca** vrátane konceptov — vynechajú
  sa len zrušené. Výkaz generujte až po uzavretí miezd. Výplatná páska, ktorej
  obdobie presahuje hranicu mesiaca, sa nezapočíta vôbec.
- **Dohody sa nevylučujú.** MVP berie každého zamestnanca s výplatnou páskou,
  VPP berie každú DoVP a DoPČ. Dohodár vyplatený v mesiaci sa tak objaví na
  oboch výkazoch; duplicitu pred podaním odstráňte.
- Každý riadok prílohy má typ vzťahu *ZEC* (zamestnanec s pravidelným
  príjmom), príznak výnimky z vymeriavacieho základu `vynimkaVZ` 0 a plný
  počet kalendárnych dní mesiaca, aj pri zamestnancovi, ktorý počas mesiaca
  nastúpil alebo skončil.
- Vymeriavací základ je *GROSS* z výplatnej pásky, nie suma vypočítaná podľa
  zákona o sociálnom poistení; maximálny vymeriavací základ sa tu
  neuplatňuje.
- Dodáva sa len vzor MVPP 2026 (platný od 1. 1. 2026); aj staršie obdobie sa
  vyexportuje v tomto tvare.
- Overenie voči schéme kontroluje tvar súboru, nie sumy. Prvý podaný výkaz
  odsúhlaste s výplatnými páskami ručne.
