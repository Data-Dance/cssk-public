---
title: Elektronické faktúry ISDOC (český formát)
summary: Odosiela faktúry a dobropisy odberateľom ako súbory ISDOC 6.0.2, vložené aj do PDF faktúry, a z prijatých súborov ISDOC vytvára koncepty dodávateľských faktúr.
verified: 19.0.1.4.0
---

## Na čo slúži {#purpose}

**ISDOC** (*Information System Document*) je český národný formát
elektronickej faktúry, ktorý číta väčšina českých účtovných programov a
používajú ho aj slovenské firmy obchodujúce s českými partnermi. Modul
pridáva verziu **6.0.2** do elektronickej fakturácie Odoo vedľa Peppol BIS 3
a ďalších formátov UBL/CII:

- **odosielanie** — faktúra alebo dobropis pre odberateľa s nastaveným
  formátom ISDOC dostane súbor `.isdoc` a ISDOC sa vloží aj do PDF faktúry
  ([odosielanie](#export));
- **prijímanie** — súbor ISDOC nahratý alebo poslaný e-mailom do
  dodávateľských faktúr sa stane konceptom faktúry: samostatný `.isdoc`,
  archív `.isdocx` alebo PDF s vloženým ISDOC ([prijímanie](#import)).

Stavia na module Odoo `account_edi_ubl_cii`, takže používa štandardný dialóg
*Poslať* a štandardné nahrávanie dodávateľských faktúr. Kvôli českým číslam
bankových účtov potrebuje [module:l10n_cz_base](module:l10n_cz_base). Modul
nemá slovenský preklad; jeho texty sa zobrazujú po anglicky.

Tri doplnky sa inštalujú samy, keď je prítomný ich náprotivok:

| Doplnok | S modulom | Pridáva |
|---|---|---|
| [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) | Predaj | zálohovú faktúru ISDOC (typ dokladu 4) z predajnej objednávky — [zálohové faktúry](#proforma) |
| [module:account_edi_isdoc_sale_advance](module:account_edi_isdoc_sale_advance) | zálohové faktúry (predaj) | daňové doklady k prijatej platbe ako typy 5 a 6 a odpočítané zálohy na konečnej faktúre — [zálohy](#advances) |
| [module:account_edi_isdoc_purchase_advance](module:account_edi_isdoc_purchase_advance) | prijaté zálohové faktúry | importované typy 4, 5 a 6 idú do evidencie prijatých záloh — [prijaté zálohy](#received-advances) |

## Právny rámec {#legal}

ISDOC je odvetvový štandard, nie zákonom predpísaný formát. Český zákon o
DPH vyžaduje súhlas odberateľa s elektronickým daňovým dokladom
([§ 26 odst. 3](law:cz/2004/235)); súbor ISDOC nesie náležitosti podľa
[§ 29](law:cz/2004/235) vrátane dňa uskutočnenia plnenia (DUZP), ktorý ISDOC
nazýva *TaxPointDate*.

Na Slovensku možno do 31. decembra 2026 vydať elektronickú faktúru len so
súhlasom príjemcu
([§ 71 ods. 1 písm. b) zákona o DPH](law:sk/2004/222#paragraf-71.odsek-1.pismeno-b)).
ISDOC však nie je žiadnou zo syntaxí európskej normy EN 16931, a preto
**nespĺňa** slovenskú povinnosť elektronickej fakturácie od 1. januára 2027,
ktorá túto štruktúru vyžaduje; pre slovenských odberateľov použite
[Peppol](module:edi_base_peppol#legal).

## Nastavenie {#setup}

1. **Českí odberatelia dostávajú ISDOC automaticky.** Český kontakt bez
   vlastného **Formátu e-faktúry** dostane ISDOC, ak o ňom nie je známe, že je
   v sieti Peppol: našla ho kontrola Peppol v Odoo, alebo má ako spôsob
   odoslania Peppol. Vtedy dostane Peppol BIS 3. Inú voľbu nastavíte pri
   kontakte: záložka *Fakturácia*, skupina *Zákaznícke faktúry*, **Formát
   e-faktúry** (zobrazuje sa len v **režime vývojára**). Slovenský a iný
   odberateľ dostane ISDOC, len keď ho tam nastavíte.
2. **Vaša spoločnosť aj odberateľ potrebujú** názov, ulicu, mesto, PSČ,
   krajinu a **IČO** (*Company ID*) alebo **DIČ / IČ DPH** (*Tax ID*). Export
   vypíše, čo chýba.
3. **Bankový účet.** Platobné údaje sa zapíšu len vtedy, keď má faktúra
   bankový účet (*Banka príjemcu*); účet sa zapíše v českom tvare (číslo a
   kód banky) aj ako IBAN.
4. **Platobné symboly.** S modulom
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols) sa do
   súboru zapíše variabilný, konštantný a špecifický symbol faktúry.

## Odosielanie ISDOC {#export}

Faktúru odošlite obvyklým dialógom **Poslať**. Pre odberateľa s nastaveným
ISDOC vytvorí Odoo súbor `INV_2026_00042.isdoc`, priloží ho k faktúre aj k
e-mailu a vloží ho do PDF faktúry, ktoré prevedie do PDF/A-3 — v tejto
podobe putuje PDF a jeho ISDOC ako jeden súbor. Ak prevod do PDF/A zlyhá,
ISDOC je aj tak vložený. Ako pri každej e-faktúre v Odoo sa súbor vytvorí raz
a pri ďalšom odoslaní sa použije znova.

**Archív ISDOCX.** Na zaúčtovanej faktúre alebo dobropise odberateľovi
stiahne **Akcia → Download ISDOCX** súbor `INV_2026_00042.isdocx`: ZIP s
ISDOC, jeho manifestom a PDF faktúry — tretia podoba, ktorú ISDOC definuje.
Ponechá sa ako príloha faktúry a pri každom stiahnutí sa nahradí.

Čo súbor obsahuje:

| ISDOC | Z Odoo |
|---|---|
| DocumentType | **1** faktúra, **2** dobropis (5 a 6 s doplnkom [záloh](#advances)) |
| ID, UUID | číslo faktúry; UUID vytvorené pri prvom exporte a uchované, aby si doklad zachoval identitu |
| IssueDate, TaxPointDate | dátum faktúry; **dátum zdaniteľného plnenia**, a ak chýba, dátum faktúry |
| VATApplicable | či faktúra obsahuje DPH |
| Dodávateľ a odberateľ | názov, IČO, DIČ, adresa s číslom domu oddeleným od ulice, telefón, e-mail |
| Riadky faktúry | popis, množstvo a jednotka (`ks`, ak chýba), jednotková cena a suma bez DPH a s DPH, sadzba DPH, čiarový kód a interná referencia produktu |
| OriginalDocumentReference | pri dobropise: číslo, dátum a UUID opravovanej faktúry |
| TaxTotal, LegalMonetaryTotal | rekapitulácia DPH podľa sadzieb a súčty — DPH, ktorú faktúra zaúčtovala, zaokrúhlená ako na faktúre, takže rekapitulácia sedí so sumou na úhradu |
| Zálohy | zálohy odpočítané na konečnej faktúre vrátane už uplatnených súm ([zálohy](#advances)) |
| PaymentMeans | prevodom: dátum splatnosti, číslo účtu, kód banky, IBAN, BIC, VS, KS, ŠS |

Faktúra musí byť v **mene spoločnosti**; faktúru v cudzej mene ISDOC odmietne.

## Prijímanie ISDOC {#import}

Súbor nahrajte do dodávateľských faktúr, presuňte ho na zoznam alebo ho
pošlite na e-mailový alias nákupného denníka. Prijme sa samostatný súbor
`.isdoc` (aj keď ho odosielateľ označí ako všeobecný typ súboru), archív
`.isdocx` — jeho PDF sa k faktúre tiež priloží — a PDF s vloženým ISDOC.
Čítajú sa aj súbory starších verzií ISDOC.

Koncept faktúry dostane:

- **dodávateľa** — nájdeného najprv podľa **IČO** (ak mu neodporuje DIČ v
  súbore), potom podľa DIČ, názvu, e-mailu alebo telefónu, alebo novo
  založeného, ak súbor obsahuje názov a DIČ; takto založený dodávateľ dostane
  aj IČO;
- **Dátum vystavenia**, **dátum zdaniteľného plnenia** (podľa dodávateľa),
  **Dátum splatnosti**;
- **Referenciu faktúry** — číslo faktúry dodávateľa — a UUID dokladu;
- **variabilný symbol** ako referenciu platby a v poli VS, k tomu konštantný
  a špecifický symbol, očistené na číslice;
- **bankový účet** dodávateľa prevedený na IBAN a doplnený k dodávateľovi;
- **riadky** s produktom nájdeným podľa názvu, internej referencie alebo
  čiarového kódu, s daňami DPH podľa sadzby a so zľavou dopočítanou tam, kde
  sa suma riadku líši od ceny × množstva. Riadok v **tuzemskom režime
  prenesenia daňovej povinnosti** (*LocalReverseCharge*, § 92a českého zákona
  o DPH) dostane nákupnú daň s prenesením z účtovej osnovy pri svojej sadzbe
  (*21% RC*, *12% RC*) alebo daň označenú ako prenesenie — nikdy bežnú sadzbu,
  ktorá by účtovala DPH, ktorú dodávateľ neúčtoval. Ak taká daň nie je,
  riadok zostane bez dane a história faktúry to uvedie;
- odpočítané zálohy ako záporné riadky „Advance payment …“ a zaokrúhlenie na
  celé koruny ako riadok „Rounding“, aby súčet faktúry zodpovedal sume na
  úhradu.

Typy dokladu 2 a 6 sa stanú dodávateľskými dobropismi, všetky ostatné
dodávateľskými faktúrami. Pole
[Deklarované obdobie DPH](module:l10n_cssk_core#vat-period-declared) zostáva
zámerne prázdne: ide o obdobie, keď odpočet uplatníte vy, a to doklad
dodávateľa vedieť nemôže. Faktúra je koncept; pred zaúčtovaním ju
skontrolujte.

## Zálohové faktúry z predajných objednávok {#proforma}

Doplnok [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) vie
zapísať predajnú objednávku ako **zálohovú faktúru** ISDOC, typ dokladu 4
(výzva na zaplatenie zálohy): číslo objednávky ako ID, dátum objednávky ako
dátum vystavenia, riadky objednávky, súčty a prvý bankový účet spoločnosti s
číslicami čísla objednávky ako variabilným symbolom a platnosťou ponuky ako
dátumom splatnosti. Na objednávke ju **Akcia → Download ISDOC Proforma**
stiahne a ponechá ako prílohu objednávky.

Prijatú zálohovú faktúru číta tento modul ako každý ISDOC — ako koncept
dodávateľskej faktúry — ak nie je nainštalovaný doplnok
[prijatých záloh](#received-advances).

## Zálohové faktúry a daňové doklady k platbe {#advances}

S doplnkom [module:account_edi_isdoc_sale_advance](module:account_edi_isdoc_sale_advance)
sa reťaz záloh modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) mapuje
na ISDOC takto:

| Doklad v Odoo | ISDOC |
|---|---|
| [daňový doklad k prijatej platbe](module:sale_order_advance_invoice#tax-document) | **5**, jeho dobropis **6** |
| konečná faktúra s odpočítanými zálohami ([vyúčtovanie](module:sale_order_advance_invoice#final-invoice)) | **1**; každý odpočet ako zdanená (alebo nezdanená) záloha s číslom daňového dokladu k platbe a variabilným symbolom a s už uplatnenou DPH po sadzbách |

Samotná zálohová faktúra je predajná objednávka a exportuje sa ako
[zálohová faktúra ISDOC](#proforma). Zálohy Odoo (*down payments*) vykazuje
ako zálohy už základný modul.

## Prijaté zálohové faktúry {#received-advances}

S doplnkom [module:account_edi_isdoc_purchase_advance](module:account_edi_isdoc_purchase_advance)
a modulom [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
idú importované zálohové doklady do evidencie prijatých záloh:

- **Typ 4 — zálohová faktúra.** Vznikne **prijatá záloha** pre dodávateľa na
  hrubú sumu dokladu, s číslom dodávateľa ako referenciou dodávateľa a s
  produktom *Advance payment (imported)* bez dane. Koncept faktúry, ktorý
  import vytvoril, zostane, prepojený so zálohou a s poznámkou, že sa **nesmie
  zaúčtovať**: zálohu zaplaťte a sledujte, koncept potom zmažte. Opakovaný
  import tej istej zálohovej faktúry (rovnaký dodávateľ a číslo dodávateľa)
  druhú zálohu nevytvorí; nový koncept sa prepojí s prvou.
- **Typy 5 a 6 — daňový doklad dodávateľa k vašej platbe** a jeho dobropis.
  Faktúra prejde do denníka *Received Advance Tax Documents Journal*, dátum
  zdaniteľného plnenia prevezme zo súboru, riadky sa preúčtujú na *Paid
  Advances Account* (pri dlhodobej zálohe na dlhodobý účet) a záväzok na
  *Paid Advances Clearing Account*. Prepojí sa s otvorenou prijatou zálohou
  dodávateľa nájdenou v tomto poradí: podľa odkazu na objednávku v súbore,
  podľa variabilného symbolu, alebo ako jediná záloha čakajúca na daňový
  doklad, ktorej zaplatená suma sa rovná sume dokladu. Ak nezodpovedá žiadna
  alebo viac, história to uvedie — prepojte ju ručne.

Čo nasleduje, opisuje
[daňový doklad dodávateľa](module:purchase_order_advance_invoice#tax-document).

## Obmedzenia {#limitations}

- **Formát e-faktúry** je viditeľný len v režime vývojára. Či je český
  odberateľ v sieti Peppol, sa pozná len z nainštalovaných modulov Peppol;
  zatiaľ neoverený dostane ISDOC.
- Faktúry v cudzej mene nemožno exportovať. Pri importe sa použijú sumy v
  domácej mene dokladu.
- Opravné doklady typu ťarchopis (typ 3) a zjednodušené faktúry (typ 7) sa
  importujú ako bežné faktúry.
- Export prvok tuzemského prenesenia daňovej povinnosti nikdy nezapisuje:
  faktúra s prenesením odíde ako plnenie bez DPH a bez kódu predmetu plnenia.
- Dodávateľ bez DIČ, ktorého nenájde IČO, názov, e-mail ani telefón, sa
  nezaloží; vyberte ho na faktúre.
