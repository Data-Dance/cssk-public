---
title: Automatické dopĺňanie partnerov zo štátnych registrov (CZ/SK)
summary: Dopĺňa kontakty z českých a slovenských registrov namiesto platenej služby Odoo a register vyberá podľa štátu partnera.
verified: 19.0.1.3.0
---

## Na čo slúži {#purpose}

Vlastné automatické dopĺňanie partnerov v Odoo hľadá firmy v platenej službe
Odoo (IAP). Pre českých a slovenských partnerov je však smerodajným zdrojom
štátny register, v ktorom sa subjekt vyhľadáva podľa IČO. Tento modul je
prepínačom medzi nimi: každej spoločnosti umožní zvoliť si **poskytovateľa**
automatického dopĺňania a vyhľadávanie podľa názvu, vyhľadávanie podľa IČ DPH aj
samotné vyplnenie kontaktu posiela tomuto poskytovateľovi.

Sám osebe nič viditeľné nerobí. Inštaluje sa spolu s jedným alebo oboma
poskytovateľmi:

| Poskytovateľ | Register | Štáty | Návod |
|---|---|---|---|
| ARES.CZ | ARES, český register ekonomických subjektov | CZ | [nižšie](#ares) |
| ORSF.SK | ORSF, otvorený súhrn slovenských registrov (RPO, ORSR, ŽRSR, RÚZ, Finančná správa) | SK | [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) |

## Nastavenie {#setup}

1. Nainštalujte modul poskytovateľa. Tento modul sa nainštaluje s ním.
2. *Nastavenia → Všeobecné nastavenia*, blok **Kontakty**: musí byť zapnuté
   **Automatické dopĺňanie partnera** (*Partner Autocomplete*).
3. Pod ním v poli **Poskytovateľ** (*Provider*) zvoľte register pre aktuálnu
   spoločnosť. Odkaz Odoo na nákup kreditov nahradí práve táto voľba. Nastavenia
   konkrétneho poskytovateľa sa zobrazia pod ňou, keď je zvolený.

Poskytovateľ sa ukladá pre každú spoločnosť zvlášť. Prepnite sa do každej
spoločnosti a nastavte ho tam.

Dve voľby nie sú registre:

- **Odoo IAP** vráti vyhľadávanie vlastnej službe Odoo, presne ako bez tohto
  modulu. Každé vyhľadávanie partnera zo štátu, ktorého register žiadny
  nainštalovaný poskytovateľ nečíta, odchádza do Odoo.
- **None** nehľadá nič mimo národných registrov. Partner zo štátu niektorého
  poskytovateľa sa tam hľadá aj naďalej (pozri nižšie); všetko ostatné nenájde
  nič a do Odoo sa nič neodošle.

Predvolená voľba je **None**. Do verzie 19.0.1.2.0 sa ako **None** označovala
dnešná voľba **Odoo IAP**, ktorá bola zároveň predvolená; prechod na 19.0.1.3.0
previedol každú spoločnosť, ktorá ju mala, na skutočnú **None**. Ak chcete
službu Odoo pre partnerov mimo národných registrov, zvoľte **Odoo IAP**.

## Ktorý register sa použije {#routing}

Najprv rozhoduje štát, až potom voľba spoločnosti:

- Poskytovateľ uvádza štáty, ktorých register číta — ARES číta CZ, ORSF SK.
  Ak je **Štát** kontaktu jedným z nich (alebo pri hľadaní podľa IČ DPH začína
  číslo predponou tohto štátu), použije sa tento poskytovateľ **bez ohľadu na
  voľbu spoločnosti**. Slovenská spoločnosť tak môže doplniť českého dodávateľa
  z ARES a naopak, ak sú nainštalovaní obaja poskytovatelia.
- Pri inom štáte alebo bez štátu sa použije **Poskytovateľ** spoločnosti.
- Keď zvolíte návrh, údaje sa načítajú z toho istého registra, ktorý ho
  ponúkol. Je to dôležité, lebo české aj slovenské IČO má osem číslic.

## Vyplnenie kontaktu {#usage}

Do poľa s názvom nového kontaktu napíšte aspoň tri znaky názvu firmy alebo
jej IČO, prípadne IČ DPH do poľa pre IČ DPH (*Tax ID*, slovenský preklad Odoo
ho označuje „DIČ“), a vyberte jeden z návrhov. Poskytovateľ vyplní adresu,
identifikátory a ďalšie údaje, ktoré podporuje; presný zoznam je v návode
poskytovateľa.

Poskytovateľ môže vrátiť aj **bankové účty** a **kontakty**. Modul preto do
formulára spoločnosti (*Nastavenia → Spoločnosti*) pridá dve záložky, *Bank
Accounts* a *Contacts*, aby ich automatické dopĺňanie vlastnej spoločnosti
mohlo vyplniť tiež. Keď poskytovateľ zoznam nahrádza (bankové účty, zoznamy z
registra), staré riadky sa odstránia, nie zdvoja.

## Aktualizácia existujúcich kontaktov {#update}

V zozname označte jeden alebo viac kontaktov a spustite *Actions → Update*.
Každý kontakt sa znova vyhľadá vo svojom registri a prepíše sa tým, čo uvádza
register.

Opýta sa registra, ktorý pri kontakte zaznamenalo predchádzajúce automatické
doplnenie, inak registra podľa **Štátu** kontaktu, inak **Provider**
spoločnosti — v rovnakom poradí ako pri vyhľadávaní.

Na vyhľadanie sa použije číslo, ktoré patrí samotnému kontaktu:

- IČO, ktoré pri ňom zaznamenalo predchádzajúce automatické doplnenie, alebo
- pole **IČO** (*Company ID*) — ale len pri spoločnosti alebo pri fyzickej
  osobe bez nadradenej spoločnosti (živnostník). Kontaktná osoba vo firme má v
  tomto poli IČO firmy, ktoré tam skopíruje Odoo, a **preskočí sa**:
  vyhľadanie tohto čísla by osobu prepísalo názvom a adresou firmy.

Ak ste označili viac kontaktov alebo sa niečo nepodarilo, oznámenie spočíta
výsledky: *updated* (aktualizované), *skipped* (nebolo podľa čoho hľadať), *with
no data returned* (register nevrátil nič) a *failed* (príčina je v logu
servera).

Registre obmedzujú, koľko úplných záznamov sa dá načítať za minútu, takže
**Update** na veľkom výbere v polovici prestane vracať údaje. Prejaví sa to ako
*with no data returned*, nie ako chyba. Pre veľa slovenských kontaktov použite
radšej [hromadnú aktualizáciu z ORSF](module:partner_autocomplete_orsf_sk#bulk).

## Doplnenie kontaktov pri importe {#import}

Importovaný súbor môže obsahovať stĺpec **Import Enrich Company** s IČO. Každý
importovaný kontakt, ktorý v ňom má hodnotu, sa pri vytvorení vyhľadá a vyplní z
registra. Ručne vytvorené kontakty sa nikdy nevyhľadávajú bez vášho vedomia:
uloženie novej spoločnosti s vyplneným **IČO** vyhľadanie nespustí.

## ARES (Česká republika) {#ares}

Modul [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz)
číta verejnú službu ARES Ministerstva financií ČR. Netreba konto ani kľúč.

- **Vyhľadávanie.** Podľa názvu firmy: prvých päť zhôd v tvare *názov, obec
  (IČO)*. IČO napísané ako číslice túto firmu ponúkne. České DIČ napísané do
  poľa pre IČ DPH firmu nájde, ak je to DIČ právnickej osoby (*CZ* + osemmiestne
  IČO) a ARES jej toto DIČ potvrdí.
- **Vyplní:** názov, ulicu, PSČ, obec, štát a do poľa pre IČ DPH české DIČ
  tak, ako ho uvádza ARES.
- **Nastavenia** (zobrazia sa, keď je ARES poskytovateľom spoločnosti):

  | Nastavenie | Čo robí |
  |---|---|
  | IČO | Pole kontaktu, do ktorého sa zapíše IČO. Predvolene prázdne, takže IČO sa nikam neuloží, kým pole nezvolíte — zvyčajne *IČO* (*Company ID*). |
  | Prevailing activity (CZ-NACE 2025) | Pole kontaktu, do ktorého sa zapíše prevažujúca činnosť z kópie štatistického registra (RES) v ARES. Ak je nainštalovaný modul [module:partner_nace](module:partner_nace), nastaví sa automaticky na *NACE (main activity)*. Stojí jednu požiadavku navyše; prázdne = nenačíta sa. |

- **Obmedzenia.** ARES neumožňuje hľadať podľa DIČ; DIČ fyzickej osoby (desať
  číslic, odvodené z rodného čísla) nemá IČO, podľa ktorého by sa dalo hľadať,
  a nič nenájde. ARES vracia DIČ bez ohľadu na to, či je firma
  práve platiteľom DPH; pred prenesením daňovej povinnosti si overte jej
  registráciu. Bankové účty a kontaktné osoby sa nevypĺňajú.

## Obmedzenia {#limitations}

- Prázdna odpoveď poskytovateľa vyzerá rovnako, či firma neexistuje, register
  nefunguje, alebo sa dosiahol limit požiadaviek. Rozlíši ich log servera.
- Popisky tohto modulu nie sú preložené.
