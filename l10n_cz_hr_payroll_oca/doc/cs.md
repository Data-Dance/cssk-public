---
title: Česká mzdová agenda (OCA)
summary: Česká měsíční výplatní páska pro aplikaci OCA payroll v Odoo Community — pracovní poměr, DPP a DPČ, s datovanými zákonnými sazbami, nepřítomnostmi a ročním zúčtováním daně.
verified: 19.0.1.13.1
family: l10n_cz_hr_payroll_base#engines
---

Úplná česká mzdová struktura pro aplikaci OCA `payroll`, *Czech Republic: Regular Pay* (`CZMONTHLY`): sociální a zdravotní pojištění s ročním maximem a minimálním vyměřovacím základem, záloha na daň nebo srážková daň u dohody, slevy na dani, daňové zvýhodnění na děti a daňový bonus, náhrada za dovolenou a za překážky v práci ve výši průměrného výdělku, náhrada mzdy při nemoci, sleva zaměstnavatele na pojistném, srážky ze mzdy a stravenkový paušál. Dodává také datované zákonné hodnoty, které pravidla čtou, v nabídce *Payroll → Configuration → Rule Parameters*, české typy nepřítomností napojené na výplatní pásku *českým mzdovým kódem* (nastavuje se na formuláři typu nepřítomnosti) a roční zúčtování daně v nabídce *Payroll → CZ Annual Tax Reconciliation*. České údaje jsou na kartě zaměstnance, záložka *Payroll*, a na formuláři šablony smlouvy.

Instaluje se záměrně; s sebou přinese základní modul nezávislý na mzdovém jádru s českými údaji zaměstnance a akruálními plány dovolené. Pro zaúčtování do hlavní knihy přidejte účetní modul pro OCA, pro příplatky ke mzdě skupinu příplatků.
