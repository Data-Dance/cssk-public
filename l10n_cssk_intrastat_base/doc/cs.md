---
title: Intrastat CZ/SK — generátor souborů (základ)
summary: Společný kód, který pro moduly Intrastat obou edic vytvoří český soubor InstatOnline CSV a slovenský soubor INSTAT XML.
verified: 19.0.1.1.0
family: l10n_cz_intrastat_oca#engine
---

Vytváří soubory, které moduly Intrastat předávají úřadům: český soubor **InstatOnline CSV** pro portál celní správy a slovenskou zprávu **INSTAT XML**, ověřenou proti přiloženému oficiálnímu schématu `instat62.xsd`. Ve formátu CSV ponechává sloupce, které modul nevyplňuje (region, statistický znak, popis zboží), prázdné a jako kód pohybu uvádí `ST`.

Nemá obrazovky ani nastavení a závisí jen na modulu `base`. Nainstaluje se automaticky s modulem [module:l10n_cz_intrastat_oca](module:l10n_cz_intrastat_oca), případně se slovenskými moduly [module:l10n_sk_intrastat](module:l10n_sk_intrastat) a [module:l10n_sk_intrastat_ee](module:l10n_sk_intrastat_ee).
