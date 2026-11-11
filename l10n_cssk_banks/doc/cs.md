---
title: Banky CZ/SK
summary: Všechny kódy českých a slovenských bank s jejich BIC podle registrů ČNB a NBS — banka se k IBAN doplní sama.
verified: 19.0.2.0.0
---

## K čemu slouží {#purpose}

Přidá do **Bank** (*Kontakty → Konfigurace → Banky*) banky z obou oficiálních
registrů kódů bank:

- **Česká republika** — Česká národní banka, *Číselník kódů bank*;
- **Slovensko** — Národná banka Slovenska, *Prevodník identifikačných kódov pre
  tuzemský platobný styk*.

Každá banka má čtyřmístný **kód banky**, **BIC**, pokud ho registr uvádí, a
zemi. Názvy jsou přesně takové, jak je registr zveřejňuje, bez překladu.

Spolu s modulem OCA *Bank from IBAN*, který nainstaluje, se po zadání českého
nebo slovenského IBAN na bankovní účet banka vybere sama: `CZ65 0800 …` je
Česká spořitelna, `SK05 1100 …` Tatra banka.

Instaluje se sám spolu s modulem *Bank from IBAN* a nemá žádná nastavení.

## Když se banka změní nebo zanikne {#updates}

Registry se mění několikrát do roka. Nová verze modulu přináší aktuální seznamy
a při její instalaci:

- **název, kód, BIC a země** banky se řídí registrem — opravený BIC nahradí
  chybný;
- banka, jejíž kód **z registru vypadl, se archivuje, nikdy nesmaže**. Bankovní
  účty, které ji používají, si ji ponechají; pro nové účty se už nenabízí;
- **adresa, telefon a e-mail** jsou vaše: registr je nezveřejňuje, proto se
  nikdy nepřepíší;
- banka, kterou jste už založili ručně se stejným kódem a zemí, se **převezme**,
  nevznikne její duplikát.

Pokud potřebujete, aby se banka lišila od registru, založte si vlastní záznam
banky místo úpravy dodaného.

## Přechod z předchozího modulu {#migration}

Modul nahrazuje *Information about banks in Czech Republic and Slovakia*
(`l10n_banks_cz_sk`). Správce ho před aktualizací přejmenuje v databázi;
bankovní účty si ponechají své banky a kontaktní údaje, které dodal starý modul,
se odstraní tam, kde jste je nezměnili.
