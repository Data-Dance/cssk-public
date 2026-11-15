---
title: CZ druh registrace k DPH (plátce / identifikovaná osoba)
summary: Eviduje, zda české DIČ partnera patří plátci, skupině nebo identifikované osobě, a upozorní, když faktura uplatní režim přenesení daňové povinnosti vůči odběrateli, který není plátcem.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

České DIČ neznamená u každého, kdo je má, totéž. **Identifikovaná osoba** je
registrována k DPH proto, že pořizuje zboží z jiného členského státu, přijímá
služby ze zahraničí nebo poskytuje služby do jiného členského státu. Má platné
DIČ, které potvrdí i VIES — ale **není plátcem**. Na tuzemská plnění daň
neuplatňuje, nemá nárok na odpočet a nelze vůči ní použít režim přenesení
daňové povinnosti.

VIES odpovídá jen platné / neplatné. Tento modul přidává ke kontaktu druh
registrace a upozorní, když faktura uplatní režim přenesení daňové povinnosti
vůči odběrateli, který není plátcem.

Statusem vaší vlastní společnosti a jeho změnami v čase se zabývá modul
[module:l10n_cz_vat_status](module:l10n_cz_vat_status). Tento modul je o
vašich odběratelích a dodavatelích.

## Právní rámec {#legal}

Odkazy jsou na [zákon o DPH (č. 235/2004 Sb.)](law:cz/2004/235).

- [§ 6](law:cz/2004/235#p6) až § 6f — kdo je **plátcem**: osoba povinná k dani
  se sídlem v tuzemsku od 1. ledna roku následujícího po roce, v němž její
  obrat překročil 2 000 000 Kč (nebo dříve, při překročení 2 536 500 Kč či z
  vlastní volby), a dále v případech § 6b až § 6f včetně dobrovolné
  registrace.
- [§ 5a](law:cz/2004/235#p5a) — **skupina** vzniká registrací jako plátce a
  jako plátce vystupuje.
- [§ 6g](law:cz/2004/235#p6g) až § 6l — kdo je **identifikovanou osobou**:
  osoba, která není plátcem a pořizuje zboží z jiného členského státu, přijímá
  zdanitelné plnění od osoby neusazené v tuzemsku nebo poskytuje službu s
  místem plnění v jiném členském státě; § 6j až § 6l upravují registraci z
  vlastní volby.
- [§ 92a odst. 1](law:cz/2004/235#p92a) — v režimu přenesení daňové
  povinnosti přiznává daň **plátce, pro kterého bylo plnění uskutečněno**.
  Odběratel, který plátcem není, daň převzít nemůže, a dodavatel ji proto
  uplatní a odvede jako obvykle.

## Nastavení {#setup}

Nic se nenastavuje. Ve formuláři kontaktu se pod DIČ zobrazí u českých
partnerů a u partnerů bez země dvě pole:

| Pole | Význam |
|---|---|
| Registrace k DPH | Plátce, Skupina (plátce), Identifikovaná osoba (není plátce) nebo Neplátce |
| Registrace k DPH od | den, od kterého registrace platí (zobrazí se po vyplnění druhu); zadává se ručně |

Druh vyplňte ručně, nebo jej nechte doplnit modulem
[module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability):
označte jeden nebo více kontaktů a spusťte *Akce → Ověřit daňovou
spolehlivost*. Akce pak vedle spolehlivosti zjistí v registru Finanční správy
i to, zda je český kontakt plátcem, skupinou nebo identifikovanou osobou.
Pokud registr DIČ nenajde nebo subjekt vede jako nespolehlivou osobu, pole
**zůstane beze změny** — nikdy se nenastaví na „není plátce“.

## Upozornění na faktuře {#warning}

Na vydané faktuře české společnosti se nahoře zobrazí žluté upozornění, česky
s anglickým překladem, jsou-li splněny všechny tyto podmínky:

- druh registrace odběratele je **Identifikovaná osoba** nebo **Neplátce**;
- zemí odběratele je Česko, nebo země není vyplněna;
- některý řádek nese daň, která označuje tuzemské přenesení daňové povinnosti.

Daň označuje tuzemské přenesení daňové povinnosti, pokud svůj základ vykazuje
na **řádku 25 přiznání k DPH** (daňová mřížka *VAT 25*, jako u daně *0% RC*
české lokalizace Odoo), nebo má-li zaškrtnuté pole *CZ formulace o přenesení
daňové povinnosti (§ 92a)* modulu
[module:l10n_cz_invoice](module:l10n_cz_invoice). Daň bez obojího modul
nepozná a kontrola mlčí.

Při zaúčtování faktury se tentýž text zapíše do její komunikace. Upozornění
zaúčtování **nikdy neblokuje**: daně opravte sami — plnění se zdaní běžnou
českou DPH.

## Omezení {#limitations}

- **Druh registrace je tak aktuální jako jeho poslední změna.** Pravidelně se
  neobnovuje; odběratel, který se stane plátcem, si ponechá starý druh, dokud
  jej nezměníte vy nebo dotaz do registru.
- **Kontroluje se jen tuzemské přenesení daňové povinnosti.** Jiné důsledky
  statusu odběratele (například u dodání do jiného členského státu nebo v
  kontrolním hlášení) se nekontrolují.
- **§ 92a má i další podmínky než to, že odběratel je plátcem** — například
  druh plnění. Modul žádnou z nich nekontroluje.
- **Registrace k DPH od** není z registru dostupná a zůstane prázdná, dokud ji
  nezadáte.
- Člen skupiny používá DIČ skupiny; evidujte skupinu, ne dřívější registraci
  člena.
- Přijaté faktury se nekontrolují.
