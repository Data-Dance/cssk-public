---
title: CZ faktura (zákonné PDF)
summary: Doplní do tištěné české faktury platební symboly a zákonné formulace o osvobození od daně a „daň odvede zákazník“.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Faktura z Odoo spolu s českou účtovou osnovou (`l10n_cz`) už obsahuje většinu
náležitostí daňového dokladu: označení obou stran a jejich daňová
identifikační čísla (pro Česko Odoo DIČ tak i nadepisuje), IČO odběratele,
evidenční číslo dokladu, den vystavení a den uskutečnění zdanitelného plnění
(*DUZP*), položky, základ daně a daň podle sazeb. Modul doplní, co chybí:

1. **variabilní, konstantní a specifický symbol** vedle dat faktury;
2. **zákonnou formulaci**, kterou musí obsahovat doklad o plnění osvobozeném
   od daně nebo v režimu přenesení daňové povinnosti — určí ji z daní na
   faktuře a ze země odběratele;
3. s nainstalovanými platebními režimy OCA i **formu úhrady** — viz
   [níže](#payment-mode).

Vše se tiskne jen na dokladech společnosti se sídlem v České republice.

DIČ odběratele se záměrně **netiskne** podruhé: v Česku DIČ *je* daňové
identifikační číslo pro DPH (`CZ` + číslice) a Odoo ho už tiskne.

## Právní rámec {#legal}

Náležitosti daňového dokladu stanoví
[§ 29 zákona o DPH (zákon č. 235/2004 Sb.)](law:cz/2004/235). Dva údaje z
jeho odstavce 2 závisejí na druhu plnění a právě ty modul tiskne:

- **Osvobození od daně** — § 29 odst. 2 písm. a): u plnění osvobozeného od
  daně se uvede odkaz na příslušné ustanovení zákona, předpisu Evropské unie
  nebo jiný údaj uvádějící, že plnění je od daně osvobozeno. Modul odkazuje
  na zákon: **§ 64** (dodání zboží do jiného členského státu osobě
  registrované k dani) a **§ 66** (vývoz zboží mimo EU).
- **Přenesení daňové povinnosti** — § 29 odst. 2 písm. c): je-li osobou
  povinnou přiznat daň odběratel, doklad obsahuje údaj *„daň odvede
  zákazník“*. U tuzemských plnění režim upravuje **§ 92a** a následující
  ustanovení; u služby osobě registrované k dani v jiném členském státě je
  místem plnění stát zákazníka (**§ 9 odst. 1**) a daň tam přiznává zákazník.
- **Třístranný obchod** — § 29 odst. 2 písm. e): doklad, který prostřední
  osoba třístranného obchodu vystavuje kupujícímu, obsahuje sdělení, že jde o
  třístranný obchod.

Formulace se tisknou česky bez ohledu na jazyk faktury, s anglickým
vysvětlením v závorce.

## Nastavení {#setup}

1. **Platební symboly** pocházejí z modulu
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   který se nainstaluje spolu s tímto modulem. Jeho nastavení určuje, jak se
   tvoří variabilní symbol a zda se používá výchozí konstantní symbol — viz
   [nastavení platebních symbolů](module:l10n_cssk_payment_symbols#setup).
2. **Označte daně pro tuzemský režim přenesení daňové povinnosti.**
   *Účetnictví → Konfigurace → Daně*, otevřete daň z prodeje, kterou
   používáte u plnění v režimu přenesení (česká osnova pro to má `0% RC`), a
   zaškrtněte **CZ formulace o přenesení daňové povinnosti (§ 92a)** vedle
   pole *Typ daně*. Při instalaci není označena žádná daň.

   Je-li nainstalována jiná česká lokalizace s vlastním příznakem přenesení
   daňové povinnosti na dani (pole `l10n_cz_reverse_charge`), počítá se i
   daň označená tam. Oba příznaky jsou záměrně oddělené, takže zaškrtnutí
   tohoto nezmění vykazování v onom modulu.
3. **Třístranný obchod (volitelně).** Jste-li prostřední osobou třístranného
   obchodu, vytvořte pro něj daň z prodeje 0 % a zaškrtněte na ní **CZ
   formulace o třístranném obchodu (§ 17)**. Česká osnova takovou daň nemá.
4. **Zboží, nebo služba.** Formulace u daně 0 % závisí na tom, zda jde o
   zboží, nebo službu. Rozhoduje *Rozsah daně* (Tax Scope) daně (`0% EU G` /
   `0% EX G` české osnovy jsou zboží, `0% EU S` / `0% EX S` služby); u daně
   bez rozsahu rozhoduje typ produktu a řádek bez obojího se počítá jako
   zboží.

## Co faktura obsahuje {#invoice}

### Platební symboly

*Variabilní symbol*, *Konstantní symbol* a *Specifický symbol* v řádku s
datem vystavení a splatnosti, každý jen tehdy, má-li hodnotu. Popisky jsou
vždy česky.

### Zákonné formulace {#phrases}

Formulace se určuje vždy znovu z daní na faktuře a z **obchodního partnera**
odběratele (firmy, ne kontaktní osoby). Tiskne se pod poznámkou s obchodními
podmínkami. Řádky se posuzují v tomto pořadí; přenesení daňové povinnosti
vylučuje ostatní a faktura osobě registrované k dani v EU může dostat více
formulací, kombinuje-li zboží, služby a třístranný obchod.

| Situace | Vytiskne se |
|---|---|
| Některý řádek má daň označenou pro přenesení daňové povinnosti | *Daň odvede zákazník — přenesení daňové povinnosti podle §92a zákona o DPH (Reverse charge).* |
| Odběratel v jiném státě EU s DIČ, daň označená pro třístranný obchod | *Třístranný obchod — zjednodušený postup, daň odvede zákazník (§29 odst. 2 písm. c) a e) zákona o DPH; čl. 141 a 197 směrnice 2006/112/ES).* |
| Odběratel v jiném státě EU s DIČ, řádek zboží s daní 0 % | *Osvobozeno od daně podle §64 zákona o DPH (Intra-Community supply of goods).* |
| Odběratel v jiném státě EU s DIČ, řádek služby s daní 0 % | *Daň odvede zákazník — místo plnění podle §9 odst. 1 zákona o DPH (čl. 196 směrnice 2006/112/ES, Reverse charge).* |
| Odběratel mimo EU, řádek zboží s daní 0 % | *Osvobozeno od daně podle §66 zákona o DPH (Exempt — export of goods).* |
| Jinak (včetně služby odběrateli mimo EU) | nic |

Stejná pravidla platí pro opravné daňové doklady (dobropisy) odběratelům.
České daně Odoo `0% EU G` a `0% EU S` mají i vlastní anglické poznámky
(články 138 a 196 směrnice), které Odoo tiskne také.

### Vlastní poznámka

Je-li automatická formulace chybná nebo nestačí, napište správný text do pole
**Zákonná poznámka faktury (ručně)** na kartě *Položky faktury* pod
obchodními podmínkami; pole je na fakturách a opravných dokladech
odběratelům. Vytiskne se za automatickou formulací. Při duplikování faktury
se nekopíruje.

## Forma úhrady na faktuře {#payment-mode}

Je-li nainstalován modul OCA `account_payment_mode`, nainstaluje se sám modul
[module:l10n_cz_invoice_payment_mode](module:l10n_cz_invoice_payment_mode) a
tiskne **platební režim** faktury (pole *Payment Mode*) pod nadpisem *Forma
úhrady* ve stejném řádku jako platební symboly — například *Převodem* nebo
*Hotově*, podle toho, jak jste své platební režimy pojmenovali. Tiskne se jen
tehdy, má-li faktura platební režim, a jen u české společnosti. Samotný
`account_payment_mode` tiskne jen poznámku režimu, v patičce faktury.

## Omezení {#limitations}

- Tuzemské osvobozené plnění s daní 0 % prodané zahraničnímu odběrateli
  dostane také formulaci podle § 64 nebo § 66; tuzemské osvobozené plnění
  českému odběrateli nedostane žádnou.
- Pravidlo neověřuje DIČ odběratele ve VIES a nezná právní důvod konkrétního
  osvobození. Nechte si je potvrdit účetním pro vaše nastavení daní.
- Formulace jsou česky s anglickým vysvětlením; popisky symbolů jsou vždy
  česky.
