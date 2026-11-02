---
title: Interaktivní hlavní kniha a obratová předvaha
summary: Hlavní kniha a obratová předvaha OCA otevřené v prohlížeči - rozbalte účet a načtou se jeho položky, porovnávejte období, procházejte jimi a pracujte s každým řádkem.
verified: 19.0.1.5.0
---

## K čemu slouží {#purpose}

*Hlavní kniha* a *Obratová předvaha* modulu
[module:account_financial_report](module:account_financial_report) počítají
všechny řádky předem a zobrazí statickou stránku: u velké knihy se dlouho
otevírá a dlouho se v ní posouvá. Tento modul přidává do obou průvodců tlačítko
**Interaktivně** vedle *Zobrazit*. Otevře týž výkaz jako živé zobrazení,
ve kterém se nic pod účtem nepočítá, dokud ho neotevřete.

## Otevření {#usage}

*Účetnictví › Výkazy › Hlavní kniha* (nebo *Obratová předvaha*), nastavte
období a filtry jako obvykle a pak **Interaktivně**. Platí všechny filtry
průvodce: data, zaúčtované nebo všechny doklady, účty, partneři, deníky,
analytické účty, vlastní doména - i cokoli, co do průvodce přidá jiný modul,
například
[module:l10n_cssk_account_financial_report](module:l10n_cssk_account_financial_report),
který vynechává deníky závěrky roku.

| Sloupec | Význam |
|---|---|
| Počáteční stav | Zůstatek před obdobím. Rozvahové účty nesou vše před ním, výsledkové jen běžné účetní období. Výsledek minulých let je na účtu nerozděleného výsledku, takže sloupec dává součet nula. |
| Má dáti / Dal | Pohyb v období. Kliknutím se otevřou účetní položky. |
| Konečný stav | Počáteční stav plus pohyb období. |

## Rozbalení účtu {#unfold}

Kliknutím na účet ho rozbalíte. Jeho položky se načítají **po 80**
(*Načíst další*), každá s **průběžným zůstatkem**, který začíná počátečním
a končí konečným stavem. Kliknutím na číslo dokladu se otevře doklad, na
partnera partner.

- **Seskupeno podle: Partneři** (průvodce hlavní knihy): účet pohledávek nebo
  závazků se nejprve rozbalí na partnery - počáteční stav, má dáti, dal
  a konečný stav za každého - a každý partner se rozbalí na své položky.
- **Aktivovat centralizaci**: účty označené jako *centralizované* ukazují jeden
  řádek za měsíc místo každé položky.
- **Zobrazit cizí měnu**: u položky v jiné měně je vedle popisu její částka
  v této měně.
- **Zobrazit hierarchii** (průvodce obratové předvahy): před účty jsou
  mezisoučty skupin účtů; *Omezit úrovně hierarchie* skončí na zvolené hloubce.

## Období a porovnání {#compare}

Šipky u období přejdou na **předchozí nebo následující období** stejné délky -
po celých měsících, je-li období celé měsíce (čtvrtletí přejde na další
čtvrtletí), jinak po dnech. Začátek účetního období se posouvá s ním, takže
počáteční stavy výsledkových účtů sedí i přes konec roku.

**Porovnat s** přidá ke každému účtu netto pohyb až dvanácti předchozích období
(*Předchozí období*) nebo stejného období v minulých letech a **růst** oproti
prvnímu z nich. Růst se měří na přirozené straně účtu, takže vyšší tržby jsou
kladné číslo; zelený je tam, kde je růst dobrý (výnosy), červený tam, kde je
špatný (náklady), jinde bez barvy. Zobrazí se i účty, které se pohnuly jen
v porovnávaném období.

## Filtrování {#filter}

**Filtr** otevře editor domény Odoo na účetních položkách: libovolné pole
i přes jeho vazby (*Produkt › Kategorie produktu*, *Partner › Země*…)
a libovolný operátor - *je*, *není*, *obsahuje*, *je nastaveno*… - takže filtr
může zahrnovat i vylučovat. Platí navíc k filtrům průvodce pro všechny údaje:
účty, partnery, položky i porovnávaná období. Dokud je filtr aktivní, tlačítko
je modré; křížek vedle něj ho zruší.

## Uložená zobrazení {#views}

**Záložka** u období uloží to, co právě vidíte: filtry, doplňkový filtr
a porovnání, pod názvem a buď s

- *Těmito daty*, nebo
- obdobím relativním ke dni otevření - tento nebo minulý měsíc, čtvrtletí nebo
  účetní období - takže „minulý měsíc“ je vždy minulý měsíc.

Zobrazení je vaše, dokud ho **nesdílíte** (vidí ho všichni, měnit ho můžete
jen vy). Jedno z vašich zobrazení může být **vaše výchozí**: *Účetnictví ›
Výkazy › Účetní výkazy OCA › Interaktivní hlavní kniha* ho otevře přímo (bez
výchozího otevře obratovou předvahu tohoto roku). Uložená zobrazení se
zobrazují, přejmenovávají a mažou v *Uložená zobrazení knihy* ve stejném menu.

## Akce na řádcích {#actions}

- ikona šipky u účtu otevře účet;
- obálka u položky otevře výpis pohybů pro partnera (OCA) za období výkazu
  k odeslání e-mailem nebo tisku - jen je-li nainstalován
  [module:partner_statement](module:partner_statement);
- schránka zkopíruje řádek jako text oddělený tabulátory pro vložení do
  tabulky.

## Poznámky {#notes}

Zobrazení jen čte: každý údaj pochází z účetních položek přes běžná přístupová
práva a pravidla záznamů, takže uživatel vidí přesně ty společnosti a doklady,
které vidět smí. Pro tisk použijte v průvodci *Exportovat PDF* nebo
*Exportovat XLSX*.
