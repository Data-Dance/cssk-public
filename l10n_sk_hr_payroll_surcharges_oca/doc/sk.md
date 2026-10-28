---
title: SK mzdové zvýhodnenia (OCA)
summary: Slovenské mzdové zvýhodnenia a doplatok do minimálneho mzdového nároku ako mzdové pravidlá aplikácie OCA payroll.
verified: 19.0.1.0.4
family: l10n_sk_hr_payroll_surcharges#engines
---

Pridá do slovenských štruktúr OCA mzdové pravidlá pre zvýhodnenia za nočnú prácu, sobotu, nedeľu, sviatok, prácu nadčas, sťažený výkon práce a pohotovosť, mzdu za prácu nadčas a doplatok do minimálneho mzdového nároku. Každé pravidlo má vlastný vstup výplatnej pásky (*Night hours*, *Saturday hours*, …) na hodiny. Zohľadňuje aj to, že engine OCA vykazuje neprítomnosť ako samostatné záporné riadky odpracovaných dní, takže doplatok porovnáva mzdu so skutočne odpracovanými hodinami. Sadzby aj výpočet pochádzajú zo základného modulu príplatkov.

Nainštaluje sa sám, keď sú nainštalované slovenské mzdy pre OCA aj základný modul príplatkov, a nemá vlastné nastavenia. Ak je už nainštalovaný účtovný mostík, priradí svojim pravidlám účet 521000.
