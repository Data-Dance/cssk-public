---
title: Pripomienka vypršiavajúcej prenesenej dovolenky (CZ/SK)
summary: Denná pripomienka zamestnancom, že prenesená dovolenka, ktorej platnosť plán nárokov čoskoro ukončí, vyprší — ako aktivita a e-mail.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Plán nárokov v Odoo môže prenášať nevyčerpanú dovolenku do ďalšieho roka
a prenesené dni nechať k určitému dátumu vypršať. Slovenské plány dovolenky
mzdových modulov to robia na konci nasledujúceho roka; české plány dovolenku
prenášajú bez vypršania. Odoo to ukazuje len pasívne, na prehľade aplikácie
*Voľné dni*. Tento modul pripomína aktívne: raz denne vyhľadá prenesenú
dovolenku, ktorá čoskoro vyprší, a aktivitou a e-mailom oznámi zamestnancovi,
o koľko dní ide a dokedy. Schvaľovateľ voľných dní alebo nadriadený dostane
vlastnú aktivitu.

Závisí len od aplikácie Odoo *Voľné dni* (`hr_holidays`), takže funguje
s každým plánom nárokov, v ktorom prenesené dni vypršia, s ktorýmkoľvek
mzdovým jadrom aj úplne bez miezd.

## Právny rámec {#legal}

Ani v jednej krajine nevyčerpaná dovolenka koncom nasledujúceho roka
nezaniká. Vyprší prenesený zostatok v Odoo podľa nastavenia plánu nárokov.
Zákon naopak ukladá zamestnávateľovi, aby sa dovolenka vyčerpala:

- **Slovensko.** Ak si zamestnanec nemôže vyčerpať dovolenku v kalendárnom
  roku, zamestnávateľ je povinný poskytnúť mu ju tak, aby sa skončila
  **najneskôr do konca nasledujúceho kalendárneho roka**; ak jej čerpanie
  neurčí najneskôr do **30. júna** nasledujúceho roka, môže si ho určiť
  zamestnanec, s písomným oznámením najmenej 30 dní vopred
  ([§ 113 ods. 2 Zákonníka práce](law:sk/2001/311#paragraf-113.odsek-2)).
  Dovolenku, ktorú nebolo možné vyčerpať pre materskú, otcovskú alebo
  rodičovskú dovolenku alebo pre dočasnú pracovnú neschopnosť, poskytne
  zamestnávateľ po ich skončení
  ([§ 113 ods. 3 a 4](law:sk/2001/311#paragraf-113.odsek-3)).
- **Česká republika.** Zamestnávateľ musí určiť čerpanie dovolenky, ktorú
  nebolo možné vyčerpať v jej roku alebo ktorá bola prevedená na písomnú
  žiadosť zamestnanca, tak, aby sa vyčerpala **najneskôr do konca
  nasledujúceho kalendárneho roka**
  ([§ 218 odst. 3 zákoníku práce](law:cz/2006/262)). Ak ju neurčí do
  **30. júna** nasledujúceho roka, môže ju určiť aj zamestnanec, s písomným
  oznámením 14 dní vopred (§ 218 odst. 4). Dovolenka, ktorú nebolo možné
  vyčerpať ani do konca nasledujúceho roka pre pracovnú neschopnosť alebo
  materskú či rodičovskú dovolenku, sa určí po skončení prekážky
  (§ 218 odst. 5).

Pripomienka je teda výzvou naplánovať dovolenku pred lehotou, ktorú má
dodržať zamestnávateľ. Žiada zamestnanca, aby sa s vedúcim dohodol, kedy
dovolenku vyčerpá, a uvádza, že podľa Zákonníka práce dovolenka neprepadá;
dátum v nej je deň, keď plán nárokov dni odoberie zo zostatku v Odoo.

## Nastavenie {#setup}

Nič netreba nastavovať. Správanie menia dva systémové parametre
(*Nastavenia → Technické → Parametre systému*, režim vývojára):

| Parameter | Predvolené | Čo robí |
|---|---|---|
| `l10n_cssk_leave_expiry.lead_days` | `60` | Koľko dní pred dátumom vypršania sa pripomienka pošle. |
| `l10n_cssk_leave_expiry.send_email` | `True` | Či sa okrem aktivity pošle aj e-mail. `False`, `0`, `no` alebo `off` ho vypnú. |

Naplánovaná akcia *Dovolenka: Upozorniť na vypršiavajúcu prenesenú dovolenku
(CZ/SK)* beží raz denne (*Nastavenia → Technické → Naplánované akcie*).
E-mailová šablóna je *Dovolenka: Pripomienka vypršiavajúcej dovolenky*; jej
znenie môžete upraviť.

Aby sa pripomienka dostala k zamestnancovi, zamestnanec potrebuje
**Súvisiaceho používateľa** (pre aktivitu) a **Pracovný e-mail** (pre
e-mail). Aby sa o nej dozvedelo personálne oddelenie, zamestnanec potrebuje
schvaľovateľa voľných dní alebo nadriadeného s používateľom.

## Ako pripomienka funguje {#usage}

Naplánovaná akcia každý deň vezme alokácie v stave *Schválené*, *Na
schválenie* alebo *Druhé potvrdenie*, ktorých prenesené dni vypršia medzi dneškom a dneškom plus
predstih (predvolene 60 dní). Alokácie plánu nárokov, ktorý prenos
nepovoľuje, sa vynechajú: ide o ročné limity typu „vyčerpaj, alebo prepadne“,
napríklad slovenské dni na lekárske vyšetrenie či sprevádzanie, v ktorých sa
nič neprenáša.

Pri každej alokácii vypočíta dni, ktoré by naozaj vypršali: prenesený
zostatok mínus dovolenku čerpanú z alokácie odvtedy. Samotné Odoo toto
odpočítanie robí až v deň vypršania, preto môže byť počet v pripomienke
nižší než hodnota uložená na alokácii. Ak nič nezostáva, pripomienka sa
nepošle.

Inak

1. naplánuje na karte **zamestnanca** aktivitu **Vypršiavajúca dovolenka**
   s termínom v deň vypršania, s počtom dní, typom voľna a dátumom, pridelenú
   vlastnému používateľovi zamestnanca a adresovanú zamestnancovi
   (*„Máte …“*);
2. naplánuje na tej istej karte druhú aktivitu **Vypršiavajúca dovolenka**
   pre *Schvaľovateľa voľných dní*, a ak ho niet, pre používateľa
   nadriadeného, formulovanú o zamestnancovi (*„<Zamestnanec> má …“*). Deje sa
   to vždy, aj keď zamestnanec používateľa má a prvú aktivitu dostal. Ak je
   schvaľovateľom alebo nadriadeným vlastný používateľ zamestnanca, druhá
   aktivita sa nevytvorí;
3. ak je to zapnuté, pošle rovnaký text na *Pracovný e-mail* zamestnanca,
   v jazyku zamestnanca. Pri type voľna, ktoré sa žiada v hodinách, je počet
   uvedený v hodinách.

Na každý dátum vypršania sa pripomína **raz**: alokácia si pamätá dátum,
na ktorý bola naposledy pripomenutá, a nová pripomienka príde až pri novom
prenesenom zostatku s novým dátumom vypršania. Ak sa nepodarí doručiť nič —
zamestnanec nemá používateľa, niet schvaľovateľa ani nadriadeného
s používateľom, chýba pracovný e-mail — alokácia sa ako pripomenutá neoznačí
a ďalší denný beh to skúsi znova.

Pri slovenských plánoch mzdových modulov prenesené dni vypršia 364 dní po
prenose 1. januára, teda 31. decembra nasledujúceho roka (v priestupnom roku
30. decembra), takže pripomienka predvolene príde na začiatku novembra. České
plány vypršanie nenastavujú, ich alokácie preto pripomienku nedostanú.

## Obmedzenia {#limitations}

- **Jedna pripomienka na jedno vypršanie.** Keď bola pripomienka doručená,
  druhá bližšie k termínu nepríde.
- Pripomienka je len taká dobrá ako plán nárokov: alokácia bez plánu nárokov
  alebo plán bez vypršania prenesených dní ju nikdy nedostane.
- Odosielateľom e-mailu je e-mail spoločnosti typu voľna, a ak typ voľna
  nemá spoločnosť, používateľ naplánovanej akcie.
