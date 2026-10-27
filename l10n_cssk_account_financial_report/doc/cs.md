---
title: CZ/SK finanční výkazy bez deníků závěrky roku
summary: Předvaha, hlavní kniha, otevřené položky a saldo dle splatnosti z OCA vynechávají deníky uzávěrky, otevření a archivu, stejně jako výkazy účetní závěrky.
verified: 19.0.1.0.1
---

## K čemu slouží {#purpose}

Česko-slovenské účetnictví každý rok uzavře účetní knihy a k prvnímu dni
následujícího roku je znovu otevře. Naše lokalizace umožňuje
označit deníky se zápisy uzávěrky a otevření — a u agendy převzaté z jiného
systému i archiv dokladů z doby před přechodem — jako **deníky závěrky roku**
(nastavení modulu [module:l10n_cssk_core](module:l10n_cssk_core)). Výkazy
účetní závěrky i daňové přiznání k dani z příjmů tyto deníky vynechávají.

Výkazy OCA z modulu
[module:account_financial_report](module:account_financial_report) je
nevynechávaly, a proto s účetní závěrkou nesouhlasily:

- **předvaha** za rok ukazovala otevírací zápis k 1. 1. jako obrat v roce:
  sloupec počátečního stavu byl nulový a celý počáteční stav byl ve sloupci
  Má dáti;
- účty, které předchozí systém kdysi přečísloval, si ponechaly zůstatek jen
  z archivu, takže předvaha ukazovala účty, které společnost už nepoužívá;
- **otevřené položky** započítaly převzatý počáteční stav i archivní doklady,
  které tento stav sumarizuje.

S tímto modulem čtyři výkazy tyto deníky ve výchozím stavu vynechávají. Modul
se nainstaluje sám, když je nainstalován `account_financial_report` i
[module:l10n_cssk_core](module:l10n_cssk_core).

## Použití {#usage}

Průvodci v *Účetnictví → Výkazy → Účetní výkazy OCA* dostanou pod *Cílové
zápisy* políčko **Vyloučit uzávěrkové a archivní deníky**:

| Výkaz | Co políčko dělá |
|---|---|
| Předvaha | Necháte-li filtr deníků prázdný, výkaz se sestaví ze všech ostatních deníků společnosti. Zvolíte-li deníky sami, použijí se přesně ty, včetně deníků uzávěrky. |
| Hlavní kniha | Výkaz se sestaví ze všech deníků společnosti kromě deníků uzávěrky. |
| Otevřené položky | Položky z deníků uzávěrky se do otevřených zůstatků nezapočítají. |
| Saldo dle splatnosti | Stejně jako u otevřených položek. |

Políčko je ve výchozím stavu zaškrtnuté, když má společnost zvolená
v průvodci alespoň jeden deník závěrky roku; když nemá žádný, je prázdné
a nic nemění. Po změně společnosti se nastaví znovu. Když ho při
jednom spuštění odškrtnete, dostanete původní chování OCA.

*Kniha deníku* a *Výkaz DPH* se nemění: první se sestavuje po jednotlivých
denících a druhý čte daně, které zápisy uzávěrky nemají.

## Omezení {#limitations}

- **Dokud nejsou deníky závěrky roku nastaveny, modul nic nedělá**, a v této
  verzi toto nastavení společnosti (`l10n_cssk_closing_journal_ids`)
  nezobrazuje žádný formulář. Nápověda pole odkazuje na nastavení účetnictví,
  tam ale není; nastavení svěřte správci.
- Deník, který tam uvedete, z těchto čtyř výkazů úplně zmizí. Je-li v takovém
  deníku zaúčtován první počáteční stav převzaté společnosti, zmizí i ten;
  zaúčtujte ho v běžném deníku.
