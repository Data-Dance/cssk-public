---
title: Fio banka — připojení
summary: Tokeny API Fio banky na bankovním deníku, test připojení, limit jednoho volání za 30 sekund a upozornění před koncem platnosti tokenu.
verified: 19.0.2.2.4
---

## K čemu slouží {#purpose}

Fio banka — v Česku i prostřednictvím své slovenské pobočky — umožňuje
klientům připojit účetní program k účtům přes **API Fio** pomocí **tokenu**
vygenerovaného v internetovém bankovnictví. Tento modul uchovává tokeny u
bankovního deníku a poskytuje to, co sdílejí všechny funkce Fio: test
připojení, limit volání a upozornění na konec platnosti.

Sám nic neplatí ani neimportuje. Funkce poskytují moduly:

- [module:account_statement_fio](module:account_statement_fio) — stahuje
  pohyby a oficiální výpisy do deníku podle plánu;
- [module:account_payment_fio](module:account_payment_fio) — odesílá platební
  příkazy do Fio z platebního příkazu OCA, nebo s modulem
  [module:account_payment_fio_batch](module:account_payment_fio_batch) z
  hromadné platby Enterprise.

## Tokeny {#tokens}

Token Fio:

- se vygeneruje v internetovém bankovnictví Fio v části **Nastavení → API**,
  autorizuje se SMS nebo push notifikací a použít ho lze **za pět minut**;
- patří **jednomu účtu** — a Fio vede každou měnu jako samostatný účet, takže
  účet v CZK a účet v EUR potřebují samostatné tokeny i samostatné deníky;
- má jedno ze dvou oprávnění: *Sledování účtu* nebo *Sledování účtu a
  zadávání platebních a inkasních příkazů*;
- platí nejvýše **180 dní**; bez data konce platnosti ho Fio nevydá.

Používejte **dva tokeny na účet**: token pro čtení pro stahování výpisů a
samostatný token pro zadávání pro platební příkazy. Token pro čtení se používá
každou hodinu, a je proto nejvíce vystaven — a token, který umí jen číst,
nemůže nikomu zaplatit. Každý token má i vlastní limit volání (viz níže).

## Nastavení {#setup}

1. Otevřete bankovní deník: *Účetnictví → Konfigurace → Účetnictví → Účetní
   deníky*. Jeho bankovní účet musí být ten účet u Fio, ke kterému tokeny
   patří.
2. V části **Fio banka** pod číslem bankovního účtu vyplňte pole z tabulky níže.

| Pole | |
|---|---|
| Token Fio pro čtení | token pro čtení (64 znaků) |
| Platnost tokenu Fio pro čtení do | datum konce platnosti opsané z internetového bankovnictví |
| Token Fio pro zadávání | token pro zadávání, budete-li odesílat platby |
| Platnost tokenu Fio pro zadávání do | jeho datum konce platnosti |
| Formát stahování Fio | *Fio XML* (výchozí) nebo *Fio JSON*; ponechte XML |

Tokeny vidí a zadávají jen uživatelé s oprávněním správce (*Nastavení*).
Ostatní vidí jen to, zda je token nastaven.

Pak stiskněte **Test connection** (tlačítko je v této verzi anglicky). Odoo
provede jedno volání, uloží, co Fio o účtu hlásí (číslo účtu, kód banky,
IBAN, BIC, měnu — zobrazí se pod nadpisem *What Fio reports about this
account*), a zapíše poznámku do chatteru deníku. Token, který patří **jinému
účtu**, než je IBAN deníku, nebo účtu v jiné měně, než má deník, se odmítne
— import by do těchto knih zaúčtoval pohyby cizího účtu.

*Účetnictví → Konfigurace → Účetnictví → Fio banka* zobrazí všechny deníky s
tokenem pro čtení a obě data konce platnosti; datum, které už uplynulo, je
červené.

## Konec platnosti tokenů {#expiry}

API Fio nikdy nesdělí, kdy token skončí, proto se obě pole s datem konce
platnosti vyplňují ručně. Plánovaná akce *Fio: warn about expiring tokens*
jednou denně vytvoří na deníku aktivitu (úkol) **14 dní** před zapsaným datem
konce platnosti a přidělí ji správci účetnictví společnosti.

**Prázdné datum konce platnosti znamená žádné upozornění** — stahování výpisů
nebo odesílání plateb pak prostě přestane fungovat v den, kdy token skončí.

## Limit volání {#rate-limit}

Fio povoluje **jedno volání na token za 30 sekund**, pro čtení i zadávání, v
jakémkoli formátu. Odoo si pamatuje poslední volání každého tokenu (*Poslední
volání Fio pro čtení*, *Poslední volání Fio pro zadávání*) a všechna volání Fio
jednoho deníku řadí za sebe:

- tlačítko stisknuté příliš brzy (například *Stáhnout hned* hned po testu
  připojení) obrazovku nezmrazí, ale oznámí, kdy bude další volání možné;
- plánované akce zbývající sekundy počkají;
- běží-li na témže deníku jiná operace s Fio, budete požádáni zkusit to za
  chvíli.

## Platební titul u partnerů {#payment-reason}

Fio vyžaduje **platební titul** — důvod platby z číselníku České národní banky
— u každé zahraniční platby a z účtu vedeného slovenskou pobočkou i u platby
SEPA nad 50 000 EUR. Modul přidává partnerovi pole **Platební titul** (karta
*Nákup a Prodej*, pod platebními podmínkami dodavatele), zvlášť pro každou
společnost. Je výchozí hodnotou pro platby tomuto partnerovi; viz
[module:account_payment_fio](module:account_payment_fio#checks).

## Klient API {#api}

Samotný protokol — volání REST, formáty výpisů Fio XML a JSON, XML platebních
příkazů (`importIB.xsd`) a odpovědi banky — je v modulu
[module:account_fio_base](module:account_fio_base), napsaném podle
dokumentace *FIO API BANKOVNICTVÍ* ve verzi 1.9 z 16. října 2025. Fio nese
token ve webové adrese každého volání, proto ho klient odstraňuje z každého
chybového hlášení a záznamu v logu.

## Omezení {#limitations}

- Fio **neprovozuje testovací prostředí**. Připojení bylo vyzkoušeno na
  zaznamenaných odpovědích banky; skutečné chování, zejména u více měn a u
  hlášení Fio k jednotlivým příkazům, lze ověřit jen na skutečném účtu.
- Kontrola účtu při testu připojení porovnává IBAN. Deník, jehož bankovní účet
  je zapsán jako `číslo/kód banky` místo IBAN, se neporovná (měna ano).
- Čas posledního volání se zapíše před voláním. Selže-li volání, tento záznam
  se vrátí zpět a další pokus může Fio odmítnout jako předčasný — s
  vysvětlujícím hlášením.
- Tokeny jsou v databázi uloženy jako čistý text, čitelný pro správce.
