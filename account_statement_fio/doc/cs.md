---
title: Fio banka — bankovní výpisy
summary: Každou hodinu stahuje pohyby a oficiální číslované výpisy z API Fio banky do bankovního deníku, se symboly VS/KS/SS a účty protistrany.
verified: 19.0.2.4.1
---

## K čemu slouží {#purpose}

S tímto modulem se deník Fio banky plní sám: Odoo se každou hodinu zeptá API
Fio na nové pohyby a vytvoří řádky výpisu s účtem protistrany, platebními
symboly a zprávou. Není co stahovat ani importovat. Funguje stejně v edici
Community i Enterprise a pro české i slovenské účty u Fio.

Potřebuje připojení nastavené podle modulu
[module:account_fio](module:account_fio#setup): **token pro čtení** u
deníku.

## Zapnutí {#setup}

1. Na bankovním deníku (*Účetnictví → Konfigurace → Účetnictví → Účetní
   deníky*) nastavte pole **Bankovní napojení** (*Bank Feeds*) na **Fio banka
   API**. Deník nastavený na Fio bez tokenu pro čtení nelze uložit.
2. V části **Fio banka** se zobrazí pravý sloupec *Bank statements*. Zvolte
   **Režim stahování Fio** (viz níže) a v režimu pohybů i **Dní zpětného čtení
   Fio**.
3. Stiskněte **Stáhnout hned** a stáhněte první dávku. Od té doby běží
   plánovaná akce *Fio: pull bank statements* každou hodinu.

Protože pole *Bankovní napojení* má jedinou hodnotu, Fio a vlastní bankovní
synchronizace Odoo Enterprise nemohou plnit tentýž deník současně — každý
pohyb by se naimportoval dvakrát. Deník plněný z Fio navíc přestane na
přehledu Účetnictví vyzývat k „připojení banky“.

Samotné tokeny lze používat i tehdy, má-li pole *Bankovní napojení* jinou
hodnotu: deník může odesílat platby do Fio a výpisy dostávat jinak.

## Režimy stahování {#modes}

| Režim stahování Fio | Co udělá každý běh | K čemu se hodí |
|---|---|---|
| **Pohyby (opakovaně čitelný rozsah dat)** — výchozí | načte pohyby od *dnes − dní zpětného čtení* do dneška a přidá ty, které Odoo ještě nemá | každodenní párování; vynechaný běh či restart nenechá díru |
| **Oficiální číslované výpisy** | zjistí od Fio číslo posledního výpisu a stáhne každý výpis, který Odoo ještě nemá (nejvýše 12 za běh); z každého vznikne bankovní výpis s názvem `<číslo>/<rok>` s počátečním a konečným zůstatkem podle banky | účetní závěrku: kontrola zůstatku v Odoo porovnává s dokladem, který vydala banka |
| **Od záložky uložené na tokenu** | stáhne vše od záložky, kterou Fio vede na tokenu, a posune ji | jen s tokenem, který nic jiného nepoužívá |

Poznámky:

- **Dní zpětného čtení** (výchozí 3): překryv nic nestojí, protože již
  naimportované pohyby se vynechají.
- **Seskupovat pohyby Fio do výpisů** (jen v režimu pohybů, výchozí vypnuto):
  jeden výpis na každý den s pohyby, s názvem `<kód deníku>/<datum>`, jehož
  počáteční a konečný zůstatek se dopočte ze zůstatku, který Fio hlásí na
  začátku rozsahu, a z předchozích pohybů. Znovu načtený den přibude na
  výpis, který už má, takže každý výpis sedí se svými zůstatky.
- **Oficiální výpisy, první běh**: stáhne se jen poslední výpis. Na přelomu
  roku modul začne znovu výpisem č. 1 nového roku. Starší výpisy a zbytek
  předchozího roku stáhnete přes *Stáhnout rozsah…*.
- **Záložka** je uložena u Fio, na tokenu. Cokoli jiného, co s týmž tokenem
  čte pohyby — jiný program, kolega při zkoušení — ji posune a tyto pohyby do
  Odoo nikdy nepřijdou.

## Ruční stažení rozsahu {#backfill}

**Stáhnout rozsah…** na deníku (i v nabídce *Akce* deníku) otevře průvodce
*Stáhnout z Fio*:

- *Pohyby v rozsahu dat*: data od–do (výchozí posledních 7 dní);
- *Oficiální číslované výpisy*: rok a první a poslední číslo výpisu.

Průvodce předem řekne, kolik volání požadavek znamená — při jednom volání za
30 sekund trvá rok pohybů rozdělený po měsících zhruba šest minut.

**Starší než 90 dní**: Fio taková data poskytne, jen dokud je pro token v
internetovém bankovnictví odemčena celá historie (*Nastavení → API*, zámek), a
odemčení platí **deset minut**. Průvodce vás požádá, abyste historii nejprve
odemkli a zaškrtli *Historie odemčena v internetovém bankovnictví*; tlačítko
**Stáhnout** se zobrazí až potom.

## Co se zapíše na řádek výpisu {#mapping}

| Fio | Odoo |
|---|---|
| ID pohybu | klíč importu řádku a *ID pohybu Fio* |
| Datum | datum (datum zaúčtování, jak ho uvádí Fio) |
| Objem | částka |
| Protiúčet + Kód banky | účet protistrany `číslo/kód banky`, podle něhož se hledá partner |
| Název protiúčtu | název partnera |
| VS, KS, SS | pole symbolů (s modulem [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements)) a značky `VS:…` v popisu |
| Zpráva pro příjemce, jinak Komentář, jinak Uživatelská identifikace, jinak Typ | popis (první vyplněný) |
| Typ | typ transakce |
| Reference plátce | reference (pole *Popis*) |
| ID pokynu | *ID pokynu Fio* |
| Upřesnění ve tvaru `20.00 EUR` | původní částka a měna platby provedené v jiné měně |

Celý záznam z Fio se uloží i u řádku. Duplicity se rozpoznávají jen podle ID
pohybu. ID pokynu sdílí převod se svým poplatkem i platba s pozdějším stornem,
proto se záměrně nepoužívá.

## Když něco selže {#errors}

- Neúspěšné plánované stahování zapíše do chatteru deníku *Naplánované
  stahování z Fio selhalo: …*; ostatní deníky se stáhnou i tak.
- Pohyb v jiné měně, než má deník, zastaví stahování pro tento deník: každý
  měnový účet u Fio potřebuje vlastní deník v této měně s vlastním tokenem.
- *Stáhnout hned* oznámí, kolik nových pohybů přišlo, nebo že nebylo nic
  nového. *Poslední stažení z Fio* se aktualizuje při každém dokončeném
  stažení, i když nic nenašlo.

## Omezení {#limitations}

- **Přechod ze souborů GPC na API** nerozpozná pohyby již naimportované z GPC:
  obě cesty používají jiné klíče importu. Přejděte na hranici dne —
  naimportujte poslední výpis GPC a stahování spusťte následující den.
- **Seskupovat pohyby Fio do výpisů**: denní výpisy jsou výpisy Odoo, ne
  doklady banky; pro výpisy číslované a odsouhlasené samotným Fio používejte
  *Oficiální číslované výpisy*. Řádky naimportované před zapnutím seskupování
  se na výpis nepřesunou, takže den, který některé z nich má, nebude sedět.
  Pokud nesedí už údaje Fio za daný rozsah, výpisy z tohoto běhu se vytvoří
  bez zůstatků.
- Původní částka platby v cizí měně se čte jen z pole *Upřesnění* v přesném
  tvaru `20.00 EUR`; cokoli jiného zůstane jen v uloženém záznamu. Na
  skutečném účtu s více měnami to ještě je třeba ověřit.
- V oficiálním režimu stáhne jeden běh nejvýše 12 chybějících výpisů; delší
  mezera se doplní během více běhů nebo přes *Stáhnout rozsah…*.
- V edici Enterprise modul přidá dva základní moduly OCA
  (`account_statement_base`, `account_statement_import_base`) pro klíč importu
  a párování partnerů.
