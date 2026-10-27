---
title: Příplatky ke mzdě CZ (OCA)
summary: České příplatky ke mzdě jako mzdová pravidla aplikace OCA payroll.
verified: 19.0.1.1.0
family: l10n_cz_hr_payroll_surcharges#engines
---

Založí pravidla pro příplatky za práci přesčas, ve svátek, v noci, v sobotu a v neděli a ve ztíženém pracovním prostředí v aplikaci OCA payroll, každé s vlastním vstupem pro hodiny (`PRESCAS`, `SVATEK`, `NOCNI`, `VIKEND`, `ZTIZENE`), a tam, kde to vyžaduje porovnání s minimální mzdou, odečte nepřítomnosti od řádku odpracovaných dnů jádra OCA. Dvě další pravidla vyplácejí mzdu za hodiny práce přesčas (*Overtime Wage (§ 114)*, ze vstupu `PRESCAS`) a doplatek do minimální mzdy (*Minimum Wage Top-up (§ 111)*). Pravidla jsou zařazena do české struktury *Česká republika: Řádná mzda*. Sazby i výpočet přebírá ze základního modulu příplatků.

Instaluje se ručně spolu s českou mzdovou agendou pro OCA; sám se nenainstaluje a vlastní nastavení nemá.
