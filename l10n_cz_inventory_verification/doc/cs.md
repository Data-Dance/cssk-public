---
title: CZ Inventarizace — inventurní soupis a inventarizační zápis
summary: Inventarizace podle zákona o účetnictví jako záznamy v Odoo — inventurní soupisy se všemi náležitostmi podle § 30 odst. 7 a interní inventarizační zápis s porovnáním se stavem v účetnictví.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Účetní jednotka musí zjistit skutečný stav veškerého majetku a závazků a
ověřit, zda odpovídá stavu v účetnictví — provést **inventarizaci**. Při ní
provádí jednu nebo více **inventur** a zjištěné skutečné stavy zaznamenává v
**inventurních soupisech**, jejichž obsah předepisuje zákon o účetnictví.

Modul tyto záznamy vede v Odoo: jeden doklad inventarizace, pod ním libovolný
počet inventurních soupisů a na samotné inventarizaci závěrečný záznam —
**inventarizační zápis**. U dokladové inventury účtu načte stav v účetnictví
z hlavní knihy. Oba záznamy se tisknou do PDF.

Zaúčtuje také inventarizační rozdíly — manka, schodky a přebytky — jako účetní
zápisy v návrhu s datem v ověřovaném období, propojené s inventarizací.
Opravné položky a jiné úpravy ocenění zůstávají na účetní.

## Právní rámec {#legal}

Odkazy jsou na [zákon o účetnictví](law:cz/1991/563), není-li uvedeno jinak.

- **Kdy.** Podle [§ 29 odst. 1](law:cz/1991/563#p29) se inventarizace provádí
  k okamžiku, ke kterému se sestavuje řádná nebo mimořádná účetní závěrka
  (**periodická inventarizace**). **Průběžnou inventarizaci** v průběhu
  účetního období lze podle § 29 odst. 2 provádět pouze u zásob, o nichž se
  účtuje podle druhů, míst uložení nebo hmotně odpovědných osob, a u
  dlouhodobého hmotného movitého majetku, který je v soustavném pohybu a nemá
  stálé místo; každý druh musí být takto inventarizován alespoň jednou za
  účetní období.
- **Jak.** Podle [§ 30 odst. 1](law:cz/1991/563#p30) se skutečný stav zjišťuje
  **fyzickou inventurou** u majetku, u kterého lze vizuálně zjistit jeho
  existenci, a **dokladovou inventurou** u závazků a majetku, u kterého to
  nelze, včetně jiných aktiv, jiných pasiv a skutečností účtovaných v knize
  podrozvahových účtů. Inventarizace se skládá z jedné nebo více inventur
  (§ 30 odst. 2).
- **Inventurní soupis** je průkazný účetní záznam, který podle § 30 odst. 7
  musí obsahovat: zjištěné skutečnosti tak, aby bylo možno majetek a závazky
  jednoznačně určit (písm. a); podpisový záznam osoby odpovědné za zjištění
  skutečností a podpisový záznam osoby odpovědné za provedení inventury
  (písm. b); způsob zjišťování skutečných stavů (písm. c); ocenění majetku a
  závazků při periodické inventarizaci k rozvahovému dni (písm. d), při
  průběžné inventarizaci ke dni ukončení inventury (písm. e), v obou případech
  popřípadě i k rozhodnému dni; okamžik, ke kterému se sestavuje účetní
  závěrka (písm. f); rozhodný den, pokud jej účetní jednotka stanovila
  (písm. g); a okamžik zahájení a okamžik ukončení inventury (písm. h).
- **Rozhodný den.** Podle § 30 odst. 4 může účetní jednotka zjišťovat skutečný
  stav ke dni, který předchází rozvahovému dni, a dokončit zjišťování podle
  účetních záznamů o přírůstcích a úbytcích mezi oběma dny.
- **Lhůty.** Podle § 30 odst. 6 lze inventuru při periodické inventarizaci
  zahájit nejdříve čtyři měsíce před rozvahovým dnem a je třeba ji ukončit
  nejpozději dva měsíce po něm.
- **Rozdíly.** Inventarizačním rozdílem je podle § 30 odst. 10 rozdíl mezi
  skutečným stavem a stavem v účetnictví, který nelze prokázat způsobem
  stanoveným zákonem: manko (u peněžních hotovostí a cenin schodek), je-li
  skutečný stav nižší, a přebytek, je-li vyšší. Vyúčtuje se do účetního
  období, za které se stav inventarizací ověřuje (§ 30 odst. 11).
- **Ocenění.** Podle § 29 odst. 1 se při inventarizaci ověřuje také, zda
  nejsou dány důvody pro účtování o položkách podle § 25 odst. 3 —
  předvídatelných rizicích, možných ztrátách a snížení hodnoty. Pro
  podnikatele k tomu [vyhláška č. 500/2002 Sb.](law:cz/2002/500) doplňuje, že
  se při inventarizaci posuzuje výše a odůvodněnost opravných položek
  (§ 55 odst. 1) a rezerv (§ 57 odst. 5).
- **Prokazování.** Provedení inventarizace musí účetní jednotka prokázat po
  dobu pěti let po jejím provedení (§ 29 odst. 3).

**Inventarizační zápis není zákonem předepsaný doklad.** Zákon předepisuje
inventurní soupis a žádný záznam, který by inventarizaci uzavíral. Podnikatelé
běžně vyhotovují *inventarizační zápis* (nebo *zprávu*) jako interní záznam, a
právě ten modul tiskne: zachycuje porovnání podle § 30 odst. 2 a posouzení
ocenění podle § 29 odst. 1. *Inventarizační zprávu* s předepsaným obsahem
znají jen vybrané účetní jednotky podle vyhlášky č. 270/2010 Sb., která se na
podnikatele nevztahuje a kterou modul neřeší.

## Nastavení {#setup}

Nic se nenastavuje. Doklady se číslují `INV/<rok>/001`, `INV/<rok>/002`, … z
jedné číselné řady společné pro všechny společnosti; rok je rokem vytvoření
dokladu, nikoli ověřovaného období.

Nabídka je *Účetnictví → Účetnictví → Inventarizace*. V Community se aplikace
jmenuje *Fakturace* a podnabídka *Účetnictví* se zobrazí jen uživatelům s
přístupem k úplným účetním funkcím. Uživatelé fakturace mohou inventarizace
vytvářet a upravovat, mazat je může jen správce účetnictví.

## Postup inventarizace {#usage}

1. **Založte inventarizaci.** *Inventarizace → Nový*, zvolte *Druh
   inventarizace* (**Periodická** nebo **Průběžná**) a vyplňte *Okamžik, ke
   kterému se sestavuje účetní závěrka* — rozvahový den. Tlačítkem
   **Zahájit** přejde doklad ze stavu *Návrh* do stavu *Probíhá*.
2. **Přidejte inventurní soupisy** na kartě **Inventurní soupisy**, jeden za
   každou inventuru — za sklad, pokladnu, skupinu majetku nebo účet. *Přidat
   řádek* otevře soupis ve vlastním okně. V bloku **Inventura (§ 30
   odst. 7)** vyplňte:
   - *Název* a *Druh inventury*: **Fyzická inventura** nebo **Dokladová
     inventura**;
   - *Způsob zjišťování skutečných stavů* — vlastními slovy, například
     *počítáním a vážením* nebo *odsouhlasením zůstatků*;
   - *Okamžik zahájení inventury* a *Okamžik ukončení inventury*, včetně
     času;
   - *Rozhodný den*, jen pokud jste jej stanovili; při periodické
     inventarizaci musí předcházet rozvahovému dni;
   - *Osoba odpovědná za zjištění skutečností* a *Osoba odpovědná za
     provedení inventury* (uživatelé; může jít o tutéž osobu).

   *Místo uložení majetku* a *Hmotně odpovědná osoba* jsou nepovinné: zákon
   je v soupisu nevyžaduje.
3. **Zadejte položky** v témže okně: *Popis*, případně *Produkt*, *Množství*,
   *Jednotka* (volný text) a *Cena za jednotku*. *Ocenění* je množství × cena
   a *Skutečný stav* soupisu je součtem položek. Výběr produktu nic
   nepředvyplní, cenu zadejte sami. Položku popište tak, aby ji bylo možno
   jednoznačně určit — inventárním číslem, výrobním číslem, číslem dokladu.
4. **Stav v účetnictví.**
   - *Dokladová inventura* s polem *Účet*: *Stav v účetnictví* je zůstatek
     účtu ze **zaúčtovaných** dokladů s datem do dne uvedeného jako *Ocenění
     ke dni* včetně — při periodické inventarizaci je to rozvahový den, při
     průběžné den ukončení inventury. Později zaúčtované doklady načte
     tlačítko **Načíst zůstatek účtu** v soupisu, nebo **Načíst stavy v
     účetnictví** v záhlaví inventarizace pro všechny dokladové inventury
     najednou.
   - *Fyzická inventura*: *Stav v účetnictví* zadejte podle skladové nebo
     majetkové evidence.

   *Rozdíl* je *Skutečný stav* − *Stav v účetnictví*, za každý soupis i
   celkem.
5. **Vyplňte závěrečný záznam** na kartě **Inventarizační zápis**: *Výsledky
   porovnání skutečného stavu se stavem v účetnictví* (včetně inventarizačních
   rozdílů a způsobu jejich vyúčtování), *Posouzení ocenění majetku a závazků*
   a *Osoba odpovědná za provedení inventarizace*.
6. Klikněte na **Ukončit**. Ukončení se odmítne, pokud inventarizace nemá
   žádný soupis nebo pokud některému soupisu chybí náležitost podle § 30
   odst. 7, kterou musí doplnit člověk: některá z obou odpovědných osob,
   způsob zjišťování nebo okamžik zahájení či ukončení inventury. Hlášení
   uvede soupis i to, co chybí. **Zpět na návrh** inventarizaci kdykoli znovu
   otevře.

### Lhůty inventury {#window}

Začíná-li některá inventura periodické inventarizace dříve než čtyři měsíce
před rozvahovým dnem nebo končí-li později než dva měsíce po něm, zobrazí se
v záhlaví inventarizace upozornění (§ 30 odst. 6). Jde jen o upozornění:
skutečné okamžiky inventury lze zaznamenat vždy.

### Práce s rozhodným dnem {#rozhodny-den}

Ocenění v soupisu je vždy k rozvahovému dni. Zjišťujete-li skutečný stav k
dřívějšímu rozhodnému dni, zadejte položky ve stavu k rozvahovému dni — tedy
zjištěný stav upravený o přírůstky a úbytky mezi oběma dny — a účetní záznamy
o těchto pohybech uschovejte spolu se soupisem.

### Znaménka u dokladové inventury {#signs}

Stav v účetnictví je zůstatek má dáti minus dal, takže účty závazků a
vlastního kapitálu vycházejí **záporně**: závazek vůči dodavateli 500 na účtu
321 se zobrazí jako −500. Potvrzené částky takového účtu zadávejte se zápornou
cenou (například množství 1, cena −500), aby *Rozdíl* porovnával srovnatelné.

## Zaúčtování inventarizačních rozdílů {#differences}

Záložka **Inventarizační rozdíly (§ 30 odst. 10 a 11)** převede rozdíly soupisů na účetní zápisy.

1. **Každému soupisu dejte účet.** *Účet* na soupisu je účet, na kterém se inventarizovaný majetek vede (211 u pokladny, 132 u zboží). U dokladové inventury tam už je; u fyzické inventury jej doplňte, protože návrh z něj vychází.
2. Klikněte na **Navrhnout vyúčtování rozdílů**. Za každý soupis, jehož rozdíl ještě není vysvětlen, přibude jeden řádek: *Manko / schodek*, je-li skutečný stav nižší než stav v účetnictví, *Přebytek*, je-li vyšší — na celou částku a s navrženými účty (viz tabulku níže). Rozdíl, který lze prokázat účetními záznamy, inventarizačním rozdílem vůbec není (§ 30 odst. 10): opravte jej vlastním dokladem a soupis označte podle kroku 4.
3. **Upravte řádky.** Manko rozdělte na část do vaší normy přirozených úbytků (*Úbytek do normy*) a část nad ni. Přidejte řádek *Náhrada od odpovědné osoby* na částku, kterou po ní požadujete, a vyplňte pole *Partner*. Kterýkoli účet změňte, pokud se vaše osnova nebo váš případ liší. Částky jsou vždy kladné: směr určuje druh. *Zbývá vyúčtovat* na soupisu ukazuje, co řádky ještě nevysvětlují.
4. **Rozdíl, který se odtud neúčtuje** (majetek vyřazený v evidenci majetku, zásoby upravené v modulu Sklad, rozdíl prokázaný dokladem): na soupisu zaškrtněte *Rozdíl se zde neúčtuje* a uveďte důvod. Důvod se vytiskne v inventarizačním zápisu.
5. Klikněte na **Zaúčtovat rozdíly**. Tlačítko se nabídne, jakmile je každý rozdíl buď celý vysvětlen, nebo označen jako neúčtovaný. Účetní zápis vznikne **v návrhu**, v *Deníku pro rozdíly* (první interní deník, nezvolíte-li jiný), s číslem inventarizace jako referencí. Jeho datum je *Ocenění ke dni* soupisu: při periodické inventarizaci rozvahový den, při průběžné den ukončení inventury — průběžná inventarizace se soupisy ukončenými v různé dny tedy dostane jeden zápis na každý den. Účetní zápisy zkontroluje a zaúčtuje v Účetnictví; otevře je tlačítko *Účetní zápisy* nahoře.

Stav *Rozdíly* v souhrnu má hodnoty *K vyúčtování*, *Připraveno k zaúčtování*, *Zápis v návrhu* nebo *Zaúčtováno*.

### Navrhované účty {#difference-accounts}

Návrhy vycházejí z Českého účetního standardu pro podnikatele č. 007 a z [vyhlášky č. 500/2002 Sb.](law:cz/2002/500) Oba předpisy stanoví jen účtové skupiny; trojmístné účty jsou obvyklé účty osnovy. Jde o návrhy: oba účty zůstávají upravitelné.

| Soupis vedený na účtu | Manko / schodek | Úbytek do normy | Přebytek |
|---|---|---|---|
| 211, 213 (peníze, ceniny) | 569 / 21x (ČÚS 007 bod 3.1, § 34 vyhlášky) | — | 21x / 668 |
| 112, 132 a ostatní účty skupin 11 a 13 | 549 / 1xx (bod 3.2.1) | 501 / 11x, 504 / 13x | 1xx / 648 |
| 121 až 124 (zásoby vlastní činnosti) | 549 / 12x (bod 3.2.2) | 58x / 12x | 12x / 58x |
| 01x, 02x (odpisovaný dlouhodobý majetek) | bez návrhu | — | 0xx / 07x, 08x — proti oprávkám (bod 3.5 písm. b)) |
| 03x (neodpisovaný dlouhodobý majetek) | 549 / 03x (bod 3.6) | — | 03x / 413 |
| ostatní (pohledávky, závazky, vlastní kapitál) | bez návrhu | — | bez návrhu |

*Náhrada od odpovědné osoby* navrhuje 378 / 648 (ČÚS 007 bod 3.7, ČÚS 017 bod 3.10.4), a 378 / 668, jde-li o soupis peněz nebo cenin (§ 33 vyhlášky). U zaměstnance je stejně běžná skupina 33 (335); účet změňte, je-li to vaše praxe.

Kde se nic nenavrhne, zápis nevznikne, dokud souvztažný účet nezvolíte sami. Tři případy potřebují víc než tento zápis:

- **Dlouhodobý majetek.** U manka odpisovaného majetku se zůstatková cena účtuje přes oprávky a majetek se vyřadí (bod 3.5 písm. a)); přebytek se ocení reprodukční pořizovací cenou a musí se zařadit. Obojí proveďte v evidenci majetku a soupis označte jako neúčtovaný; řádek na účtu třídy 0 nese upozornění.
- **Zásoby oceňované modulem Sklad.** Vede-li účet zásob Odoo samo, opravte množství ve Skladu, který rozdíl zaúčtuje. Řádek na takovém účtu nese upozornění, protože by se rozdíl jinak zaúčtoval dvakrát.
- **Vzájemné vyrovnání.** Manka a přebytky vzniklé prokazatelně neúmyslnou záměnou druhů lze vzájemně vyrovnat (bod 3.4); na soupis zadejte výsledné částky.

Přebytek nakoupených zásob, u kterého se má oprávněně za to, že vznikl chybným účtováním při vyskladnění, se účtuje ve prospěch skupiny 50 místo 648 (bod 3.1 písm. c)); změňte souvztažný účet.

Zápis neobsahuje DPH ani úpravu základu daně z příjmů. Manko přesahující náhrady není daňovým výdajem ([§ 25 odst. 1 písm. n)](law:cz/1992/586) zákona o daních z příjmů) a odpočet DPH u řádně nedoložené ztráty či odcizení majetku se vyrovnává nebo upravuje podle [§ 77 a § 78e](law:cz/2004/235) zákona o DPH; obojí zůstává na účetní.

### Zrušení zaúčtování {#difference-reversal}

**Zrušit zaúčtování rozdílů** zápis v návrhu smaže a zaúčtovaný zápis stornuje. Storno má stejné datum jako zápis, takže zůstává v ověřovaném období. **Zpět do návrhu** na inventarizaci udělá totéž dříve, než doklad znovu otevře, protože soupisy se budou měnit. Řádky vyúčtování zůstávají a lze je zaúčtovat znovu.

Řádky, ze kterých zápis vznikl, nelze měnit ani mazat, dokud se zaúčtování nezruší; stejně tak jejich soupis ani inventarizaci. Změní-li se soupis po zaúčtování, upozornění nahoře oznámí, že zaúčtované částky už nesouhlasí.

**Uzamčená období.** Rozdíly patří do období, za které se stav ověřuje ([§ 30 odst. 11](law:cz/1991/563)). Odoo samo při zaúčtování posune zápis s datem v uzamčeném období na první otevřený den. U těchto zápisů to modul místo toho odmítne: vytvoření, zaúčtování i storno se zastaví s hlášením, dokud období neodemknete.

## Tiskové výstupy {#reports}

Tlačítko **Tisk inventurních soupisů** v záhlaví inventarizace vytiskne její
soupisy, každý na samostatnou stranu: název, sídlo a IČO účetní jednotky,
druh inventarizace a inventury, způsob zjišťování, rozvahový den, rozhodný den
(nebo *nestanoven*), okamžik zahájení a ukončení inventury, místo uložení a
účet, jsou-li uvedeny, položky s množstvím, jednotkou, cenou za jednotku a
oceněním, součty se dnem ocenění, poznámky a řádky pro podpis obou osob podle
§ 30 odst. 7 písm. b). Třetí řádek pro hmotně odpovědnou osobu se tiskne jen
tehdy, je-li vyplněna.

Na inventarizaci vytiskne *Tisk → Inventarizační zápis* závěrečný záznam
označený jako interní: název, sídlo a IČO účetní jednotky, rozvahový den,
období, v němž inventury proběhly, tabulku všech soupisů se stavem v
účetnictví, skutečným stavem, rozdílem a součty, text porovnání, posouzení
ocenění (nebo *Neuvedeno*) a řádky pro podpis osoby odpovědné za provedení
inventarizace a za účetní jednotku.

Sídlem je adresa společnosti a IČO její identifikační číslo; není-li vyplněno, řádek IČO se netiskne.

Podpisové záznamy jsou prázdné řádky k podpisu na papíře; nic se nepodepisuje
elektronicky. Vedete-li záznamy jen elektronicky, připojte podpisový záznam
vyhovující § 33a zákona sami.

## Omezení {#limitations}

- Soupis nese jedno ocenění, a to k rozvahovému dni (při průběžné
  inventarizaci ke dni ukončení inventury). Druhé, nepovinné ocenění k
  rozhodnému dni, které připouští § 30 odst. 7 písm. d) a e), nemá vlastní
  pole; použijte poznámky u položek.
- Dnem ocenění při průběžné inventarizaci je den ukončení inventury v časovém
  pásmu uživatele, který soupis uložil.
- Podle § 30 odst. 8 lze při průběžné inventarizaci inventurní soupis nahradit
  průkazným účetním záznamem o provedení fyzické inventury a o vyúčtování
  inventarizačních rozdílů. Modul vždy vytváří soupis.
- Nekontroluje se, zda se průběžná inventarizace omezuje na majetek podle
  § 29 odst. 2, ani zda je každý druh inventarizován jednou za účetní období.
- *Osoba odpovědná za provedení inventarizace* je jeden uživatel a k ukončení
  se nevyžaduje.
- U dokladové inventury ručně přepsaný stav v účetnictví nevydrží — další
  přepočet nebo načtení jej nahradí.
- U fyzické inventury se nic nenačítá ze skladu ani z evidence majetku; stav
  v účetnictví se zadává ručně.
- Zda jde vůbec o inventarizační rozdíl, anebo o rozdíl, který lze prokázat
  účetními záznamy, rozhoduje účetní; návrh považuje každý rozdíl za
  inventarizační.
- Ukončená inventarizace zůstává upravitelná — stav *Ukončena* nic nezamyká.
- Úpravy ocenění (opravné položky, § 25 odst. 3) se neúčtují; zaúčtuje je
  účetní.
- Zaúčtování rozdílů nevyřazuje ani nezařazuje dlouhodobý majetek, neupravuje
  množství v modulu Sklad a neúčtuje DPH; viz
  [Zaúčtování inventarizačních rozdílů](#differences).
- Zápisy rozdílů jsou jen v měně společnosti a ukončení inventarizace
  zaúčtování rozdílů nevyžaduje.
- Pravidla vyhlášky č. 270/2010 Sb. pro vybrané účetní jednotky (plán inventur,
  inventarizační komise, inventarizační zpráva) modul neřeší.
