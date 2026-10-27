---
title: Párování OCA — účet protistrany
summary: Zobrazí bankovní účet protistrany na obrazovce párování bankovních výpisů OCA, aby šlo určit i plátce, který neuvedl variabilní symbol.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Obrazovka párování bankovních výpisů OCA (`account_reconcile_oca`) zobrazuje
pevný výběr polí řádku výpisu a **bankovní účet protistrany** mezi nimi není —
ačkoli ho vyplňuje každý import výpisů z této rodiny (GPC, MT940, KB BEST,
Fio, Tatra banka a další). V Česku a na Slovensku je to často jediný údaj,
podle kterého poznáte, kdo platil: odběratele, který zapomněl variabilní
symbol, určíte podle čísla účtu, a párování jen podle jména je právě ten
odhad, který zaúčtuje pohledávku nesprávnému odběrateli.

## Co zobrazuje {#usage}

Na obrazovce párování (otevírá se tlačítkem **Reconcile … Items** na kartě
bankovního deníku na přehledu Účetnictví), hned za popisem řádku:

| Pole | Obsah |
|---|---|
| Číslo bankovního účtu | účet protistrany přesně tak, jak ho poslala banka, např. `2600123456/2010` nebo IBAN |
| Banka příjemce | bankovní účet v Odoo, ke kterému byl řádek přiřazen, pokud se shodoval s bankovním účtem partnera |

Obě pole jsou jen pro čtení a zobrazí se, jen když jsou vyplněná. Nic jiného
se nemění: žádná nová pole, žádná nová logika a běžný formulář řádku výpisu
zůstává nedotčen.

Nainstaluje se sám vždy, když je nainstalován `account_reconcile_oca`.

## Omezení {#limitations}

- Jen zobrazuje to, co uložil import výpisu. Řádky ze zdroje, který účet
  protistrany nedodává (například ručně zadané), nezobrazí nic.
- Sám nepáruje nic podle čísla účtu; partnera podle bankovního účtu přiřazuje
  import výpisu při vzniku řádku.
