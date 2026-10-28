---
title: Kontrolní hlášení DPH (DPHKH1)
summary: České kontrolní hlášení (DPHKH1) — oddíly A.1 až B.3 vypočtené z účetnictví s hranicí 10 000 Kč, zkontrolované podle požadavků formuláře a exportované jako XML pro EPO v aktuální struktuře pro jakékoli období.
verified: 19.0.1.10.0
---

## K čemu slouží {#purpose}

Plátce DPH podává vedle přiznání k DPH **kontrolní hlášení**. Uvádí v něm
své daňové doklady — nad 10 000 Kč jednotlivě, do této částky souhrnně —, aby
mohla finanční správa spárovat daň dodavatele s odpočtem odběratele.

Tento modul je česká část společného kontrolního hlášení. Přidává oddíly
formuláře **DPHKH1**, pravidla zařazení dokladů do oddílů, kontroly, které
vyžaduje úřední formulář, a XML šablonu pro EPO. Postup práce — založení
hlášení, výpočet, export, označení jako podaného, opravy — popisuje
[společná příručka](module:l10n_cssk_kv_kh_base#usage).

Vyžaduje českou účtovou osnovu Odoo (`l10n_cz`) a modul
[module:l10n_cz_statutory](module:l10n_cz_statutory), který drží údaje o
plátci pro podání na EPO. Funguje v edici Community i Enterprise.

## Právní rámec {#legal}

Odkazy jsou na zákon č. 235/2004 Sb., o dani z přidané hodnoty.

- **Kdo podává.** Plátce podává kontrolní hlášení za období, ve kterém
  uskutečnil zdanitelné plnění s místem plnění v tuzemsku (nebo přijal
  úplatu, ze které vznikla povinnost přiznat daň), přijal plnění, u kterého
  je povinen přiznat daň sám, nebo uplatňuje nárok na odpočet daně, kterou
  vůči němu uplatnil jiný plátce, případně uskutečnil vybrané operace s
  investičním zlatem — [§ 101c](law:cz/2004/235). V hlášení uvádí
  identifikační a kontaktní údaje, údaje o plněních a úplatách, o uplatnění
  nároku na odpočet a identifikační údaje odběratele nebo dodavatele —
  [§ 101d](law:cz/2004/235).
- **Elektronicky a ve stanovené struktuře.** Kontrolní hlášení se podává
  elektronicky; podání, které nebylo učiněno stanoveným způsobem, ve
  stanoveném formátu nebo ve stanovené struktuře, je neúčinné —
  [§ 101a](law:cz/2004/235).
- **Lhůty.** Právnická osoba podává za kalendářní měsíc, do 25 dnů po jeho
  skončení. Fyzická osoba podává ve lhůtě pro podání daňového přiznání, tedy
  měsíčně nebo čtvrtletně podle svého zdaňovacího období. Lhůty nelze
  prodloužit — [§ 101e](law:cz/2004/235).
- **Opravy.** Před uplynutím lhůty lze podané hlášení nahradit **opravným**
  kontrolním hlášením; k předchozímu se nepřihlíží. Chybu zjištěnou po
  uplynutí lhůty je plátce povinen napravit **následným** kontrolním
  hlášením do 5 pracovních dnů ode dne zjištění —
  [§ 101f](law:cz/2004/235). Následným hlášením se odpovídá i na výzvu
  správce daně ke změně, doplnění nebo potvrzení údajů: do 17 dnů ode dne
  dodání výzvy do datové schránky, jinak do 5 pracovních dnů od jejího
  oznámení — [§ 101g](law:cz/2004/235).
- **Pokuty.** Za opožděné hlášení vzniká pokuta 1 000 Kč, je-li podáno bez
  výzvy, 10 000 Kč, je-li podáno až v náhradní lhůtě po výzvě, 30 000 Kč,
  není-li podáno na výzvu ke změně, doplnění či potvrzení údajů, a 50 000 Kč,
  není-li podáno ani na výzvu k podání; poslední tři se snižují na polovinu u
  fyzické osoby, čtvrtletního plátce a jednočlenné s.r.o., jejímž společníkem
  je fyzická osoba — [§ 101h](law:cz/2004/235). Pokuta nevzniká, dojde-li v
  kalendářním roce k prvnímu prodlení prvního nebo druhého druhu —
  [§ 101j](law:cz/2004/235).

## Formulář {#forms}

Na rozdíl od Slovenska zveřejňuje finanční správa pro kontrolní hlášení
**jedinou** strukturu, soubor `dphkh1_epo2.xsd`, a při změně ho přepíše.
Hlášení za jakékoli období — i následné hlášení za rok 2021 podávané dnes — se
podává v aktuální struktuře. Rozdíly mezi obdobími vyjadřují položky, které
platí jen pro některá období, ne starší formuláře.

Modul proto obsahuje jedinou verzi bez konce platnosti, **Kontrolní hlášení
(aktuální struktura)**, platnou od 1. 1. 2016:

| | |
|---|---|
| Struktura | DPHKH1, verze 03.01.15 ze dne 11. 8. 2026 (zapisuje se jako `verzePis`) |
| XML | obálka EPO `Pisemnost` s vnořeným `DPHKH1` |
| Schéma | `dphkh1_epo2.xsd`, 27. 10. 2026 porovnané bajt po bajtu se zveřejněnou kopií |
| Nejstarší období | 1. 1. 2016 — doklady s dřívějším DUZP patří na jiný formulář EPO (*Výpis z evidence*), který modul nevytváří |

Verze struktury není součástí schématu a nové schéma ověří i starý soubor,
takže změnu zveřejněnou finanční správou modul sám nezjistí. Verze je proto
zapsaná v `data/SCHEMA_VERSION` i s postupem, jak ji ověřit proti zveřejněné
struktuře, a test hlídá, aby `verzePis` šablony tomuto záznamu odpovídal. Při
změně zveřejněné struktury je třeba modul aktualizovat.

## Nastavení {#setup}

Kromě [společného nastavení](module:l10n_cssk_kv_kh_base#setup):

- **Údaje o plátci.** Finanční úřad, územní pracoviště, osoba oprávněná k
  podpisu a osoba, která podání sestavila, se berou z modulu
  [module:l10n_cz_statutory](module:l10n_cz_statutory). Odtud se vyplní
  záhlaví XML (*VetaP*).
- **Daně v režimu přenesení.** Při instalaci modul označí nákupní daně české
  osnovy v režimu přenesení daňové povinnosti podle § 92a (21 % a 12 %).
  Prodejní daň osnovy *0% RC* se rozpozná podle řádku přiznání (ř. 25) a
  ostatní plnění, u kterých daň přiznává příjemce — pořízení a služby z EU,
  služby ze třetích zemí (ř. 12 / 13) — podle DIČ dodavatele a řádku daně;
  žádné z nich označení nepotřebuje.
- **Kód předmětu plnění.** Oddíly A.1 a B.1 vyžadují kód plnění v režimu
  přenesení (zlato, nemovitost, stavební a montážní práce, zboží z přílohy
  č. 5, povolenky na emise a další kódy formuláře). Nastavte ho na produktu,
  pole *Kód předmětu plnění (§92a)* pod kategorií produktu, nebo na dani v
  režimu přenesení, kde se pole zobrazí u označených daní a u prodejní daně
  vykazované na řádku 25 (standardní *0% RC*). Kód z produktu má
  přednost před kódem z daně. Doklad, jehož řádky nesou různé kódy, se uvede
  na jednom řádku za každý kód se stejným evidenčním číslem.
- **DIČ druhé strany.** Oddíly A.1, A.4, B.1 a B.2 identifikují druhou stranu
  podle DIČ; u A.2 rozhoduje evropské DIČ dodavatele o tom, zda jde o
  pořízení z jiného členského státu.

## Oddíly {#sections}

Jak modul plní jednotlivé oddíly. Částky se dělí na základní sazbu (20 % a
víc, `zakl_dane1` / `dan1`), sníženou sazbu (`zakl_dane2` / `dan2`) a druhou
sníženou sazbu 10 % platnou do 31. 12. 2023 (`zakl_dane3` / `dan3`, i pro
pozdější opravy takových plnění) a zapisují se v celých korunách.

| Oddíl | Co do něj patří |
|---|---|
| A.1 | Vydané doklady s prodejní daní v režimu přenesení (§ 92a): DIČ odběratele, evidenční číslo dokladu, DUZP, základ daně (jeden, bez rozlišení sazby), kód předmětu plnění. |
| A.2 | Přijatá plnění, u kterých daň přiznáváte vy (§ 108 odst. 2 a 3): pořízení zboží a služby z jiného členského státu a služby či jiná plnění od dodavatele mimo EU. Stát (podle DIČ: `EL` pro Řecko, `XI` pro Severní Irsko; u dodavatele mimo EU prázdný), DIČ, evidenční číslo dokladu dodavatele, základ a daň. |
| A.4 | Vydané doklady s DPH, jejichž celková částka včetně daně přesahuje 10 000 Kč (v absolutní hodnotě, tedy i velký opravný doklad), **a** jejichž odběratel má české DIČ. Oprava u nedobytné pohledávky se uvádí vždy zde bez ohledu na částku. |
| A.5 | Jeden souhrn všech ostatních vydaných dokladů s DPH — do 10 000 Kč nebo odběrateli bez českého DIČ. |
| B.1 | Přijaté doklady s nákupní daní v režimu přenesení podle § 92a: DIČ dodavatele, evidenční číslo, základ daně, kód předmětu plnění. |
| B.2 | Přijaté doklady s DPH, jejichž celková částka včetně daně přesahuje 10 000 Kč, s evidenčním číslem **dodavatele** (*Reference faktury*). Opravy u nedobytných pohledávek vždy. |
| B.3 | Jeden souhrn všech ostatních přijatých dokladů s DPH. |

Dodavatel z jiného členského státu registrovaný k české DPH, který fakturuje
pod českým DIČ, uskutečňuje tuzemské plnění: rozhoduje DIČ na dokladu, ne
země partnera. Vydaný doklad s nulovou sazbou partnerovi z jiného členského
státu se do hlášení neuvádí (patří do souhrnného hlášení); doklad s českou
DPH je tuzemské plnění a uvede se v A.4/A.5. Dovoz zboží (§ 23) se do
kontrolního hlášení neuvádí vůbec.

Hranice 10 000 Kč se měří na **celém** dokladu včetně daně; řádky bez DPH se
neuvádějí, ale do hranice se započítají. Řádek bez DPH se do A.4/A.5 ani
B.2/B.3 nikdy neuvede.

Uvádí se *DUZP* dokladu, jinak datum faktury. Příznak opravy u nedobytné
pohledávky (`zdph_44`) se bere z pole dokladu *Oprava u nedobytné
pohledávky* (`P`, nebo `A` pro § 44 ve znění do 31. 3. 2019).

Kontrolní součty (*VetaC*) se počítají z oddílů tak, jak je formulář
definuje: A.1 v `pln_rez_pren`, B.1 v `rez_pren23` / `rez_pren5`, celý oddíl
A.2 v `celk_zd_a2` a součty snížené sazby včetně druhé snížené sazby.

**Oprava řádku.** Každou záložku oddílu lze upravit po řádcích: na řádku
zaškrtněte **Override** a opravte základ a daň v základní, snížené či druhé
snížené sazbě. Exportují se opravené údaje a zůstanou zachovány i po novém
výpočtu, na řádku téhož dokladu (a v A.1 / B.1 téhož kódu předmětu plnění).
Oprava, jejíž řádek zmizí, se vypíše v chatteru.

## Druhy podání a opravy {#usage}

Typy hlášení jsou **Řádné** (B), **Opravné** (O, ve formuláři *řádné/opravné*),
**Následné** (N) a **Následné/opravné** (E). Hlášení připravte a exportujte
podle [společné příručky](module:l10n_cssk_kv_kh_base#usage). České
zvláštnosti:

- **Následné** hlášení není rozdílem proti podání, které opravuje: obsahuje
  znovu všechny údaje za období s promítnutím oprav a modul ho tak také
  počítá. Vytvořte ho z podaného hlášení tlačítkem *Opravné / následné*,
  změňte typ na *Následné* a vypočtěte.
- U následného hlášení vyplňte **Důvody zjištěny dne**, nebo — odpovídáte-li
  na výzvu — **Č.j. výzvy** ve tvaru `99999999/99/9999-99999-999999`.
- **Odpověď na výzvu** je rychlá odpověď na výzvu, když se nic nemění:
  *B – Nemám povinnost podat KH* nebo *P – Potvrzuji správnost naposledy
  podaného KH*. Takové podání nese jen záhlaví, žádné oddíly, a vyžaduje č.j.
  výzvy.

Před vytvořením souboru export zastaví a vyjmenuje chybné doklady, pokud:

- řádek v A.1, A.4, B.1 nebo B.2 nemá DIČ druhé strany;
- řádek v A.1, A.2, A.4, B.1 nebo B.2 nemá datum plnění;
- řádek v A.1 nebo B.1 nemá kód předmětu plnění;
- následné hlášení nemá datum zjištění ani č.j. výzvy, nebo rychlá odpověď
  nemá č.j. výzvy.

Odeslání souboru na EPO přímo z Odoo popisuje [module:l10n_cz_epo](module:l10n_cz_epo).

## Omezení {#limitations}

- **Dodavatelé z EU účtující českou DPH.** Přijatý doklad od partnera s DIČ
  z jiného členského státu se uvede v A.2, i když dodavatel účtoval českou
  DPH. Je-li dodavatel registrován v tuzemsku, zaúčtujte doklad na kontakt,
  jehož DIČ je jeho české DIČ, a doklad se uvede v B.2.
- **Pevné hodnoty.** Zvláštní režimy pro cestovní službu a použité zboží
  (`kod_rezim_pl`) se nikdy neuvádějí — každý řádek A.4 se zapíše jako běžné
  plnění — a poměrný nárok na odpočet podle § 75 (`pomer`) se vždy zapíše
  jako *N*.
- Pravidla zařazení jsou nejlepším možným odhadem; zejména číselník kódů
  podle § 92a a opravy u nedobytných pohledávek ještě musí potvrdit český
  účetní. Každé hlášení před podáním zkontrolujte.
