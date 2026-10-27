---
title: SK statutárne číselníky
summary: Slovenské daňové úrady a typy daňových subjektov, aby spoločnosť mohla určiť daňový úrad, ktorému posiela elektronické podania.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Slovenské elektronické podania finančnej správe — medzi nimi daňové
priznanie k DPH a súhrnný výkaz — uvádzajú daňový úrad, ktorému sú určené.
Modul plní číselníky modulu [module:l10n_cssk_core](module:l10n_cssk_core)
slovenskými údajmi:

- **slovenské daňové úrady**: osem krajských úradov — Daňový úrad
  Bratislava, Trnava, Trenčín, Nitra, Žilina, Banská Bystrica, Prešov a
  Košice — a Daňový úrad pre vybrané daňové subjekty, každý s adresou a
  telefónnym číslom ústredne;
- **typy daňových subjektov** *Fyzická osoba* a *Právnická osoba*.

Keďže sú tieto údaje v slovenskom module, do českej databázy sa nenačítajú.

## Nastavenie {#setup}

*Nastavenia → Užívatelia & spoločnosti → Spoločnosti*, otvorte spoločnosť a
vyplňte:

| Pole | Čo zadať |
|---|---|
| Daňový úrad | Daňový úrad, u ktorého je spoločnosť registrovaná. |
| Typ subjektu | *Právnická osoba* alebo *Fyzická osoba*. |

Daňový úrad sa dá nastaviť aj v *Účtovníctvo → Konfigurácia → Nastavenia*,
blok *Česká / slovenská lokalizácia*, pole *Predvolený správca dane*. Zoznam
úradov je v *Účtovníctvo → Konfigurácia → CZ/SK lokalizácia → Daňové úrady*.

## Ako ho podania používajú {#usage}

Slovenské XML schémy podaní nemajú pre daňové úrady číselník: úrad je
voľný text (prvok `danovyUrad`). *Kód podania* každého úradu preto obsahuje
jeho celý názov, napríklad *Daňový úrad Žilina*, a práve tento text zapíšu do
súboru moduly [module:l10n_sk_vat_return](module:l10n_sk_vat_return) a
[module:l10n_sk_ec_sales](module:l10n_sk_ec_sales). Nemeňte ho, pokiaľ
finančná správa neočakáva iné znenie.

## Obmedzenia {#limitations}

- Zoznam úradov je zostavený ručne; v Odoo nie je oficiálny zoznam, z ktorého
  by sa dal načítať. Ak sa úrady zlúčia alebo premenujú, upravte záznamy.
- Adresy a telefónne čísla sa automaticky neaktualizujú; ak ich používate,
  overte ich.
- *Typ subjektu* zatiaľ nečíta žiadne slovenské podanie; eviduje sa pre
  úplnosť.
- Záznamy sa načítajú raz a pri aktualizácii modulu sa neprepisujú, takže
  vaše úpravy zostanú — ale ani opravy z novšej verzie sa do existujúcej
  databázy nedostanú.
