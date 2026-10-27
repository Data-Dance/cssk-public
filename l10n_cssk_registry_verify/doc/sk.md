---
title: Overenie firmy v registri CZ/SK
summary: Overí v českom alebo slovenskom registri, či IČO patrí existujúcej a aktívnej firme, a odpovede krátko uchováva vo vyrovnávacej pamäti.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Formálne správne IČO — také, ktoré prejde kontrolnou číslicou — ešte nie je
firma. Tento modul odpovedá na ďalšiu otázku: **existuje firma v štátnom
registri a je stále aktívna?** Vlastné tlačidlo nemá. Pýtajú sa ho iné moduly
predtým, než s IČO niečo urobia; napríklad
[module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai)
podľa IČO prečítaného z bločku prevezme z registra úradný názov predávajúceho.

Každé overenie skončí jednou z piatich odpovedí:

| Odpoveď | Význam |
|---|---|
| Not a valid company number | nesedí kontrolná číslica; register sa nepýta |
| No register for this country | nejde o české ani slovenské číslo, alebo modul poskytovateľa pre daný štát nie je nainštalovaný |
| Not in the register | register odpovedal a taký subjekt nevedie |
| Verified | register odpovedal firmou: názov, adresa, DIČ, IČ DPH, kým je registrácia pre DPH platná, a či je firma aktívna |
| Register unreachable | výpadok, časový limit alebo limit požiadaviek — nikto nevie, či firma existuje |

Posledné dve sa prísne rozlišujú. Každý modul, ktorý overenie používa, sám
rozhoduje, čo robiť, keď register nie je dostupný; výpadok nikdy nepovažuje za
„firma neexistuje“.

Ak sa zadá aj názov firmy, porovná sa s názvom v registri a výsledok je
*Matches the register* (zhoduje sa), *Close, needs a look* (podobný, treba
pozrieť) alebo *Does not match* (nezhoduje sa).

## Nastavenie {#setup}

Registre sa čítajú cez poskytovateľov automatického dopĺňania partnerov, ktorých
modul nájde za behu, no sám ich neinštaluje:

- Slovensko — [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) (ORSF);
- Česká republika — [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz) (ARES).

Nainštalujte toho, ktorého pre daný štát potrebujete. Nič iné netreba
nastavovať.

## Uchované odpovede {#cache}

*Účtovníctvo → Konfigurácia → CZ/SK lokalizácia → Register lookups* zobrazí
uchované odpovede od najnovšej: kedy, štát, IČO, názov v registri, odpoveď, či
je firma aktívna a ktorý register odpovedal. Filtre: *Verified*, *Not in the
register*, *Dissolved*; zoskupenie podľa štátu alebo odpovede.

- Odpoveď *Verified* sa použije znova 24 hodín, odpoveď *Not in the register*
  jednu hodinu — firma, ktorá dnes neexistuje, môže zajtra vzniknúť.
- *Register unreachable* sa neuchováva nikdy, takže ďalšie overenie sa opýta
  znova.
- Používatelia zoznam len čítajú; správca môže riadok zmazať a vynútiť tak nové
  overenie.

Dĺžku uchovania menia systémové parametre
`l10n_cssk_registry_verify.ttl_verified_hours` a
`l10n_cssk_registry_verify.ttl_absent_hours` (0 uchovávanie vypne).

## Obmedzenia {#limitations}

- Len české a slovenské IČO. Partner z iného štátu je vždy *No register for
  this country*.
- Uchovaná odpoveď môže byť až deň stará: firma zrušená dnes ráno sa ešte môže
  javiť ako aktívna.
- ARES nemá pole so stavom; česká firma sa považuje za aktívnu, ak nemá dátum
  zániku.
- Polia overenia, ktoré modul pridáva ku kontaktom, sa nezobrazujú na žiadnej
  obrazovke.
- Popisky na obrazovke nie sú preložené.
