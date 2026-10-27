---
title: Import bankových výpisov — GPC
summary: Importuje elektronické bankové výpisy GPC (výpisový formát ABO českých a slovenských bánk) so zostatkami, účtami protistrany a symbolmi VS/KS/SS.
verified: 19.0.2.0.1
---

## Na čo slúži {#purpose}

**GPC** je elektronický výpis s pevnou dĺžkou záznamov, ktorý väčšina českých
a slovenských bánk ponúka na stiahnutie popri iných formátoch — Fio banka, KB,
ČS, ČSOB a ďalšie. Nesie to, podľa čoho účtovník páruje platby: účet a kód
banky protistrany a **variabilný, konštantný a špecifický symbol**.

Modul pridáva GPC do sprievodcu importom výpisov OCA
(`account_statement_import_file`) v edícii Community. V edícii Enterprise ho
do vlastného importu výpisov Odoo pridáva modul
[module:account_statement_import_gpc_ee](module:account_statement_import_gpc_ee)
— pozri [nižšie](#enterprise).

## Čo sa načíta {#format}

Súbor GPC je postupnosť 130-znakových záznamov:

| Záznam | Obsah | Výsledok |
|---|---|---|
| `074` | hlavička výpisu: účet, starý a nový zostatok so znamienkom, číslo výpisu, dátum | jeden bankový výpis s názvom `GPC <účet>/<číslo>` s počiatočným a konečným zostatkom |
| `075` | transakcia: vlastný účet, účet a kód banky protistrany, číslo dokladu, suma v haliéroch, účtovný kód, VS, KS, SS, názov protistrany, mena, dátum | jeden riadok výpisu |
| `076`, `078`, `079` | doplňujúce riadky správy | pripoja sa k popisu predchádzajúceho riadku |

Ostatné záznamy sa ignorujú — banky pridávajú vlastné.

Znamienko sumy určuje účtovný kód: `1` debet, `2` kredit, `4` storno debetu
(peniaze sa vracajú), `5` storno kreditu (peniaze odchádzajú).

Na každom riadku výpisu:

- **Popis**: názov protistrany (alebo `GPC <číslo dokladu>`), potom `VS:…`,
  `KS:…`, `SS:…` a účet protistrany `číslo/kód banky`.
- **Partner**: hľadá sa podľa čísla účtu protistrany medzi bankovými účtami v
  Odoo; názov ostane na riadku.
- **Symboly**: ak je nainštalovaný modul
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements),
  VS, KS a SS sa zapíšu aj do vlastných polí symbolov riadku, z ktorých ich
  berie párovanie podľa variabilného symbolu.
- **Dátum**: dátum transakcie zo záznamu `075`.

Súbor za viac dní (jedno `074` za deň) dá jeden výpis za každý deň. Blok `074`
bez transakcií sa preskočí.

Súbor sa dekóduje ako Windows-1250, a ak to zlyhá, ako Latin-1. Mena sa číta
z transakcií; rozpoznávajú sa CZK, EUR, USD, GBP, PLN, HUF, CHF, DKK, SEK a
NOK.

## Nastavenie {#setup}

- Bankový denník (*Účtovníctvo → Konfigurácia → Účtovníctvo → Účtovné
  denníky*) musí mať vyplnený bankový účet. Hlavička GPC nesie účet **bez kódu
  banky** ; denník sa nájde porovnaním predčíslia a čísla s účtom denníka,
  takže funguje IBAN `SK` / `CZ`, `predčíslie-číslo/kód banky` aj samotné
  číslice.
- Mena denníka musí byť mena výpisu.
- Výpis si z banky stiahnite vo formáte GPC (niekedy ponúkaný ako *ABO* alebo
  `.gpc`).

## Import výpisu {#usage}

*Účtovníctvo → Účtovníctvo → Importovať výpis* alebo **Import výpisov (OCA)**
na karte bankového denníka na riadiacom paneli Účtovníctva (*Riadiaci panel*). Vyberte súbor a stlačte
**Importovať a zobraziť**.

Opakovaný import toho istého súboru je bezpečný: každý riadok nesie kľúč
importu zložený z účtu, dátumu, čísla dokladu a sumy so znamienkom a už
naimportované riadky sa preskočia. Súbor, ktorý sa prekrýva so skorším, prinesie
len nové riadky.

## Enterprise {#enterprise}

Modul [module:account_statement_import_gpc_ee](module:account_statement_import_gpc_ee)
pridá GPC do importu výpisov Enterprise popri CAMT, OFX, QIF a CSV: použite
**Importovať súbor** na karte bankového denníka na riadiacom paneli Účtovníctva (*Riadiaci panel*). Súbor
sa rozpozná podľa prvého záznamu (`074` alebo `075`); všetko opísané vyššie
platí rovnako.

Enterprise porovnáva účet zo súboru s denníkom, do ktorého sa importuje;
modul toto porovnanie rozšíri aj na predčíslie a číslo, takže denník s účtom
uloženým ako IBAN alebo `predčíslie-číslo/kód banky` svoje súbory GPC prijme.
Súbor s **viacerými účtami** Enterprise odmietne, pretože importuje do
denníka, z ktorého bol import spustený: stiahnite súbor pre každý účet
zvlášť.

## Obmedzenia {#limitations}

- Len desať vyššie uvedených mien. Súbor v inej mene sa zastaví hlásením
  *Chýbajúci kód meny v súbore výpisu.*
- GPC nenesie kód banky, takže dva účty s rovnakým predčíslím a číslom v dvoch
  bankách nemožno rozlíšiť; prednosť má denník, z ktorého importujete. Účet,
  ktorý číslice zo súboru len *obsahuje*, sa zaň nepovažuje — import sa
  zastaví a podobný denník pomenuje.
- Pri prechode účtu zo súborov GPC na bankové pripojenie (napríklad
  [API Fio](module:account_statement_fio)) sa riadky naimportované z GPC
  nerozpoznajú, lebo obe cesty používajú iné kľúče importu. Prejdite na hranici
  výpisu.
