---
title: CZ/SK Translation Overrides
summary: Slovenské a české znenie obrazoviek Odoo a modulov OCA tam, kde ich vlastný preklad chýba, je nesprávny alebo nezodpovedá účtovnej terminológii.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Odoo aj moduly OCA dodávajú vlastné slovenské a české preklady. Niektoré
výrazy chýbajú a zobrazujú sa po anglicky, iné sú doslovným prekladom z
angličtiny, ktorý by slovenský ani český účtovník nepoužil, a ten istý pojem
je niekedy na troch obrazovkách preložený trojako. Tento modul prináša naše
opravy, takže celé rozhranie je v jednom jednotnom jazyku, a to bez zásahu do
súborov Odoo či OCA.

Vyžaduje iba `base` a hodí sa pre Community aj Enterprise. Opravy pre modul,
ktorý nemáte nainštalovaný, sa jednoducho preskočia.

## Čo mení {#scope}

- **Názvy polí, pomocné texty, hodnoty výberov, menu, akcie a texty
  formulárov** iných modulov. Zapisujú sa do databázy a vidíte ich na každom
  formulári a zozname.
- **Hlásenia vytvárané v kóde** — chybové a varovné hlásenia, notifikácie,
  popisy zostavené v Pythone alebo vo webovom klientovi. Tie sa načítajú
  priamo z katalógov modulu.

## Kedy sa opravy uplatnia {#when}

Automaticky vždy, keď Odoo načítava preklady:

- pri inštalácii alebo aktualizácii tohto modulu;
- pri inštalácii alebo aktualizácii **akéhokoľvek** ďalšieho modulu vrátane
  opravovaných;
- keď pridáte alebo aktualizujete jazyk v *Nastavenia ▸ Jazyky*, aj so
  zaškrtnutým *Prepísať existujúce výrazy*.

Hlásenia z kódu sa zmenia po reštarte servera Odoo.

## Dobré vedieť {#notes}

- Preklad, ktorý ste sami zmenili v rozhraní, sa pri ďalšom načítaní prekladov
  **nahradí** našou opravou, ak pre daný výraz nejakú máme. Záznamy, ktoré Odoo
  považuje za vaše na úpravu (e-mailové šablóny a podobné údaje načítané raz),
  sa nemenia nikdy.
- Odinštalovanie modulu opravené znenie ponechá. Na návrat k zneniu Odoo
  znovu načítajte jazyk v *Nastavenia ▸ Jazyky* s voľbou *Prepísať existujúce
  výrazy*.
- Opravy hlásení z kódu platia pre celý server Odoo, teda pre každú databázu
  na ňom, len čo je modul nainštalovaný v jednej z nich.
- Záznamy, ktoré Odoo pri vytvorení pomenuje hlásením z kódu — typy skladových
  operácií ako *Príjemky*, trasy, denníky vytvorené kódom, spôsoby platby
  v mieste predaja — dostanú slovenský alebo český názov aj v databáze
  založenej v angličtine. Názov, ktorý ste preložili alebo zmenili sami, sa
  ponechá.
- Názvy účtov, daní a denníkov pochádzajú z účtovej osnovy a patria každej
  spoločnosti zvlášť; tento modul ich nemení.
