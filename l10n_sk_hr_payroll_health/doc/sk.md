---
title: SK dávka 514 — mesačný výkaz preddavkov na zdravotné poistenie
summary: Mesačný výkaz preddavkov na poistné pre slovenskú zdravotnú poisťovňu (VšZP, Dôvera, Union) v spoločnom formáte dávky 514, zostavený z výplatných pások mesiaca a vyexportovaný do XML.
verified: 19.0.1.2.1
---

## Na čo slúži {#purpose}

Zamestnávateľ každý mesiac vykazuje každej **zdravotnej poisťovni**
preddavky na poistné, ktoré odvádza za zamestnancov a za seba: *mesačný výkaz
preddavkov na poistné*. Všetky tri slovenské poisťovne — **VšZP** (25),
**Dôvera** (24) a **Union** (27) — ho prijímajú v rovnakom elektronickom
formáte, **dávke 514**.

Modul zostaví dávku 514 z výplatných pások mesiaca a vyexportuje ju do súboru
XML, ktorý nahráte cez elektronickú pobočku poisťovne. Výplatné pásky číta cez
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
takže funguje s oboma mzdovými jadrami — pozri
[príručku slovenských miezd](module:l10n_sk_hr_payroll_base#declarations).

## Právny rámec {#legal}

Odkazy sú na [zákon o zdravotnom poistení](law:sk/2004/580).

- **Mesačný výkaz.** Zamestnávateľ vykazuje príslušnej zdravotnej poisťovni
  preddavky na poistné za kalendárny mesiac v členení podľa jednotlivých
  zamestnancov a za zamestnávateľa. Uvádza celkový príjem, príjem na
  uplatnenie a výšku odpočítateľnej položky, peňažné plnenie oslobodené od
  dane, vymeriavací základ a preddavok a výkaz zasiela **elektronicky** —
  [§ 20 ods. 1](law:sk/2004/580#paragraf-20.odsek-1).
- **Splatnosť preddavkov.** Preddavok zamestnanca a zamestnávateľa je
  splatný v deň určený na výplatu príjmov zamestnancov za príslušný mesiac;
  ak taký deň nie je určený, posledný deň nasledujúceho kalendárneho mesiaca —
  [§ 17 ods. 1](law:sk/2004/580#paragraf-17.odsek-1).
- **Opravy.** Údaje, ktoré poisťovňa vráti v chybovom protokole, treba
  elektronicky opraviť do 30 dní od jeho doručenia —
  [§ 24 ods. 1 písm. m)](law:sk/2004/580#paragraf-24.odsek-1.pismeno-m).

## Nastavenie {#setup}

Na spoločnosti:

| Údaj | Kde | Použije sa ako |
|---|---|---|
| *IČO*, 8 až 12 číslic | formulár spoločnosti | `IDCode`, `CompanyIDCode` |
| *DIČ*, 10 číslic | formulár spoločnosti (zo slovenského základného modulu) | `CompanyIDTaxCode` |
| *Číslo platiteľa poistného* | formulár spoločnosti alebo formulár dávky 514 | `CodeOfPayer` — číslo, ktoré zamestnávateľovi pridelila poisťovňa |
| *Zdravotná poisťovňa (dávka 514)* | formulár spoločnosti | predvolená poisťovňa nového výkazu (ak nie je nastavená, VšZP) |
| bankový účet | kontakt spoločnosti | `IBAN` — použije sa prvý účet |

Obidva údaje sú na formulári spoločnosti, karta *Mzdové výkazy*, skupina
*Zdravotné poistenie (dávka 514)*. *Číslo platiteľa poistného* sa dá vyplniť aj
priamo vo formulári dávky 514; ukladá sa vždy na spoločnosti, takže sa zadáva
raz (na jeho zmenu treba právo upravovať spoločnosti).

Každý zamestnanec vo výkaze musí mať **rodné číslo** v poli *Identifikačné č*
a mal by mať vyplnenú **Zdravotnú poisťovňu (SK)**, hneď vedľa na karte
*Personal*. Každá dávka 514 zoberie len zamestnancov poistených v poisťovni,
ktorej je určená; zamestnanec bez vyplnenej poisťovne sa počíta do predvolenej
poisťovne spoločnosti (VšZP, ak sa nezmenila). Poisťovňu radšej vyplňte pri
každom zamestnancovi.

## Zostavenie výkazu {#usage}

*Mzdové hlásenia → SK dávka 514 (zdravotné)*, potom *Nové*.

1. Zvoľte **Zdravotnú poisťovňu**, **Rok** a **Mesiac**. *Dátum výplaty*
   určuje deň platby v `DateOfPayment`; ak ho nevyplníte, použije sa posledný
   deň mesiaca.
2. Kliknite na **Generovať**. Modul zoberie potvrdené výplatné pásky
   spoločnosti, ktorých obdobie sa v danom mesiaci končí, vytvorí riadok za každého zamestnanca
   a vygeneruje XML.
3. Súbor nahrajte cez elektronickú pobočku poisťovne a kliknite na **Označiť
   ako odoslané**. **Vrátiť do konceptu** výkaz znova otvorí.

Generovanie sa zastaví, ak chýba IČO, DIČ, číslo platiteľa alebo poisťovňa,
ak zamestnanec nemá platné rodné číslo alebo ak za mesiac neexistuje žiadna
výplatná páska.

## Obsah výkazu {#output}

| Časť | Obsah |
|---|---|
| `Identification` | typ 514, charakter *N*, IČO, číslo platiteľa, štvormiestny kód poisťovne (2500, 2400, 2700), dátum odoslania, poradové číslo 1, počet viet |
| `CorporateBody` | obdobie, deň platby, názov spoločnosti, IČO, číslo platiteľa, DIČ, IBAN |
| `InsuranceBody` | úhrny za zamestnávateľa: počet zamestnancov, dni, príjem, vymeriavací základ, preddavky zamestnávateľa a zamestnancov, doplatok, spolu |
| `PersonData` | za zamestnanca: rodné číslo, dni, sadzba zamestnávateľa a zamestnanca, príjem, vymeriavací základ, preddavky, doplatok |

Sumy sa berú z riadkov výplatných pások: *HEALTHEMPLOYER* (preddavok
zamestnávateľa), *HEALTH* (preddavok zamestnanca) a doplatok do minimálneho
základu (*HEALTHDOPLATOK* alebo *HEALTH_DOPLATOK* podľa jadra). Vymeriavací
základ aj príjem sú *GROSS* zamestnanca. Sadzby sa neberú z tabuľky, spätne sa
dopočítajú ako preddavok ÷ základ.

**Kontrola súboru.** Oficiálna schéma `514-2023.xsd` si protirečí (vzory,
ktoré pripúšťajú len jednu číslicu v poliach s dĺžkou 8 až 12 znakov,
nemožné číselné hranice), takže ňou neprejde žiadny skutočný súbor. Modul ju
preto spustí bez zastavenia a namiesto nej kontroluje štruktúru: koreňový
element, tri bloky hlavičky a zhodu počtu viet.

## Obmedzenia {#limitations}

- **Poisťovňa je údaj zamestnanca, nie mesiaca.** Zmenu poisťovne počas roka
  (možnú raz ročne, od 1. januára) treba pred generovaním zapísať pri
  zamestnancovi; staršie výkazy sa neprepočítajú.
- **Vymeriavací základ je GROSS z výplatnej pásky**, nie základ vypočítaný
  podľa zákona o zdravotnom poistení; zobrazená sadzba sa odvodzuje z neho.
- Každý zamestnanec má plný počet kalendárnych dní mesiaca a všetci sa
  vykazujú v prvej skupine (druhá skupina počtov a základov je vždy nulová).
- Len riadny výkaz (*N*) s poradovým číslom 1. Opravy po chybovom protokole
  treba urobiť cez elektronickú pobočku poisťovne.
- Keďže oficiálnu schému nemožno uplatniť, modul nezaručí, že poisťovňa súbor
  prijme. Prvý výkaz odsúhlaste s poisťovňou.
