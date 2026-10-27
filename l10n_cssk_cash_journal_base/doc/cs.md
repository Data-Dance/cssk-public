---
title: Peněžní deník CZ/SK
summary: Peněžní deník odvozený z běžného účetnictví v Odoo — každá úhrada se stane datovaným, očíslovaným řádkem v příslušném členění, pro OSVČ s daňovou evidencí nebo pro slovenské jednoduché účtovníctvo.
verified: 19.0.1.6.3
---

## K čemu slouží {#purpose}

OSVČ, která nevede účetnictví, musí přesto evidovat příjmy a výdaje **v
okamžiku jejich úhrady** a v členění, které potřebuje daňové přiznání — v
**peněžním deníku**. Odoo samo vede jen podvojné účetnictví.

Modul ho nenahrazuje. Fakturujete, platíte, importujete bankovní výpisy a
podáváte DPH v Odoo jako dosud; peněžní deník je **samostatná, uložená kniha
vygenerovaná ze zaúčtovaných dokladů**:

- samotná faktura do deníku nic nezapíše — řádek vytvoří teprve **úhrada**;
- úhrada se přes párování dohledá k faktuře, kterou uhradila, takže řádek nese
  **kategorii** toho, co se skutečně prodalo nebo koupilo (zboží, služby,
  mzdy…), ne jen „banka“;
- DPH z každé úhrady je ve vlastním sloupci, odděleně od částky, která vstupuje
  do základu daně z příjmů;
- řádky jsou v rámci roku očíslovány v časovém pořadí a zůstávají tak, dokud
  deník znovu nevygenerujete.

Toto je společný základ. Národní katalog kategorií, tisk deníku v národním
uspořádání a údaje pro daňové přiznání dodává modul země:

- [module:l10n_cz_cash_journal](module:l10n_cz_cash_journal) — Česko;
- [module:l10n_sk_cash_journal](module:l10n_sk_cash_journal) — Slovensko.

Nainstalujte modul své země; tento modul se nainstaluje s ním.

## Právní rámec {#legal}

Žádná ze zemí nepředepisuje software; zákon určuje obsah evidence.

- **Česko — daňová evidence.** Obsahuje údaje o příjmech a výdajích *„v
  členění potřebném pro zjištění základu daně“* a o majetku a dluzích —
  [§ 7b zákona o daních z příjmů](law:cz/1992/586). Pojem *peněžní deník*
  patří jednoduchému účetnictví podle
  [§ 13b zákona o účetnictví](law:cz/1991/563), které
  [§ 1f téhož zákona](law:cz/1991/563) umožňuje jen vybraným neziskovým
  subjektům, nikoli OSVČ.
- **Slovensko — daňová evidencia.** Evidence příjmů a daňových výdajů *„v
  časovom slede v členení potrebnom na zistenie základu dane“* a majetku,
  zásob, pohledávek a závazků —
  [§ 6 ods. 11 zákona o dani z príjmov](law:sk/2003/595#paragraf-6.odsek-11);
  při paušálních výdajích jen evidence příjmů, zásob a pohledávek —
  [§ 6 ods. 10](law:sk/2003/595#paragraf-6.odsek-10).
- **Slovensko — jednoduché účtovníctvo.** Účetními knihami jsou peňažný
  denník, kniha pohľadávok, kniha záväzkov a pomocné knihy —
  [§ 15 ods. 1 a 2 zákona o účtovníctve](law:sk/2002/431#paragraf-15.odsek-1);
  sloupce deníku stanoví § 4
  [opatrenia MF/27076/2007-74](law:sk/2007/628).

## Nastavení {#setup}

### Nastavení

*Účetnictví → Konfigurace → Nastavení*, blok **Peněžní deník**:

| Nastavení | Účel |
|---|---|
| Způsob vedení evidence | Podvojné účetnictví (výchozí), daňová evidence, jednoduché účetnictví (jen slovenské společnosti — české společnosti se odmítne) nebo paušální výdaje. Deník lze vygenerovat při každém způsobu; nastavení rozhoduje jen o tom, kterou tabulku stavů zobrazí údaje pro slovenské přiznání. |
| Rozdělení částečné úhrady | Jak se částečná úhrada rozdělí mezi základ daně a DPH: **poměrně** (výchozí, konvence Odoo), **nejprve DPH** nebo **nejprve základ**. Zvolte jeden způsob ve vnitřní směrnici a dodržte ho celý rok; při úplné úhradě dávají všechny tři stejný výsledek. |
| Přiřazení účtů | Tlačítko *Přiřadit účty ke kategoriím peněžního deníku* vyplní kategorii na každém účtu, který zná přiřazení dané země. Nikdy nepřepíše již nastavenou kategorii a lze je spustit znovu po doplnění účtů. |
| Začátek peněžního deníku | První den, od kterého se deník vede. Starší úhrady ignoruje — použijte při začátku v průběhu roku. |

### Kategorie na účtech

Odkud řádek bere kategorii, se určuje **na účtu**. Otevřete účet
(*Účetnictví → Konfigurace → Účtová osnova*) a jeho záložku **Peněžní deník**:

- **Kategorie peněžního deníku** — kategorie pro úhrady přes tento účet.
- **Kategorie peněžního deníku (příjem)** — jen pro účty, přes které jdou
  peníze oběma směry a každý směr patří do jiného sloupce: na účet úvěru přijde
  úvěr a odcházejí z něj splátky, přes účet DPH se daň odvádí a vrací se
  nadměrný odpočet. Pokryje-li oba směry jedna kategorie, nechte pole prázdné.

Modul země přiřadí národní účtovou osnovu automaticky — při instalaci a znovu
při každém načtení osnovy — ale vyplní jen prázdná pole. Účty pohledávek,
závazků a záloh se záměrně nepřiřazují; viz
[jak vznikají řádky](#rows).

Jednotlivý řádek faktury může kategorii účtu přepsat: v *Účetnictví →
Účetnictví → Účetní položky* zobrazte volitelný sloupec *Kategorie peněžního
deníku* a nastavte ji na řádku — například u faktury, která je zčásti zboží a
zčásti služby.

### Samotné kategorie

*Účetnictví → Účetnictví → Peněžní deník → Kategorie* (jen pro správce
účetnictví) zobrazí katalog dodaný modulem země. Každá kategorie má **druh** —
příjem, výdaj nebo průběžná položka — a dva příznaky:

- **Ovlivňuje základ daně** — vypnutý u osobní spotřeby, úvěru, odvodu DPH či
  zaplacené daně z příjmů;
- **Nepeněžní** — pro zápisy, při nichž se peníze nepohnuly, ale do deníku
  patří, typicky odpisy (viz [níže](#non-cash)).

**Kód v daňovém přiznání** určuje řádek daňového přiznání fyzické osoby, do
kterého kategorie vstupuje (SK DPFO typ B tabuľka 1, CZ Příloha č. 1);
nastavuje jej národní modul a podle něj se seskupují
[údaje pro daňové přiznání](#tax-return).

Průběžná položka nesmí ovlivňovat základ daně ani být nepeněžní; formulář to
odmítne. Můžete přidat vlastní kategorie; kód musí být v rámci země jedinečný.

## Generování deníku {#usage}

*Účetnictví → Účetnictví → Peněžní deník → Generovat*: zvolte období a
klikněte na **Generovat**.

- Řádky období se smažou a znovu vytvoří ze **zaúčtovaných** dokladů, takže
  opakované spuštění dá stejný deník.
- **Řádky označené *Ručně*** a řádky **ke dni uzamčení účetnictví nebo dříve**
  zůstanou. Období celé uzavřené dnem uzamčení vygenerovat nelze.
- Celý rok se přečísluje `2026/00001`, `2026/00002`, … v časovém pořadí.

Nic se neděje samo: úhrada zaúčtovaná dnes se v deníku objeví při nejbližším
generování. Výsledek se otevře v seznamu *Peněžní deník* s filtrem **Tento
rok**.

## Jak vznikají řádky {#rows}

Řádek vznikne při každém pohybu peněz na účtu bankovního nebo pokladního
deníku, na účtech čekajících plateb Odoo, na přechodném účtu banky a na účtu
interních převodů — v libovolném účetním deníku, takže se započítá i oprava v
*Různých operacích*, která pohne penězi. Tytéž peníze se započítají **jednou**:
úhrada už spárovaná s řádkem bankovního výpisu se objeví přes výpis, ne
dvakrát.

Od peněz se modul přes párování dostane k tomu, co bylo uhrazeno:

- **Faktura.** Úhrada se rozdělí podle řádků a sazeb DPH dokladu, takže
  faktura za zboží a služby dá dva řádky. Částečná úhrada se dělí podle
  nastavení *Rozdělení částečné úhrady*.
- **Přímý zápis** — bankovní poplatek, platba finančnímu úřadu — dostane
  kategorii protiúčtu.
- **Vrácená částka** (opravný daňový doklad, vratka od dodavatele) je
  **storno**: sníží vlastní sloupec, místo aby se objevila v opačném. Prodej
  1 000 a vratka 200 znamená příjem 800, ne příjem 1 000 a výdaj 200.
- **Převod mezi vlastní bankou a pokladnou** je průběžná položka, ani příjem,
  ani výdaj.
- **Úhrada na pohledávce nebo závazku bez dokladu** — obvykle záloha — se
  zařadí do kategorie účtu, má-li ji, jinak se označí ke kontrole. Sloupec
  závisí na tom, za co záloha je, a to víte jen vy. Zálohová faktura zaúčtovaná
  na účet konečného plnění nese kategorii toho účtu.

Každý řádek má částku, která vstupuje do základu daně (u plátce DPH bez daně),
a zvlášť **DPH**; u neplátce část DPH chybí.

### Nepeněžní řádky {#non-cash}

Odpis je výdaj, při kterém se banka nepohne, zatímco úhrada za samotný majetek
výdajem není. Každý zaúčtovaný řádek na účtu s kategorií označenou
**Nepeněžní** se stane řádkem bez peněžního sloupce, mimo bankovní a pokladní
deníky. Započítá se do základu daně, ne do peněžních součtů.
Stornovaný nebo dobropisovaný odpis je **storno**: sloupec odpisů snižuje,
nepřičte se k němu.

## Řádky ke kontrole {#review}

Modul nic neodhaduje. Když nedokáže rozhodnout, řádek přesto zapíše s částkou,
ale zvýrazní ho a označí **Ke kontrole** s důvodem:

| Důvod | Co udělat |
|---|---|
| Účet … nemá kategorii peněžního deníku. | Nastavte kategorii na účtu (nebo na řádku dokladu) a deník znovu vygenerujte. |
| Peníze přišly / odešly přes …, který má kategorii … | Přes účet jdou peníze oběma směry: nastavte na něm *Kategorii peněžního deníku (příjem)*. |
| Platba na … není spárována s dokladem — záloha? | Přiřaďte účtu kategorii nebo spárujte úhradu s fakturou a deník znovu vygenerujte. |
| Peníze na cestě přes … bez kategorie průběžné položky. | Přiřaďte účtu kategorii průběžné položky. |
| Řetězec párování je delší než 5 kroků; vyřešte jej ručně. | Dohledejte a opravte párování ručně. |

*Účetnictví → Účetnictví → Peněžní deník → Ke kontrole* je zobrazí všechny.
Opravte příčinu — účet, řádek dokladu, párování — a deník **znovu
vygenerujte**, místo úpravy řádku: upravený vygenerovaný řádek se při dalším
generování nahradí.

Řádek můžete přidat i ručně v seznamu *Peněžní deník*. Zaškrtněte u něj
**Ručně**, jinak ho nejbližší generování smaže.

## Tisk {#print}

*Účetnictví → Účetnictví → Peněžní deník → Tisk*: zvolte období a výstup.

- **PDF** — deník v národním uspořádání z modulu země. Bez něj vás tlačítko
  upozorní; vytiskněte raději tabulku.
- **Tabulka** — sešit XLSX se všemi řádky období (číslo, datum, doklad,
  partner, kategorie, druh, peníze, příjem, výdej, DPH, storno, základ daně,
  nepeněžní, kontrola) a listem **součtů za kategorie**. Slovenský modul přidá
  na začátek list se zákonným uspořádáním.

## Údaje pro daňové přiznání {#tax-return}

Moduly zemí z deníku připraví údaje, které žádá přiznání k dani z příjmů
fyzických osob: příjmy a výdaje z deníku a stavy na začátku a na konci roku z
hlavní knihy. Viz
[údaje pro Přílohu č. 1](module:l10n_cz_cash_journal#priloha) a
[údaje pro slovenské DPFO typ B](module:l10n_sk_cash_journal#dpfo).

## Omezení {#limitations}

- **Deník je jen tak dobrý jako přiřazení účtů.** Každý nepřiřazený účet
  vytváří řádky ke kontrole; před každým tiskem zkontrolujte *Ke kontrole*.
- **Generuje se ručně.** Deník sám nové úhrady nesleduje.
- **Úprava vygenerovaného řádku nevydrží.** Generování ho nahradí. Označíte-li
  ho *Ručně*, váš řádek zůstane, ale generování vedle něj přesto vytvoří nový
  řádek pro tutéž úhradu — opravte proto raději účet nebo řádek dokladu.
- **Ručně přidaný řádek dostane číslo až při nejbližším generování.**
- **Kategorie na účtech nejsou za společnost.** Společnosti se společnou
  osnovou sdílejí i přiřazení; řešením je přepsání na řádku dokladu.
- **Jen peněžní deník.** Evidenci majetku a dluhů ani knihy pohledávek a
  závazků modul nevytváří; stavy ke konci roku bere z hlavní knihy.
- Údaje pro daňové přiznání jsou pomůcka ke kontrole a přepsání do přiznání,
  ne podání.
