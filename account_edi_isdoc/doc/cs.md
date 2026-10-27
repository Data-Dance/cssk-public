---
title: Elektronické faktury ISDOC
summary: Odesílá faktury a opravné daňové doklady odběratelům jako soubory ISDOC 6.0.2, vložené i do PDF faktury, a z přijatých souborů ISDOC vytváří koncepty přijatých faktur.
verified: 19.0.1.4.0
---

## K čemu slouží {#purpose}

**ISDOC** (*Information System Document*) je český národní formát
elektronické faktury, který čte většina tuzemských účetních programů. Modul
přidává verzi **6.0.2** do elektronické fakturace Odoo vedle Peppol BIS 3 a
dalších formátů UBL/CII:

- **odesílání** — faktura nebo opravný daňový doklad pro odběratele, který má
  nastaven ISDOC, dostane soubor `.isdoc` a ISDOC se vloží i do PDF faktury
  ([odesílání](#export));
- **příjem** — soubor ISDOC nahraný nebo zaslaný e-mailem do přijatých faktur
  se stane konceptem faktury: samostatný `.isdoc`, archiv `.isdocx` nebo PDF s
  vloženým ISDOC ([příjem](#import)).

Staví na modulu Odoo `account_edi_ubl_cii`, takže používá standardní dialog
*Odeslat* a standardní nahrávání přijatých faktur. Kvůli tuzemským číslům
bankovních účtů potřebuje [module:l10n_cz_base](module:l10n_cz_base). Modul
nemá český překlad; jeho texty se zobrazují anglicky.

Tři doplňky se instalují samy, je-li přítomen jejich protějšek:

| Doplněk | S modulem | Přidává |
|---|---|---|
| [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) | Prodej | zálohovou fakturu ISDOC (typ dokladu 4) z prodejní objednávky — [zálohové faktury](#proforma) |
| [module:account_edi_isdoc_sale_advance](module:account_edi_isdoc_sale_advance) | zálohové faktury (prodej) | daňové doklady k přijaté platbě jako typy 5 a 6 a odečtené zálohy na vyúčtovací faktuře — [zálohy](#advances) |
| [module:account_edi_isdoc_purchase_advance](module:account_edi_isdoc_purchase_advance) | přijaté zálohové faktury | importované typy 4, 5 a 6 jdou do evidence přijatých záloh — [přijaté zálohy](#received-advances) |

## Právní rámec {#legal}

ISDOC je oborový standard, ne zákonem předepsaný formát. Zákon vyžaduje
souhlas odběratele s elektronickým daňovým dokladem: daňový doklad má
elektronickou podobu, je-li vystaven a obdržen elektronicky, a s jeho
použitím musí souhlasit osoba, pro kterou se plnění uskutečňuje —
[§ 26 odst. 3 zákona o DPH](law:cz/2004/235). Soubor ISDOC nese náležitosti
podle [§ 29](law:cz/2004/235) včetně dne uskutečnění zdanitelného plnění
(DUZP), který ISDOC nazývá *TaxPointDate*.

ISDOC není žádnou ze syntaxí evropské normy EN 16931. Nesplňuje proto
slovenskou povinnost elektronické fakturace od 1. ledna 2027, která tuto
strukturu vyžaduje; pro slovenské odběratele použijte
[Peppol](module:edi_base_peppol#legal).

## Nastavení {#setup}

1. **Čeští odběratelé dostávají ISDOC automaticky.** Český kontakt bez
   vlastního **Formátu e-faktury** dostane ISDOC, pokud o něm není známo, že je
   v síti Peppol: našla ho kontrola Peppol v Odoo, nebo má jako způsob odeslání
   Peppol. Pak dostane Peppol BIS 3. Jinou volbu nastavíte u kontaktu: záložka
   *Fakturace*, skupina *Zákaznické faktury*, **Formát e-faktury** (zobrazuje se
   jen v **režimu vývojáře**). Odběratel mimo Českou republiku dostane ISDOC,
   jen když ho tam nastavíte.
2. **Vaše společnost i odběratel potřebují** název, ulici, město, PSČ, zemi a
   **IČO** (*Company ID*) nebo **DIČ** (*Tax ID*). Export vypíše, co chybí.
3. **Bankovní účet.** Platební údaje se zapíší jen tehdy, má-li faktura
   bankovní účet (*Banka příjemce*); účet se zapíše v tuzemském tvaru (číslo a
   kód banky) i jako IBAN.
4. **Platební symboly.** S modulem
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols) se do
   souboru zapíše variabilní, konstantní a specifický symbol faktury.

## Odesílání ISDOC {#export}

Fakturu odešlete obvyklým dialogem **Odeslat**. Pro odběratele s nastaveným
ISDOC Odoo vytvoří soubor `INV_2026_00042.isdoc`, připojí ho k faktuře i k
e-mailu a vloží ho do PDF faktury, které převede do PDF/A-3 — v této podobě
putuje PDF a jeho ISDOC jako jeden soubor. Pokud převod do PDF/A selže, ISDOC
je přesto vložen. Jako u každé e-faktury v Odoo se soubor vytvoří jednou a
při dalším odeslání se použije znovu.

**Archiv ISDOCX.** Na zaúčtované faktuře nebo opravném dokladu odběrateli
stáhne **Akce → Download ISDOCX** soubor `INV_2026_00042.isdocx`: ZIP s
ISDOC, jeho manifestem a PDF faktury — třetí podoba, kterou ISDOC definuje.
Ponechá se jako příloha faktury a při každém stažení se nahradí.

Co soubor obsahuje:

| ISDOC | Z Odoo |
|---|---|
| DocumentType | **1** faktura, **2** opravný daňový doklad (5 a 6 s doplňkem [záloh](#advances)) |
| ID, UUID | číslo faktury; UUID vytvořené při prvním exportu a uchované, aby si doklad zachoval identitu |
| IssueDate, TaxPointDate | datum faktury; **DUZP**, a pokud chybí, datum faktury |
| VATApplicable | zda faktura obsahuje DPH |
| Dodavatel a odběratel | název, IČO, DIČ, adresa s číslem domu odděleným od ulice, telefon, e-mail |
| Řádky faktury | popis, množství a jednotka (`ks`, pokud chybí), jednotková cena a částka bez DPH a s DPH, sazba DPH, čárový kód a interní reference produktu |
| OriginalDocumentReference | u opravného dokladu: číslo, datum a UUID opravované faktury |
| TaxTotal, LegalMonetaryTotal | rekapitulace DPH podle sazeb a součty — DPH, kterou faktura zaúčtovala, zaokrouhlená jako na faktuře, takže rekapitulace odpovídá částce k úhradě |
| Zálohy | zálohy odečtené na vyúčtovací faktuře včetně již uplatněných částek ([zálohy](#advances)) |
| PaymentMeans | převodem: datum splatnosti, číslo účtu, kód banky, IBAN, BIC, VS, KS, SS |

Faktura musí být v **měně společnosti**; fakturu v cizí měně ISDOC odmítne.

## Příjem ISDOC {#import}

Soubor nahrajte do přijatých faktur, přetáhněte ho na seznam nebo ho pošlete
na e-mailový alias nákupního deníku. Přijme se samostatný soubor `.isdoc` (i
když ho odesílatel označí jako obecný typ souboru), archiv `.isdocx` — jeho
PDF se k faktuře také připojí — a PDF s vloženým ISDOC. Čtou se i soubory
starších verzí ISDOC.

Koncept faktury dostane:

- **dodavatele** — nalezeného nejprve podle **IČO** (pokud mu neodporuje DIČ
  v souboru), pak podle DIČ, názvu, e-mailu nebo telefonu, nebo nově
  založeného, má-li soubor název a DIČ; takto založený dodavatel dostane i
  IČO;
- **Datum přijaté faktury**, **DUZP** (podle dodavatele), **Datum
  splatnosti**;
- **Referenci faktury** — číslo faktury dodavatele — a UUID dokladu;
- **variabilní symbol** jako platební referenci a v poli VS, k tomu konstantní
  a specifický symbol, očištěné na číslice;
- **bankovní účet** dodavatele převedený na IBAN a doplněný k dodavateli;
- **řádky** s produktem nalezeným podle názvu, interní reference nebo
  čárového kódu, s daněmi DPH podle sazby a se slevou dopočtenou tam, kde se
  částka řádku liší od ceny × množství. Řádek v **režimu přenesení daňové
  povinnosti** (*LocalReverseCharge*, § 92a ZDPH) dostane nákupní daň s
  přenesením z účtové osnovy při své sazbě (*21% RC*, *12% RC*) nebo daň
  označenou jako přenesení — nikdy běžnou sazbu, která by účtovala DPH, kterou
  dodavatel neúčtoval. Není-li taková daň, řádek zůstane bez daně a historie
  faktury to uvede;
- odečtené zálohy jako záporné řádky „Advance payment …“ a zaokrouhlení na
  celé koruny jako řádek „Rounding“, aby součet faktury odpovídal částce k
  úhradě.

Typy dokladu 2 a 6 se stanou přijatými opravnými doklady, všechny ostatní
přijatými fakturami. Pole
[Deklarované období DPH](module:l10n_cssk_core#vat-period-declared) zůstává
záměrně prázdné: jde o období, kdy odpočet uplatníte vy, a to doklad
dodavatele vědět nemůže. Faktura je koncept; před zaúčtováním ji
zkontrolujte.

## Zálohové faktury z prodejních objednávek {#proforma}

Doplněk [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) umí
zapsat prodejní objednávku jako **zálohovou fakturu** ISDOC, typ dokladu 4
(výzva k platbě zálohy): číslo objednávky jako ID, datum objednávky jako
datum vystavení, řádky objednávky, součty a první bankovní účet společnosti s
číslicemi čísla objednávky jako variabilním symbolem a platností nabídky jako
datem splatnosti. Na objednávce ji **Akce → Download ISDOC Proforma**
stáhne a ponechá jako přílohu objednávky.

Přijatou zálohovou fakturu čte tento modul jako každý ISDOC — jako koncept
přijaté faktury — pokud není nainstalován doplněk
[přijatých záloh](#received-advances).

## Zálohové faktury a daňové doklady k platbě {#advances}

S doplňkem [module:account_edi_isdoc_sale_advance](module:account_edi_isdoc_sale_advance)
se český řetěz záloh modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) mapuje
na ISDOC takto:

| Doklad v Odoo | ISDOC |
|---|---|
| [daňový doklad k přijaté platbě](module:sale_order_advance_invoice#tax-document) | **5**, jeho opravný doklad **6** |
| vyúčtovací faktura s odečtenými zálohami ([vyúčtování](module:sale_order_advance_invoice#final-invoice)) | **1**; každý odpočet jako zdaněná (nebo nezdaněná) záloha s číslem daňového dokladu k platbě a variabilním symbolem a s již uplatněnou DPH po sazbách |

Samotná zálohová faktura je prodejní objednávka a exportuje se jako
[zálohová faktura ISDOC](#proforma). Zálohy Odoo (*down payments*) vykazuje
jako zálohy už základní modul.

## Přijaté zálohové faktury {#received-advances}

S doplňkem [module:account_edi_isdoc_purchase_advance](module:account_edi_isdoc_purchase_advance)
a modulem [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
jdou importované zálohové doklady do evidence přijatých záloh:

- **Typ 4 — zálohová faktura.** Vznikne **přijatá záloha** pro dodavatele na
  hrubou částku dokladu, s číslem dodavatele jako referencí dodavatele a s
  produktem *Advance payment (imported)* bez daně. Koncept faktury, který
  import vytvořil, zůstane, propojený se zálohou a s poznámkou, že se **nesmí
  zaúčtovat**: zálohu zaplaťte a sledujte, koncept pak smažte. Opakovaný
  import téže zálohové faktury (stejný dodavatel a číslo dodavatele) druhou
  zálohu nevytvoří; nový koncept se propojí s první.
- **Typy 5 a 6 — daňový doklad dodavatele k vaší platbě** a jeho opravný
  doklad. Faktura přejde do deníku *Received Advance Tax Documents Journal*,
  DUZP převezme ze souboru, řádky se přeúčtují na *Paid Advances Account*
  (u dlouhodobé zálohy na dlouhodobý účet) a závazek na *Paid Advances
  Clearing Account*. Propojí se s otevřenou přijatou zálohou dodavatele
  nalezenou v tomto pořadí: podle odkazu na objednávku v souboru, podle
  variabilního symbolu, nebo jako jediná záloha čekající na daňový doklad,
  jejíž zaplacená částka odpovídá částce dokladu. Neodpovídá-li žádná nebo
  odpovídá více, historie to uvede — propojte ji ručně.

Co následuje, popisuje
[daňový doklad dodavatele](module:purchase_order_advance_invoice#tax-document).

## Omezení {#limitations}

- **Formát e-faktury** je vidět jen v režimu vývojáře. Zda je český odběratel
  v síti Peppol, se pozná jen z nainstalovaných modulů Peppol; dosud
  neověřený dostane ISDOC.
- Faktury v cizí měně nelze exportovat. Při importu se použijí částky v
  tuzemské měně.
- Opravné daňové doklady typu vrubopis (typ 3) a zjednodušené daňové doklady
  (typ 7) se importují jako běžné faktury.
- Export prvek přenesení daňové povinnosti nikdy nezapisuje: faktura v režimu
  přenesení odejde jako plnění bez DPH a bez kódu předmětu plnění.
- Dodavatel bez DIČ, kterého nenajde IČO, název, e-mail ani telefon, se
  nezaloží; vyberte ho na faktuře.
