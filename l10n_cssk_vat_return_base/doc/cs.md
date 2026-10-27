---
title: Přiznání k DPH CZ/SK — společný základ
summary: Obrazovky a postup, na kterých stojí české i slovenské přiznání k DPH — výpočet řádků z daňových štítků, kontrola proti účetním záznamům, export úředního XML a uchování podané verze.
verified: 19.0.1.11.0
---

## K čemu slouží {#purpose}

Modul je společným jádrem přiznání k DPH (v Česku *přiznání k DPH*, na
Slovensku *daňové priznanie k DPH*). Sám o sobě nic nepodává: samotný
formulář — jeho řádky, úřední XSD schéma a pravidla dané země — dodává modul
[module:l10n_cz_vat_return](module:l10n_cz_vat_return) nebo
[module:l10n_sk_vat_return](module:l10n_sk_vat_return). Tento modul přidává
vše, co mají obě země společné:

- obrazovku **Přiznání k DPH**, kde se přiznání zakládá, počítá, kontroluje,
  exportuje a označuje jako podané;
- **verze formuláře**, které určují, jaké řádky, jaká XML šablona a jaké XSD
  schéma platí pro která období;
- výpočet, který sčítá zaúčtované položky podle **daňových štítků**, takže
  funguje stejně v edici Community i Enterprise bez výkaznického nástroje Odoo;
- proklik z každého řádku na účetní záznamy, ze kterých vznikl;
- uchování podané verze, dodatečná a opravná přiznání a historické sazby daně
  pro import starších dokladů.

## Před prvním přiznáním {#setup}

- **Společnost** musí mít vyplněné DIČ (pole *DIČ*) — bez něj export neproběhne —
  a svůj finanční úřad: *Účetnictví → Konfigurace → Nastavení*, pole **Finanční
  úřad**, případně totéž pole na kartě společnosti.
- **Modul země** musí být nainstalovaný. Přináší verze formuláře, bez kterých
  nelze nic vypočítat.
- **Přístupová práva.** Účetní může přiznání zakládat, počítat a exportovat.
  Upravovat verze formuláře a **vrátit podané přiznání do konceptu** může jen
  administrátor účetnictví.

## Příprava přiznání {#usage}

*Účetnictví → Výkazy → Zákonné výkazy → Přiznání k DPH*, potom *Nový*.

| Pole | Co vyplnit |
|---|---|
| Společnost | Společnost, za kterou se podává (výchozí je aktuální). |
| Datum od / Datum do | První a poslední den zdaňovacího období. |
| Typ období | *Měsíčně* nebo *Čtvrtletně* — do XML se zapíše měsíc nebo čtvrtletí podle *Data od*. |
| Verze | Verze formuláře. Nabízejí se jen verze země společnosti platné v daném období, viz [Verze formuláře](#versions). |
| Typ výkazu | Řádné, opravné nebo dodatečné — možnosti určuje verze. |

Potom klikněte na **Vypočítat**. Přiznání přejde do stavu *Náhled* a záložka
**Řádky** se naplní řádky formuláře.

**Které doklady patří do období.** Obě strany přiznání se datují jinak, tak jak
je datuje zákon:

- **Faktury a opravné daňové doklady odběratelům** se zahrnou do období podle
  **DUZP**; pokud ho nemají, rozhoduje datum účetního případu.
- **Přijaté faktury a ostatní doklady** se zahrnou podle **data účetního
  případu**, protože to je obvyklé období uplatnění odpočtu. Interní doklad s
  DUZP se řídí tímto datem.
- Má-li doklad vyplněné **Deklarované období DPH** (pole jádra lokalizace),
  rozhoduje toto pole na obou stranách — u odpočtu uplatněného později než
  plnění nebo u opravy přiznané v období, kdy opravný daňový doklad dorazil.

Čtou se jen zaúčtované záznamy s daňovými štítky.

## Kontrola řádků {#lines}

Každý řádek má kód (kód formuláře, např. `obrat23` nebo `r03`), název a
**Hodnotu**. Řádek je jednoho ze tří druhů:

- **daňové štítky** — součet zůstatků účetních položek se štítky řádku se
  znaménkem. Sloupec ✓ ukazuje, zda proklik dává stejnou částku, a **Doklady**
  otevře tyto položky seskupené podle dokladu;
- **souhrn** — vzorec nad jinými řádky (zobrazený šedě, vzorec je ve sloupci
  *Odvození*);
- **ručně** — údaj, který účetnictví neumí dodat (převáděný nadměrný odpočet,
  koeficient, rozdíl oproti dřívějšímu přiznání). Dokud ho nezadáte, je
  nulový.

Chcete-li údaj zadat nebo opravit, zapněte na řádku **Přepis**, vepište
**Ruční hodnotu** a znovu stiskněte **Vypočítat**. Přepsané řádky jsou
zvýrazněné, při každém přepočtu si hodnotu ponechají a vstupují do souhrnných
řádků, které na nich závisejí.

V záhlaví se zobrazí **Řádky souhlasí**, pokud každý řádek ze štítků souhlasí
se svými položkami, jinak červené tlačítko **Nesouhlasící řádky** se seznamem
těch, které nesouhlasí. Řádek, který bere jen svůj podíl štítku (rozdělení
specifické pro zemi, např. slovenské řádky § 69 ods. 3 před rokem 2021), se
prokliká a porovnává jen s tímto podílem.

## Vypořádání a nadměrný odpočet {#settlement}

Záložka **Vypořádání** sleduje nadměrný odpočet z jednoho období do dalšího:

| Pole | Význam |
|---|---|
| Předchozí období | Přiznání předcházejícího období. |
| Nadměrný odpočet z předchozího období | Co předchozí přiznání převedlo; **Převést nadměrný odpočet** ho (i *Předchozí období*) z něj doplní. |
| Nadměrný odpočet k převodu | Část nadměrného odpočtu tohoto období, kterou si nenecháte vrátit; nesmí převýšit nadměrný odpočet období. |
| K úhradě / (vrácení) | Vlastní daň − nadměrný odpočet − převedeno z minula + převedeno dál; kladná částka je daň k úhradě, záporná vrácení. |

Pole lze měnit, dokud je přiznání v konceptu nebo náhledu. Které řádky jsou
vlastní daň a nadměrný odpočet, určuje verze formuláře dané země; záložka
žádný řádek formuláře nemění.

## Export XML {#export}

**Exportovat XML** (ve stavu *Náhled* nebo *Exportováno*) provede v tomto
pořadí:

1. kontrolu, zda má společnost DIČ;
2. obsahové kontroly, které definuje modul země; chyba export zastaví a
   pojmenuje porušené pravidlo;
3. vygenerování XML podle šablony verze;
4. ověření proti úřednímu XSD schématu verze. Verze bez schématu export
   odmítne, místo aby vytvořila neověřený soubor.

Soubor se připojí k přiznání (*XML příloha*) a přiznání přejde do stavu
*Exportováno*. Přepočítat a exportovat ho můžete opakovaně, dokud ho
neoznačíte jako podané.

## Podání a podaná verze {#submission}

XML podejte na portálu finanční správy, nebo přes modul podacího kanálu, jako
je [module:l10n_cz_epo](module:l10n_cz_epo). Potom:

- **Označit jako podané** zmrazí exportované XML jako podanou verzi, přidá ho
  do **Historie podání**, zaznamená datum a přidá poznámku do chatteru. Zároveň
  založí záznam o doručení ve stavu koncept — místo pro potvrzení z portálu.
  Jeho stav ukazuje záhlaví v poli **Doručení**.
- **Podat** otevře (nebo založí) tento záznam o doručení. Je-li nainstalováno
  víc kanálů, vyberete si; je-li jen ruční kanál, zaznamená, kdo přiznání podal
  na portálu, a uchová potvrzení.
- Podané přiznání je zamčené: nelze ho přepočítat, znovu exportovat ani
  smazat. **Vrátit do konceptu** (jen administrátor) ho znovu otevře; podaná
  verze i historie zůstanou zachovány.

## Opravné a dodatečné přiznání {#amendments}

Na podaném přiznání tlačítko **Dodatečné / opravné** založí nový koncept
propojený s původním (*Opravuje*) a přenese do něj ruční přepisy. Na novém
přiznání:

1. zvolte správný **Typ výkazu** — kopie začíná typem původního přiznání;
2. vyplňte **Den zjištění rozdílu**, který formulář u přiznání opravujícího
   jiné vyžaduje (výchozí je dnešní den);
3. opravte účetnictví, **Vypočítejte**, zkontrolujte, exportujte a podejte jako
   obvykle.

Co dále vyžaduje formulář konkrétní země (například české pole *Důvody
zjištěny dne*), popisuje stránka modulu země.

## Verze formuláře {#versions}

*Účetnictví → Konfigurace → CZ/SK lokalizace → Verze přiznání k DPH* ukazuje
verze dodané moduly zemí. Každá obsahuje období platnosti, řádky se vzorci
štítků nebo souhrnnými vzorci, typy podání, XML šablonu a XSD schéma. Jsou to
data modulu země: měňte je jen na pokyn účetního. Archivovaná verze se u
přiznání za svá období nabízí dál, archivací se jen zpřehlední seznam.

## Historické sazby DPH {#historic-rates}

Když společnost načte českou nebo slovenskou účtovou osnovu (a při instalaci
modulu země), vytvoří se sazby platné před dnešními jako **archivované** daně,
zkopírované z dnešní daně stejného druhu, aby se vykazovaly ve stejných
řádcích. Slouží k importu starších dokladů; při vystavování nové faktury se
nikdy nenabídnou. Najdete je v *Účetnictví → Konfigurace → Daně* s filtrem
*Archivováno* a **Historická sazba**; formulář daně ukazuje **Sazba platná
od**, **Sazba platná do** a **Odvozeno z**. Které sazby se vytvářejí, uvádí
stránka modulu země. Chcete-li je pro společnost vytvořit znovu (opakování je
bezpečné), otevře správce účetnictví společnost v *Nastavení → Společnosti*
a v nabídce *Akce* spustí **Vytvořit historické sazby DPH**.

Pokud historická sazba existuje, jiné moduly lokalizace podle ní zdaní doklad
sazbou platnou k jeho datu.

## Historická podání {#legacy}

Přiznání převzaté z předchozího systému je **Historické podání**: záznam o
tom, co bylo podáno, označený stuhou. Nelze ho přepočítat, exportovat ani
podat. Jediná akce, **Porovnat s vypočteným**, přepočítá období z účetnictví a
zaznamená rozdíly v *Účetnictví → Výkazy → Zákonné výkazy → Podané vs
vypočtené*. Je-li třeba takové období opravit, založte z něj dodatečné
přiznání; to už je běžné přiznání.

## Omezení {#limitations}

- Verzi za vás nikdo nevybere: zvolte ji u každého přiznání. Nekontroluje se,
  zda data tvoří celý měsíc nebo čtvrtletí. *Typ období* se kontroluje jen
  proti obdobím, která verze připouští (každá dodaná verze připouští obě).
- Kontrola sazby, která jen varuje (odvozená sazba neodpovídá žádné zákonné),
  se zapíše pouze do serverového logu a na obrazovce se nezobrazí; export
  zastaví jen chyby.
- Sloupec ✓ porovnává absolutní částky, chybu ve znaménku tedy neukáže.
- Dodatečné přiznání převezme typ výkazu původního; změnit ho musíte sami.
- Výpočet ukáže to, co říkají štítky. Daň se špatnými štítky nebo doklad bez
  štítků skončí ve špatném řádku nebo v žádném; před podáním si projděte
  proklik **Doklady**.
