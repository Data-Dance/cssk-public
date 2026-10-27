---
title: Interní doklad CZ/SK
summary: Vytiskne účetní záznam jako interní doklad — s náležitostmi účetního dokladu, které vyžaduje zákon o účetnictví.
verified: 19.0.1.0.1
---

## K čemu slouží {#purpose}

Každý účetní zápis musí být doložen účetním dokladem. U faktury nebo
bankovního výpisu je jím samotný externí doklad; u zápisu, za kterým nic
externího není — časové rozlišení, odpisy, přecenění, závěrkový zápis, ruční
oprava — vyhotoví účetní **interní doklad**.

Odoo takovou tiskovou sestavu nemá. Modul ji přidává: každý účetní záznam lze
vytisknout jako interní doklad s náležitostmi účetního dokladu a s řádkem pro
každý podpis.

Závisí jen na modulu `account` a nepotřebuje zbytek česko-slovenské
lokalizace.

## Právní rámec {#legal}

- **Česko.** Podle [§ 11 odst. 1 zákona o účetnictví č. 563/1991 Sb.](law:cz/1991/563)
  musí účetní doklad obsahovat označení účetního dokladu, obsah účetního
  případu a jeho účastníky, peněžní částku, okamžik vyhotovení účetního
  dokladu, okamžik uskutečnění účetního případu, není-li shodný s okamžikem
  vyhotovení, a podpisový záznam osoby odpovědné za účetní případ a podpisový
  záznam osoby odpovědné za jeho zaúčtování.
- **Slovensko.** Slovenský [§ 10 ods. 1 zákona o účtovníctve č. 431/2002 Z. z.](law:sk/2002/431#paragraf-10.odsek-1)
  druhý podpis nevyžaduje.

Sestava se řídí českým výčtem, který je delší, takže vyhoví oběma.

## Jak ho vytisknout {#usage}

Otevřete účetní záznam (*Účetnictví → Účetnictví → Účetní záznamy* nebo
libovolnou fakturu či zápis) a zvolte *Tisk → Interní / interný doklad*.
Můžete označit i více záznamů v seznamu a vytisknout je najednou; každý dostane
vlastní stranu. Soubor se pojmenuje podle dokladu, např.
`Interní doklad - MISC-2026-10-0007.pdf`.

Nic se nenastavuje.

## Co doklad obsahuje {#content}

| Na dokladu | Odkud se bere |
|---|---|
| Označení dokladu | číslo záznamu |
| Účetní jednotka | společnost a její IČO, je-li vyplněno |
| Deník | deník záznamu |
| Obsah účetního případu | pole *Popis* (reference záznamu); je-li prázdné, interní poznámka; chybí-li i ta, popisy řádků |
| Účastníci účetního případu | společnost a každý partner na záznamu a jeho řádcích |
| Peněžní částka | součet záznamu (součet strany Má dáti) v měně společnosti |
| Datum vyhotovení | den, kdy byl záznam v Odoo **vytvořen** |
| Datum uskutečnění účetního případu | datum účtování |
| Řádky | účet, popis, partner, analytické rozdělení s podílem (např. `Sklad (60 %)`), Má dáti, Dal a součty |
| Podpisové záznamy | vlevo uživatel, který záznam **vytvořil**, jako osoba odpovědná za účetní případ; vpravo ten, kdo ho **zaúčtoval**, jako osoba odpovědná za zaúčtování; u každého řádek pro podpis |

Nezaúčtovaný koncept má pod nadpisem **NEZAÚČTOVÁNO** a u podpisu za
zaúčtování není jméno.

## Jazyk {#language}

Texty jsou zákonné pojmy a **nepřekládají se**: řídí se zemí daňové
příslušnosti společnosti. Slovenská společnost tiskne slovenské znění, každá
jiná české. Jazyk uživatele nerozhoduje.

## Omezení {#limitations}

- *Datum vyhotovení* je den vytvoření záznamu v Odoo, ne datum, které zvolíte.
  Byl-li doklad vyhotoven jindy, sestava to neukáže.
- Kdo záznam zaúčtoval, se čte z historie záznamu (poslední změna stavu). Při
  automatickém zaúčtování naplánovanou akcí je to uživatel, pod kterým akce
  běží; byla-li historie smazána, jméno zůstane prázdné.
- Vytištěná jména jsou uživatelé Odoo, kteří záznam vytvořili a zaúčtovali, ne
  nutně osoby odpovědné za případ podle vaší vnitřní směrnice. Řádky slouží
  pro skutečný podpis; modul nic elektronicky nepodepisuje.
- Množství a jednotková cena se netisknou; peněžní částka je součet záznamu.
- Takto lze vytisknout každý záznam včetně faktur, ačkoli ty již externí doklad
  mají.
