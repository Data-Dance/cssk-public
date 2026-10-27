---
title: SK účtovné vzory — predkontácie interných dokladov
summary: Pripravené slovenské predkontácie interných dokladov — peniaze na ceste cez 261 a preúčtovanie schváleného výsledku hospodárenia — ktoré z jednej zadanej sumy urobia vyrovnaný účtovný zápis v stave návrh.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Niektoré zápisy nemajú zdrojový doklad, z ktorého by Odoo odvodilo účty:
hotovosť odvedená z pokladnice do banky, zisk alebo strata preúčtovaná po
schválení účtovnej závierky valným zhromaždením. Účtovník ich zaúčtuje ako
interný doklad, zvyčajne podľa zaužívanej predkontácie.

Modul takéto predkontácie dodáva ako **účtovné vzory** nástroja OCA
`account_move_template` pre spoločnosti so slovenskou osnovou. Vyberiete
vzor, zadáte jednu sumu a dostanete vyrovnaný účtovný zápis v stave
**návrh**.

**Čo to nie je.** V slovenských účtovných programoch sa predkontácia
zvyčajne vyberá **na doklade** — na faktúre, bankovom výpise, pokladničnom
doklade — a určuje, ako sa doklad zaúčtuje. Nástroj OCA nemá väzbu na žiadny
doklad: len zostaví nový ručný zápis. Faktúry, banka a pokladnica dostávajú
účty aj naďalej od samotného Odoo — z produktu alebo kategórie produktu, z
účtov pohľadávok a záväzkov partnera, z fiškálnej pozície, nastavenia daní,
denníka a modelov párovania. Zoznam predkontácií z iného programu sa väčšinou
premietne do týchto nastavení, nie do vzorov.

## Vzory {#templates}

Vytvoria sa v denníku spoločnosti typu *Rôzne* (v osnove kód `general`).
Riadok 1 je suma, ktorú zadáte; riadok 2 ju preberá.

| Vzor | MD (riadok 1) | D (riadok 2) |
|---|---|---|
| Výber z pokladnice (na peniaze na ceste) | Liquidity Transfer (261…) | účet pokladničného denníka |
| Príjem na bankový účet (z peňazí na ceste) | účet bankového denníka | Liquidity Transfer (261…) |
| Výber z bankového účtu (na peniaze na ceste) | Liquidity Transfer (261…) | účet bankového denníka |
| Vklad do pokladnice (z peňazí na ceste) | účet pokladničného denníka | Liquidity Transfer (261…) |
| Preúčtovanie schváleného zisku (431 na 428) | 431000 Výsledok hospodárenia v schvaľovaní | 428000 Nerozdelený zisk minulých rokov |
| Preúčtovanie schválenej straty (431 na 429) | 429000 Neuhradená strata minulých rokov | 431000 Výsledok hospodárenia v schvaľovaní |

Štyri vzory pre peniaze na ceste tvoria dve polovice prevodu medzi
pokladnicou a bankou: výber v jeden deň, vklad v iný, s účtom 261 medzi
nimi. Používajú účty, na ktoré účtovníctvo spoločnosti skutočne účtuje:

- **Peniaze na ceste**: účet *Liquidity Transfer*, ktorý Odoo vytvorí s
  osnovou (účet 261, napríklad 261001, nastavený ako účet interných prevodov
  spoločnosti), nie 261000: v slovenskej osnove Odoo je 261000 prechodný účet
  bankových výpisov, na ktorom čakajú nespárované riadky výpisu.
- **Banka a pokladnica**: účet prvého bankového a prvého pokladničného
  denníka spoločnosti (Odoo dáva každému denníku vlastný, napríklad 221001).
  Slovenská osnova Odoo pokladničný denník nevytvára, takže kým ho
  nezaložíte, pokladničné vzory používajú súhrnný účet 211000; po jeho
  založení zmeňte pokladničné riadky na jeho účet.

Dva vzory pre výsledok hospodárenia nasledujú po rozhodnutí o zisku
alebo strate; otvorenie roka, ktoré výsledok prenesie na 431, opisuje
[module:l10n_sk_fiscal_year_closing](module:l10n_sk_fiscal_year_closing#result-431).

## Nastavenie {#setup}

Vzory sa vytvoria pri načítaní slovenskej osnovy do spoločnosti a pri
inštalácii pre spoločnosti, ktoré ju už majú. Spoločnosť bez denníka *Rôzne*
z osnovy sa preskočí. Opätovná inštalácia vzor nikdy nezdvojí ani nevráti
vašu zmenu.

Pred prvým použitím otvorte každý vzor v *Účtovníctvo → Konfigurácia →
Účtovníctvo → Účtovné vzory (predkontácie)* (ponuka vyžaduje práva
administrátora účtovníctva) a skontrolujte:

- **Bankové a pokladničné účty.** Vzory preberú účet prvého bankového a
  pokladničného denníka. Pri viacerých bankových účtoch si vzor skopírujte
  pre každý bankový účet a zmeňte jeho riadok.

Vzory sú bežné záznamy: premenujte ich, zmeňte účty, pridajte riadky alebo
vytvorte nové podľa vnútornej smernice spoločnosti.

## Zaúčtovanie zápisu {#usage}

1. *Účtovníctvo → Účtovníctvo → Vytvoriť zápis podľa vzoru*, alebo tlačidlo
   **Vytvoriť účtovný zápis** na formulári vzoru.
2. Vyberte vzor a kliknite na **Ďalej**.
3. Skontrolujte dátum, denník, referenciu a partnera a na ponúknutom riadku
   zadajte sumu.
4. Kliknite na **Vytvoriť účtovný zápis**.

Zápis vznikne **v stave návrh**; skontrolujte ho a zaúčtujte ako obvykle.

## Obmedzenia {#limitations}

- Vzory vytvárajú len nové ručné zápisy; nemožno ich pripojiť k faktúre,
  bankovému výpisu ani pokladničnému dokladu a nemenia, ako sa tie
  zaúčtujú.
- Vzory vytvorené pred verziou 19.0.1.1.0 používali 221000, 211000 a
  261000; aktualizácia presunie riadky, ktoré na nich ešte sú, na účty
  uvedené vyššie, a riadok, ktorý ste zmenili, nechá tak.
- Jeden bankový a jeden pokladničný účet na vzor; pozri
  [Nastavenie](#setup).
- Úvodná sada je zámerne malá. Nepokrýva napríklad dividendy, rezervný fond
  ani prevod výsledku na účty spoločníkov; doplňte ich podľa potrieb
  spoločnosti.
- Priradenie účtov si prejdite so svojím účtovníkom.
