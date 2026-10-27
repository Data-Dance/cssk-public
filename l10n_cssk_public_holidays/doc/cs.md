---
title: Svátky: Slovensko a Česko
summary: Doplňuje české a slovenské dny pracovního klidu do kalendáře svátků OCA, rok po roce, se zákonnými výjimkami.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Dovolená a docházka nesmí počítat den pracovního klidu jako pracovní den.
Modul OCA `calendar_public_holiday` (používá ho `hr_holidays_public` a
docházkové a mzdové moduly OCA) vede jeden záznam svátků na rok a zemi, ale
prázdný. Tento modul ho naplní českými a slovenskými **dny pracovního klidu**.

Generují se jen dny pracovního klidu. Svátek, který zákon v daném roce činí
pracovním dnem, se v tom roce vynechá, protože dovolená a docházka ho musí
počítat jako pracovní den. Mzda za svátek se řídí vlastními pravidly a modul ji
neovlivňuje.

## Právní rámec {#legal}

**Česko** — [§ 1 až § 3 zákona č. 245/2000 Sb.](law:cz/2000/245):
1. leden, Velký pátek (od roku 2016), Velikonoční pondělí, 1. květen,
8. květen, 5. červenec, 6. červenec, 28. září, 28. říjen, 17. listopad a
24.–26. prosinec.

**Slovensko** — [§ 1 a § 2 zákona č. 241/1993 Z. z.](law:sk/1993/241#paragraf-2):
1. leden, 6. leden, Velký pátek, Velikonoční pondělí, 1. květen, 8. květen,
5. červenec, 29. srpen, 15. září, 1. listopad a 24.–26. prosinec. Výjimky,
které modul uplatňuje:

- 1. září (Den Ústavy) je dnem pracovního klidu jen do roku 2023 a 17. listopad
  jen do roku 2024. [§ 2 odst. 3](law:sk/1993/241#paragraf-2.odsek-3) je (spolu
  s 28. říjnem) ponechává jako státní svátky, které nejsou dny pracovního klidu.
- 8. květen a 15. září jsou pracovními dny **jen v roce 2026**: přechodné
  ustanovení [§ 4b](law:sk/1993/241#paragraf-4b) uvádí jen tento rok, takže v
  roce 2027 se vracejí, pokud se zákon znovu nezmění.

## Jak to funguje {#usage}

- Při instalaci se vygeneruje aktuální a následující rok pro obě země (pokud
  země v databázi existuje).
- Měsíční naplánovaná akce *Státní svátky: vytvořit další rok (SK, CZ)*
  udržuje aktuální a následující rok, takže nový rok přibude sám.
- Záznamy jsou v *Kalendář → Konfigurace → Public Holidays*.

Generování jen doplňuje chybějící dny. Řádky, které už pro dané datum
existují, zůstanou i s vašimi úpravami; regionální řádek (s vyplněnými kraji)
se za celostátní den nepovažuje. Chcete-li změnu vynutit, smažte řádek nebo
celý rok a naplánovanou akci spusťte znovu (*Nastavení → Technická nastavení →
Opakované akce*, *Spustit ručně*).

## Omezení {#limitations}

- Pravidla jsou tabulkou v kódu. Při změně zákona je třeba modul aktualizovat;
  již vygenerované roky se samy neopraví — smažte dotčený rok a vygenerujte ho
  znovu.
- Jen Česko a Slovensko, jen celostátní dny.
- Neděle se negenerují: kalendář eviduje svátky, pracovní dobu určuje pracovní
  kalendář zaměstnance.
