---
title: Platební symboly CZ/SK (VS/KS/SS)
summary: Variabilní, konstantní a specifický symbol na fakturách, platbách a bankovních výpisech a párování přijatých plateb podle nich.
verified: 19.0.1.4.1
---

## K čemu slouží {#purpose}

Plátce v Česku a na Slovensku neoznačuje platbu volným textem, ale číselnými
**platebními symboly**:

| Symbol | Název | Délka | Obvyklé použití |
|---|---|---|---|
| VS | variabilní symbol | nejvýše 10 číslic | číslo faktury — to, co má odběratel uvést při platbě |
| KS | konstantní symbol | nejvýše 4 číslice | druh platby, např. `0008` zboží, `0308` služby |
| SS | specifický symbol | nejvýše 10 číslic | doplňkový identifikátor, který vyžadují někteří příjemci (pojišťovny, leasing) |

Samotné Odoo zná jen volný text *Payment Reference*. Tento modul dává třem
symbolům vlastní kontrolovaná pole, vyplní je za vás, přenese je do platebních
QR kódů, plateb a bankovních souborů, načte je zpět z bankovních výpisů a — s
jedním z doplňkových modulů — páruje přijaté platby s fakturami podle
variabilního symbolu.

**Pozor na záměnu:** český překlad Odoo nazývá volné textové pole *Payment
Reference* „Variabilní symbol“. Není to variabilní symbol — ten je v
samostatném poli, které přidává tento modul a které přijme jen číslice.
Modul proto pole ve formuláři faktury přejmenovává zpět na *Payment Reference*.

Závisí jen na modulu `account`, takže funguje v edici Community i Enterprise a
nepotřebuje zbytek česko-slovenské lokalizace.

## Právní rámec {#legal}

Symboly jsou v obou zemích **bankovní konvencí**, ne zákonnou povinností u
běžných obchodních plateb:

- **Česko.** Symboly dříve vymezovala vyhláška ČNB č. 62/2004 Sb. Tu zrušil
  [§ 7 vyhlášky č. 169/2011 Sb.](law:cz/2011/169), která je už nevymezuje.
  Zůstaly jako konvence bank a součást platebních pokynů příjemců, kteří je
  vyžadují, například finanční správy nebo správy sociálního zabezpečení.
- **Slovensko.** U SEPA převodu se symboly přenášejí v referenci plátce ve
  tvaru `/VS…/SS…/KS…`. Od 18. března 2024 banky na základě doporučení
  Národnej banky Slovenska stále častěji přidávají na začátek otazník:
  `?/VS…/SS…/KS…` (VS a SS nejvýše 10 číslic, KS 4). Modul čte obě podoby.

Protože variabilní symbol je jedinečný jen **u jednoho vystavitele** — dva
dodavatelé mohou mít fakturu s číslem 2026001 — párování popsané níže se nikdy
nespoléhá jen na symbol, pokud ví, kdo platil.

## Nastavení {#setup}

*Účetnictví → Konfigurace → Nastavení*, blok **Czech / Slovak Payment
Symbols** (popisky nastavení jsou v této verzi anglicky):

| Nastavení | Co dělá |
|---|---|
| Variabilní symbol dobropisu (*Credit note variable symbol*) | Zda opravný daňový doklad odběrateli nese **vlastní číslo** (výchozí), nebo **variabilní symbol faktury, kterou opravuje**. Druhou možnost zvolte, pokud si odběratelé dobropisy započítávají proti původní faktuře. |
| Výchozí konstantní symbol (*Default constant symbol*) | Předvyplní se na každé faktuře a dobropisu odběrateli, např. `0308`, pokud prodáváte služby. Prázdné = žádný. |
| Payment Reference = variabilní symbol (*Payment reference = variable symbol*) | Při zaúčtování dokladu odběrateli se jeho *Payment Reference* nastaví na variabilní symbol. Vlastní QR kódy Odoo, identifikátor platby v e-faktuře (UBL) i standardní párování výpisů pak nesou VS bez dalšího nastavování. Již zaúčtované doklady se nemění. |

## Na fakturách, dobropisech a přijatých fakturách {#invoices}

Tři pole — *Variable Symbol*, *Constant Symbol*, *Specific Symbol* — jsou hned
za polem *Payment Reference*: na přijaté faktuře v hlavní části formuláře, na
faktuře a dobropisu odběrateli na kartě *Další informace*.

- **Faktura odběrateli.** Variabilní symbol se vyplní z číslic čísla dokladu,
  ponechá se posledních 10: z `FV/2026/00042` vznikne `202600042`. Konstantní
  symbol se převezme z výchozí hodnoty společnosti.
- **Dobropis odběrateli.** Vlastní číslo, nebo symbol původní faktury, podle
  nastavení výše.
- **Přijatá faktura.** Variabilní symbol se vezme z číslic pole *Reference
  faktury* — obvykle číslo faktury dodavatele, které je zároveň VS, jenž
  očekává. Pokud dodavatel žádá jiný VS, přepište ho.

Všechna pole lze upravit. Hodnotu, která není jen z číslic nebo je delší než
10 / 4 / 10 číslic, Odoo při uložení odmítne.

Prodejní účtenky (*out_receipt*) symboly nezobrazují, protože Odoo u nich
nezobrazuje ani *Payment Reference*.

## Platební QR kódy {#qr}

Když faktura tiskne platební QR kód, její symboly se předají generátoru QR
kódu, takže kód, který odběratel naskenuje, nese VS, KS a SS jako samostatné
údaje. České a slovenské formáty QR kódů poskytují moduly
[module:account_qr_code_qr_platba_cz](module:account_qr_code_qr_platba_cz)
(QR Platba),
[module:account_qr_code_pay_by_square_sk](module:account_qr_code_pay_by_square_sk)
(PAY by square) a
[module:account_qr_code_payme_sk](module:account_qr_code_payme_sk)
(payme.sk).

## Platby {#payments}

Tlačítko *Zaplatit* (průvodce registrací platby) přenese symboly na vytvořenou
platbu, pokud mají všechny hrazené doklady stejnou hodnotu. Hromadná platba za
faktury s různými variabilními symboly nedostane žádný — banka příjemce by ji
stejně nedokázala přiřadit jedné faktuře. Symboly jsou na formuláři platby za
polem *Poznámka* a lze je upravit.

## Bankovní výpisy {#bank-statements}

Když vznikne řádek výpisu — z bankovního konektoru nebo importem souboru —
symboly se vyplní v tomto pořadí z:

1. hodnot, které konektor předá přímo;
2. podrobností transakce od konektoru pod obvyklými názvy klíčů
   (`variable_symbol`, `variableSymbol`, `vs`, `variable_code` a obdobně pro
   KS a SS);
3. značek v popisu, referenci a poznámce: `VS:123`, `VS 123`, `/VS123`,
   `/VS/123`, `?/VS123/SS/KS`. Soubory CAMT často nesou symboly jen v
   referenci, proto se čte i ta.

Nulový symbol (`SS0`) se považuje za žádný. Variabilní symbol se navíc zapíše
na začátek popisu (`123 - původní popis`, nikdy dvakrát), aby ho vidělo i
standardní párování Odoo. Řádky, které existovaly před instalací modulu, se
zpětně nečtou.

## Párování přijatých plateb podle variabilního symbolu {#bank-matching}

Jeden ze dvou doplňkových modulů přidá do automatického párování výpisů přesné
porovnání variabilního symbolu. Oba se nainstalují samy, je-li přítomen jejich
párovací nástroj:

- [module:l10n_cssk_payment_symbols_ee](module:l10n_cssk_payment_symbols_ee)
  — pro párování výpisů v Odoo Enterprise;
- [module:l10n_cssk_payment_symbols_oca](module:l10n_cssk_payment_symbols_oca)
  — pro párovací nástroj OCA (`account_reconcile_oca`) v edici Community.

Pravidlo mají společné. Řádek výpisu s variabilním symbolem se porovná s
otevřenými zaúčtovanými doklady téže společnosti se stejným symbolem, přičemž
se **ignorují úvodní nuly** (`0042` = `42`):

- Pokud řádek výpisu už zná plátce (podle čísla účtu), berou se v úvahu jen
  doklady tohoto partnera.
- Nese-li symbol právě jeden doklad, spáruje se s ním.
- Nese-li ho více dokladů, vezme se ten, jehož otevřená částka se rovná
  platbě — ale jen je-li takový právě jeden, a jen v měně společnosti. Dva
  doklady se stejným symbolem i částkou (dva prodejní deníky mohou oba vystavit
  …00001) zůstanou na vás.
- Jinak se nespáruje nic a řádek zůstane na vás. Modul nikdy nehádá.

Zálohové faktury (proformy) se podle variabilního symbolu párují ve stejném
kroku, je-li nainstalován modul
[module:sale_order_advance_invoice_payment_match](module:sale_order_advance_invoice_payment_match#matching).

Rozdíly mezi nimi:

| | Enterprise | OCA |
|---|---|---|
| Kdy běží | před vlastním párováním Odoo, které ignoruje řetězce do 5 znaků, a proto krátký VS nespáruje nikdy | před vlastním párováním faktur v OCA |
| Platba pokryje fakturu | spárováno | spárováno |
| Částečná úhrada | spárováno, zbytek faktury zůstane otevřený | spárováno, zbytek faktury zůstane otevřený |
| Přeplatek | faktura se spáruje, přebytek jde do vlastního párování Odoo a na vás | navrhne se v nástroji, automaticky se nikdy nespáruje |
| Cizí měna | jen párování s jedním dokladem | ponechá se na OCA a na vás |
| Více řádků v jednom importu | — | řádek najde jen to, co předchozí řádky téhož importu nechaly otevřené: druhá úplná úhrada téže faktury zůstane na vás, splátky ji uhradí společně a přeplatek ponechaný na vás neubere nic dalšímu řádku |
| Navíc | sloupec VS a vyhledávání podle VS v seznamu bankovních transakcí (KS, SS volitelně) | — |

## Platební příkazy {#payment-orders}

Jsou-li nainstalovány platební příkazy OCA (`account_payment_order`), modul
[module:l10n_cssk_payment_symbols_payment_order](module:l10n_cssk_payment_symbols_payment_order)
přenese VS, KS a SS každého dokladu na řádky platebního příkazu, které z něj
vzniknou. Exportéry tuzemských bankovních souborů —
[module:account_abo](module:account_abo) (formát ABO) a
[module:account_multicash](module:account_multicash) — je zapíší do souboru
jako strukturované symboly. Vlastní obrazovku nemá.

## SEPA převody / ISO 20022 {#iso20022}

Při exportu ISO 20022 v Odoo Enterprise přidá modul
[module:l10n_cssk_payment_symbols_iso20022](module:l10n_cssk_payment_symbols_iso20022)
ke každému bankovnímu deníku volbu **CZ/SK Symbols in pain.001**:

| Volba | Co se zapíše do souboru |
|---|---|
| *Remittance info* (výchozí) | `/VS/…/KS/…/SS/…` připojené k nestrukturované informaci pro příjemce; `PLATBA/VS/…`, pokud žádná nebyla. Strukturovaná reference věřitele (RF) zůstane beze změny. |
| *EndToEndId = variable symbol* | samotný variabilní symbol jako identifikátor end-to-end |
| *Do not export symbols* | standardní soubor Odoo |

**Před použitím kterékoli volby si to ověřte u své banky.** Banky se liší v
tom, co zpětně rozpoznají jako symboly, a slovenská konvence popsaná
[výše](#legal) zapisuje `?/VS…/SS…/KS…` — písmena a číslice bez lomítka mezi
nimi, v pořadí VS–SS–KS — což nevytváří ani jedna z voleb. Pošlete jednu
zkušební platbu a podívejte se, jak se zobrazí na výpisu příjemce.

## Omezení {#limitations}

- Variabilní symbol se odvozuje z čísla dokladu. Číselná řada s předponou roku
  dá symboly jako `202600042`; pokud jsou odběratelé zvyklí na jiný tvar,
  upravte číselnou řadu nebo symbol.
- Automatické párování je přesné a opatrné: žádné přibližné párování, žádné
  párování více dokladů v cizí měně, nic napříč společnostmi.
- Symboly se z řádků výpisu čtou při jejich vzniku, ne později.
