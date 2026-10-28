---
title: Súhrnný výkaz CZ/SK
summary: Spoločné obrazovky a postup slovenského súhrnného výkazu a českého souhrnného hlášení — jeden riadok na odberateľa, IČ DPH a kód plnenia, skontrolovaný a exportovaný do XML.
verified: 19.0.1.7.1
---

## Na čo slúži {#purpose}

Platiteľ DPH, ktorý dodáva tovar alebo služby odberateľom identifikovaným pre
daň v inom členskom štáte EÚ, tieto dodania vykazuje v **súhrnnom výkaze**
(SV); v Česku je to *souhrnné hlášení* (SH). Oba majú rovnaký tvar — jeden
riadok na IČ DPH odberateľa a kód plnenia s celkovou hodnotou dodaní tomuto
odberateľovi za obdobie.

Tento modul poskytuje práve tento tvar: samotný výkaz, jeho výpočet zo
zaúčtovaných položiek denníka, kontroly pred exportom a export do XML. Sám
osebe nerobí nič. Kódy, oficiálnu XML šablónu a schému dodáva modul krajiny:

- [module:l10n_sk_ec_sales](module:l10n_sk_ec_sales) — slovenský súhrnný výkaz;
- [module:l10n_cz_ec_sales](module:l10n_cz_ec_sales) — české souhrnné hlášení.

Právny rámec — kto výkaz podáva, ako často a dokedy — je na stránkach týchto
modulov. Táto stránka opisuje obrazovky, ktoré majú obe krajiny spoločné.

## Nastavenie {#setup}

1. **Dane pre dodania do EÚ nesú kód plnenia.** Položka denníka sa do výkazu
   dostane len cez daň označenú *Kódom súhrnného výkazu* (technické pole
   `cssk_ec_summary_code`). Modul krajiny ho pri inštalácii nastaví na
   štandardných daniach pre dodania do EÚ v českej alebo slovenskej účtovej
   osnove Odoo (pozri jeho stránku). Pri dani, ktorú vytvoríte sami, alebo pri
   daniach spoločnosti, ktorej osnova sa nainštaluje neskôr, nastavte **EC
   sales list code** vo formulári dane (*Rozšírené možnosti*, zobrazuje sa pri
   slovenských a českých predajných daniach).
2. **IČ DPH spoločnosti** (pole *IČ DPH*) musí byť vyplnené, inak export
   odmietne.
3. **Daňový úrad.** *Účtovníctvo → Konfigurácia → Nastavenia*, blok **Česká /
   slovenská lokalizácia**, nastavenie **Predvolený správca dane**. Z neho XML
   uvádza daňový úrad.
4. **Odberatelia.** Každý odberateľ na faktúre do EÚ potrebuje IČ DPH s
   predponou krajiny a krajinu v adrese. Riadok berie krajinu z adresy, nie z
   predpony IČ DPH.

## Príprava výkazu {#usage}

*Účtovníctvo → Výkazy → Zákonné výkazy → Súhrnný výkaz*, potom *Nové*.

1. Vyplňte obdobie (*Dátum od*, *Dátum do*), **Typ obdobia** (mesačne alebo
   štvrťročne), **Verziu** a **Typ výkazu** (riadny, opravný, dodatočný —
   názvy dodáva modul krajiny). Ponúkajú sa len verzie platné pre dané
   obdobie; pozri [Verzie](#versions).
2. Kliknite na **Vypočítať**. Výkaz prejde do stavu *Náhľad* a zobrazí jeden
   riadok na **krajinu, IČ DPH odberateľa a kód plnenia** s počtom dokladov a
   celkovou hodnotou.

Čo sa započíta:

- zaúčtované položky denníka spoločnosti s označenou daňou;
- hodnota je zostatok položky v mene spoločnosti (EUR alebo CZK), so
  znamienkom otočeným tak, aby dodanie bolo kladné a dobropis záporný;
- obdobie sa pri faktúrach a dobropisoch odberateľom určuje podľa **dátumu
  zdaniteľného plnenia** (ak doklad žiadny nemá, podľa dátumu účtovania), pri
  ostatných dokladoch podľa dátumu účtovania. Ak má doklad vyplnené
  *Deklarované obdobie DPH*, rozhoduje to.

Na každom riadku:

| Stĺpec | Význam |
|---|---|
| ✓ | Zdrojové položky stále dávajú hodnotu riadku (s odchýlkou do 0,50). |
| **Doklady** | Otvorí položky denníka, z ktorých riadok vznikol, zoskupené podľa dokladu. |
| **Prepísať** / *Manuálna hodnota* | Zaškrtnite, ak chcete vykázať vlastnú hodnotu — napríklad opravu, ktorá ešte nie je zaúčtovaná. Riadok sa zafarbí na oranžovo. |

**Vypočítať** možno opakovať, kým je výkaz v stave *Návrh* alebo *Náhľad*.
Ručné prepisy prepočet prežijú: znova sa uplatnia na riadok s rovnakou
krajinou, IČ DPH a kódom. Prepis, ktorého riadok už neexistuje, sa vypíše v
chatteri, nikdy sa nestratí potichu.

## Export a podanie {#submission}

Kliknite na **Exportovať XML**. Pred vygenerovaním sa skontroluje:

1. IČ DPH spoločnosti;
2. IČ DPH na každom riadku — musí byť vyplnené, začínať dvoma písmenami a
   krajina riadku musí byť členským štátom EÚ. Každá chyba export **zablokuje**
   a vypíše dotknuté riadky;
3. vlastné pravidlá modulu krajiny (napríklad povolené kódy plnenia);
4. vygenerované XML voči oficiálnej schéme verzie.

XML sa potom priloží k výkazu (*XML príloha*) a stav sa zmení na
*Exportované*. V tomto stave možno výkaz exportovať znova.

Súbor nahrajte na portál finančnej správy alebo ho podajte cez kanál (nižšie)
a kliknite na **Označiť ako podané**. Podaná kópia sa zmrazí: zostáva v poli
*História podaní*, aj keď sa výkaz neskôr vráti do konceptu a podá znova, a
podaný výkaz nemožno zmazať.

**Podať** otvorí záznam o doručení pre exportovaný alebo podaný výkaz. So
samotným štandardným kanálom zaznamená, že podanie sa urobilo ručne na
portáli, a uchová potvrdenia. S modulom
[module:l10n_cz_epo](module:l10n_cz_epo) možno český výkaz podpísať a odoslať
priamo na EPO. Odznak v hlavičke ukazuje stav doručenia.

**Vrátiť do konceptu** znovu otvorí exportovaný alebo podaný výkaz. Môžu to
urobiť len používatelia v skupine *Účtovníctvo / Správca*; podaná kópia sa
zachová.

## Opravy {#corrections}

Na podanom výkaze tlačidlo **Dodatočný / opravný** vytvorí kópiu prepojenú s
pôvodným výkazom (*Opravuje*) a otvorí ju ako návrh. Zmeňte jej **Typ výkazu**
na opravný alebo dodatočný a potom ju vypočítajte a exportujte ako obvykle.
Kópia začína bez riadkov a prepočíta sa z aktuálneho stavu účtovníctva.

Opravný výkaz, ktorý pôvodný nahrádza, vykáže **celý výkaz**. Neskoršie
podanie, ktoré vykazuje len zmeny — slovenský *dodatočný* výkaz, české
*následné* hlášení —, sa pri **Vypočítať** zúži na to, čo sa zmenilo oproti
podaniam zaznamenaným za obdobie (podaným alebo historickým, v poradí
podania): nové riadky tak, ako sú, zmenené opravené, zmiznuté zrušené. Ako sa
riadok ruší, určuje krajina: Slovensko ho podá s hodnotou 0, české tlačivo
storno riadkom, zobrazeným sivo so zaškrtnutým *Ruší podaný riadok*. Takéto
podanie bez zaznamenaného podania za svoje obdobie sa odmietne. Pozri stránky
krajín.

Výkaz prenesený z predchádzajúceho systému ako **historické podanie** je
záznamom toho, čo sa podalo: nemožno ho prepočítať, exportovať ani podať, ale
možno k nemu vytvoriť opravu. Tlačidlo **Porovnania** sa zobrazí pri výkaze,
ktorý bol porovnaný s iným základom, napríklad s novým výpočtom.

## Overenie vo VIES s konzultačným číslom {#vies}

Kontrola opísaná vyššie overuje len formát. S modulom
[module:l10n_cssk_vies](module:l10n_cssk_vies) sa sám nainštaluje doplnok
[module:l10n_cssk_ec_summary_vies](module:l10n_cssk_ec_summary_vies), ktorý pri
exporte overí každý riadok v službe VIES Európskej komisie — len však pri
spoločnostiach so zapnutou voľbou **Použiť priame EU VIES (bez IAP)**
(*Účtovníctvo → Konfigurácia → Nastavenia*, pri nastavení **Overiť číslo
DPH**).

Pri každom riadku uloží *Platné vo VIES*, *Stav VIES*, *Konzultačné číslo VIES*
vrátené službou VIES a *VIES overený dňa* (predvolene skryté), takže z
podaného výkazu je vidieť, čo a kedy bolo potvrdené.

- IČ DPH, ktoré VIES označí za **neplatné**, export zablokuje. Výkaz zobrazí
  trvalé upozornenie a chatter vymenuje dotknuté riadky; konzultačné čísla
  získané pre platné riadky sa zachovajú, takže sa pri ďalšom pokuse
  nestratia.
- Ak **VIES nie je dostupné**, riadok sa označí ako *Porucha služby* a export
  pokračuje, aby výpadok nespôsobil zmeškanie lehoty. Chatter tieto riadky
  vymenuje; overenie zopakujete ďalším exportom.
- Každý export sa na VIES pýta znova, raz za každý riadok.

## Verzie {#versions}

*Účtovníctvo → Konfigurácia → CZ/SK lokalizácia → Verzie súhrnného výkazu*
obsahuje verzie tlačiva, ktoré inštalujú moduly krajín: platnosť, XML šablónu,
schému a na karte *Typy podania* typy výkazu s hodnotou, ktorú každý zapíše do
XML. Výkaz ponúka len verzie, ktorých platnosť pokrýva jeho obdobie, vrátane
archivovaných, takže archiváciou verzie si zoznam sprehľadníte bez toho, aby
sa staré obdobia nedali podať. Bežne tu nič nemeníte.

**Upozornenia exportu.** Kontroly, ktoré export nezastavia, sa zobrazia v
žltom pruhu navrchu formulára a v chatteri až do ďalšieho exportu.

## Obmedzenia {#limitations}

- Kód plnenia sa číta len z dane (pozri [Nastavenie](#setup)).
- Krajina riadku sa berie z adresy odberateľa. Predpony IČ DPH, ktoré sa líšia
  od ISO kódu krajiny — **EL** pre Grécko, **XI** pre Severné Írsko — sa
  neodvodzujú; odberateľ zo Severného Írska s adresou v Spojenom kráľovstve
  neprejde kontrolou členstva v EÚ.
- Príznaky *Povoliť mesačné* / *Povoliť štvrťročné* na verzii odmietnu typ
  obdobia, ktorý tlačivo nemá; či môžete podávať štvrťročne, posúďte sami
  podľa vnútroštátnych pravidiel.
- Oprava sa porovnáva len s podaniami zaznamenanými tu (pozri
  [Opravy](#corrections)).
- Režim call-off stock (v Česku *režim skladu*) nepodporuje ani jeden modul
  krajiny.
- Bez doplnku VIES je kontrola pred exportom len kontrolou formátu, nie
  platnosti.
