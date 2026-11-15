---
title: CZ Inventarizace — inventurní soupis a inventarizační zápis
summary: Inventarizace podle zákona o účetnictví jako záznamy v Odoo — inventurní soupisy se všemi náležitostmi podle § 30 odst. 7 a interní inventarizační zápis s porovnáním se stavem v účetnictví.
verified: 19.0.1.0.0
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

Inventarizaci eviduje a prokazuje, inventarizační rozdíly však **neúčtuje**:
manka, schodky, přebytky, opravné položky a podobně z inventarizace vyplývají
a zaúčtuje je účetní.

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
- Rozdíl se zobrazuje jako číslo. Zda jde o manko, schodek nebo přebytek —
  anebo vůbec ne o inventarizační rozdíl, protože jej lze prokázat — uvede
  účetní v inventarizačním zápisu.
- Ukončená inventarizace zůstává upravitelná — stav *Ukončena* nic nezamyká.
- Rozdíly se neúčtují; manka, přebytky a úpravy ocenění zaúčtuje účetní. U
  zásob se inventarizačními rozdíly a ztrátami v rámci norem přirozených
  úbytků zabývá Český účetní standard pro podnikatele č. 007.
- Pravidla vyhlášky č. 270/2010 Sb. pro vybrané účetní jednotky (plán inventur,
  inventarizační komise, inventarizační zpráva) modul neřeší.
