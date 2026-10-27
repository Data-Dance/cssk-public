---
title: Zálohové faktury — párování bankovních výpisů
summary: Páruje přijaté bankovní platby s otevřenými zálohovými fakturami podle čísla zálohy nebo variabilního symbolu, zaeviduje platbu a podle nastavení vytvoří daňový doklad k přijaté platbě.
verified: 19.0.1.0.2
---

## K čemu slouží {#purpose}

Zálohová faktura z modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) nemá
před zaplacením žádný účetní zápis, takže ji žádné párování výpisů — ani
Odoo, ani OCA — k přijaté platbě nikdy nenabídne. Tento modul to řeší.
Najde zálohu, kterou bankovní pohyb hradí, a zaeviduje platbu přesně tak
jako tlačítko **Registrovat platbu** na záloze. Podle nastavení vytvoří
i daňový doklad k přijaté platbě.

Je obdobou párování faktur v modulu
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-matching):
ten páruje platby se zaúčtovanými fakturami, tento se zálohovými fakturami.
Oba průchody jsou na sobě nezávislé.

Modul nemá český překlad; jeho nastavení a tlačítka se zobrazují anglicky.

## Nastavení {#setup}

*Účetnictví → Konfigurace → Nastavení*, blok **Advance Invoices — Bank
Matching**:

| Nastavení | Účel |
|---|---|
| Automatické párování (*Auto-match bank statements*) | Zapne automatické párování pro společnost (výchozí vypnuto). Ruční průvodce funguje v každém případě. |
| Daňový doklad ke spárované platbě (*Tax document on matched payment*) | Co se stane, když bankovní pohyb uhradí zálohu: **Leave for manual creation** — nechat k ručnímu vytvoření (výchozí), **Create as draft** — vytvořit koncept, nebo **Create and post** — vytvořit a zaúčtovat. Zaúčtování zároveň vyrovná zúčtovací účet. |

Nastavení záloh v modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice#setup)
musí být úplné, především **Zúčtovací účet záloh**. Bankovní deník potřebuje
způsob příchozí platby s účtem čekajících plateb.

## Jak se pohyb páruje {#matching}

V úvahu přicházejí jen přijaté platby v měně společnosti. Porovnávají se se
zálohovými fakturami společnosti, které nejsou zrušené a mají ještě něco
nezaplaceno. Zná-li bankovní pohyb už zákazníka (například podle čísla
účtu), berou se v úvahu jen zálohy tohoto zákazníka.

Pohyb se hledá ve třech úrovních od nejsilnější a rozhoduje první úroveň,
která něco najde:

| Úroveň | Co se porovnává | Kdy se uplatní automaticky |
|---|---|---|
| Číslo zálohy | `ADV00042` v popisu, referenci nebo podrobnostech transakce od banky | částka nepřevyšuje nezaplacenou část |
| Variabilní symbol | variabilní symbol pohybu s číslicemi čísla zálohy, **bez ohledu na úvodní nuly** (`42` = `00042`) | částka nepřevyšuje nezaplacenou část |
| Číslice | kterýkoli řetězec 3 až 10 číslic v popisu nebo referenci, porovnaný stejně | částka se **rovná** nezaplacené části |

Úroveň variabilního symbolu potřebuje variabilní symbol na bankovním pohybu.
Z výpisů ho čte modul
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements);
bez něj se tato úroveň přeskočí.

Najde-li úroveň **více než jednu** zálohu, nespáruje se nic. Číslo zálohy je
jedinečné jen v rámci vystavitele, takže párování nikdy nehádá. V prvních
dvou úrovních se přijmou i částečné platby. Platba vyšší než nezaplacená část
se automaticky nikdy neuplatní.

Požádejte zákazníky, aby uváděli číslo zálohy nebo jeho číslice jako
variabilní symbol: u `ADV00042` variabilní symbol `42` nebo `00042`.

## Co spárování udělá {#applying}

1. V bankovním deníku vznikne platba zákazníka na částku a datum pohybu,
   zaúčtovaná na **zúčtovací účet záloh** a provázaná se zálohou. Nabídka se
   potvrdí.
2. Bankovní pohyb bez zákazníka dostane zákazníka ze zálohy.
3. Pohyb se spáruje s platbou, takže se zobrazí jako spárovaný.
4. Při volbě **Create as draft** nebo **Create and post** se vytvoří daňový
   doklad k přijaté platbě tak, jak ho popisuje
   [module:sale_order_advance_invoice](module:sale_order_advance_invoice#tax-document),
   u druhé volby i zaúčtovaný.

## Automatické a ruční párování {#triggers}

- **Naplánovaná akce** *Advance Invoices: match bank statement lines* běží
  každých 15 minut. Projde nejvýše 200 nespárovaných přijatých pohybů
  v bankovních denících společností se zapnutým automatickým párováním:
  nejprve ty, které ještě neviděla, pak zbytkem z 200 postupně starší.
  Pohyb, který nelze spárovat bezpečně, nechá být a přijde na něj řada znovu
  později, takže se zkouší každý otevřený pohyb, ať je jich kolik chce.
- **Match Advance Invoice** v nabídce *Akce* bankovního pohybu (v seznamu
  i ve formuláři) otevře průvodce. Navrhne zálohu podle pravidel a můžete
  vybrat kteroukoli otevřenou zálohu téže společnosti (a téhož zákazníka,
  má-li ho pohyb). **Register Payment** pak udělá totéž co automatické
  spárování. Průvodce nepotřebuje automatické nastavení a odmítne částku
  vyšší než nezaplacenou část.

### V párování bankovních výpisů {#bank-reconciliation}

Dva doplňky spouštějí totéž párování v rámci automatického párování výpisů,
a to **před** ním. Pohyb s číslem zálohy se tak nemůže nejdřív podle slov
spárovat s nesouvisejícím dokladem. Oba se nainstalují samy, je-li přítomen
jejich základ, a oba respektují nastavení automatického párování:

- [module:sale_order_advance_invoice_payment_match_ee](module:sale_order_advance_invoice_payment_match_ee)
  — párování výpisů Odoo Enterprise (`account_accountant`): běží před jeho
  automatickým párováním;
- [module:sale_order_advance_invoice_payment_match_oca](module:sale_order_advance_invoice_payment_match_oca)
  — párovací widget OCA (`account_reconcile_oca`) v Community: běží před jeho
  modely párování a párováním faktur, a jen když skutečně páruje, ne když
  pouze počítá návrh.

Spárované pohyby se v obou widgetech zobrazí jako spárované.

## Omezení {#limitations}

- Jen přijaté platby v měně společnosti, které hradí zálohu v téže měně.
- Žádné rozhodování podle částky: dvě zálohy, které se hodí do téže úrovně,
  zůstanou na vás, i kdyby správnou částku měla jen jedna z nich. V tom se
  liší od párování faktur v modulu
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-matching).
- Přeplatek se nikdy nerozdělí. Platbu i přeplatek zaevidujte ručně.
- Úroveň číslic může zmást číslo, které není symbolem, například datum nebo
  číslo účtu. Proto páruje jen při přesné částce.
