---
title: Časová osa odpracovaných dnů a vstupů mezd
summary: Časová osa, kontingenční tabulka a seznam odpracovaných dnů a dalších vstupů, ze kterých se počítala každá výplatní páska, podle zaměstnanců v čase, v aplikaci Mzdy OCA.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Výplatní páska se počítá z **odpracovaných dnů** (dny a hodiny podle druhu —
běžná práce, dovolená, nemoc…) a z **dalších vstupů** (částky zadané za
období). V aplikaci **Mzdy** (OCA) je vidět jen uvnitř každé pásky. Odoo
Enterprise je kontroluje na Ganttově diagramu pracovních záznamů; tento modul
nabízí alternativu pro Community: řádky všech výplatních pásek na jedné
časové ose a v kontingenční tabulce pro kontrolu.

Modul **není vázán na žádnou zemi**: závisí jen na modulech `payroll` a
`web_timeline` (OCA). Na každý řádek odpracovaných dnů a vstupů uloží
zaměstnance a data období výplatní pásky (pole *Employee*, *Period Start*,
*Period End*), aby šlo řádky samostatně seskupovat a umístit v čase.

## Nastavení {#setup}

Nic se nenastavuje. Musí být k dispozici modul `web_timeline` z repozitáře
OCA `web`. Při instalaci se tři pole doplní i pro existující řádky
výplatních pásek.

## Odpracované dny {#worked-days}

*Mzdy → Worked Days Timeline* otevře časovou osu seskupenou podle
zaměstnanců. Každý řádek odpracovaných dnů je pruh od začátku do konce
**období jeho výplatní pásky** s kódem a počtem dnů a hodin; řádky s kódem
`WORK100` (běžné pracovní dny) jsou zelené. Kliknutím na pruh řádek otevřete;
podržením *Ctrl* a kolečkem myši přiblížíte.

Přepněte na **kontingenční tabulku** pro kontrolní matici — zaměstnanec a kód
v řádcích, měsíce ve sloupcích, hodiny a dny jako míry — nebo na **seznam**,
který sečte dny a hodiny. Vyhledávání nabízí filtr *Worked (WORK100)* a
seskupení podle *Employee*, *Code* a *Period*.

## Další vstupy {#inputs}

*Mzdy → Other Inputs* zobrazí vstupy všech výplatních pásek jako
kontingenční tabulku (zaměstnanec a kód podle měsíců, součet *Částka*) nebo
jako seznam se součtem; seskupit je lze stejně.

## Omezení {#limitations}

- **Pruhy pokrývají období výplatní pásky, ne samotné dny.** Řádek
  odpracovaných dnů zaznamenává, kolik dnů daného druhu páska započítala, ne
  ve které dny; každý řádek měsíční pásky proto pokrývá celý měsíc a dovolená
  uprostřed měsíce se nezobrazí ve skutečných dnech.
- Zobrazí se jen řádky vypočtených výplatních pásek; dokud pásky neexistují,
  není co ukázat. Zahrnuty jsou i řádky konceptů a zrušených pásek — filtr
  podle stavu chybí.
- Vlastní barvu má jen `WORK100`; ostatní kódy mají výchozí barvu.
- Modul nemá vlastní český ani slovenský překlad; jeho menu, filtry a názvy
  polí jsou anglicky.
