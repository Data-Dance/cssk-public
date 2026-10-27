---
title: Kód NACE partnera
summary: Hlavná ekonomická činnosť partnera ako kód NACE — vyplnený z registra a vykazovaný na českých a slovenských štatutárnych formulároch.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Viaceré štatutárne formuláre vyžadujú hlavnú ekonomickú činnosť spoločnosti ako
kód klasifikácie NACE a registre ten istý kód zverejňujú pri každej firme. Modul
dáva kontaktom jedno pole pre všetky štáty: **NACE (main activity)**.

Národné klasifikácie sú európska NACE s doplnenými národnými číslicami a partner
má jeden štát, takže štát určuje, o ktorý variant ide:

| Štát | Klasifikácia | Kód |
|---|---|---|
| Česká republika | CZ-NACE 2025 — NACE Rev. 2.1 s piatou, národnou číslicou | najviac 5 číslic |
| Slovensko | NACE Rev. 2.1 (4 číslice), ako ju zverejňuje register, alebo päťmiestna SK NACE | 4 alebo 5 číslic |

Uchováva sa len kód, ako číslice: `62100`, nie `62.10.0`. Čitateľné,
hierarchické odvetvie je opísané [nižšie](#industries).

## Zadanie kódu {#usage}

Pole je vo formulári kontaktu pod poľom **Priemysel** (*Industry*), len pri
spoločnostiach.

- Môžete ho zadať s bodkami a medzerami alebo bez nich — `62.10`, `62 10 0` —,
  uloží sa ako číslice. Prijme sa dve až šesť číslic; čokoľvek iné sa pri
  uložení odmietne.
- Kontakty vo firme preberajú kód firmy, podobne ako IČ DPH, a nedá sa pri nich
  zmeniť.
- Kód vlastnej spoločnosti sa zadáva pri kontakte spoločnosti (otvorte ho v
  aplikácii *Kontakty*).

Poskytovatelia automatického dopĺňania ho vyplnia z registra:

- [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz) —
  **prevažujúcu** činnosť podľa CZ-NACE 2025 z kópie štatistického registra v
  ARES;
- [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) —
  NACE, ktorú pri subjekte uvádza slovenský register.

Obaja na toto pole nasmerujú svoje mapovanie automaticky, ak existuje.

## Kde sa používa {#output}

Kód vašej spoločnosti sa vykazuje:

- v českom daňovom priznaní k DPH DPHDP3 (pole `c_okec`) modulom
  [module:l10n_cz_vat_return](module:l10n_cz_vat_return);
- v českom priznaní k dani z príjmov právnických osôb DPPO (pole `c_nace`)
  modulom [module:l10n_cz_dppo](module:l10n_cz_dppo);
- v slovenskej účtovnej závierke (údaj `SK NACE` v hlavičke) modulom
  [module:l10n_sk_fs](module:l10n_sk_fs), ktorý kratší kód doplní nulami na päť
  číslic.

Overte si, že kód je v klasifikácii, ktorú formulár pre dané obdobie vyžaduje.

## Čitateľné odvetvia (EU NACE) {#industries}

Pole **Priemysel** (*Industry*) na kontakte je čitateľný názov zo zoznamu
odvetví. Modul OCA [module:l10n_eu_nace](module:l10n_eu_nace) tento zoznam
naplní klasifikáciou NACE zo služby slovníkov EÚ, vo všetkých nainštalovaných
jazykoch, v ktorých je zverejnená. Modul
[module:l10n_eu_nace_cssk](module:l10n_eu_nace_cssk), ktorý sa nainštaluje sám,
keď sú prítomné oba moduly, prepojí zoznam s kódom:

- **Import podľa verzie.** *Kontakty → Konfigurácia → Import NACE industries*
  sa opýta, ktorú verziu importovať: **NACE Rev. 2.1** (predvolene) alebo
  predchádzajúcu **NACE Rev. 2**. Obe používajú tie isté kódy s iným významom,
  preto si každé odvetvie pamätá svoju verziu a kód; zoznam odvetví zobrazuje
  oba stĺpce.
- **České podtriedy.** Pri Rev. 2.1 pridá voľba *Czech subclasses (CZ-NACE
  2025)* národnú piatu číslicu — 716 podtried z číselníka Českého štatistického
  úradu — pod príslušné triedy, s anglickým a českým názvom.
- **Vždy jedna klasifikácia.** *Archive the other version* (predvolene zapnuté)
  archivuje odvetvia druhej verzie, aby zoznam ponúkal len jednu. Partneri si
  svoje odvetvie ponechajú.
- **Kód → odvetvie.** Uloženie kódu NACE nastaví kontaktu zodpovedajúce
  **odvetvie**: podľa samotného kódu, inak podľa jeho štvormiestnej triedy,
  najprv v Rev. 2.1, potom v Rev. 2. **Päťmiestny kód slovenského kontaktu** je
  SK NACE Rev. 2 — slovenská Rev. 2.1 piatu číslicu nemá —, preto sa hľadá len
  v Rev. 2, aj keď je táto verzia archivovaná: tie isté štyri číslice môžu v
  Rev. 2.1 znamenať inú činnosť. Národná podtrieda sa priradí len kontaktom
  svojho štátu. Ak ste zvolili odvetvie, ktoré nie je z NACE, nezmení sa.
- **Odvetvie → kód.** Výber odvetvia NACE vo formulári vyplní kód.

Odvetvia importované pred inštaláciou modulu sa označia ako NACE Rev. 2, jediná
verzia, ktorú import OCA vedel načítať.

## Obmedzenia {#limitations}

- Pole uchováva jeden kód, hlavnú činnosť. Vedľajšie činnosti sa neuchovávajú;
  predmety podnikania zo slovenského registra pozri v module
  [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry).
- Nekontroluje sa, či kód v klasifikácii existuje, len či má 2 až 6 číslic.
- **Štvormiestny** kód slovenského kontaktu sa berie ako Rev. 2.1, ktorú
  slovenský register zverejňuje od roku 2026. Starší štvormiestny kód Rev. 2
  zadaný ručne dostane odvetvie z Rev. 2.1; skontrolujte ho. Kontakt bez štátu
  sa priraďuje ako český.
