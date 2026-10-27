---
title: Intrastat CZ (InstatOnline CSV) — Community
summary: Měsíční výkaz pro Intrastat vytvořený na modulu OCA jako soubor CSV, který přijímá portál InstatOnline celní správy.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Podnik, jehož obchod se zbožím s ostatními členskými státy EU dosáhne prahu
pro vykazování, podává celní správě každý měsíc **výkaz pro Intrastat**:
jeden za zboží odeslané do jiných členských států a jeden za zboží z nich
přijaté.

V edici Community sbírá údaje z faktur modul OCA `intrastat_product`, český
výstup ale nemá. Ten doplňuje tento modul: u české společnosti je souborem
výkazu **CSV**, které importuje portál **InstatOnline** celní správy, a ne
soubor XML. Rozložení sloupců, pevné hodnoty i formát čísel odpovídají
vlastnímu českému modulu Intrastat v Odoo Enterprise, takže při přechodu mezi
edicemi podává společnost stejná data.

Záměrně se nejmenuje `l10n_cz_intrastat`: to je modul Odoo Enterprise, který
databáze Enterprise používá místo něj. Instalujte jen jeden z nich.

## Právní rámec {#legal}

- **Rámec EU.** Intrastat je součástí evropské statistiky podniků podle
  [nařízení (EU) 2019/2152](law:eu/reg/2019/2152). Jeho článek 13 odst. 1
  vyjmenovává, co členský stát vývozu předává o každém vývozu zboží v rámci
  EU, včetně **DIČ obchodního partnera** v členském státě dovozu a **země
  původu**.
- **Kdo a kdy vykazuje** — [celní zákon č. 242/2016 Sb., § 57 až
  § 60](law:cz/2016/242):
  - zpravodajská jednotka vykazuje po dosažení prahu pro vykazování
    (§ 57 odst. 1), za kalendářní měsíce (§ 58 odst. 2), do konce
    kalendářního roku a celý následující kalendářní rok (§ 58 odst. 4);
  - údaje vykazuje **nejpozději dvanáctý pracovní den** měsíce následujícího
    po skončení referenčního období, podáním prostřednictvím elektronického
    portálu Generálního ředitelství cel (§ 58 odst. 5);
  - opravené nebo chybějící údaje vykáže **nejpozději třicátý den** po dni,
    kdy se o nesprávnosti dozvěděla (§ 60 písm. a).
- **Prahy** — [nařízení vlády č. 333/2021 Sb., příloha
  č. 3](law:cz/2021/333): práh pro vykazování je **15 000 000 Kč** hodnoty
  zboží vyvezeného do jiných členských států a samostatně 15 000 000 Kč
  hodnoty zboží dovezeného, počítáno od počátku kalendářního roku; každý
  směr se vykazuje samostatně od referenčního období, ve kterém práh dosáhl.

Modul prahy nesleduje. Směry nastavte podle své zpravodajské povinnosti.

## Nastavení {#setup}

1. *Účetnictví → Konfigurace → Nastavení*, blok **Intrastat**: pro každý
   směr, který vykazujete, nastavte **Přijetí** a **Odeslání** na
   *Standardní* nebo *Rozšířená*, pro druhý na *Exempt* (osvobozeno; v
   češtině zatím nepřeloženo); volitelně **Výchozí druh dopravy**.
2. Kódy zboží musí v Odoo existovat: zadejte je ručně, nebo kombinovanou
   nomenklaturu načtěte modulem OCA `intrastat_product_hscodes_import`,
   který tento modul sám neinstaluje.
3. U každého skladového produktu vyplňte **Kód zboží (KN)**, **Země
   původu** a **hmotnost** v kg.
4. Společnost musí mít vyplněné **DIČ**, jinak se soubor nevytvoří.

## Měsíční výkaz {#usage}

*Účetnictví → Výkazy → Intrastat → Výkaz produktů Intrastat*, potom *Nový*.
V edici Community bez plného účetnictví se kořenová nabídka jmenuje
*Fakturace*.

1. Zvolte **rok**, **měsíc** a **typ** — *Přijetí* nebo *Odeslání*.
2. **Generovat řádky z faktur**, zkontrolujte záložku **Transakce**, opravte
   faktury nebo produkty a podle potřeby řádky vygenerujte znovu.
3. **Potvrdit** seskupí transakce do řádků výkazu.
4. **Generovat XML soubor** (tlačítko si ponechává název z modulu OCA)
   vytvoří CSV, přiloží je jako `RRRR-MM_<typ>_<revize>.csv` a označí výkaz
   jako *Dokončeno*.
5. Soubor nahrajte do **InstatOnline** na portálu celní správy, který jej
   kontroluje při nahrání (předem není proti čemu ověřit).

Každý řádek souboru obsahuje: měsíc; rok; vaše DIČ; směr (`A` přijetí,
`D` odeslání); DIČ partnera; partnerský stát; region (prázdný); zemi
původu; povahu transakce (dvoumístnou, např. `11`); druh dopravy; dodací
podmínky (Incoterm); kód zvláštního pohybu `ST`; kód zboží (bez mezer);
statistický znak a popis zboží (oba prázdné); vlastní hmotnost; množství v
doplňkových jednotkách; fakturovanou hodnotu v měně společnosti. Hmotnost a
doplňkové jednotky do 1 se zapisují se třemi desetinnými místy, větší jako
celá čísla.

## Výskyt ve výkazech {#footprint}

Je-li nainstalován [module:l10n_cssk_core](module:l10n_cssk_core), sám se
nainstaluje [module:l10n_cssk_intrastat_footprint](module:l10n_cssk_intrastat_footprint)
a ve **výskytu ve výkazech** zaúčtovaného dokladu uvede každý výkaz pro
Intrastat, který převzal některý z jeho řádků — období, směr a stav — s
odkazem na něj. Měsíc, za který výkaz ještě nebyl vygenerován, neukáže nic.
Podrobný popis je v
[návodu ke slovenskému Intrastatu](module:l10n_sk_intrastat#footprint).

## Společný generátor {#engine}

Samotné CSV vytváří modul
[module:l10n_cssk_intrastat_base](module:l10n_cssk_intrastat_base), který
generuje i slovenský INSTAT XML. Nemá obrazovky a nainstaluje se s tímto
modulem automaticky.

## Omezení {#limitations}

- **Desetinná místa se odříznou, nezaokrouhlí**: vlastní hmotnost a
  doplňkové jednotky nad 1 a fakturovaná hodnota se zapíší jako celá část
  (13,9 kg jako 13; 800,75 Kč jako 800). Odpovídá to českému modulu Odoo
  Enterprise; mají-li vaše hodnoty desetinná místa, ověřte to proti
  pravidlům InstatOnline.
- Region, statistický znak a popis zboží zůstávají vždy prázdné, kód
  zvláštního pohybu je vždy `ST`.
- Opravy: zkopírovaný výkaz dostane další revizi a nový název souboru, sám
  soubor ale žádné označení opravy nenese. Opravy provádějte v InstatOnline
  v třicetidenní lhůtě.
- Zjednodušené hlášení modul nevytváří.
- Prahy se nekontrolují: modul podá to, co mu zadáte.
- Samotné podání probíhá v InstatOnline, mimo Odoo.
