---
title: CZ Vyúčtování daně z příjmů ze závislé činnosti (DPZVD)
summary: Roční vyúčtování daně z příjmů ze závislé činnosti zaměstnavatele pro Finanční správu — zálohy na daň za jednotlivé měsíce, měsíční počty zaměstnanců a příloha č. 1 (zaměstnanci podle obcí) jako XML pro EPO ve struktuře DPZVD6.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Každý plátce daně, který v roce zúčtoval nebo vyplatil příjmy ze závislé
činnosti, podává svému správci daně *vyúčtování daně z příjmů fyzických
osob ze závislé činnosti vybírané srážkou formou záloh* — roční přehled
sražených záloh.

Modul připraví vyúčtování za kalendářní rok z výplatních pásek tohoto roku
a vyexportuje ho jako XML pro EPO (`<Pisemnost>` s jednou větou `<DPZVD6>`),
ověřené proti dodanému schématu `dpzvd6_epo2.xsd`. Výplatní pásky čte přes
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
takže funguje s oběma jádry českých mezd — viz
[příručku českých mezd](module:l10n_cz_hr_payroll_base#declarations).

Nejde o **roční zúčtování záloh** zaměstnance; to se provádí u každého
zaměstnance přímo v mzdovém modulu.

**Modul vyplní jen část tiskopisu** — viz [Omezení](#limitations).

## Právní rámec {#legal}

Odkazy směřují na [zákon o daních z příjmů](law:cz/1992/586).

- **Kdo podává.** Plátce daně, který ve zdaňovacím období zúčtoval nebo
  vyplatil příjmy ze závislé činnosti, podává vyúčtování místně příslušnému
  správci daně (§ 38j odst. 4), a to i tehdy, když mu kvůli slevám na dani
  nevznikla povinnost nic odvést (§ 38j odst. 9).
- **Kdy.** Do dvou měsíců po uplynutí kalendářního roku, při elektronickém
  podání do **20. března** (§ 38j odst. 5). Lhůtu nelze prodloužit (§ 38j
  odst. 7).
- **Přílohy.** K vyúčtování patří počet zaměstnanců k 1. prosinci podle
  obce místa výkonu práce, přehled o daňových nerezidentech a přehledy
  o dodatečných opravách (§ 38j odst. 8). Modul vytváří první z nich,
  *přílohu č. 1 — Počet zaměstnanců* (§ 38j odst. 1); ostatní ne.
- **Oddíl I, sloupec 1** tiskopisu (`kc_dpzi01`) je podle pokynů
  k vyplnění (MFin 5459/1) úhrn záloh na daň **po měsíčních slevách na
  dani** (§ 35ba, § 35c a § 35d), které měly být za příslušný měsíc sraženy;
  **sloupec 5** úhrn vyplacených měsíčních daňových bonusů. Řádek 1
  oddílu II je úhrn sloupce 1, řádek 4 úhrn sloupce 5.
- **Počet zaměstnanců** (bod 05) se uvádí za každý měsíc k poslednímu dni
  měsíce.
- **Příloha č. 1** uvádí počet zaměstnanců k 1. prosinci podle obce místa
  výkonu práce, určené kódem ZÚJ (*základní územní jednotka*). U dohod (DPP,
  DPČ) je místem výkonu práce sídlo zaměstnavatele.

## Nastavení {#setup}

Na společnosti:

| Údaj | Použije se jako |
|---|---|
| *DIČ* | `dic` ve větě `VetaP`: jeho číslice, nejvýše 10 |
| *Kód finančního úřadu (FÚ)*, 1 až 4 číslice | `c_ufo_cil`, finanční úřad, kterému vyúčtování patří |
| *Typ podávajícího subjektu* | `typ_ds`: *F — fyzická osoba*, *P — právnická osoba* (výchozí) nebo *L — plátcova pokladna* |
| *Kód obce (ZÚJ)*, 6 číslic, a *Název obce (ZÚJ)* | obec vlastní adresy společnosti (sídla) v příloze č. 1 |
| název, obec, PSČ | identifikace plátce |

*Kód finančního úřadu (FÚ)*, *Typ podávajícího subjektu* a obě pole ZÚJ jsou
na záložce **Mzdové výkazy** formuláře společnosti (viz
[základ mzdových hlášení](module:l10n_cssk_payroll_declaration_base#company)).

Pro přílohu č. 1 potřebuje kód ZÚJ také každá adresa, která je místem výkonu
práce zaměstnance. Místem výkonu práce je **Pracovní adresa** na verzi
smlouvy zaměstnance; dohody (DPP, DPČ) a zaměstnanci bez pracovní adresy se
počítají na vlastní adrese společnosti. U českého kontaktu nebo adresy jsou
pole *Kód obce (ZÚJ)* a *Název obce (ZÚJ)* na záložce
*Nákup a Prodej* ve skupině *Různé*. Kód i název převezměte z registru
Finanční správy *Obce ZUJ*.

## Sestavení vyúčtování {#usage}

*Mzdová hlášení → CZ Roční vyúčtování daně (daň z příjmů)*, pak *Nový*.

1. Zvolte **Rok**. Obdobím je 1. leden až 31. prosinec.
2. Klikněte na **Vygenerovat**. Modul vybere všechny potvrzené výplatní
   pásky společnosti, jejichž období v daném roce končí (koncepty a zrušené
   se nezapočítají; viz [základ mzdových hlášení](module:l10n_cssk_payroll_declaration_base#payslips)),
   sestaví XML, ověří ho proti schématu a přiloží.
3. Otevřete XML v aplikaci EPO Finanční správy, doplňte části, které modul
   nevyplňuje, podejte ho a klikněte na **Označit jako odeslané**.

Generování se zastaví, nemá-li společnost DIČ nebo kód finančního úřadu,
nebo není-li v roce žádná výplatní páska. Zastaví se také, se seznamem adres,
nemá-li některé místo výkonu práce započtené v příloze č. 1 šestimístný kód
ZÚJ.

## Co vyúčtování obsahuje {#output}

| Položka | Zdroj |
|---|---|
| zdaňovací období, tiskopis `VD6`, typ `B` (řádné) | zvolený rok |
| oddíl I, řádek za každý měsíc (`VetaO`): sloupce 1 a 2 | záloha po měsíčních slevách: řádek daně z příjmů (`INCOMETAX`) výplatních pásek daného měsíce snížený o slevy na dani (`TAXCREDIT`) a o daňové zvýhodnění uplatněné jako sleva (`CHILDBEN`) — v obou sloupcích stejná částka |
| oddíl I, sloupec 5 (`kc_dpzi05`) | daňové bonusy vyplacené v daném měsíci (`CHILDBONUS`), pokud nějaké jsou |
| oddíl II, řádek 1 (`kc_dpzii01`) | úhrn sloupce 1 |
| oddíl II, řádek 4 (`kc_dpzii03a`) | úhrn sloupce 5, pokud nějaký je |
| počet zaměstnanců za měsíc (`poc_zam1`–`poc_zam12`) | zaměstnanci s výplatní páskou v daném měsíci, jejichž pracovní poměr trvá ještě poslední den měsíce |
| plátce (`VetaP`) | DIČ, název, obec, PSČ, typ podávajícího subjektu |
| příloha č. 1 (`VetaB`), řádek za každou obec | zaměstnanci s potvrzenou výplatní páskou v roce, kteří jsou k 1. prosinci v zaměstnání, sečtení podle kódu ZÚJ (a názvu obce) místa výkonu práce |

Výplatní páska se přiřadí k měsíci, ve kterém končí její období.

## Omezení {#limitations}

- **Jen sloupce 1, 2 a 5 oddílu I a řádky 1 a 4 oddílu II.** Ostatní řádky
  oddílu II (roční zúčtování, vrácené přeplatky, opravy, odvedené částky),
  ostatní sloupce oddílu I, přílohy kromě přílohy č. 1 a přehledy
  o nerezidentech (`VetaC`, `VetaH`) je třeba doplnit.
- **Daň vybíraná srážkou** podle zvláštní sazby (u malých dohod) se
  nezahrnuje; vykazuje se v samostatném vyúčtování, které modul nevytváří.
- **Počty zaměstnanců** vycházejí ze zaměstnanců s výplatní páskou v měsíci;
  kdo k poslednímu dni měsíce trvá v zaměstnání, ale v měsíci nemá výplatní
  pásku, se nezapočte.
- Sloupec 2 (původně sražené zálohy) se vždy rovná sloupci 1, takže opravy
  provedené podle § 38i se neprojeví.
- Jen řádné vyúčtování (typ *B*); opravné nebo dodatečné je třeba připravit
  v EPO. Schéma je jediný soubor s pevnou hodnotou `verzePis` *1.0*; nic
  v modulu nekontroluje, zda je stále aktuální.
- Ověření proti schématu kontroluje tvar souboru, ne částky. Žádné
  vyúčtování z tohoto modulu dosud nebylo potvrzeno ostrým podáním.
