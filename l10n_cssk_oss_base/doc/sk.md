---
title: Daňové priznanie k DPH OSS CZ/SK (úprava pre Úniu)
summary: Štvrťročné daňové priznanie v osobitnej úprave pre predaj tovaru na diaľku a služby spotrebiteľom v iných štátoch EÚ — z daní OSS v Odoo, prepočítané na eurá kurzom ECB, s opravami predchádzajúcich štvrťrokov.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Predajca, ktorý uplatňuje **osobitnú úpravu pre Úniu** (One-Stop-Shop, OSS),
účtuje pri predaji tovaru na diaľku a pri službách spotrebiteľom v iných
štátoch EÚ daň členského štátu zákazníka a celú ju priznáva v jednom
štvrťročnom priznaní podanom doma: na Slovensku je to *daňové priznanie k DPH —
osobitná úprava pre Úniu*, v Česku *daňové přiznání ve zvláštním režimu jednoho
správního místa — režim Evropské unie*.

Štandardný modul Odoo `l10n_eu_oss` už vytvára všetko potrebné na *fakturáciu*
tejto dane: fiškálnu pozíciu *OSS B2C* pre každý členský štát a dane so
sadzbou štátu určenia, všetky označené značkou `OSS`. Čo Odoo pre Slovensko a
Česko nevytvorí, je samotné *priznanie*. Tento modul ho vypočíta z
označených účtovných položiek:

- jeden riadok za každú kombináciu **členský štát spotreby × tovar/služby ×
  sadzba dane**, v eurách;
- **opravy predchádzajúcich štvrťrokov** za každý členský štát;
- zostatok za každý členský štát a celkovú splatnú daň.

Úradné XML vytvorí národný modul, ktorý nainštalujete spolu s týmto:

| Členský štát identifikácie | Modul | Tlačivo |
|---|---|---|
| Slovensko | [module:l10n_sk_oss](module:l10n_sk_oss) | eFormulár DPOSS_EUv01 |
| Česko | [module:l10n_cz_oss](module:l10n_cz_oss) | tlačivo EPO OSSEI1 |

Modul tiež dopĺňa do mapovania daní OSS v Odoo chýbajúcu slovenskú sadzbu 5 %
— pozri [Slovenská sadzba 5 %](#tax-mapping). Funguje v edícii Community aj
Enterprise: vlastný výkaz OSS v Enterprise exportuje len Belgicko a Luxembursko.

## Právny rámec {#legal}

Oba štáty preberajú rovnaké pravidlá EÚ a modul sa riadi tam, kde sa zhodujú:

- **Štvrťročné priznanie do konca nasledujúceho mesiaca**, podáva sa aj vtedy,
  ak sa nič nedodalo — SK
  [§ 68b ods. 12 zákona o DPH](law:sk/2004/222#paragraf-68b.odsek-12); CZ
  [§ 110zb a § 110zc zákona o DPH](law:cz/2004/235). Podľa oboch zákonov sa
  lehota neposúva, ak pripadne na sobotu, nedeľu alebo sviatok.
- **Sumy v eurách.** Úhrada v inej mene sa prepočíta referenčným výmenným
  kurzom Európskej centrálnej banky platným posledný deň zdaňovacieho obdobia
  alebo nasledujúci deň, ak v posledný deň kurz určený a vyhlásený nebol — SK
  [§ 68b ods. 17](law:sk/2004/222#paragraf-68b.odsek-17) (ktorý pripúšťa aj
  kurz vyhlásený Národnou bankou Slovenska); CZ
  [§ 110ze odst. 2 písm. a)](law:cz/2004/235).
- **Opravy sa uvádzajú v nasledujúcom priznaní** s uvedením členského štátu
  spotreby, zdaňovacieho obdobia a sumy dane, najneskôr do troch rokov odo dňa
  uplynutia lehoty na podanie pôvodného priznania, kurzom, ktorý sa mal použiť
  pri pôvodnom dodaní — SK
  [§ 68b ods. 19](law:sk/2004/222#paragraf-68b.odsek-19); CZ
  [§ 110zd a § 110ze odst. 2 písm. b)](law:cz/2004/235).

Registráciu, podanie a samotné tlačivá opisujú národné návody.

## Nastavenie {#setup}

1. **Mapovanie OSS v Odoo.** *Účtovníctvo → Konfigurácia → Nastavenia*, blok
   **Predaj na diaľku v rámci Európskej únie**, tlačidlo **OSS mapovanie
   daní**. Vytvorí fiškálne pozície a dane OSS. Skontrolujte ich podľa toho,
   čo skutočne predávate, ako odporúča aj Odoo.
2. **Typ produktu.** Každý riadok sa delí na tovar a služby podľa produktu na
   riadku faktúry: produkt typu *Služba* je služba, všetko ostatné — aj riadok
   bez produktu — sa počíta ako tovar. Kto predáva elektronické alebo iné
   služby, nech má na riadkoch produkty.
3. **Kurzy.** Ak fakturujete v inej mene ako v eurách, udržiavajte kurzový
   lístok spoločnosti aktuálny: priznanie z neho navrhuje kurzy.
4. **Verzia tlačiva.** Nainštaluje ju národný modul. Nájdete ju v
   *Účtovníctvo → Konfigurácia → CZ/SK lokalizácia → Verzie priznania OSS* s
   kódom tlačiva, platnosťou, šablónou a úradnou XSD; spravidla v nej netreba
   nič meniť.

## Príprava priznania {#usage}

*Účtovníctvo → Výkazy → Zákonné výkazy → Daňové priznania k DPH OSS*, potom
*Nové*.

1. **Rok** a **Štvrťrok** a verzia tlačiva pre vašu krajinu (pole ponúka len
   verzie členského štátu spoločnosti platné pre daný štvrťrok). Priznanie
   možno zostaviť od tretieho štvrťroka 2021, keď sa osobitná úprava pre Úniu
   začala uplatňovať.
2. **Registrovaný od / Registrovaný do** vyplňte, len ak sa registrácia začala
   alebo skončila počas štvrťroka. Dátumy sa zapíšu do tlačiva ako začiatok
   alebo koniec obdobia a priznanie vezme len doklady s dátumom medzi nimi.
   Oba musia ležať vo štvrťroku.
3. Kliknite na **Vypočítať**. Modul vezme každú zaúčtovanú účtovnú položku so
   značkou `OSS`:
   - faktúra patrí do štvrťroka podľa dátumu dodania, a ak nie je vyplnený,
     podľa dátumu faktúry;
   - dobropis patrí do štvrťroka, v ktorom bol **vystavený** — teda keď sa
     zmena zistila;
   - členský štát sa určí podľa dane OSS (každá daň OSS patrí jednému štátu
     určenia), inak podľa fiškálnej pozície dokladu a nakoniec podľa dodacej
     adresy.
4. Skontrolujte tri záložky:
   - **Dodania** — riadky so základom dane a DPH v eurách. DPH riadku sa
     vypočíta ako základ × sadzba. Lupa otvorí účtovné položky, z ktorých
     riadok vznikol.
   - **Opravy predchádzajúcich štvrťrokov** — pozri [Opravy](#corrections).
   - **Výmenné kurzy** — pozri [Výmenné kurzy](#rates).
5. *Zaúčtovaná DPH (EUR)* ukazuje daň OSS skutočne zaúčtovanú na dokladoch,
   prepočítanú rovnako, vedľa vypočítaných súčtov. Porovnajte ich.

Kým je priznanie v koncepte, riadky a opravy možno pridávať a upravovať ručne.
Riadok, ktorý pridáte, je *Ručné* už sám; zaškrtnite *Ručné* aj pri
vypočítanom riadku, ktorý zmeníte. **Vypočítať** ručné riadky ponechá
a ostatné nahradí, takže úprava nezaškrtnutého vypočítaného riadku sa pri
ďalšom výpočte stratí. Na ručnom riadku zadávate
základ dane aj DPH.

Tovar odoslaný zo skladu v inom členskom štáte alebo služby dodané z
prevádzkarne v inom štáte sa vykazujú osobitne za tento štát. Na bežnej faktúre
Odoo nie je zaznamenané, odkiaľ sa tovar odoslal, preto sa takéto riadky
**nevypočítajú**: zadajte ich ručne s poľom *Dodané zo štátu* a, ak ho máte,
*IČ DPH v tomto štáte*.

## Opravy predchádzajúcich štvrťrokov {#corrections}

Dobropis (alebo ťarchopis), ktorý odkazuje na pôvodnú faktúru z niektorého
predchádzajúceho štvrťroka, neznižuje riadky tohto štvrťroka. Stane sa opravou
pôvodného štvrťroka za daný členský štát, prepočítanou kurzom pôvodného
štvrťroka. Dobropis k faktúre z toho istého štvrťroka sa jednoducho odpočíta
od riadku.

Dobropis bez odkazu na pôvodnú faktúru zostane v tomto štvrťroku. Ak tým
vznikne záporný riadok, export priznanie odmietne — ani jedno tlačivo záporný
riadok nepripúšťa. Prepojte dobropis s faktúrou alebo opravu zadajte ručne.

Pred exportom modul overí, že každá oprava sa týka štvrťroka od 3. štvrťroka
2021 po štvrťrok pred týmto priznaním, a odmietne opravu, ktorej trojročná
lehota uplynula — takú opravu treba urobiť priamo voči členskému štátu
spotreby.

## Výmenné kurzy {#rates}

Sumy fakturované v eurách sa preberajú tak, ako boli fakturované. Pre každú inú
menu potrebuje priznanie jeden kurz za menu a referenčný dátum: posledný deň
tohto štvrťroka a posledný deň každého štvrťroka, ktorého sa týka oprava.

**Vypočítať** navrhne každý kurz z kurzového lístka spoločnosti — prvý kurz s
dátumom v referenčný deň alebo neskôr, teda pravidlo „nasledujúceho dňa“.
Lístok môže obsahovať kurzy ČNB alebo banky namiesto kurzov ECB a nič v ňom
nehovorí ktoré, preto je navrhnutý kurz označený *Kurzový lístok spoločnosti
(na potvrdenie)* a zobrazený červeno. Každý kurz porovnajte s referenčným
kurzom ECB, prípadne ho opravte (kurz sa zadáva ako *jednotiek meny za 1 EUR*)
a kliknite na **Potvrdiť kurzy ECB**. Export odmietne priznanie s chýbajúcim
alebo nepotvrdeným kurzom. Potvrdený alebo zadaný kurz sa pri ďalšom výpočte
zachová.

## Export a podanie {#export}

**Exportovať XML** postupne:

1. skontroluje údaje spoločnosti — spoločnosť musí mať IČ DPH v tvare, ktorý
   vyžaduje národný modul;
2. skontroluje obsah: chýbajúce alebo nepotvrdené kurzy, záporné riadky,
   členský štát mimo EÚ, dodanie do štátu, z ktorého sa dodáva, riadok, pri
   ktorom nemožno určiť typ sadzby (štandardná alebo znížená), a opravy mimo
   obdobia alebo po lehote;
3. vytvorí národné tlačivo a overí ho voči úradnej XSD uloženej vo verzii
   tlačiva.

Každá chyba export zastaví s uvedením dôvodu. Platný súbor sa priloží k
priznaniu, ktoré prejde do stavu *Exportované*.

XML podajte podľa národného návodu a potom kliknite na **Označiť ako podané**.
Podaný súbor sa tým uchová ako podaná kópia a priznanie sa uzamkne. **Podať**
otvorí záznam podania, ktorý sleduje doručenie a uchováva potvrdenia (pozri
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base)).
**Vrátiť do konceptu** — len pre administrátorov účtovníctva — znovu otvorí
podané priznanie a podanú kópiu zachová.

Typ sadzby každého riadku sa určí z tabuľky štandardných sadzieb členských
štátov s dátumom ich účinnosti: sadzba rovná štandardnej sadzbe platnej
posledný deň štvrťroka je *štandardná*, každá iná *znížená*.

## Slovenská sadzba 5 % {#tax-mapping}

Mapovanie daní OSS v Odoo nepozná slovenskú sadzbu 5 % ani v jednom smere,
hoci ju [§ 27 ods. 3](law:sk/2004/222#paragraf-27.odsek-3) od 1. 1. 2025
uplatňuje aj na časť toho, čo sa do roku 2024 zdaňovalo sadzbou 10 %. Bez
mapovania by si predaj OSS s touto daňou ponechal tuzemskú sadzbu. Modul
chýbajúce položky doplní vždy, keď mapovanie Odoo beží, bez zásahu do Odoo:

- **Slovenská 5 % → iný členský štát**: zahraničná sadzba, ktorú Odoo používa
  pre pôvodnú slovenskú 10 %.
- **Iný členský štát → slovenská 5 %**, pre predajcu z iného štátu, ktorý
  predáva na Slovensko: najnižšia znížená sadzba daného štátu a navyše česká
  sadzba 12 %.

Odoo 19 prepojí tuzemskú daň s daňou OSS len vtedy, keď daň OSS vytvára, takže
druhá tuzemská daň s rovnakou sadzbou v štáte určenia — napríklad slovenská 5 %
popri 19 % — by zostala nenamapovaná. Modul prepojí každú takú tuzemskú daň s
existujúcou daňou OSS. Len pridáva prepojenia; nikdy nevytvára dane ani nemení
mapovanie, ktoré už na fiškálnej pozícii je.

Pri inštalácii sa mapovanie doplní každej spoločnosti, ktorá už dane OSS má.
Spoločnosti, ktoré OSS nikdy nepoužili, ostanú bez zmeny. Mapovanie je návrh,
rovnako ako v samotnom Odoo: skontrolujte ho podľa tovaru, ktorý predávate.

## Obmedzenia {#limitations}

- Len **osobitná úprava pre Úniu**. Úprava mimo Únie a úprava pri dovoze
  (IOSS) nie sú pokryté — Odoo pre ne nemá dane.
- Dodania tovaru odoslaného z iného členského štátu alebo z prevádzkarne v inom
  štáte sa nerozpoznajú; zadajte ich ako ručné riadky.
- Tovar a služby sa rozlišujú len podľa typu produktu; riadok bez produktu sa
  počíta ako tovar.
- Porovnanie *zaúčtovanej DPH* s vypočítanou a upozornenie, že opravu treba
  podať skôr, aby sa stihla trojročná lehota, sa zapisujú len do záznamu
  servera; formulár ich nezobrazí. *Zaúčtovanú DPH* porovnajte s *DPH z
  dodaní* a *Opravami* sami.
- DPH riadku sa zaokrúhli na centy zo základu riadku, nespočítava sa z faktúr.
  Český zákon pritom žiada vyčíslenie na dve desatinné miesta bez zaokrúhľovania
  — pozri [návod k českému tlačivu](module:l10n_cz_oss#limitations).
- Navrhnuté kurzy pochádzajú z kurzového lístka spoločnosti a musí ich
  skontrolovať človek.
- Tabuľka typov sadzieb a mapovanie 5 % zodpovedajú sadzbám známym pri vydaní
  modulu. Neskoršia zmena štandardnej sadzby si vyžaduje aktualizáciu modulu.
