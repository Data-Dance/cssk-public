---
title: Spracovanie pokladničných dokladov — výdavky zamestnancov
summary: Zo zachyteného dokladu vytvorí jeden výdavok zamestnanca s DPH zaúčtovanou podľa sadzieb a prečíta doklady nahraté alebo naskenované v aplikácii Výdavky.
verified: 19.0.1.1.0
family: l10n_cssk_receipt_capture#expenses
---

Pridá na zachytený doklad tlačidlo **Create Expenses** — jeden výdavok za celý doklad bez ohľadu na sadzby DPH, pričom DPH aj účtovný zápis sa zostavia sadzbu po sadzbe z rekapitulácie dokladu — a naučí aplikáciu Výdavky čítať doklady: každý obrázok, ktorý zamestnanec nahrá, sa stane zachyteným dokladom a ak sa prečíta bez chyby, vyplní svoj výdavok; v ponuke *Výdavky → Moje výdaje* pribudnú **Scan Receipt** a **My Receipts**. Výdavok, ktorý sa od dokladu zmenil, sa odmietne zaúčtovať, a doklad uplatnený ako výdavok sa už nemôže stať nákupnou účtenkou.

Potrebuje [module:l10n_cssk_receipt_capture](module:l10n_cssk_receipt_capture) a aplikáciu Výdavky (Community). Nastavenia *Capture on Expense Upload* (predvolene zapnuté) a *Receipt Expense Category* sú v *Výdavky → Konfigurácia → Nastavenia*; s nainštalovaným čítaním pomocou AI je každé nahratie plateným čítaním.
