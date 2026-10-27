---
title: Fio banka — pripojenie
summary: Tokeny API Fio banky na bankovom denníku, test pripojenia, limit jedného volania za 30 sekúnd a upozornenia pred koncom platnosti tokenu.
verified: 19.0.2.2.4
---

## Na čo slúži {#purpose}

Fio banka — v Česku aj prostredníctvom svojej slovenskej pobočky — umožňuje
klientom pripojiť účtovný program k účtom cez **API Fio** pomocou **tokenu**
vygenerovaného v internetbankingu. Tento modul uchováva tokeny pri bankovom
denníku a poskytuje to, čo zdieľajú všetky funkcie Fio: test pripojenia, limit
volaní a upozornenia na koniec platnosti.

Sám nič neplatí ani neimportuje. Funkcie poskytujú moduly:

- [module:account_statement_fio](module:account_statement_fio) — sťahuje
  pohyby a oficiálne výpisy do denníka podľa plánu;
- [module:account_payment_fio](module:account_payment_fio) — odosiela
  platobné príkazy do Fio z platobného príkazu OCA, alebo s modulom
  [module:account_payment_fio_batch](module:account_payment_fio_batch) z
  hromadnej platby Enterprise.

## Tokeny {#tokens}

Token Fio:

- sa vygeneruje v internetbankingu Fio v časti **Nastavení → API**, autorizuje
  sa SMS alebo push notifikáciou a použiť ho možno **o päť minút**;
- patrí **jednému účtu** — a Fio vedie každú menu ako samostatný účet, takže
  účet v CZK a účet v EUR potrebujú samostatné tokeny aj samostatné denníky;
- má jedno z dvoch oprávnení: *Sledování účtu* (čítanie účtu) alebo
  *Sledování účtu a zadávání platebních a inkasních příkazů* (čítanie a
  zadávanie platobných a inkasných príkazov);
- platí najviac **180 dní**; bez dátumu konca platnosti ho Fio nevydá.

Používajte **dva tokeny na účet**: token na čítanie pre sťahovanie výpisov a
samostatný token na zadávanie pre platobné príkazy. Token na čítanie sa
používa každú hodinu, a preto je najviac vystavený — a token, ktorý vie len
čítať, nemôže nikomu zaplatiť. Každý token má aj vlastný limit volaní (pozri
nižšie).

## Nastavenie {#setup}

1. Otvorte bankový denník: *Účtovníctvo → Konfigurácia → Účtovníctvo →
   Účtovné denníky*. Jeho bankový účet musí byť ten účet vo Fio, ku ktorému
   tokeny patria.
2. V časti **Fio banka** pod číslom bankového účtu vyplňte polia z tabuľky nižšie.

| Pole | |
|---|---|
| Token Fio na čítanie | token na čítanie (64 znakov) |
| Platnosť tokenu Fio na čítanie do | dátum konca platnosti prepísaný z internetbankingu |
| Token Fio na zadávanie | token na zadávanie, ak budete odosielať platby |
| Platnosť tokenu Fio na zadávanie do | jeho dátum konca platnosti |
| Formát sťahovania Fio | *Fio XML* (predvolené) alebo *Fio JSON*; ponechajte XML |

Tokeny vidia a zadávajú len používatelia s oprávnením správcu
(*Nastavenia*). Ostatní vidia len to, či je token nastavený.

Potom stlačte **Test connection** (tlačidlo je v tejto verzii po anglicky). Odoo
urobí jedno volanie, uloží, čo Fio o účte hlási (číslo účtu, kód banky,
IBAN, BIC, menu — zobrazí sa pod nadpisom *What Fio reports about this
account*), a zapíše poznámku do chatteru denníka. Token, ktorý patrí **inému
účtu**, než je IBAN denníka, alebo účtu v inej mene, než má denník, sa
odmietne — import by do týchto kníh zaúčtoval pohyby cudzieho účtu.

*Účtovníctvo → Konfigurácia → Účtovníctvo → Fio banka* zobrazí všetky denníky
s tokenom na čítanie a oba dátumy konca platnosti; dátum, ktorý už uplynul, je
červený.

## Koniec platnosti tokenov {#expiry}

API Fio nikdy neoznámi, kedy token skončí, preto sa obe polia s dátumom konca
platnosti vypĺňajú ručne. Plánovaná akcia *Fio: warn about expiring tokens*
raz denne vytvorí na denníku aktivitu (úlohu) **14 dní** pred zapísaným
dátumom konca platnosti a pridelí ju správcovi účtovníctva spoločnosti.

**Prázdny dátum konca platnosti znamená žiadne upozornenie** — sťahovanie
výpisov alebo odosielanie platieb potom jednoducho prestane fungovať v deň,
keď token skončí.

## Limit volaní {#rate-limit}

Fio povoľuje **jedno volanie na token za 30 sekúnd**, na čítanie aj
zadávanie, v akomkoľvek formáte. Odoo si pamätá posledné volanie každého tokenu
(*Posledné volanie Fio na čítanie*, *Posledné volanie Fio na zadávanie*) a
všetky volania Fio jedného denníka radí za sebou:

- tlačidlo stlačené príliš skoro (napríklad *Stiahnuť hneď* hneď po teste
  pripojenia) obrazovku nezamrazí, ale oznámi, kedy bude ďalšie volanie možné;
- plánované akcie zvyšné sekundy počkajú;
- ak na tom istom denníku práve beží iná operácia s Fio, budete požiadaný
  skúsiť to o chvíľu.

## Platobný titul pri partneroch {#payment-reason}

Fio vyžaduje **platobný titul** — dôvod platby z číselníka Českej národnej
banky — pri každej zahraničnej platbe a z účtu vedeného slovenskou pobočkou aj
pri platbe SEPA nad 50 000 EUR. Modul pridáva partnerovi pole **Platobný
titul** (karta *Predaj a nákup*, pod platobnými podmienkami dodávateľa),
osobitne pre každú spoločnosť. Je predvolenou hodnotou pre platby tomuto
partnerovi; pozri
[module:account_payment_fio](module:account_payment_fio#checks).

## Klient API {#api}

Samotný protokol — volania REST, formáty výpisov Fio XML a JSON, XML
platobných príkazov (`importIB.xsd`) a odpovede banky — je v module
[module:account_fio_base](module:account_fio_base), napísanom podľa
dokumentácie *FIO API BANKOVNICTVÍ* vo verzii 1.9 zo 16. októbra 2025. Fio
nesie token vo webovej adrese každého volania, preto ho klient odstraňuje z
každého chybového hlásenia a záznamu v logu.

## Obmedzenia {#limitations}

- Fio **neprevádzkuje testovacie prostredie**. Pripojenie bolo vyskúšané na
  zaznamenaných odpovediach banky; skutočné správanie, najmä pri viacerých
  menách a pri hláseniach Fio k jednotlivým príkazom, sa dá overiť len na
  skutočnom účte.
- Kontrola účtu pri teste pripojenia porovnáva IBAN. Denník, ktorého bankový
  účet je zapísaný ako `číslo/kód banky` namiesto IBAN, sa neporovná (mena
  áno).
- Čas posledného volania sa zapíše pred volaním. Ak volanie zlyhá, tento
  záznam sa vráti späť a ďalší pokus môže Fio odmietnuť ako predčasný — s
  vysvetľujúcim hlásením.
- Tokeny sú v databáze uložené ako čistý text, čitateľný pre správcov.
