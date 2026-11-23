---
title: Svátky: Slovensko a Česko
summary: Doplňuje české a slovenské dny pracovního klidu do kalendáře svátků OCA, rok po roce, se zákonnými výjimkami, a slovenské udržuje i jako státní svátky pracovních kalendářů.
verified: 19.0.1.0.2
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

## Pracovní kalendáře {#calendars}

Volno a mzdy kalendář svátků nečtou. Svátek znají jen jako *státní svátek*
pracovních kalendářů (*Volno → Konfigurace → Státní svátky*). Modul proto
slovenské svátky udržuje i tam:

- každá společnost, jejíž zemí je Slovensko, dostane jeden státní svátek za
  každý celostátní řádek, bez určeného pracovního kalendáře, takže platí pro
  všechny kalendáře společnosti, nynější i budoucí;
- řádek, který přejmenujete, přesunete, změníte na regionální nebo smažete,
  vezme svůj státní svátek s sebou a opakované generování nic nezdvojí;
- den, na který už společnost má ručně zadaný státní svátek, se ponechá
  tomuto záznamu;
- společnost vytvořenou později zachytí nejbližší běh naplánované akce, od
  prvního dne měsíce před tímto během; chcete-li svátky hned, spusťte ji
  ručně.

Zápis provádí naplánovaná akce a zapisuje dny od prvního dne předchozího
kalendářního měsíce. Mzdy za měsíc se počítají začátkem následujícího,
takže právě skončený měsíc je ještě otevřený: při běhu 5. září akce zapíše
i 29. srpen a 5. červenec nechá být. V lednu vygeneruje i předchozí rok,
aby byl prosinec na místě.

Státní svátek, který je pro společnost nový, způsobí, že Volno přepočítá
žádosti o volno, které přes něj procházejí. Schválený týden dovolené přes
pátek 29. srpna se změní z pěti dnů na čtyři, den se vrátí do nároku a
Volno to zaměstnanci oznámí v historii žádosti. Pro otevřený měsíc je to
správný počet; se starším obdobím to modul bez vyžádání nedělá. Svátek,
který už v kalendářích je, se znovu nezapisuje, takže opakovaný běh nic
nepřepočítá a nikomu nic neoznámí.

Instalace nebo aktualizace modulu požádá naplánovanou akci o okamžitý běh,
takže svátky přibudou za chvíli; kde naplánované akce neběží, spusťte ji
ručně. Řádek, který přidáte nebo změníte ručně, se uplatní hned a bez ohledu
na datum. Chcete-li do kalendářů dostat i starší
svátky, zavolejte `cssk_sync_calendar_leaves(date_from=…)` na modelu
`calendar.public.holiday`, například ze serverové akce.

Systémový parametr `l10n_cssk_public_holidays.calendar_leave_countries`
obsahuje seznam zemí oddělených čárkou. Výchozí hodnota je `SK`. České
společnosti jsou vynechány, dokud se české mzdy neověří se svátkem uvnitř
nepřítomnosti; `SK,CZ` je přidá a `none` funkci vypne. Změna se projeví při
nejbližším běhu naplánované akce, která zároveň odstraní svátky země
vyřazené ze seznamu, od předchozího měsíce.

## Omezení {#limitations}

- Pravidla jsou tabulkou v kódu. Při změně zákona je třeba modul aktualizovat;
  již vygenerované roky se samy neopraví — smažte dotčený rok a vygenerujte ho
  znovu.
- Jen Česko a Slovensko, jen celostátní dny.
- Státní svátek zadaný ručně jen pro jeden pracovní kalendář nepustí na ten
  den celopodnikový záznam modulu, takže ostatní kalendáře společnosti ho
  nedostanou. Ručně zadaný záznam odstraňte, nebo den zadejte i pro ostatní
  kalendáře.
- Neděle se negenerují: kalendář eviduje svátky, pracovní dobu určuje pracovní
  kalendář zaměstnance.
