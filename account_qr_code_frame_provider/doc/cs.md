---
title: Platební QR kódy CZ/SK — společný základ
summary: Co mají české a slovenské platební QR kódy na fakturách společné — zapnutí, výběr formátu pro každou fakturu a rámeček s logem schématu.
verified: 19.0.1.1.1
---

## K čemu slouží {#purpose}

Odoo umí na fakturu odběrateli vytisknout platební QR kód. Odběratel ho
naskenuje v aplikaci své banky a dostane platební příkaz s vyplněným účtem,
částkou a platebními údaji. Každá země má vlastní formát:

| Formát | Země | Modul |
|---|---|---|
| QR Platba (*Short Payment Descriptor*) | Česko | [module:account_qr_code_qr_platba_cz](module:account_qr_code_qr_platba_cz) |
| PAY by square | Slovensko | [module:account_qr_code_pay_by_square_sk](module:account_qr_code_pay_by_square_sk) |
| payme | Slovensko | [module:account_qr_code_payme_sk](module:account_qr_code_payme_sk) |
| SEPA Credit Transfer QR (EPC) | eurozóna | vlastní formát Odoo, instaluje se s Účetnictvím |

Tento modul je to, co mají tři národní formáty společné. Nainstaluje se s
kterýmkoli z nich a nemá nastavení. Modul:

- **vybere správný formát** pro každou fakturu, pokud výběr necháte na Odoo
  (viz [níže](#method-choice));
- vykreslí národní kód **v rámečku jeho schématu** — s logem, které odběratel
  zná ze své bankovní aplikace;
- odstraní logo Odoo, které standardní rozvržení faktury umísťuje doprostřed
  platebního QR kódu.

## Zapnutí QR kódů {#setup}

1. *Účetnictví → Konfigurace → Nastavení*, blok *Zákaznické platby*:
   zaškrtněte **QR kódy**.
2. Nainstalujte modul(y) formátů, které potřebujete.
3. Bankovní účet, na který má odběratel platit, musí být zadán ve tvaru
   **IBAN** a mít vyplněné *Jméno majitele účtu* (nebo patřit kontaktu se
   jménem). Tuzemské číslo účtu ve tvaru `123-4567890/0100` nestačí, zadejte
   jeho IBAN. Je to účet, který faktura zobrazuje jako *Banka příjemce*.

Kód se tiskne na PDF fakturu, dokud má faktura neuhrazenou částku, a zní na
**částku, která zbývá uhradit** — částečně uhrazená faktura tedy žádá jen
zbytek. Uhrazená faktura kód netiskne.

Je-li nainstalován modul
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr),
předají se kódu variabilní, konstantní a specifický symbol faktury jako
samostatné údaje; kam přesně se dostanou, popisuje stránka každého formátu.

## Jaký formát faktura dostane {#method-choice}

Rozhoduje pole *QR kód platby* na kartě *Další informace* faktury.

- **Pokud v něm formát vyberete**, použije se — a nelze-li ho pro danou
  fakturu použít (jiná měna, účet není IBAN), tisk se zastaví se zprávou proč.
- **Pokud ho necháte prázdné**, Odoo vezme první formát, který faktuře
  vyhovuje, v tomto pořadí, a uloží ho do pole:

| Pořadí | Formát | Použije se automaticky, když |
|---|---|---|
| 1 | QR Platba | faktura je v CZK **nebo** je odběratel z Česka |
| 2 | PAY by square | faktura je v EUR **a** vaše společnost (majitel účtu) i odběratel jsou ze Slovenska |
| 3 | payme | jako u PAY by square |
| 4 | SEPA Credit Transfer QR | faktura je v EUR |

Všechny formáty navíc vyžadují IBAN ze země SEPA. Nemá-li strana vyplněnou
zemi, formátu to nevadí: slovenská společnost, která fakturuje odběrateli bez
země, dostane PAY by square.

Česká společnost tedy u faktury v eurech německému odběrateli dostane kód
SEPA, slovenská společnost u faktury českému odběrateli QR Platbu a faktura
mezi dvěma slovenskými firmami slovenský formát.

Formát uložený na faktuře už zůstane. Má-li Odoo vybírat znovu, pole vymažte.

## Omezení {#limitations}

- **PAY by square má přednost před payme**, a to pevným pořadím, ne pořadím
  načtení modulů: jsou-li nainstalovány oba, mezi slovenskými stranami se
  automaticky vybere PAY by square. Chcete-li na faktuře payme, vyberte ho
  v poli *QR kód platby*.
- QR Platba se vybere pro každou fakturu českému odběrateli, i v eurech a i
  tehdy, když vaše společnost není česká.
- Logo Odoo zmizí jen z platebního QR kódu. Samostatný QR kód s odkazem na
  platbu (*Přidejte odkaz s QR kódem v PDFu*) se nemění.
- Národní formáty se vybírají automaticky jen na fakturách. Jinde (například
  u platebního požadavku vytvořeného přímo z bankovního účtu) platí
  standardní pořadí Odoo.
