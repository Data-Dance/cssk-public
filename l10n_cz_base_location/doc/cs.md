---
title: České okresy, obce a PSČ
summary: Všechny české okresy, obce a PSČ, aby se po zadání PSČ nebo obce u kontaktu doplnila obec, PSČ, okres i země.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Modul OCA *Location management* (`base_location`) přidává ke kontaktům a
společnostem pole **ZIP Location**: zadáte PSČ nebo začátek názvu obce,
vyberete ze seznamu a adresa se doplní. Sám ale žádná česká data neobsahuje.
Tento modul je doplňuje:

| V Odoo | V Česku | Počet |
|---|---|---|
| Stát (State) | okres s krajem („okres Kladno, Středočeský kraj“); Praha je „Hlavní město Praha“ | 77 |
| Město (City) | obec | 6 258 |
| PSČ (ZIP) | PSČ tak, jak je uvádí Česká pošta a ARES („27201“) | 7 871 |

Obce se stejným názvem jsou samostatné položky, každá ve svém okrese (Nových
Vsí je čtrnáct), proto vybírejte podle okresu uvedeného u názvu. Dva názvy se
opakují v rámci jednoho okresu a nesou PSČ v závorce: „Březina (66601)“ a
„Březina (67905)“ v okrese Brno-venkov, „Mezholezy (34506)“ a „Mezholezy
(34601)“ v okrese Domažlice.

## Instalace {#install}

S balíčkem české lokalizace se neinstaluje. Chcete-li výběr podle PSČ,
nainstalujte jej z *Aplikací*; `base_location` se nainstaluje s ním.

## Odkud jsou data {#source}

Ze seznamu, který zveřejňuje Česká pošta (*Seznam částí obcí a obcí s adresním
PSČ*). Soubor `data/SOURCE` v modulu uvádí, ze kterého stažení vznikl. Novější
verze modulu při aktualizaci přidá nové obce a PSČ; nikdy neodstraní ani
nepřejmenuje položku, kterou už můžete mít u kontaktu, a vaše úpravy položek
zůstanou zachovány.
