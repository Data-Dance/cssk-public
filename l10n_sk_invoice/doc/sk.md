---
title: SK faktúra (zákonné PDF)
summary: Doplní do tlačenej slovenskej faktúry DIČ odberateľa, platobné symboly a zákonné formulácie o oslobodení od dane a prenesení daňovej povinnosti.
verified: 19.0.1.0.4
---

## Na čo slúži {#purpose}

Faktúra z Odoo spolu so slovenskou účtovou osnovou (`l10n_sk`) už obsahuje
väčšinu toho, čo slovenská faktúra potrebuje: názov, adresu a IČ DPH oboch
strán, IČO odberateľa, číslo a dátumy faktúry, položky, základ dane a daň
podľa sadzieb a zápis dodávateľa v obchodnom registri. Modul doplní tri veci,
ktoré v nej chýbajú:

1. **DIČ odberateľa** pod jeho adresou;
2. **variabilný, konštantný a špecifický symbol** vedľa dátumov faktúry;
3. **zákonnú formuláciu**, ktorú musí obsahovať faktúra za plnenie oslobodené
   od dane alebo s prenesením daňovej povinnosti — určí ju z daní na faktúre a
   z krajiny odberateľa.

Všetko sa tlačí len na dokladoch spoločnosti so sídlom na Slovensku, takže
modul neprekáža v databáze, kde sú aj spoločnosti z iných krajín.

## Právny rámec {#legal}

Obsah faktúry určuje
[§ 74 ods. 1 zákona o DPH](law:sk/2004/222#paragraf-74.odsek-1). Dva z jeho
údajov závisia od druhu plnenia a práve tie modul tlačí:

- **Oslobodenie od dane** —
  [§ 74 ods. 1 písm. h)](law:sk/2004/222#paragraf-74.odsek-1.pismeno-h): pri
  oslobodení od dane sa uvedie odkaz na ustanovenie zákona alebo smernice
  2006/112/ES, alebo slovná informácia *„dodanie je oslobodené od dane“*.
  Modul odkazuje na zákon: [§ 43](law:sk/2004/222#paragraf-43) pri dodaní
  tovaru do iného členského štátu odberateľovi identifikovanému pre daň a
  [§ 47](law:sk/2004/222#paragraf-47) pri vývoze tovaru mimo EÚ.
- **Prenesenie daňovej povinnosti** —
  [§ 74 ods. 1 písm. k)](law:sk/2004/222#paragraf-74.odsek-1.pismeno-k): ak
  je osobou povinnou platiť daň príjemca, faktúra obsahuje slovnú informáciu
  *„prenesenie daňovej povinnosti“*. Týka sa to tuzemských plnení podľa
  [§ 69 ods. 12](law:sk/2004/222#paragraf-69.odsek-12) (kovový odpad a
  šrot, emisné kvóty, stavebné práce a ďalšie) aj služby dodanej zdaniteľnej
  osobe z iného členského štátu, ktorej miestom dodania je podľa
  [§ 15 ods. 1](law:sk/2004/222#paragraf-15.odsek-1) krajina príjemcu.

Formulácie sa tlačia po slovensky bez ohľadu na jazyk faktúry, s anglickým
vysvetlením v zátvorke.

§ 74 vyžaduje *identifikačné číslo pre daň*, teda IČ DPH, ktoré Odoo tlačí
samo. DIČ medzi povinnými údajmi nie je; modul ho tlačí, pretože ho slovenskí
odberatelia na faktúre bežne očakávajú.

## Nastavenie {#setup}

1. **Vyplňte DIČ odberateľa.** Na kontakte pole **DIČ** (pridáva ho modul
   [module:l10n_sk_base](module:l10n_sk_base)). Z IČ DPH sa neodvodzuje.
2. **Platobné symboly** pochádzajú z modulu
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols), ktorý
   sa nainštaluje spolu s týmto modulom. Jeho nastavenia určujú, ako sa tvorí
   variabilný symbol a či sa používa predvolený konštantný symbol — pozri
   [nastavenie platobných symbolov](module:l10n_cssk_payment_symbols#setup).
3. **Označte dane pre tuzemské prenesenie daňovej povinnosti.**
   *Účtovníctvo → Konfigurácia → Dane*, otvorte daň z predaja, ktorú
   používate pri plneniach podľa § 69 ods. 12, a zaškrtnite **SK prenesenie
   daňovej povinnosti (§ 69/12)** vedľa poľa *Typ dane*. Pri inštalácii nie je
   označená žiadna daň: slovenská účtová osnova Odoo pre tieto plnenia nemá
   samostatnú daň z predaja, takže ju určíte vy.
4. **Skontrolujte rámec nulových daní.** Pri predaji do EÚ modul rozlišuje
   tovar a služby podľa poľa **Rámec dane** (*Tovar* / *Služby*) na dani. Dane
   `0% EU M` a `0% EU S` zo slovenskej osnovy ho už majú vyplnené. Pri nulovej
   dani bez rámca rozhodne typ produktu (produkt typu služba sa počíta ako
   služba, všetko ostatné ako tovar).

## Čo faktúra obsahuje {#invoice}

### DIČ odberateľa

`DIČ: 2020123456` pod IČ DPH odberateľa, ak je DIČ vyplnené.

### Platobné symboly

*Variabilný symbol*, *Konštantný symbol* a *Špecifický symbol* v riadku s
dátumom vyhotovenia a splatnosti, každý len vtedy, keď má hodnotu. Označenia
sa riadia jazykom faktúry: po slovensky pre slovensky hovoriaceho odberateľa,
inak po anglicky (*Variable Symbol*, …).

### Zákonné formulácie {#phrases}

Formulácia sa určuje vždy nanovo z daní na faktúre a z **obchodného partnera**
odberateľa (firmy, nie kontaktnej osoby). Tlačí sa pod poznámkou s obchodnými
podmienkami. Pravidlá v tomto poradí:

| Situácia | Vytlačí sa |
|---|---|
| Niektorý riadok má daň označenú *SK prenesenie daňovej povinnosti (§ 69/12)* | *Prenesenie daňovej povinnosti podľa §69 ods. 12 zákona o DPH (Reverse charge).* — a žiadna iná automatická formulácia |
| Odberateľ v inom štáte EÚ s IČ DPH a riadok s nulovou daňou za **tovar** | *Dodanie oslobodené od dane podľa §43 zákona o DPH (Intra-Community supply of goods).* |
| Odberateľ v inom štáte EÚ s IČ DPH a riadok s nulovou daňou za **služby** | *Prenesenie daňovej povinnosti — miesto dodania služby podľa §15 ods. 1 zákona o DPH (Reverse charge, services).* |
| Odberateľ mimo EÚ a riadok s nulovou daňou za **tovar** | *Oslobodené od dane podľa §47 zákona o DPH (Exempt — export of goods).* |
| Tuzemský odberateľ alebo zdanené plnenie | nič |

Faktúra za tovar aj služby odberateľovi z EÚ dostane obe prostredné
formulácie. Služba odberateľovi mimo EÚ nedostane žiadnu: nie je predmetom
slovenskej DPH a niet oslobodenia, na ktoré by sa dalo odkázať.

**Trojstranný obchod** (daň `0% EU T` z osnovy) je z pravidla pre § 43
zámerne vynechaný: Odoo preň tlačí vlastnú poznámku s odkazom na článok 141
smernice.

„Nulová daň“ je akákoľvek daň so sadzbou 0 % na riadku. Slovenské dane Odoo
`0% EU M` a `0% EU S` majú aj vlastné anglické poznámky (články 138 a 196
smernice), ktoré Odoo tlačí tiež; slovenská formulácia sa vytlačí popri nich.

Rovnaké pravidlá platia pre dobropisy odberateľom.

### Vlastná poznámka

Ak automatické formulácie nestačia — iné oslobodenie, odkaz na zmluvu —
napíšte text do poľa **Zákonná poznámka faktúry (ručne)** na karte *Položky
faktúry* pod obchodnými podmienkami; pole je na faktúrach a dobropisoch
odberateľom. Vytlačí sa za automatickou formuláciou. Pri duplikovaní faktúry
sa nekopíruje.

## Obmedzenia {#limitations}

- Formulácia je odvodená z pravidla podľa sadzby dane a krajiny odberateľa.
  Modul nepozná právny dôvod konkrétneho oslobodenia a IČ DPH odberateľa
  neoveruje vo VIES. Nechajte si ju potvrdiť účtovníkom pre vaše nastavenie
  daní a tam, kde nesedí, použite vlastnú poznámku.
- Rozpoznáva len oslobodenie podľa § 43 a § 47. Tuzemské oslobodené plnenie
  (§ 28 až § 42a) formuláciu nedostane; uveďte ju vo vlastnej poznámke.
- Formulácia o prenesení daňovej povinnosti vždy odkazuje na § 69 ods. 12,
  čo je správne len pri tuzemskom prenesení. Ak označíte daň, ktorú používate
  aj v iných prípadoch prenesenia, odkaz bude nesprávny.
- Modul nepridáva žiadne dátumy. Dátum dodania sa vytlačí len vtedy, keď je
  na faktúre vyplnený *Dátum dodania* (Odoo ho doplní z dodávok, ak je
  nainštalovaný Sklad); ak sa líši od dátumu vyhotovenia, vyžaduje ho
  § 74 ods. 1 písm. d).
- Zákonné formulácie sú po slovensky s anglickým vysvetlením; do jazyka
  odberateľa sa neprekladajú.
