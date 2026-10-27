---
title: Kurzy měn pro Českou republiku (ČNB)
summary: Stahuje denní kurz devizového trhu ČNB, sám založí poskytovatele a podporuje pevný měsíční kurz, přičemž skutečné denní kurzy uchovává pro přecenění k rozvahovému dni.
verified: 19.0.1.3.2
---

## K čemu slouží {#purpose}

Česká účetní jednotka, která účtuje v korunách, přepočítává doklady v cizí
měně **kurzem devizového trhu vyhlášeným Českou národní bankou**. Standardní
služba ECB v Odoo dává jiné číslo, proto modul přidává ČNB jako zdroj do
rámce OCA pro aktualizaci kurzů
([module:currency_rate_update](module:currency_rate_update)) a navíc:

- **poskytovatele ČNB založí sám** při instalaci;
- správně načte **celé období zpětně**, z ročních souborů ČNB po jednotlivých
  letech;
- podporuje **pevný měsíční kurz** pro účetní jednotky, které ho používají, a
  přitom uchovává skutečné denní kurzy pro přecenění k rozvahovému dni.

Funguje v edici Community i Enterprise.

## Právní rámec {#legal}

- **Účetnictví.** Majetek a závazky v cizí měně se přepočítávají *obecným
  kurzem* — kurzem, který centrální banka příslušná pro měnu účetnictví (u
  koruny ČNB) vyhlásí pro den přepočtu — jak k okamžiku uskutečnění účetního
  případu, tak k rozvahovému dni. K okamžiku uskutečnění účetního případu lze
  místo toho použít **pevný kurz**: obecný kurz vyhlášený pro první den
  zvoleného období, které účetní jednotka určí vnitřním předpisem a které
  končí nejpozději posledním dnem účetního období. Banky, pojišťovny a některé
  další regulované subjekty pevný kurz použít nesmějí. Viz § 24c a § 24d
  [zákona o účetnictví](law:cz/1991/563).
- **DPH.** Cizí měna se přepočítá kurzem platným pro osobu provádějící
  přepočet ke dni vzniku povinnosti přiznat daň — kurzem devizového trhu ČNB,
  nebo referenčním kurzem ECB. Viz § 4 odst. 8
  [zákona o DPH](law:cz/2004/235). Účetní jednotka s pevným kurzem ho tedy
  použije i pro DPH.

## Co nastaví instalace {#setup}

Při instalaci dostane každá společnost, jejíž zemí (nebo daňovou zemí) je
Česká republika, poskytovatele **Česká národní banka** — pokud už databáze má
alespoň jednu aktivní cizí měnu, kterou ČNB vyhlašuje. Poskytovatel:

- kótuje **měny, které jsou v databázi už aktivní** a které ČNB vyhlašuje,
  nikdy vlastní měnu společnosti — nové měny neaktivuje;
- stahuje kurzy **denně**, v režimu *Daily rate*;
- má zapnuté *Fill non-publishing days* (doplňování dnů bez kurzu), je-li
  nainstalován i [module:currency_rate_update_sk](module:currency_rate_update_sk)
  (tato volba patří jemu).

Společnost, která už poskytovatele ČNB má, byť archivovaného, modul nechá
být. Společnost bez aktivní cizí měny poskytovatele nedostane.

Poskytovatelé jsou v *Účetnictví → Konfigurace → Currency Rates Providers* —
v edici Community bez plného účetnictví se kořenová nabídka jmenuje
*Fakturace*. Obrazovka pochází z modulu OCA a stejně jako vlastní pole tohoto
modulu se zobrazuje anglicky.

Pokud měnu aktivujete **až po instalaci** a seznam je stále prázdný, založte
poskytovatele sami: *Nové*, *Provider* = **Česká národní banka**, vyberte
*Currencies*, interval nechte 1 den a uložte. Seznam má na to i tlačítko
**Create the Czech default provider**, zobrazené i v prázdném seznamu; založí
jen to, co chybí, a vyžaduje oprávnění k Nastavení. (Je-li nainstalován i
slovenský modul, seznam ukáže jen jedno z obou tlačítek; druhé zůstane
v nabídce *Akce* označeného řádku.)

Automatické stahování vyžaduje také zaškrtnuté *Automatic Currency Rates
(OCA)* v *Účetnictví → Konfigurace → Nastavení*, blok *Měny* (výchozí stav je
zaškrtnuto).

## Denní kurz {#daily}

Ve výchozím režimu, *ČNB rate* = **Daily rate (denní kurz)**, se každý kurz
ČNB uloží se svým datem (*Účetnictví → Konfigurace → Měny*). Doklad použije
nejnovější kurz s datem v den dokladu nebo dříve; o víkendu či svátku je to
poslední kurz vyhlášený před ním.

Kurzy za minulé období načtete tak, že otevřete poskytovatele, kliknete na
**Update Rates Now** a zvolíte *Start Date* a *End Date*. Období se čte z
ročních souborů ČNB, takže se uloží každý den, pro který byl kurz vyhlášen,
nejen poslední. Začíná-li období o víkendu nebo svátku, uloží se i poslední
kurz před ním.

Některé měny ČNB kótuje za 100 jednotek (HUF, JPY a další); modul je
přepočítá, takže uložený kurz je vždy za jednu jednotku.

## Pevný měsíční kurz {#fixed-rate}

Nastavte na poskytovateli *ČNB rate* = **Fixed monthly rate (pevný kurz)**,
pokud váš vnitřní předpis stanoví přepočet jedním kurzem za měsíc. Pak:

- se ukládá **jeden kurz za měsíc** s datem 1. dne a Odoo ho použije pro
  všechny doklady daného měsíce;
- *Fixed rate taken from* určuje, který kurz to je:

| Volba | Kurz měsíce je |
|---|---|
| *Rate valid on the 1st of the month* (výchozí) | kurz vyhlášený pro 1. den, a není-li 1. den dnem vyhlášení, poslední kurz před ním |
| *Last fixing of the previous month* | poslední kurz vyhlášený před 1. dnem |

  Obě volby se liší jen tehdy, když je 1. den sám dnem vyhlášení. Zákon o
  účetnictví vymezuje pevný kurz jako kurz vyhlášený pro první den zvoleného
  období, proto druhou volbu před použitím proberte se svým účetním.

- **skutečné denní kurzy se uchovávají zvlášť.** Mezi kurzy měny se
  nezobrazují a žádný doklad je nepoužije. Čte je jen české přecenění k
  rozvahovému dni,
  [module:l10n_cz_currency_revaluation](module:l10n_cz_currency_revaluation),
  protože rozvaha se přeceňuje kurzem svého dne, ne pevným kurzem.

Přepnutí existujícího poskytovatele do měsíčního režimu **nesmaže** denní
kurzy, které už uložil. Smažte je za měsíce, které mají používat pevný kurz,
jinak doklady v těchto měsících dál berou denní kurzy.

## Omezení {#limitations}

- Pevný kurz je vždy měsíční. Zákon dovoluje zvolit vnitřním předpisem jiné
  období; jakékoli jiné období je nutné udržovat ručně.
- Skutečné denní kurzy používá jen
  [module:l10n_cz_currency_revaluation](module:l10n_cz_currency_revaluation)
  (přecenění založené na OCA). Vlastní přecenění Odoo Enterprise a ostatní
  sestavy vidí pevný kurz.
- Stahují se jen měny kurzu devizového trhu ČNB (asi třicet). Kurzy ostatních
  měn, které ČNB vyhlašuje měsíčně, se nestahují.
- Poskytovatel se zakládá automaticky jen při instalaci. Měny aktivované
  později se do existujícího poskytovatele nepřidají.
