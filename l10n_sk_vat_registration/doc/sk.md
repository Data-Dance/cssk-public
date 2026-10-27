---
title: SK druh registrácie DPH (§ 4 / § 7 / § 7a)
summary: Eviduje, podľa ktorého paragrafu zákona o DPH bolo partnerovi pridelené IČ DPH, a upozorní, keď sa prenesenie daňovej povinnosti uplatní voči osobe registrovanej podľa § 7 alebo § 7a, ktorá nie je platiteľom.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

IČ DPH neznamená pre každého, kto ho má, to isté. Osoba registrovaná podľa
**§ 7** (nadobúdanie tovaru z iného členského štátu) alebo **§ 7a** (prijatie
alebo dodanie služby cez hranicu) má platné IČ DPH, ktoré VIES potvrdí — ale
**nie je platiteľom dane**. Daň z tuzemských dodaní neuplatňuje, daň na
vstupe neodpočítava a prenesenie daňovej povinnosti podľa § 69 ods. 12 sa na
ňu nevzťahuje.

VIES odpovedá len platné / neplatné. Modul doplní na kontakt paragraf
registrácie a upozorní, keď faktúra uplatňuje tuzemské prenesenie daňovej
povinnosti voči odberateľovi, ktorý nie je platiteľom.

## Právny rámec {#legal}

Odkazy sú na [zákon o DPH](law:sk/2004/222).

- [§ 4](law:sk/2004/222#paragraf-4) — zdaniteľná osoba so sídlom, miestom
  podnikania alebo prevádzkarňou v tuzemsku sa stáva **platiteľom**, napríklad
  po prekročení obratu 50 000 eur za kalendárny rok;
  [§ 4b](law:sk/2004/222#paragraf-4b) — registrácia skupiny;
  [§ 4c](law:sk/2004/222#paragraf-4c) — registrácia skupiny z úradnej moci;
  [§ 5](law:sk/2004/222#paragraf-5) — zahraničná osoba sa stáva platiteľom
  dodaním tovaru alebo služby v tuzemsku.
- [§ 7](law:sk/2004/222#paragraf-7) — osoba, ktorá nie je povinná
  registrovať sa podľa § 4 alebo § 5 (alebo právnická osoba, ktorá nie je
  zdaniteľnou osobou), sa registruje pred nadobudnutím tovaru z iných
  členských štátov, ktorým celková hodnota dosiahne v kalendárnom roku
  14 000 eur, prípadne dobrovoľne.
- [§ 7a](law:sk/2004/222#paragraf-7a) — zdaniteľná osoba, ktorá nie je
  povinná registrovať sa podľa § 4, sa registruje pred prijatím služby od
  zahraničnej osoby, z ktorej je povinná platiť daň, alebo pred dodaním
  služby s miestom dodania v inom členskom štáte.
- [§ 69 ods. 12](law:sk/2004/222#paragraf-69.odsek-12) — prenesenie daňovej
  povinnosti v tuzemsku platí, ak sú **dodávateľ aj príjemca** platiteľmi s
  IČ DPH prideleným podľa § 4, § 4b, § 4c alebo § 5. Osoba registrovaná podľa
  § 7 alebo § 7a takou nie je, takže daň uplatní a odvedie dodávateľ.

## Nastavenie {#setup}

Nič sa nenastavuje. Na formulári kontaktu sa pod IČ DPH zobrazia dve polia
pri slovenských partneroch a partneroch bez krajiny:

| Pole | Význam |
|---|---|
| Druh registrácie DPH | paragraf, podľa ktorého bolo IČ DPH pridelené: § 4, § 4b, § 4c, § 5, § 7 alebo § 7a; § 6 *zásielkový predaj* pri registrácii na zásielkový predaj pred 1. 7. 2021 |
| Platiteľ DPH od | dátum účinnosti registrácie pre DPH podľa záznamu Finančnej správy (zobrazí sa po vyplnení druhu registrácie) |

Vyplňte ich ručne, alebo ich pri vyhľadaní firmy vyplní z registra modul
[module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk).
Hodnoty, ktoré register zapisuje v rôznych podobách (`§4`, `§ 7a`, `7A`), sa
rozpoznajú; nerozpoznaná hodnota nechá pole **prázdne**, nikdy ho nenastaví na
„nie je platiteľ“.

## Upozornenie na faktúre {#warning}

Na odberateľskej faktúre slovenskej spoločnosti sa navrchu zobrazí žlté
upozornenie (po slovensky, s anglickým prekladom), ak súčasne platí:

- druh registrácie odberateľa je **§ 7** alebo **§ 7a**;
- krajina odberateľa je Slovensko alebo nie je vyplnená;
- niektorý riadok nesie daň označenú ako tuzemské prenesenie daňovej
  povinnosti (príznak *SK Reverse Charge (§69/12)* z modulu
  [module:l10n_sk_invoice](module:l10n_sk_invoice)).

Pri zaúčtovaní sa rovnaký text zapíše do chatteru faktúry. Upozornenie
zaúčtovanie **nikdy nezablokuje**: dane opravte sami — plnenie sa zdaní
bežnou slovenskou DPH.

Bez modulu [module:l10n_sk_invoice](module:l10n_sk_invoice) dane príznak
prenesenia nemajú a kontrola mlčí.

## Obmedzenia {#limitations}

- **Druh registrácie je taký aktuálny ako jeho posledná zmena.** Nič ho
  pravidelne neobnovuje; odberateľ, ktorý sa stane platiteľom podľa § 4, si
  starý údaj ponechá, kým ho nezmeníte vy alebo vyhľadanie v registri.
- **Kontroluje sa len tuzemské prenesenie daňovej povinnosti.** Iné dôsledky
  registrácie podľa § 7 / § 7a (napríklad pri dodaní tovaru do iného
  členského štátu alebo v kontrolnom výkaze) nie.
- **Voľba § 6 je historická.** Zodpovedá registrácii na zásielkový predaj
  podľa § 6 v znení do 30. 6. 2021, ktorej držitelia boli platiteľmi, a tak
  sa aj počíta. Dnešný § 6 je osobitná oznamovacia povinnosť platiteľa o
  bankových účtoch a nikoho neregistruje, takže aktuálny záznam v registri
  by ju nemal obsahovať.
- **Platiteľ DPH od** je dátum registrácie pri každom druhu, aj pri osobách
  podľa § 7 / § 7a, ktoré platiteľmi nie sú.
- Dodávateľské faktúry sa nekontrolujú.
