---
title: CZ/SK VIES — přímé ověření a doklad o ověření
summary: Ověřuje DIČ z jiných členských států přímo v systému VIES Evropské komise, bez Odoo IAP, a každé ověření i s číslem ověření uchová jako doklad.
verified: 19.0.2.1.0
---

## K čemu slouží {#purpose}

Dodání zboží do jiného členského státu je osvobozeno od daně jen tehdy, je-li
pořizovatel registrován k dani v jiném členském státě a své DIČ vám sdělil.
Ověření čísla v systému **VIES** (systém výměny informací o DPH Evropské
komise) je způsob, jak to doložit.

Odoo ověřuje DIČ přes vlastní službu IAP a uchovává jen příznak ano/ne.
Tento modul:

- volá službu VIES Evropské komise **přímo**, bez účtu Odoo a kreditů IAP;
- provádí **kvalifikované** ověření — s vaší společností jako žadatelem —, na
  které VIES vrátí **číslo ověření** (*consultation number*), identifikátor
  konkrétního dotazu;
- uchovává **každé ověření** — datum, výsledek, číslo ověření, název a adresu
  podle VIES, kdo ověřoval a za kterou společnost — jako needitovatelný záznam
  na kontaktu;
- kontakty denně ověřuje znovu.

Popisky modulu jsou v této verzi v češtině přeloženy jen zčásti; níže je u
nich uveden i anglický originál, jak se zobrazuje.

## Právní rámec {#legal}

Podmínky osvobození, pro které DIČ odběratele rozhoduje:

- **Česko** — [§ 64 odst. 1 zákona o DPH](law:cz/2004/235): dodání zboží
  plátcem osobě registrované k dani v jiném členském státě je osvobozeno,
  pokud tato osoba **sdělila plátci své daňové identifikační číslo**, zboží
  je odesláno nebo přepraveno do jiného členského státu a plátce dodání uvede
  v souhrnném hlášení.
- **Slovensko** — [§ 43 ods. 1 zákona o DPH](law:sk/2004/222#paragraf-43.odsek-1):
  dodání je osvobozeno, je-li pořizovatelem osoba povinná k dani (nebo
  právnická osoba nepovinná k dani) identifikovaná k dani v jiném členském
  státě, **která toto číslo dodavateli sdělila**.

Žádný z těchto zákonů nepředepisuje VIES ani číslo ověření jako formu
důkazu; je to doklad, který si správce daně obvykle vyžádá, když se později
ukáže, že číslo odběratele bylo neplatné.

## Nastavení {#setup}

1. Vaše společnost musí mít vyplněné vlastní **DIČ**. Číslo ověření vydá VIES
   jen při kvalifikovaném ověření, které DIČ žadatele potřebuje.
2. *Účetnictví → Konfigurace → Nastavení*, blok **Daně**, nastavení
   **Ověrení DIČ** (*Verify VAT Numbers*): zaškrtněte **Použít přímé EU VIES
   (bez IAP)**. Nastavuje se pro každou společnost zvlášť.

Se zaškrtnutou volbou jde vlastní ověření Odoo (spouští se při zadání DIČ,
je-li zapnuté *Ověrení DIČ*) místo IAP přímo na Evropskou komisi a pro
společnost běží denní obnova. Tlačítko *Check now* popsané níže funguje bez
ohledu na volbu.

## Ověření kontaktu {#usage}

Na formuláři kontaktu je pod DIČ řádek **VIES**:

- ***Check now*** (ověřit nyní) — kontakt uloží a jeho DIČ hned ověří ve
  VIES za společnost, ve které právě pracujete. Výsledek oznámí notifikace:
  *Valid in VIES* (platné) s číslem ověření, *Not valid in VIES* (neplatné)
  nebo *VIES did not answer* (VIES neodpověděl).
- zelená fajfka nebo červený křížek — aktuální výsledek; kliknutím otevřete
  kartu **VIES**. Pomlčka znamená, že společnost kontakt ještě neověřila.

Karta **VIES** (zobrazí se, má-li kontakt DIČ):

| Skupina | Pole |
|---|---|
| Ověření (*Consultation*) | datum ověření (*VIES Checked On*), číslo ověření (*VIES Consultation No.*), datum dotazu podle VIES (*VIES Request Date*), poslední chyba (*VIES Last Fault*, jen po ověření, na které VIES neodpověděl) |
| Údaje ve VIES (*As registered in VIES*) | název (*VIES Registered Name*), adresa (*VIES Registered Address*), shoda názvu (*VIES Name Match* — zda se název ve VIES shoduje s názvem kontaktu) |

Tato pole ukazují poslední zodpovězené ověření **aktuální společnosti**. Pod
nimi je úplný seznam ověření všech společností, k nimž máte přístup, s
datem, výsledkem, číslem ověření a uživatelem. Neplatné odpovědi jsou
červeně, chyby šedě.

Záznamy nikdo nemůže upravovat. Mazat je mohou jen administrátoři.

## Denní obnova {#refresh}

Naplánovaná akce **VIES: obnovit přímé kontroly (CZ/SK)** běží jednou denně.
Za každou společnost se zapnutým přímým VIES ověří kontakty nejvyšší úrovně,
jejichž DIČ začíná předponou jiného členského státu EU než státu společnosti
(včetně `EL` pro Řecko a `XI` pro Severní Irsko), které jsou sdílené nebo
patří této společnosti a které tato společnost neověřila za posledních 7 dní —
nejvýše 200 za společnost a běh, s krátkou pauzou mezi dotazy, protože VIES
omezuje počet dotazů. Každý výsledek se zaznamená a aktualizuje výsledek VIES
na kontaktu.

## Když VIES neodpoví {#faults}

VIES často odpoví, že národní systém je nedostupný nebo přetížený. Taková
odpověď (`MS_UNAVAILABLE`, `MS_MAX_CONCURRENT_REQ`,
`GLOBAL_MAX_CONCURRENT_REQ`, `SERVICE_UNAVAILABLE`, `TIMEOUT`, `BUSY`) nebo
žádná odpověď se zaznamená jako *No answer* (bez odpovědi). Číslo nikdy
neoznačí za neplatné a nikdy nenahradí poslední skutečný doklad; denní obnova
to zkusí znovu po 7 dnech. Každá jiná záporná odpověď se považuje za
neplatnost.

## Omezení {#limitations}

- **Neuložený kontakt se ověří, ale nezaznamená.** Automatické ověření, které
  Odoo spustí při zadání DIČ, se zaznamená i s číslem ověření jako každé jiné
  — u nového kontaktu ho ale není k čemu přiřadit, dokud se neuloží.
  Potřebujete-li doklad hned, po uložení stiskněte *Check now*.
- **Bez vlastního DIČ není číslo ověření.** Nemá-li společnost vyplněné DIČ,
  VIES odpoví platné / neplatné, ale číslo ověření nevrátí.
- **Denní obnova se neomezuje na odběratele.** Každá společnost se zapnutým
  přímým ověřením ověřuje všechny sdílené i vlastní kontakty nejvyšší úrovně
  se zahraničním DIČ z EU, ať s nimi obchoduje, nebo ne. Tuzemská DIČ a
  kontakty jiných společností vynechává.
- **Výsledek je společný, doklad ne.** Fajfka nebo křížek je jedna hodnota na
  kontakt podle toho, která společnost ověřovala naposledy; číslo ověření a
  údaje z registru jsou za každou společnost zvlášť.
- Ověření dokládá, co VIES v daném okamžiku odpověděl. Ostatní podmínky
  osvobození (přeprava, souhrnné hlášení) nepokrývá.
