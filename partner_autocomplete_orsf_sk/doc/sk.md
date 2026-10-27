---
title: Automatické dopĺňanie partnerov zo slovenských registrov (ORSF)
summary: Dopĺňa slovenské kontakty zo štátnych registrov cez ORSF — identifikáciu, adresu, IČ DPH, DIČ, zápis v registri, stav a predmety podnikania — a aktualizuje veľa kontaktov naraz.
verified: 19.0.1.4.1
---

## Na čo slúži {#purpose}

ORSF (orsf.sk) sprístupňuje slovenské štátne registre cez jedno otvorené
rozhranie: register právnických osôb (RPO), obchodný register (ORSR),
živnostenský register (ŽRSR), register účtovných závierok (RÚZ) a zoznam
platiteľov DPH Finančnej správy. Tento modul robí z ORSF poskytovateľa
automatického dopĺňania partnerov, takže slovenský kontakt sa vyplní z registra
namiesto ručného prepisovania a dá sa neskôr aktualizovať.

Zapája sa do
[prepínača poskytovateľov](module:partner_autocomplete_dispatcher), ktorý
rozhoduje, ktorý register sa použije: kontakt so štátom Slovensko sa v ORSF
vyhľadá z každej spoločnosti bez ohľadu na to, akého poskytovateľa si zvolila.

Všetko, čo tento modul robí, funguje bez konta ORSF. Údaje ORSF sú pod licenciou
CC-BY 4.0; ak ich ďalej zverejňujete, uveďte ORSF a zdrojové registre.

## Nastavenie {#setup}

*Nastavenia → Všeobecné nastavenia*, blok **Kontakty**, pole **Poskytovateľ**:
zvoľte **ORSF.SK**. Pod ním sa zobrazia jeho nastavenia:

| Nastavenie | Čo robí |
|---|---|
| Základná URL adresa ORSF API | Prázdne = verejná adresa ORSF. Prijme sa len adresa `http(s)`. |
| Token ORSF API | Voliteľný token z konta ORSF. Zvyšuje limit požiadaviek a sprístupní úplnú adresu živnostníka, ktorú ORSF inak neposkytuje. Na nič iné ho netreba. |
| E-mail konta ORSF / Heslo konta ORSF | Potrebné len pre modul [module:partner_autocomplete_orsf_sk_related_parties](module:partner_autocomplete_orsf_sk_related_parties). Heslo sa ukladá **ako čitateľný text** v databáze aj v každej zálohe: použite samostatné konto ORSF, nikdy nie osobné. |
| Časový limit požiadavky (s) | Ako dlho čakať na ORSF. Predvolene 15. |
| ORSF: vyplniť IČO | IČO sa zapíše do poľa *IČO* (*Company ID*) aj do mapovaného poľa. Predvolene zapnuté. |
| ORSF: nastaviť typ subjektu | Kontakt sa podľa registra nastaví na fyzickú osobu (*Individual*) pri živnostníkovi a na spoločnosť inak. Predvolene zapnuté. |
| ORSF: formátovať PSČ ako 851 01 | ORSF vracia PSČ ako päť číslic; na slovenských dokladoch sa píše 3 + 2. Predvolene zapnuté. |

Tri voľby *ORSF:* sa ukladajú pre každú spoločnosť zvlášť, ostatné platia pre
celú databázu.

### Kam sa údaje z registra zapisujú {#mapping}

V časti **Field mapping** má každý údaj z registra cieľové pole na kontakte.
Ak mapovanie vymažete, údaj sa neuloží; ak ho nasmerujete na vlastné pole, údaj
pôjde tam.

| Mapovanie | Štandardné pole | Poskytuje ho |
|---|---|---|
| IČO | *IČO* (*Company ID*) | Odoo |
| DIČ | DIČ | [module:l10n_sk_base](module:l10n_sk_base) |
| SK NACE | NACE (main activity) | [module:partner_nace](module:partner_nace) |
| Právna forma, Register, Registrový súd, Číslo zápisu, Stav subjektu, Veľkostná kategória, Dátum vzniku, Dátum zániku | rovnomenné polia registra | [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry) |
| Druh registrácie DPH (§), Platiteľ DPH od | Druh registrácie DPH, Platiteľ DPH od | [module:l10n_sk_vat_registration](module:l10n_sk_vat_registration) |

Pri inštalácii modulu sa mapovania nastavia na štandardné polia automaticky. Ak
niektorý z modulov v pravom stĺpci nainštalujete neskôr, stlačte **Použiť
štandardné SK polia**. Modré pole nad mapovaním vymenúva moduly, ktoré ešte
chýbajú. Len s nimi majú údaje význam aj inde v Odoo — vo vete podľa § 3a, v
upozornení na § 69 ods. 12, v páse pri zrušenom partnerovi.

## Vyplnenie kontaktu {#usage}

Do poľa s názvom nového kontaktu napíšte:

- **názov firmy** (aspoň tri znaky) — najviac päť zhôd z fulltextového indexu
  registra;
- **IČO** (6 až 8 číslic) — register sa opýta priamo na toto číslo.

Subjekt, ktorý nie je aktívny, má v návrhu slovo, ktorým jeho stav uvádza
register, napr. *Firma s.r.o. (12345678) — zrušená*. Pre starší doklad môže byť
stále správnou voľbou; označený je preto, aby sa IČO zaniknutého subjektu
nedostalo na novú faktúru nepozorovane.

Slovenské IČ DPH napísané do poľa pre IČ DPH (*Tax ID*, slovenský preklad Odoo
ho označuje „DIČ“) nájde jeho držiteľa. Ponúkne sa len presná zhoda: register
musí potvrdiť, že subjekt toto IČ DPH práve teraz má.

Výber návrhu vyplní:

| Údaj | Poznámka |
|---|---|
| Názov, ulica, obec, PSČ, štát | |
| Pole pre IČ DPH (*Tax ID*) | IČ DPH, **len kým register uvádza platnú registráciu pre DPH**. Zrušené IČ DPH sa nezapíše. |
| *IČO* (*Company ID*) | ak je zapnuté *ORSF: vyplniť IČO* |
| Spoločnosť / fyzická osoba | ak je zapnuté *ORSF: nastaviť typ subjektu* |
| Mapované údaje | pozri [mapovanie](#mapping) |
| Zoznamy z registra | s modulom [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry): predmety podnikania, uložené účtovné závierky, predchádzajúce názvy a sídla a čas overenia v registri. Každý zoznam sa nahradí, nie doplní. |

## Aktualizácia kontaktov {#refresh}

V zozname kontaktov sú v ponuke *Actions* tri akcie:

| Akcia | Načíta | Vhodná pre |
|---|---|---|
| **Update** (z prepínača poskytovateľov) | úplný záznam z registra, po jednom kontakte | niekoľko kontaktov, pri ktorých záleží na zápise v registri, druhu registrácie DPH alebo predmetoch podnikania |
| **Aktualizovať identifikačné údaje z ORSF (hromadne)** | len identifikačné údaje, až 100 IČO na jednu požiadavku | celú databázu partnerov |
| **Doplniť chýbajúce DIČ z ORSF** | len DIČ, až 100 IČO na jednu požiadavku | kontakty, ktorým chýba DIČ (napríklad pre identifikátor Peppol *0245:DIČ*) a nič iné sa im meniť nemá |

ORSF povoľuje za minútu oveľa menej načítaní úplného záznamu než identifikačných
údajov, takže **Update** na dlhom výbere v polovici prestane vracať údaje.

### Hromadná aktualizácia {#bulk}

**Aktualizovať identifikačné údaje z ORSF (hromadne)** vezme IČO, ktoré pri
každom označenom kontakte zaznamenalo predchádzajúce automatické doplnenie,
alebo jeho pole *IČO*,
opýta sa registra na všetky po dávkach a prepíše názov, adresu, IČ DPH a
mapované identifikačné údaje: DIČ, právnu formu, register, stav, SK NACE, dátum
vzniku a zániku. Registrový súd a číslo zápisu, druh registrácie DPH, predmety
podnikania ani závierky nemení — na tie použite **Update**.

Oznámenie uvedie, koľko kontaktov sa aktualizovalo, koľko IČO sa v registri
nenachádza a koľko kontaktov nemalo použiteľné IČO.

Kontaktná osoba vo firme sa **preskočí** a započíta medzi kontakty bez
použiteľného IČO. V poli *IČO* má IČO firmy, ktoré tam skopíruje Odoo, a jeho
vyhľadanie by jej meno a adresu prepísalo údajmi firmy. Pole *IČO* sa použije
len pri spoločnosti alebo pri fyzickej osobe bez nadradenej spoločnosti
(živnostník) — rovnako ako pri **Update**.

### Doplnenie chýbajúceho DIČ {#dic}

**Doplniť chýbajúce DIČ z ORSF** zapíše DIČ do kontaktov, ktoré majú pole
**DIČ** prázdne, a nič iné nemení — ani názov, adresu, ani IČ DPH. DIČ, ktoré
už na kontakte je, sa nikdy neprepíše, takže akciu možno spustiť kedykoľvek
znova. Potrebuje modul [module:l10n_sk_base](module:l10n_sk_base), ktorý pole
pridáva; bez neho akcia len oznámi, že nie je čo doplniť. Oznámenie spočíta
doplnené kontakty, IČO, ktoré register nepozná, kontakty bez zverejneného DIČ a
kontakty bez použiteľného IČO.

## Obmedzenia {#limitations}

- Zrušené IČ DPH sa nezapíše, ale IČ DPH, ktoré už na kontakte je, sa
  **neodstráni** — ani pri **Update**, ani pri hromadnej aktualizácii. Status
  zrušeného platiteľa si overte sami alebo modulom
  [module:l10n_cssk_vies](module:l10n_cssk_vies).
- Kópia registrov v ORSF môže byť neúplná — napríklad firma bez registrového
  súdu a čísla zápisu, hoci v ORSR je. S modulom
  [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry) má záložka
  registra na kontakte tlačidlo, ktorým ORSF požiadate o opätovné načítanie
  firmy; **Update** spustite o minútu.
- Bez tokenu API vracia ORSF pri živnostníkovi len obec, nie ulicu a PSČ.
- Keď ORSF neodpovie — výpadok, časový limit, limit požiadaviek —, prejaví sa to
  ako žiadne návrhy alebo *no data returned*, nikdy ako chybové hlásenie.
  Príčina je v logu servera.
- Len slovenské subjekty. Ostatné štáty idú k vlastnému poskytovateľovi alebo k
  poskytovateľovi spoločnosti.
