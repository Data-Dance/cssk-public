---
title: SK JCD — dovoz tovaru (colné vyhlásenie)
summary: Colné vyhlásenie pri dovoze tovaru ako účtovný doklad — daň pri dovoze do správnych riadkov priznania, clo do obstarávacej ceny zásob a odpočet až s dovozným dokladom potvrdeným colným orgánom.
verified: 19.0.1.2.0
---

## Na čo slúži {#purpose}

Tovar kúpený mimo EÚ sa prepúšťa do voľného obehu na základe **colného
vyhlásenia** (historicky *JCD*, jednotný colný doklad). Jeden dovoz rozdelí v
účtovníctve tri veci:

1. **Clo a colné poplatky**, ktoré patria do obstarávacej ceny tovaru;
2. **Daň pri dovoze**, ktorá musí prísť do správnych riadkov daňového
   priznania;
3. **Samotný colný doklad**, bez ktorého sa daň pri dovoze nesmie odpočítať.

Modul eviduje colné vyhlásenie ako jeden doklad a zaúčtuje z neho všetky tri.
Používa dovozné dane zo slovenskej účtovej osnovy Odoo a vykazovanie necháva na
daňové priznanie, takže nič z priznania tu nie je naprogramované nanovo.

## Právny rámec {#legal}

Ak nie je uvedené inak, odkazy sú na [zákon o DPH](law:sk/2004/222).

- **Základ dane.** Podľa [§ 24](law:sk/2004/222#paragraf-24) je základom
  dane colná hodnota tovaru, a ak v nej nie sú zahrnuté, aj dane, clá a iné
  platby splatné pri dovoze (okrem dane, ktorá sa má vymerať) a súvisiace
  náklady, napr. provízia, balenie, preprava a poistenie do prvého miesta
  určenia v tuzemsku.
- **Právo na odpočet.**
  [§ 49 ods. 2 písm. d)](law:sk/2004/222#paragraf-49.odsek-2.pismeno-d):
  platiteľ môže odpočítať daň, ktorú uplatnil pri dovoze tovaru alebo
  zaplatil colnému orgánu.
- **Podmienka dokladu.** Právo možno uplatniť, ak platiteľ *„má dovozný doklad
  potvrdený colným orgánom, v ktorom je platiteľ uvedený ako príjemca alebo
  dovozca“* —
  [§ 51 ods. 1 písm. d)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-d).
  [§ 51 ods. 2](law:sk/2004/222#paragraf-51.odsek-2) určuje lehotu: najskôr v
  zdaňovacom období, v ktorom právo vzniklo, a najneskôr v poslednom
  zdaňovacom období toho kalendárneho roka, ak má platiteľ doklad do uplynutia
  lehoty na podanie priznania.
- **Samozdanenie pri dovoze.** Podľa
  [§ 84a ods. 2 a 3](law:sk/2004/222#paragraf-84a.odsek-2) platiteľ so
  sídlom, miestom podnikania alebo prevádzkarňou v tuzemsku, s IČ DPH a s
  účinným povolením **statusu schváleného hospodárskeho subjektu** (AEO)
  daň pri dovoze sám vypočíta a uvedie v daňovom priznaní; colný úrad ju
  nevyrubuje. Rozhoduje status platiteľa, nie jednotlivá zásielka. Podľa
  [§ 85l](law:sk/2004/222#paragraf-85l) sa postup prvýkrát použije na dovoz,
  pri ktorom daňová povinnosť vznikla po 30. 6. 2025, a podľa
  [§ 21 ods. 2](law:sk/2004/222#paragraf-21.odsek-2) vzniká dňom prijatia
  colného vyhlásenia.
- **Clo v obstarávacej cene.** Obstarávacia cena zahŕňa aj náklady súvisiace
  s obstaraním —
  [§ 25 ods. 6 písm. a) zákona o účtovníctve](law:sk/2002/431#paragraf-25.odsek-6.pismeno-a).
- Samotné colné konanie — colné vyhlásenie a jeho MRN — upravuje
  [Colný kódex Únie](law:eu/reg/2013/952).

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Dovoz tovaru (JCD)**,
zobrazený len pri spoločnostiach so slovenskou účtovou osnovou:

| Nastavenie | Predvolené | Účel |
|---|---|---|
| Zúčtovací účet (*Import clearing account*) | 379000 | Nesie pomyselný základ dane pri dovoze (pozri [Účtovanie](#posting)). Zmeňte ho, ak účtovník uprednostňuje iný účet. |
| Produkt cla (*Customs duty product*) | *Clo (colný poplatok)* | Služobný produkt, cez ktorý sa clo pripočíta k obstarávacej cene zásob. Musí mať nákladový účet, na produkte alebo jeho kategórii. |
| Predvolený režim dane | daň zaplatená colnému orgánu | Režim, s ktorým nové colné vyhlásenie začína. Samozdanenie zvoľte, len ak spoločnosť spĺňa podmienky § 84a. |

Účet a produkt sa pri inštalácii modulu vyplnia automaticky pre každú
spoločnosť so slovenskou osnovou, ak ešte nie sú nastavené.

Pred prvým dovozom skontrolujte:

- **Zásoby sa oceňujú metódou FIFO alebo váženým priemerom.** Odoo uplatní
  dodatočné náklady len pri takých kategóriách produktov; pri štandardnej cene
  clo do obstarávacej ceny nepripočíta.
- **Historické sadzby (voliteľne).** S modulom
  [module:l10n_cssk_vat_return_base](module:l10n_cssk_vat_return_base) sa
  colné vyhlásenie s dátumom pred zmenou sadzby zdaní sadzbou platnou k jeho
  dátumu — napríklad 20 % namiesto 23 % pri dovoze v základnej sadzbe pred
  1. 1. 2025. Bez neho sa použije aktuálna sadzba a staršie doklady musíte
  skontrolovať sami.

## Zadanie colného vyhlásenia {#usage}

*Účtovníctvo → Účtovníctvo → Colné vyhlásenia (JCD)*, potom *Nové*.

1. **Colné vyhlásenie.** Dátum prijatia, **MRN** potvrdeného colného
   vyhlásenia a colný úrad ako partner, voči ktorému vzniká záväzok.
2. **Hodnoty.** *Colná hodnota*, *Clo* a *Iné colné poplatky* z colného
   vyhlásenia.
3. **Daň pri dovoze.** Režim, sadzbové pásmo (23 %, 19 % alebo 5 %,
   pomenované podľa dnešných sadzieb) a základ dane. Základ sa predvyplní ako
   colná hodnota + clo + iné poplatky; **upravte ho**, ak základ v colnom
   vyhlásení zahŕňa viac, napríklad prepravu do prvého miesta určenia.
   *Použitá sadzba* ukazuje sadzbu, ktorá sa k dátumu dokladu skutočne
   zaúčtuje.
4. **Väzby.** Faktúry zahraničného dodávateľa a príjemky, ku ktorým clo patrí.
5. **Priložte dovozný doklad potvrdený colným orgánom** v chatteri.

Kým chýba MRN alebo príloha, formulár zobrazuje upozornenie a **zaúčtovanie
odmietne** — to je vynútená podmienka § 51 ods. 1 písm. d). Rovnako sa
odmietne samozdanenie pri colnom vyhlásení prijatom pred 1. 7. 2025.

Potom kliknite na **Zaúčtovať**.

## Čo zaúčtovanie vytvorí {#posting}

- **Faktúru od colného úradu** v prvom nákupnom denníku, s dátumom colného
  vyhlásenia a s MRN ako referenciou:
  - základ dane dvakrát na zúčtovacom účte — raz s daňou pri dovoze, raz
    záporne bez nej — takže pomyselný základ sa vynuluje a reálna zostane len
    daň;
  - clo na nákladovom účte produktu cla;
  - iné poplatky na predvolenom nákladovom účte spoločnosti.
- **Dodatočné náklady** (*Rozpustenie cla*) na prepojené príjemky, s
  rozdelením cla podľa aktuálnej obstarávacej ceny, hneď **potvrdené**, takže sa
  clo pripočíta k hodnote zásob. Riadok nákladov ide v prospech toho istého
  nákladového účtu, na ktorý faktúra účtovala clo, takže sa clo nezapočíta
  dvakrát. Ak ich Odoo uplatniť nevie — napríklad pri produkte so štandardnou
  cenou — colné vyhlásenie sa nezaúčtuje vôbec, namiesto toho, aby sa
  zaúčtovala len faktúra.

Faktúru uhraďte ako každú inú. Zaúčtované colné vyhlásenie sa z formulára
zrušiť nedá; na opravu faktúru stornujte dobropisom a colné vyhlásenie zadajte
znova.

## V daňovom priznaní {#vat-return}

Vykazuje modul [module:l10n_sk_vat_return](module:l10n_sk_vat_return) podľa
daňových značiek slovenskej účtovej osnovy Odoo:

| Režim | Riadky priznania |
|---|---|
| Daň zaplatená colnému orgánu | len odpočet: r. 22 (19 %), r. 22a (5 %), r. 23 (23 %); základ sa nevykazuje |
| Samozdanenie pri dovoze (§ 84a ods. 3) | základ r. 11c – 11e, daň r. 12c – 12e, odpočet r. 23a – 23c |

## Obmedzenia {#limitations}

- Clo sa pripočíta k obstarávacej cene len pri zásobách oceňovaných FIFO
  alebo váženým priemerom a len pri prepojených príjemkách. *Iné colné
  poplatky* idú do nákladov, do obstarávacej ceny nie.
- Formulár nekontroluje, či spoločnosť spĺňa podmienky samozdanenia podľa
  § 84a (status AEO, sídlo); len odmietne tento režim pred 1. 7. 2025.
- Odpočet sa zaúčtuje k dátumu colného vyhlásenia. Lehotu podľa § 51 ods. 2
  pre doklad, ktorý príde neskôr, modul nesleduje.
- Ide len o účtovný doklad: colnému orgánu sa nič nepodáva.
- Predvolený základ dane a priradenie účtov sú východiskom a treba ich
  odsúhlasiť s účtovníkom.
