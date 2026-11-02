---
title: Interaktívna hlavná kniha a obratová súvaha
summary: Hlavná kniha a obratová súvaha OCA otvorené v prehliadači - rozbaľte účet a načítajú sa jeho položky, porovnávajte obdobia, prechádzajte nimi a pracujte s každým riadkom.
verified: 19.0.1.5.0
---

## Na čo slúži {#purpose}

*Hlavná kniha* a *Obratová súvaha* modulu
[module:account_financial_report](module:account_financial_report) počítajú
všetky riadky vopred a zobrazia statickú stránku: pri veľkej knihe sa dlho
otvára a dlho sa v nej posúva. Tento modul pridáva do oboch sprievodcov tlačidlo
**Interaktívne** vedľa *Zobraziť*. Otvorí ten istý výkaz ako živé zobrazenie,
v ktorom sa nič pod účtom nepočíta, kým ho neotvoríte.

## Otvorenie {#usage}

*Účtovníctvo › Výkazy › Hlavná kniha* (alebo *Obratová súvaha*), nastavte
obdobie a filtre ako zvyčajne a potom **Interaktívne**. Platia všetky filtre
sprievodcu: dátumy, zaúčtované alebo všetky doklady, účty, partneri, denníky,
analytické účty, vlastná doména - aj čokoľvek, čo do sprievodcu pridá iný
modul, napríklad
[module:l10n_cssk_account_financial_report](module:l10n_cssk_account_financial_report),
ktorý vynecháva denníky koncoročnej uzávierky.

| Stĺpec | Význam |
|---|---|
| Počiatočný stav | Zostatok pred obdobím. Súvahové účty nesú všetko pred ním, výsledkové len bežný účtovný rok. Výsledok minulých rokov je na účte nerozdeleného výsledku, takže stĺpec dáva súčet nula. |
| Má dať / Dal | Pohyb v období. Kliknutím sa otvoria účtovné položky. |
| Konečný stav | Počiatočný stav plus pohyb obdobia. |

## Rozbalenie účtu {#unfold}

Kliknutím na účet ho rozbalíte. Jeho položky sa načítavajú **po 80**
(*Načítať ďalšie*), každá s **priebežným zostatkom**, ktorý začína počiatočným
a končí konečným stavom. Kliknutím na číslo dokladu sa otvorí doklad, na
partnera partner.

- **Zoskupené podľa: Partneri** (sprievodca hlavnej knihy): účet pohľadávok alebo
  záväzkov sa najprv rozbalí na partnerov - počiatočný stav, má dať, dal
  a konečný stav za každého - a každý partner sa rozbalí na svoje položky.
- **Aktivovať centralizáciu**: účty označené ako *centralizované* ukazujú jeden
  riadok za mesiac namiesto každej položky.
- **Zobraziť cudziu menu**: pri položke v inej mene je vedľa popisu jej suma
  v tejto mene.
- **Zobraziť hierarchiu** (sprievodca obratovej súvahy): pred účtami sú
  medzisúčty skupín účtov; *Obmedziť úrovne hierarchie* skončí na zvolenej
  hĺbke.

## Obdobia a porovnanie {#compare}

Šípky pri období prejdú na **predchádzajúce alebo nasledujúce obdobie** rovnakej
dĺžky - po celých mesiacoch, ak je obdobie celé mesiace (štvrťrok prejde na
ďalší štvrťrok), inak po dňoch. Začiatok účtovného roka sa posúva s ním, takže
počiatočné stavy výsledkových účtov sedia aj cez koniec roka.

**Porovnať s** pridá ku každému účtu netto pohyb až dvanástich predchádzajúcich
období (*Predchádzajúce obdobia*) alebo rovnakého obdobia v minulých rokoch
a **rast** oproti prvému z nich. Rast sa meria na prirodzenej strane účtu, takže
vyššie tržby sú kladné číslo; zelený je tam, kde je rast dobrý (výnosy),
červený tam, kde je zlý (náklady), inde bez farby. Zobrazia sa aj účty, ktoré
sa pohli len v porovnávanom období.

## Filtrovanie {#filter}

**Filter** otvorí editor domény Odoo na účtovných položkách: ľubovoľné pole aj
cez jeho väzby (*Produkt › Kategória produktu*, *Partner › Krajina*…)
a ľubovoľný operátor - *je*, *nie je*, *obsahuje*, *je nastavené*… - takže
filter môže zahŕňať aj vylučovať. Platí navyše k filtrom sprievodcu pre všetky
údaje: účty, partnerov, položky aj porovnávané obdobia. Kým je filter aktívny,
tlačidlo je modré; krížik vedľa neho ho zruší.

## Uložené zobrazenia {#views}

**Záložka** pri období uloží to, čo práve vidíte: filtre, doplnkový filter
a porovnanie, pod názvom a buď s

- *Týmito dátumami*, alebo
- obdobím relatívnym k dňu otvorenia - tento alebo minulý mesiac, štvrťrok
  alebo účtovný rok - takže „minulý mesiac“ je vždy minulý mesiac.

Zobrazenie je vaše, kým ho **nezdieľate** (vidia ho všetci, meniť ho môžete
len vy). Jedno z vašich zobrazení môže byť **vaše predvolené**: *Účtovníctvo ›
Výkazy › Účtovné výkazy OCA › Interaktívna hlavná kniha* ho otvorí priamo (bez
predvoleného otvorí obratovú súvahu tohto roka). Uložené zobrazenia sa
zobrazujú, premenúvajú a mažú v *Uložené zobrazenia knihy* v tom istom menu.

## Akcie na riadkoch {#actions}

- ikona šípky pri účte otvorí účet;
- obálka pri položke otvorí výpis pohybov pre partnera (OCA) za obdobie výkazu
  na odoslanie e-mailom alebo tlač - len ak je nainštalovaný
  [module:partner_statement](module:partner_statement);
- schránka skopíruje riadok ako text oddelený tabulátormi na vloženie do
  tabuľky.

## Poznámky {#notes}

Zobrazenie len číta: každý údaj pochádza z účtovných položiek cez bežné
prístupové práva a pravidlá záznamov, takže používateľ vidí presne tie
spoločnosti a doklady, ktoré vidieť smie. Na tlač použite v sprievodcovi
*Exportovať PDF* alebo *Exportovať XLSX*.
