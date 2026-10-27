---
title: Ověření firmy v registru CZ/SK
summary: Ověří v českém nebo slovenském registru, zda IČO patří existující a aktivní firmě, a odpovědi krátce uchovává v mezipaměti.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Formálně správné IČO — takové, které projde kontrolní číslicí — ještě není
firma. Tento modul odpovídá na další otázku: **existuje firma ve státním
registru a je stále aktivní?** Vlastní tlačítko nemá. Ptají se ho jiné moduly
dříve, než s IČO něco udělají; například
[module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai)
podle IČO přečteného z účtenky převezme z registru úřední název prodávajícího.

Každé ověření skončí jednou z pěti odpovědí:

| Odpověď | Význam |
|---|---|
| Not a valid company number | nesedí kontrolní číslice; registr se neptá |
| No register for this country | nejde o české ani slovenské číslo, nebo modul poskytovatele pro daný stát není nainstalován |
| Not in the register | registr odpověděl a takový subjekt nevede |
| Verified | registr odpověděl firmou: název, adresa, DIČ a zda je firma aktivní; jako číslo pro DPH se DIČ vrátí, jen dokud je registrace k DPH aktivní |
| Register unreachable | výpadek, časový limit nebo limit požadavků — nikdo neví, zda firma existuje |

Poslední dvě se přísně rozlišují. Každý modul, který ověření používá, sám
rozhoduje, co dělat, když registr není dostupný; výpadek nikdy nepovažuje za
„firma neexistuje“.

Zadá-li se i název firmy, porovná se s názvem v registru a výsledek je *Matches
the register* (shoduje se), *Close, needs a look* (podobný, je třeba se
podívat) nebo *Does not match* (neshoduje se).

## Nastavení {#setup}

Registry se čtou přes poskytovatele automatického doplňování partnerů, které
modul najde za běhu, ale sám je neinstaluje:

- Slovensko — [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) (ORSF);
- Česká republika — [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz) (ARES).

Nainstalujte toho, kterého pro daný stát potřebujete. Nic jiného není třeba
nastavovat.

## Uchované odpovědi {#cache}

*Účetnictví → Konfigurace → CZ/SK lokalizace → Register lookups* zobrazí
uchované odpovědi od nejnovější: kdy, stát, IČO, název v registru, odpověď, zda
je firma aktivní a který registr odpověděl. Filtry: *Verified*, *Not in the
register*, *Dissolved*; seskupení podle státu nebo odpovědi.

- Odpověď *Verified* se použije znovu 24 hodin, odpověď *Not in the register*
  jednu hodinu — firma, která dnes neexistuje, může zítra vzniknout.
- *Register unreachable* se neuchovává nikdy, takže další ověření se zeptá
  znovu.
- Uživatelé seznam jen čtou; správce může řádek smazat a vynutit tak nové
  ověření.

Dobu uchování mění systémové parametry
`l10n_cssk_registry_verify.ttl_verified_hours` a
`l10n_cssk_registry_verify.ttl_absent_hours` (0 uchovávání vypne).

## Omezení {#limitations}

- Jen česká a slovenská IČO. Partner z jiného státu je vždy *No register for
  this country*.
- Uchovaná odpověď může být až den stará: firma zrušená dnes ráno se ještě může
  jevit jako aktivní.
- ARES nemá pole se stavem; česká firma se považuje za aktivní, pokud nemá datum
  zániku.
- Pole ověření, která modul přidává ke kontaktům, se nezobrazují na žádné
  obrazovce.
- Popisky na obrazovce nejsou přeložené.
