---
title: Banky CZ/SK
summary: Všetky kódy českých a slovenských bánk s ich BIC podľa registrov ČNB a NBS — banka sa k IBAN doplní sama.
verified: 19.0.2.0.0
---

## Na čo slúži {#purpose}

Pridá do **Bánk** (*Kontakty → Konfigurácia → Banky*) banky z oboch oficiálnych
registrov kódov bánk:

- **Česká republika** — Česká národná banka, *Číselník kódů bank*;
- **Slovensko** — Národná banka Slovenska, *Prevodník identifikačných kódov pre
  tuzemský platobný styk*.

Každá banka má štvormiestny **kód banky**, **BIC**, ak ho register uvádza, a
krajinu. Názvy sú presne také, ako ich register zverejňuje, bez prekladu.

Spolu s modulom OCA *Bank from IBAN*, ktorý nainštaluje, sa po zadaní českého
alebo slovenského IBAN na bankový účet banka vyberie sama: `SK05 1100 …` je
Tatra banka, `CZ65 0800 …` Česká spořitelna.

Inštaluje sa sám spolu s modulom *Bank from IBAN* a nemá žiadne nastavenia.

## Keď sa banka zmení alebo zanikne {#updates}

Registre sa menia niekoľkokrát do roka. Nová verzia modulu prináša aktuálne
zoznamy a pri jej inštalácii:

- **názov, kód, BIC a krajina** banky sa riadia registrom — opravený BIC
  nahradí chybný;
- banka, ktorej kód **z registra vypadol, sa archivuje, nikdy nezmaže**.
  Bankové účty, ktoré ju používajú, ju ponechajú; pre nové účty sa už neponúka;
- **adresa, telefón a e-mail** sú vaše: register ich nezverejňuje, preto sa
  nikdy neprepíšu;
- banka, ktorú ste už založili ručne s rovnakým kódom a krajinou, sa **prevezme**,
  nevznikne jej duplikát.

Ak potrebujete, aby sa banka líšila od registra, založte si vlastný záznam banky
namiesto úpravy dodaného.

## Prechod z predchádzajúceho modulu {#migration}

Modul nahrádza *Information about banks in Czech Republic and Slovakia*
(`l10n_banks_cz_sk`). Správca ho pred aktualizáciou premenuje v databáze;
bankové účty si ponechajú svoje banky a kontaktné údaje, ktoré dodal starý
modul, sa odstránia tam, kde ste ich nezmenili.
