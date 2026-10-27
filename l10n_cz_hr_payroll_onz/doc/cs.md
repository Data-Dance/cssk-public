---
title: CZ Oznámení o nástupu do zaměstnání (ONZ)
summary: Oznámení o nástupu do zaměstnání a o skončení zaměstnání pro ČSSZ ve struktuře XML ONZ 2022 — od 1. dubna 2026 nahrazené evidencí zaměstnanců podle zákona o JMHZ.
verified: 19.0.1.0.3
---

## K čemu slouží {#purpose}

*Oznámení o nástupu do zaměstnání* (**ONZ**, tiskopis sloužící i jako
odhláška) oznamovalo ČSSZ, že zaměstnanec nastoupil do zaměstnání
zakládajícího účast na nemocenském pojištění nebo že zaměstnání skončilo.

Modul sestaví hromadné ONZ pro seznam zaměstnanců — buď samé nástupy, nebo
samá skončení — a vyexportuje ho do XML ověřeného proti oficiálnímu schématu
`ONZ2022_20230616.xsd`. Údaje bere ze záznamů zaměstnanců a smluv, ne
z výplatních pásek. Patří do skupiny mzdových hlášení postavených na
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
— viz [příručku českých mezd](module:l10n_cz_hr_payroll_base#declarations).

**Tiskopis už nelze podat.** Viz následující oddíl.

## Právní rámec {#legal}

- **Od 1. dubna 2026** splní zaměstnavatel povinnost oznámit ČSSZ den
  nástupu zaměstnance do zaměstnání a den skončení zaměstnání přihlášením
  zaměstnance do *evidence zaměstnanců* podle
  [zákona o jednotném měsíčním hlášení zaměstnavatele](law:cz/2025/323)
  a jeho odhlášením z ní —
  [§ 94 zákona o nemocenském pojištění](law:cz/2006/187) ve znění
  [zákona č. 360/2025 Sb.](law:cz/2025/360) (čl. XXIV, účinný od 1. dubna
  2026 podle čl. XXXIV písm. d)).
- **Ani za starší události se ONZ nepodává.** Pokud skutečnost nastala před
  1. dubnem 2026 a zaměstnavatel ji do té doby neoznámil, splní povinnost
  novým způsobem (čl. XXV bod 4 zákona č. 360/2025 Sb.). Zaměstnanec vedený
  v registru pojištěnců k 31. březnu 2026 se považuje za přihlášeného do nové
  evidence (bod 6).

Modul proto od 1. dubna 2026 ONZ **odmítne vygenerovat**, stejně jako ONZ
s událostí od tohoto dne; oznámení vygenerovaná dříve zůstávají u svých
záznamů. Přihlášku do evidence JMHZ nevytváří.

## Nastavení {#setup}

Na společnosti:

| Údaj | Použije se jako |
|---|---|
| *Variabilní symbol ČSSZ (VS)*, 8 až 10 číslic | `<comp vs>` |
| *Kód OSSZ*, číslo od 100 do 999 | `dep`, příslušná správa sociálního zabezpečení; výchozí hodnota je 100 |
| *IČO* | `<comp id>` |

Pole *Variabilní symbol ČSSZ (VS)* a *Kód OSSZ* **nejsou na žádném
formuláři**; vyplňte je importem v seznamu společností. Sdílejí je i moduly
PVPOJ a ELDP.

U zaměstnance: rodné číslo v poli *Identifikační č.*, datum narození (pole
*Birthday*), případně *Místo narození*, soukromá adresa a *Počáteční datum
smlouvy* (pro nástup) nebo *Datum ukončení smlouvy* (pro skončení).

## Sestavení oznámení {#usage}

*Mzdová hlášení → CZ ONZ (přihláška)*, pak *Nový*.

1. Zvolte **Typ události** — *Nástup do zaměstnání* nebo *Ukončení
   zaměstnání*. Platí pro všechny zaměstnance v oznámení.
2. Přidejte **Zaměstnance**.
3. Klikněte na **Vygenerovat**. XML se sestaví a ověří proti schématu.
   **Označit jako odeslané** a **Vrátit do konceptu** fungují jako
   u ostatních hlášení.

Generování se zastaví bez zaměstnanců, bez platného VS nebo kódu OSSZ,
u zaměstnance bez data narození nebo bez data smlouvy, které událost
potřebuje, a — se zprávou odkazující na registraci v JMHZ — od 1. dubna 2026
nebo u události s datem od tohoto dne.

## Co každý záznam obsahuje {#output}

| Položka | Zdroj |
|---|---|
| akce (`act`) | *1* nástup, *2* skončení |
| datum vyplnění (`dat`) | den, kdy kliknete na *Vygenerovat* |
| rodné číslo | *Identifikační č.*, má-li 9 nebo 10 číslic; jinak se vynechá |
| příjmení (`sur`), jméno (`fir`) | jméno zaměstnance: poslední slovo je příjmení, vše před ním jméno (jména); má-li zaměstnanec samostatná pole jména a příjmení (OCA `hr_employee_firstname`), použijí se ta |
| rodné příjmení | současné příjmení |
| adresa | soukromá adresa; číslo na konci ulice se bere jako číslo domu |
| začátek / konec zaměstnání (`fro`, `to`) | počáteční a koncové datum současné smlouvy |
| druh činnosti (`rel`) | vždy *1* |
| místo výkonu činnosti (`per`) | země společnosti |

## Omezení {#limitations}

- **Od 1. dubna 2026 nahrazeno** — viz [Právní rámec](#legal).
- Rodné příjmení je současné příjmení a víceslovné příjmení se rozpozná jen
  se samostatnými poli jména a příjmení.
- Jen dvě akce, nástup a skončení; změny a opravy modul nezná. Druh činnosti
  je vždy *1*, i u dohod a zaměstnání malého rozsahu.
- Data se berou ze smlouvy platné ke dnešku, takže zpětně změněná nebo
  nahrazená smlouva může dát jiné datum, než jaké bylo skutečně oznámeno.
- Ověření proti schématu kontroluje tvar souboru, ne obsah.
