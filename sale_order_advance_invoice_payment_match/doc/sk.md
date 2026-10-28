---
title: Zálohové faktúry — párovanie bankových výpisov
summary: Páruje prijaté bankové platby s otvorenými zálohovými faktúrami podľa čísla preddavku alebo variabilného symbolu, zaeviduje platbu a podľa nastavenia vytvorí faktúru k prijatej platbe.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Zálohová faktúra z modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) nemá
pred úhradou žiadny účtovný zápis, takže ju žiadne párovanie výpisov — ani
Odoo, ani OCA — k prijatej platbe nikdy neponúkne. Tento modul to rieši.
Nájde preddavok, ktorý bankový pohyb uhrádza, a zaeviduje platbu presne tak
ako tlačidlo **Zaevidovať platbu** na preddavku. Podľa nastavenia vytvorí aj
faktúru k prijatej platbe.

Je obdobou párovania faktúr v module
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-matching):
ten páruje platby so zaúčtovanými faktúrami, tento so zálohovými faktúrami.
Oba prechody sú na sebe nezávislé.

Modul nemá slovenský preklad; jeho nastavenia a tlačidlá sa zobrazujú po
anglicky.

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Advance Invoices — Bank
Matching**:

| Nastavenie | Účel |
|---|---|
| Automatické párovanie (*Auto-match bank statements*) | Zapne automatické párovanie pre spoločnosť (predvolene vypnuté). Ručný sprievodca funguje v každom prípade. |
| Faktúra k spárovanej platbe (*Tax document on matched payment*) | Čo sa stane, keď bankový pohyb uhradí preddavok: **Leave for manual creation** — nechať na ručné vytvorenie (predvolené), **Create as draft** — vytvoriť koncept, alebo **Create and post** — vytvoriť a zaúčtovať. Zaúčtovanie zároveň vyrovná zúčtovací účet. |

Nastavenia preddavkov v module
[module:sale_order_advance_invoice](module:sale_order_advance_invoice#setup)
musia byť úplné, predovšetkým **Zúčtovací účet preddavkov**. Bankový denník
potrebuje spôsob prijatej platby s účtom neuhradených príjmov.

## Ako sa pohyb páruje {#matching}

Do úvahy prichádzajú len prijaté platby v mene spoločnosti. Porovnávajú sa
so zálohovými faktúrami spoločnosti, ktoré nie sú zrušené a majú ešte niečo
neuhradené. Ak bankový pohyb už pozná zákazníka (napríklad podľa čísla účtu),
berú sa do úvahy len preddavky tohto zákazníka.

Pohyb sa hľadá v troch úrovniach od najsilnejšej a rozhoduje prvá úroveň,
ktorá niečo nájde:

| Úroveň | Čo sa porovnáva | Kedy sa uplatní automaticky |
|---|---|---|
| Číslo preddavku | `ADV00042` v popise, referencii alebo podrobnostiach transakcie od banky | suma neprevyšuje neuhradenú časť |
| Variabilný symbol | variabilný symbol pohybu s číslicami čísla preddavku, **bez ohľadu na úvodné nuly** (`42` = `00042`) | suma neprevyšuje neuhradenú časť |
| Číslice | ktorýkoľvek reťazec 3 až 10 číslic v popise alebo referencii, porovnaný rovnako | suma sa **rovná** neuhradenej časti |

Úroveň variabilného symbolu potrebuje variabilný symbol na bankovom pohybe.
Z výpisov ho číta modul
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements);
bez neho sa táto úroveň preskočí.

Ak úroveň nájde **viac ako jeden** preddavok, nespáruje sa nič. Číslo
preddavku je jedinečné len v rámci vystaviteľa, takže párovanie nikdy
nehádá. V prvých dvoch úrovniach sa prijmú aj čiastočné platby. Platba vyššia
než neuhradená časť sa automaticky nikdy neuplatní.

Požiadajte zákazníkov, aby uvádzali číslo preddavku alebo jeho číslice ako
variabilný symbol: pri `ADV00042` variabilný symbol `42` alebo `00042`.

## Čo spárovanie urobí {#applying}

1. V bankovom denníku vznikne platba zákazníka na sumu a dátum pohybu,
   zaúčtovaná na **zúčtovací účet preddavkov** a prepojená s preddavkom.
   Ponuka sa potvrdí.
2. Bankový pohyb bez zákazníka dostane zákazníka z preddavku.
3. Pohyb sa spáruje s platbou, takže sa zobrazí ako spárovaný.
4. Pri voľbe **Create as draft** alebo **Create and post** sa vytvorí faktúra
   k prijatej platbe tak, ako ju opisuje
   [module:sale_order_advance_invoice](module:sale_order_advance_invoice#tax-document),
   pri druhej voľbe aj zaúčtovaná.

## Automatické a ručné párovanie {#triggers}

- **Plánovaná akcia** *Advance Invoices: match bank statement lines* beží
  každých 15 minút. Prejde najviac 200 nespárovaných prijatých pohybov v
  bankových denníkoch spoločností so zapnutým automatickým párovaním: najprv
  tie, ktoré ešte nevidela, potom zvyškom z 200 postupne staršie. Pohyb,
  ktorý sa nedá spárovať bezpečne, nechá tak a príde naň rad znova neskôr,
  takže sa skúša každý otvorený pohyb, nech ich je koľkokoľvek.
- **Match Advance Invoice** v ponuke *Akcie* bankového pohybu (v zozname aj
  vo formulári) otvorí sprievodcu. Navrhne preddavok podľa pravidiel a
  môžete vybrať ktorýkoľvek otvorený preddavok tej istej spoločnosti (a toho
  istého zákazníka, ak ho pohyb má). **Register Payment** potom urobí to isté
  ako automatické spárovanie. Sprievodca nepotrebuje automatické nastavenie a
  odmietne sumu vyššiu než neuhradenú časť.

### V párovaní bankových výpisov {#bank-reconciliation}

Dva doplnky spúšťajú to isté párovanie v rámci automatického párovania
výpisov, a to **pred** ním. Pohyb s číslom preddavku sa tak nemôže najprv
podľa slov spárovať s nesúvisiacim dokladom. Oba sa nainštalujú samy, keď je
prítomný ich základ, a oba rešpektujú nastavenie automatického párovania:

- [module:sale_order_advance_invoice_payment_match_ee](module:sale_order_advance_invoice_payment_match_ee)
  — párovanie výpisov Odoo Enterprise (`account_accountant`): beží pred jeho
  automatickým párovaním;
- [module:sale_order_advance_invoice_payment_match_oca](module:sale_order_advance_invoice_payment_match_oca)
  — párovací widget OCA (`account_reconcile_oca`) v Community: beží pred jeho
  modelmi párovania a párovaním faktúr, a len keď skutočne páruje, nie keď
  iba počíta návrh.

Spárované pohyby sa v oboch widgetoch zobrazia ako spárované.

## Obmedzenia {#limitations}

- Len prijaté platby v mene spoločnosti, ktoré uhrádzajú preddavok v tej
  istej mene.
- Žiadne rozhodovanie podľa sumy: dva preddavky, ktoré sa hodia do tej istej
  úrovne, ostanú na vás, aj keby správnu sumu mal len jeden z nich. V tom sa
  líši od párovania faktúr v module
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-matching).
- Preplatok sa nikdy nerozdelí. Platbu aj preplatok zaevidujte ručne.
- Úroveň číslic môže pomýliť číslo, ktoré nie je symbolom, napríklad dátum
  alebo číslo účtu. Preto spáruje len pri presnej sume.
