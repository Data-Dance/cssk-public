---
title: Mzdová hlášení CZ/SK
summary: Společný základ českých a slovenských mzdových hlášení — nabídka Mzdová hlášení, postup Vygenerovat / Označit jako odeslané, opravná hlášení, verze tiskopisů a čtení výplatních pásek z obou mzdových jader.
verified: 19.0.1.5.0
---

## K čemu slouží {#purpose}

Každé české a slovenské mzdové hlášení v této lokalizaci — měsíční přehledy
sociálního a zdravotního pojištění, daňová hlášení, evidenční listy
důchodového pojištění, oznámení o nástupu a skončení — je samostatný modul.
Všechna fungují stejně, protože stojí na tomto modulu. Tato stránka popisuje
to, co mají společné; obsah jednotlivých tiskopisů popisují jejich vlastní
stránky.

Modul přidává nabídku **Mzdová hlášení**, tabulku verzí tiskopisů a mechanismus
každého hlášení: období, stavy, export XML s kontrolou proti schématu,
opravná hlášení a čtení výplatních pásek. Nezávisí ani na Odoo Enterprise
*Mzdy*, ani na OCA aplikaci *payroll*; výplatní pásky čte z té, která je
nainstalována. Nainstaluje se sám jako závislost tiskopisů a samostatně nedělá
nic.

## Tiskopisy, které na něm stojí {#forms}

| Země | Modul | Tiskopis | Komu se podává |
|---|---|---|---|
| SK | [module:l10n_sk_hr_payroll_mvp](module:l10n_sk_hr_payroll_mvp) | Mesačný výkaz poistného a príspevkov | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_vpp](module:l10n_sk_hr_payroll_vpp) | Výkaz poistného a príspevkov (nepravidelný príjem) | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_rlfo](module:l10n_sk_hr_payroll_rlfo) | Registračný list fyzickej osoby — přihlášení a odhlášení zaměstnanců | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_eldp](module:l10n_sk_hr_payroll_eldp) | Evidenčný list dôchodkového poistenia | Sociálna poisťovňa |
| SK | [module:l10n_sk_hr_payroll_health](module:l10n_sk_hr_payroll_health) | Mesačný výkaz preddavkov na poistné (dávka 514) | zdravotní pojišťovny |
| SK | [module:l10n_sk_hr_payroll_monthly_tax_overview](module:l10n_sk_hr_payroll_monthly_tax_overview) | Prehľad o zrazených a odvedených preddavkoch | Finančná správa |
| SK | [module:l10n_sk_hr_payroll_annual_tax_report](module:l10n_sk_hr_payroll_annual_tax_report) | Hlásenie o vyúčtovaní dane | Finančná správa |
| CZ | [module:l10n_cz_hr_payroll_pvpoj](module:l10n_cz_hr_payroll_pvpoj) | Přehled o výši pojistného (PVPOJ) | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_eldp](module:l10n_cz_hr_payroll_eldp) | Evidenční list důchodového pojištění | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_onz](module:l10n_cz_hr_payroll_onz) | Oznámení o nástupu / skončení zaměstnání | ČSSZ |
| CZ | [module:l10n_cz_hr_payroll_health](module:l10n_cz_hr_payroll_health) | Přehled o platbě pojistného zaměstnavatelem (PPPZ) a Hromadné oznámení zaměstnavatele (HOZ) | zdravotní pojišťovny |
| CZ | [module:l10n_cz_hr_payroll_annual_tax_settlement](module:l10n_cz_hr_payroll_annual_tax_settlement) | Vyúčtování daně z příjmů fyzických osob ze závislé činnosti | Finanční správa |

## Postup {#workflow}

Každý tiskopis má v nabídce *Mzdová hlášení* vlastní položku. Jedno hlášení
patří jedné společnosti a jednomu období:

1. **Nové**, pak zvolte **Rok** a **Měsíc**. Předvolen je aktuální měsíc,
   proto ho u hlášení za minulý měsíc změňte. Hlášení zobrazí první a poslední
   den období. *Datum výplaty* je den výplaty, který se uvádí tam, kde ho
   tiskopis vyžaduje (na slovenských tiskopisech *denVyplaty*); není-li
   vyplněno, použije se konec období.
2. Zkontrolujte **Verzi** (viz [Verze tiskopisů](#versions)). Výběr nabízí
   jen verze připravovaného tiskopisu.
3. Klikněte na **Vygenerovat**. Modul ověří kmenové údaje, které tiskopis
   potřebuje (každý tiskopis přidává vlastní kontroly — identifikátory
   společnosti, rodná čísla, adresy), shromáždí výplatní pásky období, sestaví
   řádek za každého zaměstnance, vytvoří XML, ověří ho proti oficiálnímu XSD
   schématu a přiloží ho. Stav se změní na *Vygenerováno*.
4. Stáhněte XML a podejte ho na portálu příslušného úřadu. Žádný tiskopis
   z této skupiny nic sám neodesílá.
5. Klikněte na **Označit jako odeslané**. Vygenerované XML se stane **Podaným
   XML**, přidá se do **Historie podání**, zaznamená se datum a hlášení se
   uzamkne: nelze ho znovu vygenerovat ani smazat.
6. **Vrátit do konceptu** ho opět odemkne. Podaná kopie i historie zůstanou
   zachovány, takže to, co bylo skutečně podáno, zůstane zaznamenáno i tehdy,
   když se údaje později přegenerují.

Před generováním výplatní pásky období potvrďte: pásky v konceptu se
nezapočítají (viz [Které výplatní pásky se započítají](#payslips)).

Generování se zastaví se zprávou, nemá-li období žádné výplatní pásky,
neplatí-li žádná verze nebo neprojde-li XML kontrolou proti schématu. Každý
krok se zapíše do chatteru.

## Opravná hlášení {#corrections}

Úřady přijímají opravy již podaných hlášení a každý je nazývá jinak —
*opravné*, *dodatečné*, *storno*. Hlášení má pole **Typ opravy** s nejvýše
čtyřmi hodnotami, zobrazenými anglicky:

| Hodnota | Význam |
|---|---|
| Regular | řádné hlášení za období |
| Corrective | opravné — nahrazuje již podané hlášení |
| Supplementary | dodatečné — doplňuje již podané hlášení, které nadále platí |
| Cancellation | storno — ruší hlášení, které nemělo být podáno |

Tiskopis nabízí jen ty hodnoty, které jeho úřad přijímá a které byly ověřeny
proti pravidlům úřadu. V současnosti:

| Tiskopis | Nabízené typy |
|---|---|
| SK Prehľad o zrazených a odvedených preddavkoch | Regular, Corrective |
| SK Hlásenie o vyúčtovaní dane | Regular, Corrective, Supplementary |
| CZ PPPZ | Regular, Corrective |
| všechny ostatní | jen Regular — opravy podávejte na portálu |

U jiného typu než *Regular* odmítne **Vygenerovat** pokračovat, dokud není
hlášení téhož tiskopisu za tutéž společnost a období ve stavu *Odesláno* —
oprava něčeho, co nebylo podáno, by byla odmítnuta. Období se porovnává podle
prvního a posledního dne, takže u ročního tiskopisu nezáleží na tom, v jakém
měsíci bylo hlášení založeno. Potřebuje-li úřad opravu
spárovat s původním hlášením, zadejte jeho označení do pole **Reference
opravy**.

Opravné hlášení se sestaví z výplatních pásek období v jejich aktuálním stavu,
stejně jako řádné; viz [Omezení](#limitations).

## Které výplatní pásky se započítají {#payslips}

Neuvádí-li stránka tiskopisu jinak, hlášení za období započítá každou
výplatní pásku společnosti, která

- **končí** v období — páska patří do období, do kterého připadá její
  koncové datum, takže páska přesahující hranici měsíce nebo roku se
  započítá právě jednou, v období, kde končí, a
- je **potvrzená**: v jádře OCA ve stavu *Hotovo* (*Done*), v Enterprise
  *Potvrzeno* (*Validated*) nebo *Zaplaceno* (*Paid*). Pásky v konceptu
  (a v jádře OCA pásky *Čekající*) se nezapočítají, stejně jako zrušené.
  Před kliknutím na *Vygenerovat* pásky období potvrďte.

Z těchto pásek modul sečte řádky podle kódu mzdového pravidla, za každého
zaměstnance i celkem. Kódy pravidel se v jádře Enterprise a OCA mírně liší
(například slovenská záloha na daň je v jádře OCA jeden řádek a v Enterprise
jeden řádek za každé daňové pásmo); modul zná oba zápisy, takže tiskopis dá
v obou jádrech stejný výsledek.

Řádek zaměstnance obsahuje ve výchozím stavu také:

| Údaj | Odkud se bere |
|---|---|
| vyměřovací základ (*Vyměřovací základ*) | **hrubá mzda (GROSS)** zaměstnance za období |
| dny pojištění (*Dny pojištění*) | dny zaměstnání v období podle všech verzí smlouvy zaměstnance (začátek a konec smlouvy); celé období, nemá-li žádná verze datum začátku smlouvy |
| odpracované hodiny (*Odpracované hodiny*) | hodiny všech řádků odpracovaných dnů, včetně nepřítomností |

Jednotlivé tiskopisy tyto hodnoty převezmou, nebo si je spočítají samy;
viz stránka tiskopisu.

## Verze tiskopisů {#versions}

Úřady čas od času mění tiskopisy a schémata. Každý vzor tiskopisu je záznam
v *Mzdová hlášení → Konfigurace → Verze hlášení*: kód hlášení, země,
**Platné od** / **Platné do**, šablona XML, očekávaný kořenový element
a soubor XSD. Nový vzor se dodává jako nový záznam verze s vlastní šablonou
a schématem; staré vzory zůstávají k dispozici.

Nové hlášení navrhne verzi svého tiskopisu platnou **dnes** v zemi vaší
aktuální společnosti a při změně roku nebo měsíce ji změní. Rozhodne
**Vygenerovat**: přepne na verzi tohoto tiskopisu platnou pro období (roční
tiskopis se řídí 1. lednem, tiskopis o událostech jejich daty) a období, na
které se žádná verze nevztahuje, odmítne. Byl-li tiskopis zrušen — verze
s *Platné do* bez nástupce — zpráva to uvede a, ví-li to tiskopis, řekne, co
ho nahradilo. Verze může číst každý interní
uživatel a spravuje je *Zaměstnanci / Administrátor*; běžně je neupravujete.

## Nastavení společnosti {#company}

Formulář české nebo slovenské společnosti má záložku **Mzdové výkazy**.
U české společnosti obsahuje identifikaci zaměstnavatele, kterou potřebují
tiskopisy ČSSZ: **Variabilní symbol ČSSZ (VS)** a **Kód OSSZ** místně
příslušné okresní správy sociálního zabezpečení. Bez nich tiskopisy odmítnou
generovat. Další moduly přidávají na stejnou záložku vlastní pole.

## Doručení a potvrzení {#delivery}

*Označit jako odeslané* zaznamená, že někdo XML podal, a otevře k němu
**doručení** ve stavu *Koncept* — záznam, který eviduje, jak se XML dostalo na
úřad, zda bylo přijato, a potvrzení, která to dokládají. Doručení patří modulu
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base), který
používá každé mzdové hlášení; najdete je v *Účetnictví → Výkazy → Zákonné
výkazy → Doručení*. Viz [Podání výkazu](module:l10n_cssk_submission_base#usage).

## Omezení {#limitations}

- **Opravy předchozích měsíců se neoddělují.** Páska se započítá do měsíce
  svého vlastního období. Doplatek nebo oprava za dřívější měsíc zadaná na
  pásce tohoto měsíce se vykáže v tomto měsíci; nevytvoří opravné hlášení za
  dřívější měsíc ani se do něj nepřesune. Opravné hlášení se sestaví z pásek
  opravovaného měsíce v jejich aktuálním stavu, nikoli jako rozdíl proti
  podanému, takže dodatečné hlášení (*Supplementary*) obsahuje celé částky,
  neřeší-li to šablona samotného tiskopisu. Před podáním opravu porovnejte
  s podanou kopií.
- **Rok** lze zvolit od 2020 do příštího roku.
- **Podání se jen zaznamenává, neprovádí.** Tento modul ani tiskopisy na něm
  postavené nic úřadům neodesílají.
- **Kontrola proti schématu ověřuje tvar, ne částky.** První hlášení každého
  tiskopisu odsouhlaste ručně.
