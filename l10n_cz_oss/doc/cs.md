---
title: Přiznání k DPH OSS — režim Unie (OSSEI1)
summary: České přiznání ve zvláštním režimu jednoho správního místa, režim Evropské unie, jako formulář EPO OSSEI1 ověřený proti úřednímu schématu.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Český plátce nebo identifikovaná osoba registrovaná ve **zvláštním režimu
jednoho správního místa — režimu Evropské unie** podává čtvrtletně přiznání
k dani uplatněné u prodeje zboží na dálku a u služeb spotřebitelům v jiných
státech EU. Tento modul převede přiznání spočtené modulem
[module:l10n_cssk_oss_base](module:l10n_cssk_oss_base) do formuláře EPO
**OSSEI1** (*DAP OSS — režim EU — Přiznání k DPH*) a před připojením ho ověří
proti úřednímu schématu.

Vše o přípravě přiznání — řádky, opravy, směnné kurzy a kroky exportu —
popisuje [společný návod](module:l10n_cssk_oss_base#usage). Tato stránka
popisuje to, co je české.

## Právní rámec {#legal}

Odkazy jsou na [zákon č. 235/2004 Sb., o dani z přidané hodnoty](law:cz/2004/235).

- **Kdo může režim použít.** Podle [§ 110l odst. 1](law:cz/2004/235) osoba, která má sídlo
  v tuzemsku (nebo bez sídla a provozovny v EU zahajuje odeslání zboží
  v tuzemsku), je plátcem nebo identifikovanou osobou a nepoužívá režim
  Evropské unie v jiném členském státě. Přihláška k registraci se podává podle
  [§ 110p](law:cz/2004/235).
- **Jeden správce daně pro všechny.** Zvláštní režim spravuje *Finanční úřad
  pro Jihomoravský kraj* ([§ 110a odst. 3](law:cz/2004/235)), nikoli místně příslušný úřad
  společnosti. Formulář proto kód finančního úřadu neobsahuje.
- **Jen elektronicky.** Formulářová podání ve zvláštním režimu, s výjimkou
  přihlášky k registraci, se činí elektronicky prostřednictvím elektronického
  portálu ([§ 110o odst. 1](law:cz/2004/235)).
- **Období a lhůta.** Zdaňovacím obdobím je kalendářní čtvrtletí ([§ 110zb](law:cz/2004/235));
  přiznání se podává do konce následujícího měsíce, i když nebylo uskutečněno
  žádné plnění, a lhůta se na další pracovní den neposouvá ([§ 110zc](law:cz/2004/235)).
- **Částky.** Daň se vyčísluje v eurech s přesností na dvě desetinná místa bez
  zaokrouhlování; přepočítává se kurzem ECB zveřejněným pro poslední den
  období nebo nejbližší následující den, u opravy kurzem použitým u původního
  plnění ([§ 110ze](law:cz/2004/235)).
- **Opravy.** Oprava daně je součástí přiznání za období, ve kterém se
  uživatel o rozhodných skutečnostech dozvěděl, a nelze ji uvést po uplynutí
  tří let od lhůty pro podání původního přiznání ([§ 110zd](law:cz/2004/235)).

## Formulář {#form}

Modul vytváří jediný formulář **OSSEI1**, verze struktury **01.01.04** ze dne
13. 12. 2021, použitelný pro každé čtvrtletí od 3. čtvrtletí 2021. Tak se
v Česku verzuje: EPO zveřejňuje jediné schéma `ossei1_epo2.xsd` a přepisuje ho
na místě, a přiznání za staré čtvrtletí se podává ve struktuře platné v době
podání. Existuje proto **jedna časově neomezená verze formuláře**, *DAP OSS —
režim EU (OSSEI1)*, a podle roku se nic nevybírá.

Ani schéma, ani verze struktury v souboru (`verzePis`) neprozradí, že jsou
zastaralé — zastaralé schéma ověří zastaralý soubor bez chyby. Modul má schéma
připnuté velikostí a kontrolním součtem a test selže, pokud přibalené schéma
neodpovídá. Když Finanční správa zveřejní novou strukturu, je třeba modul
aktualizovat.

Co soubor obsahuje:

| Věta | Obsah |
|---|---|
| `VetaD` | čtvrtletí, rok, DIČ bez předpony `CZ`, název společnosti, `A` u přiznání s údaji nebo `N` u nulového přiznání a datum začátku nebo konce, pokud registrace začala nebo skončila během čtvrtletí |
| `VetaP` | DIČ |
| `VetaR` | jedna za stát spotřeby × sazbu × zboží (`G`) nebo služby (`S`): stát, ze kterého se dodává, typ sazby `Z` (základní) nebo `S` (snížená), sazba, základ daně a daň v eurech; Řecko jako `EL` |
| `VetaO` | jedna za opravované čtvrtletí a stát spotřeby: oprava daně v eurech se znaménkem |

## Nastavení {#setup}

- **DIČ** společnosti musí být české: `CZ` a 8 až 10 číslic. Export jiné
  odmítne dřív, než by to udělalo EPO.
- Verze formuláře se nainstaluje s modulem. Na každém přiznání zvolte
  *DAP OSS — režim EU (OSSEI1)*.
- Daně OSS v Odoo nastavte podle
  [společného návodu](module:l10n_cssk_oss_base#setup).

## Podání {#usage}

1. Přiznání připravte a spočtěte v *Účetnictví → Výkazy → Zákonné výkazy →
   Přiznání k DPH OSS* a potvrďte kurzy ECB.
2. **Exportovat XML**. Soubor se ověří proti OSSEI1 a připojí.
3. Podejte ho přes elektronický portál Finanční správy (EPO) — načtením souboru
   tam, nebo odesláním z Odoo modulem [module:l10n_cz_epo](module:l10n_cz_epo)
   tlačítkem **Podat**.
4. **Označit jako podané**, aby se uchovala podaná kopie.

Daň zaplaťte v eurech bezhotovostním převodem na účet správce daně vedený
v eurech s uvedením referenčního čísla přiznání ([§ 110h](law:cz/2004/235)). Modul platbu
nevytváří.

## Omezení {#limitations}

- **Zaokrouhlování.** § 110ze odst. 1 žádá částky v eurech na dvě desetinná
  místa bez zaokrouhlování. Modul daň každého řádku zaokrouhluje na centy
  matematicky, takže řádek se může od useknuté částky lišit o jeden cent.
  Ověřte si to před podáním s daňovým poradcem.
- Jen režim Evropské unie (OSSEI1). Režim mimo Evropskou unii (OSSNI1),
  dovozní režim (OSSII1) ani přiznání MOSS za čtvrtletí před 3. čtvrtletím 2021
  (OSSDI1) vytvořené nejsou.
- Opravu, kterou je po uplynutí tří let třeba podat přímo státu spotřeby, modul
  nepřipravuje.
- Nová struktura EPO vyžaduje aktualizaci modulu; jiné varování než odmítnutí
  souboru v EPO neexistuje.
- Kontroly jsou ty, které popisuje
  [společný návod](module:l10n_cssk_oss_base#limitations); vlastní obsahové
  kontroly EPO proběhnou až při podání nebo kontrole souboru tam.
