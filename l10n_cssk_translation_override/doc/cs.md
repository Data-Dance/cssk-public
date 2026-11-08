---
title: CZ/SK Translation Overrides
summary: České a slovenské znění obrazovek Odoo a modulů OCA tam, kde jejich vlastní překlad chybí, je nesprávný nebo neodpovídá účetní terminologii.
verified: 19.0.1.3.0
---

## K čemu slouží {#purpose}

Odoo i moduly OCA dodávají vlastní české a slovenské překlady. Některé výrazy
chybí a zobrazují se anglicky, jiné jsou doslovným překladem z angličtiny,
který by český ani slovenský účetní nepoužil, a tentýž pojem je někdy na třech
obrazovkách přeložen trojím způsobem. Tento modul přináší naše opravy, takže
celé rozhraní je v jednom jednotném jazyce, a to bez zásahu do souborů Odoo
či OCA.

Vyžaduje pouze `base` a hodí se pro Community i Enterprise. Opravy pro modul,
který nemáte nainstalovaný, se jednoduše přeskočí.

## Co mění {#scope}

- **Názvy polí, nápovědy, hodnoty výběrů, nabídky, akce a texty formulářů**
  jiných modulů. Zapisují se do databáze a vidíte je na každém formuláři a
  seznamu.
- **Hlášení vytvářená v kódu** — chybová a varovná hlášení, notifikace,
  popisky sestavené v Pythonu nebo ve webovém klientovi. Ta se načítají přímo
  z katalogů modulu.

## Kdy se opravy uplatní {#when}

Automaticky vždy, když Odoo načítá překlady:

- při instalaci nebo aktualizaci tohoto modulu;
- při instalaci nebo aktualizaci **jakéhokoli** dalšího modulu včetně
  opravovaných;
- když přidáte nebo aktualizujete jazyk v *Nastavení ▸ Jazyky*, i se
  zaškrtnutým *Přepsat existující výrazy*.

Hlášení z kódu se změní po restartu serveru Odoo.

## Dobré vědět {#notes}

- Překlad, který jste sami změnili v rozhraní, se při dalším načtení překladů
  **nahradí** naší opravou, pokud pro daný výraz nějakou máme. Záznamy, které
  Odoo považuje za vaše k úpravě (e-mailové šablony a podobná data načtená
  jednou), se nemění nikdy.
- Odinstalace modulu opravené znění ponechá. Pro návrat ke znění Odoo znovu
  načtěte jazyk v *Nastavení ▸ Jazyky* s volbou *Přepsat existující výrazy*.
- Opravy hlášení z kódu platí pro celý server Odoo, tedy pro každou databázi
  na něm, jakmile je modul nainstalovaný v jedné z nich.
- Záznamy, které Odoo při vytvoření pojmenuje hlášením z kódu — typy skladových
  operací jako *Příjemky*, trasy, deníky vytvořené kódem, způsoby platby
  v prodejních místech — dostanou český nebo slovenský název i v databázi
  založené v angličtině. Název, který jste přeložili nebo změnili sami, se
  ponechá.
- Účetní pojmy se řídí zákonem o účetnictví a zákonem o DPH, ne komunitním
  překladem Odoo: typ účtu je *Výnosy* / *Náklady* (ne *Příjem* / *Výdaj*),
  typ daně je *Výstup* / *Vstup* (ne *Prodej* / *Nákup*) a účet výnosů je
  *Účet výnosů*. Prodejní deníky, prodejní objednávky, nabídka *Prodej*
  a peněžní deník daňové evidence si ponechávají zavedená slova.
- Způsoby platby deníku se pojmenují v jazyce společnosti, takže popisy
  plateb v české nebo slovenské společnosti už nejsou „Manual Payment: …“.
- Názvy účtů, daní a deníků pocházejí z účtové osnovy a patří každé
  společnosti zvlášť; tento modul je nemění.
