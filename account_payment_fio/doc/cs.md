---
title: Fio banka — platební příkazy
summary: Sestaví platební příkazy Fio XML z platebního příkazu OCA nebo z hromadné platby Enterprise a odešle je přes API do Fio banky k autorizaci v internetovém bankovnictví.
verified: 19.0.1.3.0
---

## K čemu slouží {#purpose}

Místo stahování platebního souboru a jeho nahrávání do internetového
bankovnictví odešlete dávku plateb z Odoo do Fio banky jedním tlačítkem. Fio ji
uloží jako **neautorizovanou dávku**; někdo s podpisovým právem ji pak potvrdí
v internetovém bankovnictví Fio (SMS nebo podpisem Fio). **Odoo samo žádné
peníze nepošle.**

Soubor je ve vlastním XML formátu Fio (`importIB.xsd`), jediném formátu pro
Fio, který nese variabilní, konstantní a specifický symbol jako samostatná
pole — pain.001 je jen pro EUR a ABO jen pro tuzemské platby v CZK. Modul
pracuje s **platebním příkazem** OCA (`account_payment_order`); v edici
Enterprise dělá totéž s **hromadnou platbou** modul
[module:account_payment_fio_batch](module:account_payment_fio_batch) — viz
[níže](#batch).

Potřebuje připojení podle modulu [module:account_fio](module:account_fio#setup)
s **tokenem pro zadávání** u deníku.

## Tři druhy příkazů {#kinds}

Každý řádek platebního příkazu se automaticky stane jedním ze tří příkazů Fio:

| Účet příjemce | Příkaz Fio | Poznámky |
|---|---|---|
| český: IBAN `CZ` nebo `[předčíslí-]číslo/kód banky` | tuzemská platba | libovolná měna, kterou Fio povoluje mezi vlastními účty; VS, KS, SS, zpráva pro příjemce |
| EUR na IBAN v zemi SEPA (včetně Slovenska) | Europlatba (SEPA) | VS, KS, SS; vyžaduje se jméno příjemce |
| cokoli jiného | zahraniční platba | vyžaduje se BIC, jméno, ulice, město a země příjemce, reference platby a *platební titul* |

U platebního příkazu se na každém řádku nastaví **Priority** (*Urgent* odešle
prioritní platbu) a **Charge Bearer** (u zahraničních plateb); výchozí je
standardní platba a sdílené poplatky.

Příkazy se zapíšou v pořadí tuzemské, Europlatby, zahraniční, jak to Fio
vyžaduje. Soubor má název `FIO-<kód deníku>-<datum a čas>.xml`.

## Nastavení {#setup}

1. Bankovní deník: jeho bankovní účet je účet u Fio, ze kterého peníze
   odcházejí — IBAN `CZ` nebo `SK`, případně `číslo/2010` (Fio CZ) nebo
   `číslo/8330` (Fio SK). Potřebuje **Token Fio pro zadávání** (viz
   [module:account_fio](module:account_fio#tokens)).
2. Způsob platby (*Účetnictví → Konfigurace → Účetnictví → Payment Modes*) s
   platební metodou **Fio XML (Fio banka API)** a tímto deníkem.
3. Partneři: bankovní účet u každého, komu platíte; u zahraničních plateb i
   adresu, BIC jeho banky a **Platební titul** u partnera (karta *Nákup a
   Prodej*), aby se vyplňoval sám.
4. Doporučujeme [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   aby se VS/KS/SS faktur dostaly na řádky platebního příkazu samy (viz
   [module:account_abo](module:account_abo#setup)).

## Placení {#usage}

Popisky platebních příkazů OCA jsou v této verzi anglicky.

1. *Účetnictví → Dodavatelé → Payment Orders*, **Nové**, zvolte způsob platby
   Fio, **Create Payment Lines from Journal Items**.
2. Zkontrolujte řádky: **Variabilní symbol**, **Konstantní symbol**,
   **Specifický symbol** a **Platební titul** jsou vedle pole *Communication*.
   Prázdný symbol se vezme ze značky `VS:` / `KS:` / `SS:` v poli
   *Communication*.
3. **Confirm Payments**. Zde se vše zkontroluje (viz níže).
4. **Generate Payment File** a pak **Odeslat do Fio**.
5. Dávku autorizujte v internetovém bankovnictví Fio.

Když Fio dávku přijme, příkaz zobrazí *Sent to Fio as batch …* s číslem dávky
Fio a sám přejde do stavu nahraného souboru — tlačítko *File Successfully
Uploaded* není potřeba. Odpověď Fio včetně upozornění k jednotlivým příkazům se
zapíše do chatteru příkazu.

### Co se kontroluje {#checks}

Při **Confirm Payments** se zkontroluje celý příkaz a **všechny** problémy se
vypíšou v jednom hlášení (*This payment order cannot be sent to Fio yet*):

- částka není kladná nebo chybí měna, datum či účet příjemce;
- tuzemská platba nemá kód banky;
- Europlatba nebo zahraniční platba nemá jméno příjemce;
- zahraniční platbě chybí BIC, ulice, město nebo země příjemce, reference
  platby (pole *Communication*) nebo platný *platební titul*;
- Europlatba nad 50 000 EUR z účtu vedeného **slovenskou** pobočkou Fio nemá
  platný *platební titul*;
- účet není IBAN ani tuzemské `číslo/kód banky`.

*Platební titul* je trojmístný kód důvodu platby z číselníku České národní
banky. Na řádku platebního příkazu se předvyplní z partnera.

## Odeslání do Fio {#send}

Tlačítko **Odeslat do Fio** se zobrazí na každém platebním příkazu, který má
vygenerovaný soubor a ještě nebyl odeslán. Druh souboru rozpozná ze samotného
souboru, takže odešle i:

- soubor ABO z modulu [module:account_abo](module:account_abo),
- soubor SEPA pain.001 (a pain.008) z modulů SEPA od OCA,

pokud je deník účtem u Fio s tokenem pro zadávání. Soubory nad 2 MB Fio
odmítne; pak příkaz rozdělte.

**Pokud se odpověď ztratí.** Když soubor z Odoo odešel, ale odpověď nepřišla,
nikdo neví, zda Fio dávku má. Příkaz pak přejde do stavu **Neznámo — ověřte v
bance** a zobrazí červené upozornění; opětovné odeslání je zablokováno,
protože druhá dávka by při autorizaci obou zaplatila vše dvakrát. Podívejte se
v internetovém bankovnictví Fio, zda tam je neautorizovaná dávka, a zapište,
co jste zjistili:

- **V bance JE** — příkaz se označí jako odeslaný a znovu odeslat nejde;
- **V bance NENÍ** — odeslání se znovu povolí.

Dávka, kterou Fio **odmítne**, zůstane *Neodesláno*; důvody se zobrazí na
obrazovce i v chatteru a po opravě ji můžete odeslat znovu.

## Hromadné platby Enterprise {#batch}

Modul [module:account_payment_fio_batch](module:account_payment_fio_batch)
sestaví totéž Fio XML z **hromadné platby** Enterprise a odešle ho stejným
tlačítkem se stejnou pojistkou stavu *Neznámo*.

- Po instalaci se odchozí platební metoda **Fio XML (Fio banka API)** přidá
  do bankovních deníků, jejichž vlastní účet je u Fio (kód banky 2010 nebo
  8330, nebo BIC Fio), a do takových deníků založených později nebo deníků,
  jimž se účet u Fio doplní později. Deníky jiných bank ji nedostanou.
- Formulář platby dodavateli dostane pole **Platební titul** předvyplněné z
  partnera.
- Zaregistrujte platby s touto metodou, seskupte je do hromadné platby
  (*Účetnictví → Dodavatelé → Hromadné platby*) a stiskněte **Potvrdit**:
  hromadná platba před zapsáním souboru vypíše všechny platby, které nelze
  odeslat, seskupené podle problému. Pak stiskněte **Odeslat do Fio**. Odpověď
  banky je na kartě *Fio* hromadné platby.
- Všechny platby hromadné platby se provedou k **datu hromadné platby**,
  protože v internetovém bankovnictví se dávka autorizuje jako celek.
- S modulem ISO 20022 od Odoo se platba označená jako urgentní odešle jako
  prioritní.

Oba moduly lze mít nainstalované současně.

## Omezení {#limitations}

- **„Odesláno“ neznamená „zaplaceno“**: dávka čeká v internetovém bankovnictví
  na autorizaci.
- Číslo dávky Fio není ID pokynu, které se později objeví na řádcích výpisu,
  takže platbu přes něj k řádku výpisu nedohledáte — párujte podle VS, částky
  a data.
- Účet plátce nemůže mít **předčíslí**: `accountFrom` je u Fio holé číslo.
  Nastavte deníku číslo účtu tak, jak ho ukazuje samo Fio.
- **Slovenské příjemce zadávejte jako IBAN.** Účet `číslo/kód banky` se čte
  jako český. Když Odoo ví, že je slovenský — země jeho banky, jinak země
  majitele je Slovensko — platba se odmítne s žádostí o IBAN `SK`, místo aby
  odešla české bance s tím kódem; bez zaznamenané země odejde dál jako česká
  tuzemská platba.
- Fio neprovozuje testovací prostředí; první dávku si před autorizací v
  internetovém bankovnictví důkladně zkontrolujte.
