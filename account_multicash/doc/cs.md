---
title: Platební soubory MultiCash
summary: Tuzemské, prioritní, inkasní a zahraniční platby exportované do souborů MultiCash (CFD, CFU, CFA, MT101) z platebního příkazu OCA nebo z hromadné platby Enterprise.
verified: 19.0.2.2.0
---

## K čemu slouží {#purpose}

**MultiCash** je klientská aplikace, kterou několik českých bank dává firemním
klientům k odesílání dávek plateb a stahování výpisů. Přijímá platební soubory
v pevných formátech. Tento modul je sestavuje z **platebního příkazu** OCA
(`account_payment_order`), takže funguje v edici Community bez jakéhokoli
modulu Enterprise. V edici Enterprise sestaví tytéž soubory z **hromadné
platby** modul [module:account_multicash_batch](module:account_multicash_batch)
— viz [níže](#batch).

Struktura souborů vychází z popisu formátů *MultiCash 3.2* České spořitelny.
Opačný směr MultiCash — výpisy `*.STA` ve formátu MT940 — importuje modul
[module:account_statement_import_mt940](module:account_statement_import_mt940).

## Formáty {#formats}

Formát určíte výběrem platební metody. Každá metoda zapisuje jeden druh
souboru (názvy metod jsou v této verzi anglicky):

| Platební metoda | Co to je | Soubor | Měna a účty |
|---|---|---|---|
| MultiCash CFD (Czech domestic transfer) | tuzemské úhrady | `.cfd` | CZK, jen české účty |
| MultiCash CFD (Czech direct debit / inkaso) | tuzemská inkasa — stahujete peníze od odběratelů | `.cfd` | CZK, jen české účty |
| MultiCash CFU (Czech urgent transfer) | prioritní tuzemské úhrady | `.cfu` | CZK, jen české účty |
| MultiCash CFA (foreign transfer) | zahraniční platby | `.cfa` | libovolná měna; účet příjemce, jak je zadán (obvykle IBAN) |
| MultiCash MT101 (SWIFT Request For Transfer) | žádost o převod SWIFT MT101 | `.mt101` | libovolná měna; účty, jak jsou zadány |

„Český účet“ znamená IBAN `CZ` nebo `[předčíslí-]číslo/kód banky`.

Co se zapíše do souboru:

- **CFD / CFU**: za každou platbu blok s vlastním datem, částkou v haléřích,
  oběma účty, jmény a adresami plátce a příjemce (ze společnosti a z partnera,
  nejvýše čtyři řádky po 35 znacích), VS, KS a SS a nejvýše čtyřmi řádky
  zprávy z pole *Communication*. Text je velkými písmeny v kódové stránce 852.
- **CFA**: záhlaví souboru se součtem a počtem, pak za každou platbu blok ve
  stylu SWIFT: plátce, účet plátce, účet, jméno a adresa příjemce, banka
  příjemce podle BIC (nebo podle názvu a adresy, nemá-li banka BIC), údaje pro
  příjemce a nositel poplatků. Kódová stránka 852.
- **MT101**: jedna zpráva za celý soubor s jediným datem provedení, v ní
  transakce za každou platbu. Čisté ASCII.

## Nastavení {#setup}

1. **Bankovní deník** (*Účetnictví → Konfigurace → Účetnictví → Účetní
   deníky*) potřebuje bankovní účet. Pro CFD a CFU a pro účet plátce v CFA
   musí jít o český účet. Pro **CFA a MT101 musí mít banka deníku i BIC** —
   bez něj se export nespustí.
2. **Způsob platby** pro každý používaný formát (*Účetnictví → Konfigurace →
   Účetnictví → Payment Modes*) s odpovídající platební metodou MultiCash a
   deníkem. Metodu *direct debit / inkaso* použijte u příchozího způsobu
   platby.
3. **Partneři**: bankovní účet u každého partnera, kterému platíte nebo od
   kterého inkasujete. Pro CFA a MT101 i adresu a zemi partnera a nejlépe i
   BIC jeho banky.
4. Doporučujeme [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   aby se symboly faktur dostaly na řádky platebního příkazu samy (jak, popisuje
   [module:account_abo](module:account_abo#setup)).

Ověřte si u banky, které formáty pokrývá vaše smlouva — CFU, CFA a MT101 se
často sjednávají zvlášť.

## Vytvoření platebního souboru {#usage}

Popisky platebních příkazů OCA jsou v této verzi anglicky.

1. Úhrady dodavatelům: *Účetnictví → Dodavatelé → Payment Orders*. Inkaso od
   odběratelů: *Účetnictví → Zákazníci → Debit Orders*.
2. **Nové**, zvolte způsob platby MultiCash, **Create Payment Lines from
   Journal Items**.
3. Zkontrolujte na řádcích variabilní, konstantní a specifický symbol
   (*Variable Symbol*, *Constant Symbol*, *Specific Symbol*). Prázdný se vezme
   ze značky `VS:` / `KS:` / `SS:` v poli *Communication*; pokud tam není,
   soubor obsahuje `0`. U platby CFA nastavte na řádku **Priority** (*Urgent*
   pro expresní zpracování) a **Charge Bearer** (*Shared*, *Payer*,
   *Beneficiary*); výchozí je běžná priorita a sdílené poplatky.
4. **Confirm Payments**, **Generate Payment File**. Soubor se přiloží k příkazu
   jako `<formát>-<kód deníku>-<datum a čas>.<přípona>`.
5. Naimportujte soubor do MultiCash, odešlete ho odtud do banky a příkaz
   označte tlačítkem **File Successfully Uploaded**.

Příkaz se zastaví u **prvního** zjištěného problému — řádek bez bankovního
účtu, řádek s nulovou nebo zápornou částkou, řádek v jiné měně než CZK
u CFD/CFU, účet, který není český, kde se český vyžaduje, chybějící BIC,
a u MT101 řádky s různými daty.

## Hromadné platby Enterprise {#batch}

Modul [module:account_multicash_batch](module:account_multicash_batch)
sestaví tytéž soubory z **hromadné platby** Enterprise, s jednou platební
metodou na formát pod stejnými názvy.

- Po instalaci dostanou bankovní deníky společností s fiskální zemí Česko obě
  metody **CFD** (odchozí úhrada, příchozí inkaso); dostanou je i nové bankovní
  deníky těchto společností. Deníky jiných zemí je nedostanou, ale lze je do
  nich přidat ručně. **CFU, CFA a MT101 si do deníku přidáte sami** (karta *Odchozí
  platby*), až vám je banka zpřístupní.
- Zaregistrujte platby s metodou požadovaného formátu, seskupte je do hromadné
  platby (*Účetnictví → Dodavatelé → Hromadné platby*, u inkasa *Zákazníci*) a
  stiskněte **Potvrdit**. Soubor se přiloží do chatteru hromadné platby.
- Před zapsáním souboru hromadná platba vypíše **všechny** nepoužitelné
  platby: chybí bankovní účet příjemce, nulová částka, u CFD/CFU platba v jiné
  měně než CZK nebo účet příjemce, který není český, u CFA/MT101 platba bez
  partnera (jméno a adresa příjemce by byly prázdné).
- MT101 má pro celou zprávu jediné datum provedení, proto se všechny platby
  provedou k **datu hromadné platby** a u plateb s jiným datem se zobrazí
  upozornění. CFD, CFU a CFA si ponechají datum každé platby.
- Prioritu a nositele poplatků u platby CFA převezme z polí ISO 20022 platby,
  je-li nainstalován modul ISO 20022 od Odoo.

Oba moduly lze mít nainstalované současně.

## Omezení {#limitations}

- Dobropis seskupený s fakturou v platebním příkazu (volba způsobu platby
  *Group Transactions in Payment Orders*) se zapíše jako **jedna položka
  v čisté částce** — té, kterou příkaz zaúčtuje jako platbu. Nese variabilní
  symbol faktury; započte-li se jeden dobropis proti více fakturám, symboly se
  liší a neodejde žádný. Skupiny bez dobropisu mají dál jednu položku za
  fakturu. Bez seskupení se řádek dobropisu odmítne.
- **České tuzemské formáty.** CFD a CFU přijmou jen CZK a české účty; slovenský
  IBAN se odmítne. CFA vyžaduje český účet i na straně plátce.
- **MT101 z platebního příkazu** má pro celou zprávu jedno datum provedení,
  takže příkaz s řádky s různými daty se odmítne — nastavte na příkazu
  *Payment Execution Date Type* na *Fixed Date* nebo *Immediately*, nebo ho
  rozdělte.
- Znaky mimo kódovou stránku 852 (CFD, CFU, CFA) nebo ASCII (MT101) se
  zjednoduší na základní písmena; MT101 navíc vynechá znaky mimo znakovou sadu
  SWIFT.
- Soubor se do banky automaticky nenahraje; to dělá MultiCash.
- Jako specifikace sloužil jen popis České spořitelny. Import MultiCash v
  jiných bankách ho obvykle přijme, první soubor si však s bankou vyzkoušejte.
