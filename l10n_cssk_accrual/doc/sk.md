---
title: Dohadné položky CZ/SK
summary: Zaúčtovanie odhadu nákladu alebo výnosu, ku ktorému do konca obdobia neprišla faktúra, a jeho vyrovnanie so skutočnou faktúrou tak, aby v novom období zostal len rozdiel.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Ku koncu obdobia sú niektoré náklady už spotrebované, ale ešte
nevyfaktúrované: elektrina za december, služba dodaná v decembri a
fakturovaná v januári, odmena audítora za uzatváraný rok. V Česku sa také
položky účtujú na **dohadných účtoch** (388 aktívny, 389 pasívny); na
Slovensku na účte **326** *Nevyfaktúrované dodávky*, prípadne ako rezerva,
ak výška nie je istá (pozri [Právny rámec](#legal)).

Odoo taký doklad nemá. Modul pridáva **dohadnú položku**: odhad zadáte a
zaúčtujete ku koncu obdobia, a keď príde faktúra, prepojíte ju a dohadnú
položku vyrovnáte. Vyrovnanie zaúčtuje storno odhadu k dátumu faktúry, takže
účet dohadnej položky sa vynuluje a do nového obdobia pripadne len rozdiel
medzi odhadom a faktúrou.

Dohadná položka nie je časové rozlíšenie: to rozkladá **známu** sumu do
viacerých období a riešia ho moduly
[module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff) a
[module:l10n_cz_account_cutoff](module:l10n_cz_account_cutoff).

Modul funguje s akoukoľvek účtovou osnovou: účty a denník vyberáte pri každej
dohadnej položke. Potrebuje len modul `account` a
[module:l10n_cssk_core](module:l10n_cssk_core), takže beží v edícii
Community aj Enterprise.

## Právny rámec {#legal}

Oba zákony o účtovníctve vyžadujú účtovať účtovné prípady v období, s ktorým
časovo a vecne súvisia —
[§ 3 ods. 1 slovenského zákona o účtovníctve](law:sk/2002/431#paragraf-3.odsek-1)
a [§ 3 odst. 1 českého zákona o účetnictví](law:cz/1991/563). Spôsob
zachytenia nevyfaktúrovanej položky sa líši:

- **Slovensko.** [Opatrenie 740/2002 Z. z.](law:sk/2002/740) dohadné účty
  nepozná. Na účte **326** *Nevyfaktúrované dodávky* sa účtujú položky
  neúčtované ako obvyklé záväzky, ak účtovná jednotka na základe zmluvy,
  dodacieho listu alebo iného dokladu **pozná výšku záväzku**
  ([§ 50 ods. 6](law:sk/2002/740#paragraf-50.odsek-6)). Ak je neurčité
  časové vymedzenie alebo výška záväzku, tvorí sa krátkodobá rezerva na účte
  323 ([§ 50 ods. 3](law:sk/2002/740#paragraf-50.odsek-3)). Nevyfaktúrovaná
  pohľadávka sa účtuje na príslušnom účte pohľadávok na samostatnom
  analytickom účte ([§ 48 ods. 3](law:sk/2002/740#paragraf-48.odsek-3)).
- **Česko.** [Vyhláška č. 500/2002 Sb.](law:cz/2002/500) (§ 10 odst. 7,
  § 17 odst. 6 a príloha č. 1) vymedzuje *dohadné účty aktivní* a *dohadné
  účty pasivní* ako sumy stanovené napríklad podľa zmlúv, ktoré nie sú
  doložené všetkými potrebnými dokladmi, a preto nie je známa ich presná
  výška. Ide o účty 388 a 389.

Modul zaúčtuje na účty, ktoré mu zadáte. Ktorý účet sa na danú položku
použije — a na Slovensku, či ide o nevyfaktúrovanú dodávku alebo o rezervu —
rozhoduje váš účtovník.

## Nastavenie {#setup}

Modul nemá žiadne nastavenia. Pred prvou dohadnou položkou:

- **Povoľte párovanie na účte dohadnej položky.** Pri vyrovnaní sa odhad
  páruje so stornom práve na tomto účte, preto modul odmietne zaúčtovať, ak
  účet nemá zaškrtnuté *Povoliť párovanie*. Slovenská osnova Odoo má účet
  326000 a česká účty 388000 a 389000 **bez** neho: otvorte účet v
  *Účtovníctvo → Konfigurácia → Účtovníctvo → Účtový rozvrh* a zaškrtnite
  ho.
- **Denník typu Rôzne.** Dohadné položky sa účtujú v denníku typu *Rôzne*.

Ponuka je v *Účtovníctvo → Účtovníctvo*; v edícii Community sa zobrazí, len
ak sú zapnuté úplné účtovné funkcie, a samotná aplikácia sa tam volá
*Fakturácia*.

## Zadanie dohadnej položky {#usage}

*Účtovníctvo → Účtovníctvo → Transakcie → Dohadné položky*, potom *Nový*.

| Pole | Čo vyplniť |
|---|---|
| Partner | Dodávateľ (alebo odberateľ), od ktorého (alebo ktorému) sa faktúra očakáva. Povinné. |
| Typ dohadnej položky | **Odhadovaný záväzok** — nevyfaktúrovaný náklad; alebo **Odhadovaná pohľadávka** — nevyfaktúrovaný výnos. |
| Dátum | Dátum zaúčtovania odhadu, zvyčajne posledný deň obdobia. |
| Suma | Odhadovaná suma v mene spoločnosti, bez DPH. Musí byť kladná. |
| Popis | Vytlačí sa na oboch riadkoch zápisu. |
| Denník | Denník spoločnosti typu *Rôzne*. |
| Účet dohadnej položky | 326 pre nevyfaktúrovanú dodávku, alebo samostatný analytický účet pohľadávky pre nevyfaktúrovanú pohľadávku — podľa rozhodnutia účtovníka (SK); 389 / 388 (CZ). |
| Protiúčet | Nákladový účet (pri odhadovanom záväzku) alebo výnosový účet (pri odhadovanej pohľadávke). |

Kliknite na **Zaúčtovať odhad**. Modul vytvorí a zaúčtuje jeden zápis,
číslovaný od `DOHAD/<rok>/0001`:

| Typ dohadnej položky | MD | D |
|---|---|---|
| Odhadovaný záväzok | protiúčet (náklad) | účet dohadnej položky |
| Odhadovaná pohľadávka | účet dohadnej položky | protiúčet (výnos) |

Oba riadky nesú partnera. Zápis je bez DPH: odhad nie je daňový doklad.

## Vyrovnanie so skutočnou faktúrou {#settle}

Skutočnú faktúru zaúčtujte obvyklým spôsobom na nákladový alebo výnosový
účet. Potom otvorte dohadnú položku:

1. V poli **Skutočná faktúra** vyberte faktúru. Ponúknu sa zaúčtované
   faktúry a dobropisy toho istého partnera a spoločnosti.
2. Kliknite na **Vyrovnať (prepojiť faktúru)**.

Modul zaúčtuje storno zápisu odhadu k **dátumu faktúry** (alebo k dátumu
odhadu, ak je faktúra datovaná skôr) a odhad so stornom spáruje na účte
dohadnej položky. Účet sa pre túto položku vynuluje, storno v novom období
zruší odhadovaný náklad a faktúra zaúčtuje skutočný. V novom období zostane
presne rozdiel.

Príklad: odhad 1 000 za elektrinu za december, januárová faktúra 1 050 bez
DPH. V januári storno zaúčtuje 1 000 v prospech nákladu a faktúra 1 050 na
ťarchu nákladu — v januári zostane 50, v decembri 1 000.

Dohadná položka prejde do stavu *Vyrovnané*; polia *Účtovný zápis odhadu* a
*Vyrovnávací / storno zápis* odkazujú na oba zápisy.

## Zrušenie dohadnej položky {#cancel}

**Zrušiť** pri zaúčtovanej dohadnej položke zaúčtuje storno k **dnešnému
dátumu**, spáruje ho a položku nastaví na *Zrušené*. Položka v stave návrh sa
len zruší.

**Nastaviť na návrh** vráti zrušenú položku do návrhu, aby ju bolo možné
opraviť a znovu zaúčtovať. Zrušený zápis a jeho storno zostanú v účtovníctve
(navzájom sa vyrušia) a chatter ich uvedie; nové zaúčtovanie vytvorí nový
zápis.

Pred každým stornom (pri vyrovnaní aj zrušení) prebehnú dve kontroly:

- Ak je riadok na účte dohadnej položky už spárovaný s niečím iným, modul
  storno odmietne a uvedie zápisy, s ktorými je spárovaný. Najprv párovanie
  zrušte.
- Ak dátum storna padne do uzamknutého obdobia, modul ho odmietne a uvedie,
  o ktorý zámok ide. Upravte dátum uzamknutia alebo vyrovnajte voči faktúre s
  neskorším dátumom.

## Obmedzenia {#limitations}

- Modul odhad s faktúrou neporovnáva a faktúru s ničím nepáruje. Nekontroluje
  ani typ: prepojiť možno akúkoľvek zaúčtovanú faktúru alebo dobropis
  partnera.
- Jedna dohadná položka sa vyrovná s jednou faktúrou. Odhad za viac faktúr
  treba rozdeliť na viac položiek, alebo ho vyrovnať s jednou z nich a
  ostatné zaúčtovať bežne.
- Sumy sú len v mene spoločnosti; odhad v cudzej mene ani analytické
  rozúčtovanie zápis nepodporuje.
- Zrušenie stornuje k dnešnému dátumu, nie k dátumu, ktorý si zvolíte.
- Nič sa neodhaduje automaticky a modul neupozorní na dohadné položky, ktoré
  zostali otvorené aj pri ďalšej závierke; filtrujte zoznam podľa stavu
  *Zaúčtované*.
