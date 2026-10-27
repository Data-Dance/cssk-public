---
title: QR Platba (Česká republika)
summary: Tiskne na faktury odběratelům český platební kód QR Platba s variabilním, konstantním a specifickým symbolem jako samostatnými údaji.
verified: 19.0.1.1.3
---

## K čemu slouží {#purpose}

**QR Platba** je standard platebního QR kódu České bankovní asociace,
postavený na formátu Short Payment Descriptor (SPD). Čte ho každá česká
bankovní aplikace: odběratel naskenuje kód na vaší faktuře a dostane platební
příkaz s vyplněným vaším účtem, částkou a variabilním symbolem.

Modul přidává QR Platbu jako formát QR kódu na fakturách Odoo. To, co mají
národní formáty společné — zapnutí QR kódů, potřebný bankovní účet a způsob,
jakým Odoo pro každou fakturu vybírá formát — popisuje modul
[module:account_qr_code_frame_provider](module:account_qr_code_frame_provider),
který se nainstaluje spolu s tímto modulem.

## Nastavení {#setup}

1. Zapněte *QR kódy* v *Účetnictví → Konfigurace → Nastavení* — viz
   [společné nastavení](module:account_qr_code_frame_provider#setup).
2. Bankovní účet zadejte ve tvaru **IBAN** (například `CZ65 0800 …`), ne jako
   tuzemské číslo účtu s kódem banky, a vyplňte *Jméno majitele účtu*. IBAN
   musí být ze země SEPA.

QR Platba je v automatickém výběru Odoo **první** a použije se pro každou
fakturu, která je **v CZK, nebo je určena odběrateli z Česka** v jakékoli
měně. Ostatní faktury propadnou k dalšímu formátu. *QR Platba (Czech
Republic)* — popisek se zobrazuje anglicky — můžete v poli *QR kód platby* na
faktuře vždy vybrat i ručně; viz
[Jaký formát faktura dostane](module:account_qr_code_frame_provider#method-choice).

## Co kód obsahuje {#content}

Pole, které Odoo v anglickém originálu nazývá *Payment Reference*, je v české
verzi přeloženo jako *Variabilní symbol*; níže se o něm mluví jako o
referenci platby.

| Pole SPD | Odkud se bere |
|---|---|
| `ACC` účet | IBAN účtu v poli *Banka příjemce* na faktuře |
| `AM` částka, `CC` měna | částka, která na faktuře zbývá uhradit, v měně faktury |
| `MSG` zpráva pro příjemce | reference platby, a není-li, číslo faktury; prvních 60 znaků, hvězdička zapsaná jako `%2A` a `%` jako `%25`, jak standard předepisuje |
| `RF` identifikátor platby pro příjemce | variabilní symbol, jinak číslice ze zprávy; nejvýše 16 číslic |
| `RN` jméno příjemce | *Jméno majitele účtu*, nebo jméno vlastníka účtu; ošetřené stejně jako `MSG` |
| `X-VS`, `X-SS`, `X-KS` | variabilní, specifický a konstantní symbol faktury, je-li nainstalován modul [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr) |

Kód se vykresluje v rámečku QR Platby.

## Omezení {#limitations}

- Datum splatnosti (`DT`) se nepředává; bankovní aplikace navrhne vlastní
  datum platby.
- QR Platba se vybere pro každou fakturu českému odběrateli, i v eurech a i
  tehdy, když je vaše společnost slovenská. Pokud to nechcete, vyberte na
  faktuře jiný formát.
- Bez modulu platebních symbolů nejsou v kódu pole `X-VS`/`X-SS`/`X-KS`;
  variabilní symbol se pak k odběrateli dostane jen přes `RF` a zprávu, pokud
  ho reference obsahuje.
