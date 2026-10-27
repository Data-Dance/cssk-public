---
title: Intrastat CZ/SK — generátor súborov (základ)
summary: Spoločný kód, ktorý pre moduly Intrastat oboch edícií vyhotoví slovenský súbor INSTAT XML a český súbor InstatOnline CSV.
verified: 19.0.1.1.0
family: l10n_sk_intrastat#engine
---

Vyhotovuje súbory, ktoré moduly Intrastat odovzdávajú úradom: slovenskú správu **INSTAT XML**, overenú voči priloženej oficiálnej schéme `instat62.xsd` (jedno hlásenie v súbore alebo obálka s viacerými), a český súbor **InstatOnline CSV**. Dvojmiestny druh obchodu rozdelí na kód A a kód B, ako to INSTAT očakáva, a hmotnosť, množstvo a hodnotu zaokrúhli na celé čísla, ako to vyžaduje schéma.

Nemá obrazovky ani nastavenia a závisí len od modulu `base`. Nainštaluje sa automaticky s modulom [module:l10n_sk_intrastat](module:l10n_sk_intrastat), [module:l10n_sk_intrastat_ee](module:l10n_sk_intrastat_ee) alebo [module:l10n_cz_intrastat_oca](module:l10n_cz_intrastat_oca).
