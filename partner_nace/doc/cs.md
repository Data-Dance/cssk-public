---
title: Kód NACE partnera
summary: Hlavní ekonomická činnost partnera jako kód NACE — vyplněný z registru a vykazovaný v českých daňových přiznáních a ve slovenské účetní závěrce.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Několik formulářů pro finanční správu vyžaduje hlavní ekonomickou činnost
společnosti jako kód klasifikace NACE a registry tentýž kód zveřejňují u každé
firmy. Modul dává kontaktům jedno pole pro všechny státy: **NACE (main
activity)**.

Národní klasifikace jsou evropská NACE s doplněnými národními číslicemi a
partner má jeden stát, takže stát určuje, o kterou variantu jde:

| Stát | Klasifikace | Kód |
|---|---|---|
| Česká republika | CZ-NACE 2025 — NACE Rev. 2.1 s pátou, národní číslicí | nejvýše 5 číslic |
| Slovensko | NACE Rev. 2.1 (4 číslice), jak ji zveřejňuje registr, nebo pětimístná SK NACE | 4 nebo 5 číslic |

Uchovává se jen kód, jako číslice: `62100`, ne `62.10.0`. Čitelné, hierarchické
odvětví je popsáno [níže](#industries).

## Zadání kódu {#usage}

Pole je ve formuláři kontaktu pod polem **Odvětví** (*Industry*), jen u
společností.

- Můžete ho zadat s tečkami a mezerami i bez nich — `62.10`, `62 10 0` —, uloží
  se jako číslice. Přijmou se dvě až šest číslic; cokoli jiného se při uložení
  odmítne.
- Kontakty ve firmě přebírají kód firmy, podobně jako DIČ, a nelze ho u nich
  změnit.
- Kód vlastní společnosti se zadává u kontaktu společnosti (otevřete ho v
  aplikaci *Kontakty*).

Poskytovatelé automatického doplňování ho vyplní z registru:

- [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz) —
  **převažující** činnost podle CZ-NACE 2025 z kopie statistického registru v
  ARES;
- [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) —
  NACE, kterou u subjektu uvádí slovenský registr.

Oba na toto pole nasměrují své mapování automaticky, pokud existuje.

## Kde se používá {#output}

Kód vaší společnosti se vykazuje:

- v přiznání k DPH DPHDP3 (pole `c_okec`) modulem
  [module:l10n_cz_vat_return](module:l10n_cz_vat_return);
- v přiznání k dani z příjmů právnických osob DPPO (pole `c_nace`) modulem
  [module:l10n_cz_dppo](module:l10n_cz_dppo);
- ve slovenské účetní závěrce (údaj `SK NACE` v záhlaví) modulem
  [module:l10n_sk_fs](module:l10n_sk_fs), který kratší kód doplní nulami na pět
  číslic.

Ověřte si, že kód je v klasifikaci, kterou formulář pro dané období vyžaduje.

## Čitelná odvětví (EU NACE) {#industries}

Pole **Odvětví** (*Industry*) na kontaktu je čitelný název ze seznamu odvětví.
Modul OCA [module:l10n_eu_nace](module:l10n_eu_nace) tento seznam naplní
klasifikací NACE ze služby slovníků EU, ve všech nainstalovaných jazycích, v
nichž je zveřejněna. Modul
[module:l10n_eu_nace_cssk](module:l10n_eu_nace_cssk), který se nainstaluje sám,
jsou-li přítomny oba moduly, propojí seznam s kódem:

- **Import podle verze.** *Kontakty → Konfigurace → Import NACE industries* se
  zeptá, kterou verzi importovat: **NACE Rev. 2.1** (výchozí) nebo dřívější
  **NACE Rev. 2**. Obě používají tytéž kódy s jiným významem, proto si každé
  odvětví pamatuje svou verzi a kód; seznam odvětví zobrazuje oba sloupce.
- **České podtřídy.** U Rev. 2.1 přidá volba *Czech subclasses (CZ-NACE 2025)*
  národní pátou číslici — 716 podtříd z číselníku Českého statistického úřadu —
  pod příslušné třídy, s anglickým a českým názvem.
- **Vždy jedna klasifikace.** *Archive the other version* (ve výchozím stavu
  zapnuto) archivuje odvětví druhé verze, aby seznam nabízel jen jednu. Partneři
  si své odvětví ponechají.
- **Kód → odvětví.** Uložení kódu NACE nastaví kontaktu odpovídající
  **odvětví**: podle samotného kódu, jinak podle jeho čtyřmístné třídy, nejprve v
  Rev. 2.1, potom v Rev. 2. **Pětimístný kód slovenského kontaktu** je SK NACE
  Rev. 2 — slovenská Rev. 2.1 pátou číslici nemá —, proto se hledá jen v
  Rev. 2, i když je tato verze archivovaná: tytéž čtyři číslice mohou v
  Rev. 2.1 znamenat jinou činnost. Národní podtřída se přiřadí jen kontaktům
  svého státu. Zvolené odvětví, které není z NACE, se nezmění.
- **Odvětví → kód.** Výběr odvětví NACE ve formuláři vyplní kód.

Odvětví importovaná před instalací modulu se označí jako NACE Rev. 2, jediná
verze, kterou import OCA uměl načíst.

## Omezení {#limitations}

- Pole uchovává jeden kód, hlavní činnost. Vedlejší činnosti se neuchovávají.
- Nekontroluje se, zda kód v klasifikaci existuje, jen zda má 2 až 6 číslic.
- **Čtyřmístný** kód slovenského kontaktu se bere jako Rev. 2.1, kterou
  slovenský registr zveřejňuje od roku 2026. Starší čtyřmístný kód Rev. 2
  zadaný ručně dostane odvětví z Rev. 2.1; zkontrolujte ho. Kontakt bez státu
  se přiřazuje jako český.
