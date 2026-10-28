---
title: Platební soubory ABO
summary: Tuzemské úhrady v CZK exportované do souboru ABO k nahrání do banky, z platebního příkazu OCA nebo z hromadné platby Enterprise.
verified: 19.0.2.1.0
---

## K čemu slouží {#purpose}

**ABO** je textový soubor s pevnou strukturou, který české banky přijímají
jako hromadný příkaz k úhradě tuzemských plateb. Místo zadávání plateb do
internetového bankovnictví po jedné vyberete v Odoo přijaté faktury k úhradě,
vygenerujete jeden soubor ABO a nahrajete ho do banky.

Modul sestavuje soubor z **platebního příkazu** OCA (`account_payment_order`),
takže funguje v edici Community bez jakéhokoli modulu Enterprise. V edici
Enterprise sestaví tentýž soubor z **hromadné platby** modul
[module:account_abo_batch](module:account_abo_batch) — viz [níže](#batch).

Co zapisuje:

| | |
|---|---|
| Druh záznamu | úhrady, datový typ ABO `1501` |
| Uspořádání | hromadné: účet plátce je uveden jednou, v záhlaví skupiny |
| Měna | jen CZK |
| Účty | jen české účty — IBAN `CZ` nebo `[předčíslí-]číslo/kód banky` |
| Kódování | Windows-1250, konce řádků CR LF; znaky, které kódování nezná, se zjednoduší na ASCII |
| Název souboru | `ABO-<kód deníku>-<datum a čas>.abo` |

Soubor se nikam neodesílá: stáhnete ho a nahrajete v internetovém nebo přímém
bankovnictví sami. U Fio banky ho můžete odeslat i přímo z Odoo — viz
[module:account_payment_fio](module:account_payment_fio#send).

## Nastavení {#setup}

Popisky platebních příkazů OCA a tohoto modulu jsou v této verzi anglicky.

1. **Bankovní deník** (*Účetnictví → Konfigurace → Účetnictví → Účetní
   deníky*) musí mít vyplněný bankovní účet, a to jako český IBAN nebo jako
   `předčíslí-číslo/kód banky`. Z tohoto účtu peníze odcházejí.
2. **Způsob platby** (*Účetnictví → Konfigurace → Účetnictví → Payment
   Modes*): zvolte platební metodu **ABO (Czech credit transfer)** a
   bankovní deník z bodu 1.
3. **Každý dodavatel**, kterému platíte, musí mít v Odoo bankovní účet, opět
   jako český IBAN nebo `předčíslí-číslo/kód banky`.
4. Doporučujeme nainstalovat
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols). Jeho
   doplněk
   [module:l10n_cssk_payment_symbols_payment_order](module:l10n_cssk_payment_symbols_payment_order)
   se pak nainstaluje sám a přenese variabilní, konstantní a specifický symbol
   každé faktury na řádky platebního příkazu, takže je nemusíte přepisovat.

## Úhrada faktur platebním příkazem {#usage}

1. *Účetnictví → Dodavatelé → Payment Orders*, **Nové**, zvolte způsob platby
   ABO.
2. **Create Payment Lines from Journal Items** a vyberte faktury k úhradě.
3. Zkontrolujte řádky. Každý má pole variabilní symbol (*Variable Symbol*),
   konstantní symbol (*Constant Symbol*) a specifický symbol (*Specific
   Symbol*) vedle pole *Communication*.
4. **Confirm Payments** a pak **Generate Payment File**. Soubor `.abo` se
   přiloží k příkazu.
5. Nahrajte soubor do banky, autorizujte ho tam a příkaz označte tlačítkem
   **File Successfully Uploaded**.

### Odkud se berou symboly {#symbols}

Každý symbol řádku se vezme v tomto pořadí z:

1. pole symbolu na řádku platebního příkazu;
2. značky v poli *Communication*: `VS:12345`, `VS 12345`, `VS=12345`
   (obdobně `KS:` a `SS:`);
3. nikde — soubor pak obsahuje `0`.

Pole symbolu přijme jen číslice, nejvýše 10 u VS a SS a 4 u KS. Jak se symboly
dostanou na faktury, popisuje modul
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#invoices).

Text z pole *Communication* se stane i zprávou pro příjemce: sloučí se
mezery, odstraní se znaky, které banky ve zprávách ABO odmítají (například
`@ # ; § ! & _ * = + ? [ ]`), a text se zkrátí na 35 znaků.

## Co se kontroluje {#checks}

Generování souboru se zastaví s hlášením, pokud:

- řádek nemá bankovní účet příjemce;
- řádek není v CZK;
- účet deníku nebo příjemce není český (slovenský IBAN se odmítne);
- deník nemá bankovní účet.

Platební příkaz se zastaví u **prvního** problému; opravte ho a generujte
znovu. Varianta pro Enterprise vypíše všechny problémy najednou — viz
[níže](#batch).

## Hromadné platby Enterprise {#batch}

Modul [module:account_abo_batch](module:account_abo_batch) sestaví stejný
soubor z **hromadné platby** Enterprise (`account_batch_payment`).

- Po instalaci dostanou bankovní deníky společností, jejichž fiskální zemí
  (*Fiskální země*) je Česko, odchozí platební metodu **ABO (Czech
  credit transfer)** (karta *Odchozí platby* deníku). Dostanou ji i později
  založené bankovní deníky takové společnosti; deníky jiných zemí si ji mohou
  přidat ručně.
- Zaregistrujte platby dodavatelům na tomto deníku s touto platební metodou,
  zařaďte je do hromadné platby (*Účetnictví → Dodavatelé → Hromadné platby*) a
  stiskněte **Potvrdit**. Soubor se vygeneruje a přiloží do chatteru hromadné
  platby.
- Symboly se berou z polí VS/KS/SS samotné platby (modul
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#payments)
  je vyplní z hrazené faktury), jinak ze značky `VS:` v poli *Poznámka*.
- Před zapsáním souboru hromadná platba vypíše **všechny** platby, pro které by
  byl soubor nepoužitelný: chybí bankovní účet příjemce, platba není v CZK,
  účet příjemce není český, nulová částka.
- Bez zablokování upozorní na platby bez variabilního symbolu (odejdou jako
  `VS 0`, což banka přijme, ale příjemce platbu nespáruje) a na platby s jiným
  datem, než má hromadná platba.
- **Všechny platby se provedou k datu hromadné platby**, protože soubor ABO má
  pro všechny položky jediné datum splatnosti.

Oba moduly lze mít nainstalované současně.

## Společný sestavovač {#format}

Sestavovače souborů ABO a MultiCash jsou v modulu
[module:account_cz_bankfile_base](module:account_cz_bankfile_base), takže
varianty pro Community i Enterprise vytvářejí bajtově shodné soubory. Tentýž
modul čte česká čísla účtů v obou zápisech (IBAN i `předčíslí-číslo/kód
banky`) pro moduly KB BEST a Fio a pro importy výpisů MT940 a KB. Vlastní
obrazovku nemá.

## Omezení {#limitations}

- Dobropis seskupený s fakturou v platebním příkazu (volba způsobu platby
  *Group Transactions in Payment Orders*) se zapíše jako **jedna položka
  v čisté částce** — té, kterou příkaz zaúčtuje jako platbu. Nese variabilní
  symbol faktury; započte-li se jeden dobropis proti více fakturám, symboly se
  liší a neodejde žádný. Skupiny bez dobropisu mají dál jednu položku za
  fakturu. Bez seskupení se řádek dobropisu odmítne.
- **Jen CZK a české účty.** Soubor odmítne jakoukoli jinou měnu než CZK
  i každý jiný než český účet, včetně slovenských IBAN. Platby v
  EUR posílejte přes SEPA (ISO 20022) nebo
  [module:account_multicash](module:account_multicash) (CFA).
- **Jedno datum splatnosti na soubor.** Platební příkaz, jehož řádky mají
  různá data, se odmítne se zprávou, která je vypíše — místo aby se všechny
  řádky provedly k datu prvního. Výchozí typ data provedení (*Payment
  Execution Date Type*) *Due Date* dá každému řádku datum splatnosti jeho
  faktury — při placení přes ABO proto zvolte *Fixed Date* nebo *Immediately*,
  nebo příkaz rozdělte.
- Jen úhrady. Inkasa ve formátu ABO se nezapisují; na ně použijte MultiCash
  CFD nebo KB BEST.
- Řádek s nulovou nebo zápornou částkou zastaví export se zprávou, která ho
  jmenuje (banka by soubor odmítla).
- Soubor se do banky automaticky nenahraje (kromě Fio, jak je uvedeno výše).
