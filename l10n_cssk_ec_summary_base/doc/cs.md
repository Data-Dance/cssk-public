---
title: Souhrnné hlášení CZ/SK
summary: Společné obrazovky a postup českého souhrnného hlášení a slovenského súhrnného výkazu — jeden řádek na odběratele, DIČ a kód plnění, zkontrolovaný a exportovaný do XML.
verified: 19.0.1.7.0
---

## K čemu slouží {#purpose}

Plátce DPH, který dodává zboží nebo poskytuje služby odběratelům
registrovaným k dani v jiném členském státě EU, tato plnění vykazuje v
**souhrnném hlášení** (SH); na Slovensku je to *súhrnný výkaz* (SV). Obě mají
stejný tvar — jeden řádek na DIČ pořizovatele a kód plnění s celkovou hodnotou
plnění tomuto odběrateli za období.

Tento modul poskytuje právě tento tvar: samotné hlášení, jeho výpočet ze
zaúčtovaných položek deníku, kontroly před exportem a export do XML. Sám o
sobě nedělá nic. Kódy, oficiální XML šablonu a schéma dodává modul země:

- [module:l10n_cz_ec_sales](module:l10n_cz_ec_sales) — české souhrnné hlášení;
- [module:l10n_sk_ec_sales](module:l10n_sk_ec_sales) — slovenský súhrnný výkaz.

Právní rámec — kdo hlášení podává, jak často a do kdy — je na stránkách těchto
modulů. Tato stránka popisuje obrazovky, které mají obě země společné.

## Nastavení {#setup}

1. **Daně pro plnění do EU nesou kód plnění.** Položka deníku se do hlášení
   dostane jen přes daň označenou *Kódem souhrnného hlášení* (technické pole
   `cssk_ec_summary_code`). Modul země ho při instalaci nastaví na
   standardních daních pro plnění do EU v české nebo slovenské účtové osnově
   Odoo (viz jeho stránku). U daně, kterou vytvoříte sami, nebo u daní
   společnosti, jejíž osnova se nainstaluje později, nastavte **EC sales list
   code** ve formuláři daně (*Pokročilé možnosti*, zobrazuje se u českých a
   slovenských prodejních daní).
2. **DIČ společnosti** (pole *DIČ*) musí být vyplněno, jinak export odmítne.
3. **Finanční úřad.** *Účetnictví → Konfigurace → Nastavení*, blok **Česká /
   slovenská lokalizace**, nastavení **Výchozí správce daně**. Z něj XML uvádí
   finanční úřad.
4. **Odběratelé.** Každý odběratel na faktuře do EU potřebuje DIČ s předponou
   státu a stát v adrese. Řádek bere stát z adresy, ne z předpony DIČ.

## Příprava hlášení {#usage}

*Účetnictví → Výkazy → Zákonné výkazy → Souhrnné hlášení*, potom *Nový*.

1. Vyplňte období (*Datum od*, *Datum do*), **Typ období** (měsíčně nebo
   čtvrtletně), **Verzi** a **Typ výkazu** (řádné, opravné, následné — názvy
   dodává modul země). Nabízejí se jen verze platné pro dané období; viz
   [Verze](#versions).
2. Klikněte na **Vypočítat**. Hlášení přejde do stavu *Náhled* a zobrazí jeden
   řádek na **stát, DIČ odběratele a kód plnění** s počtem dokladů a celkovou
   hodnotou.

Co se započítá:

- zaúčtované položky deníku společnosti s označenou daní;
- hodnota je zůstatek položky v měně společnosti (CZK nebo EUR), se
  znaménkem otočeným tak, aby plnění bylo kladné a opravný daňový doklad
  záporný;
- období se u faktur a opravných daňových dokladů odběratelům určuje podle
  **DUZP** (nemá-li doklad žádné, podle data účetního případu), u ostatních
  dokladů podle data účetního případu. Má-li doklad vyplněno *Deklarované
  období DPH*, rozhoduje to.

Na každém řádku:

| Sloupec | Význam |
|---|---|
| ✓ | Zdrojové položky stále dávají hodnotu řádku (s odchylkou do 0,50). |
| **Doklady** | Otevře položky deníku, ze kterých řádek vznikl, seskupené podle dokladu. |
| **Přepsat** / *Ruční hodnota* | Zaškrtněte, chcete-li vykázat vlastní hodnotu — například opravu, která ještě není zaúčtovaná. Řádek se obarví oranžově. |

**Vypočítat** lze opakovat, dokud je hlášení ve stavu *Koncept* nebo *Náhled*.
Ruční přepisy přepočet přežijí: znovu se uplatní na řádek se stejným státem,
DIČ a kódem. Přepis, jehož řádek už neexistuje, se vypíše v chatteru, nikdy se
neztratí potichu.

## Export a podání {#submission}

Klikněte na **Exportovat XML**. Před vygenerováním se zkontroluje:

1. DIČ společnosti;
2. DIČ na každém řádku — musí být vyplněno, začínat dvěma písmeny a stát
   řádku musí být členským státem EU. Každá chyba export **zablokuje** a vypíše
   dotčené řádky;
3. vlastní pravidla modulu země (například povolené kódy plnění);
4. vygenerované XML proti oficiálnímu schématu verze.

XML se poté přiloží k hlášení (*XML příloha*) a stav se změní na
*Exportováno*. V tomto stavu lze hlášení exportovat znovu.

Soubor nahrajte na daňový portál, nebo ho podejte přes kanál (níže), a
klikněte na **Označit jako podané**. Podaná kopie se zmrazí: zůstává v poli
*Historie podání*, i když se hlášení později vrátí do konceptu a podá znovu, a
podané hlášení nelze smazat.

**Podat** otevře záznam o doručení pro exportované nebo podané hlášení. Se
samotným standardním kanálem zaznamená, že podání proběhlo ručně na portálu,
a uchová potvrzení. S modulem [module:l10n_cz_epo](module:l10n_cz_epo) lze
české hlášení podepsat a odeslat přímo na EPO. Odznak v záhlaví ukazuje stav
doručení.

**Vrátit do konceptu** znovu otevře exportované nebo podané hlášení. Mohou to
udělat jen uživatelé ve skupině *Účetnictví / Administrátor*; podaná kopie se
zachová.

## Opravy {#corrections}

Na podaném hlášení tlačítko **Dodatečné / opravné** vytvoří kopii propojenou
s původním hlášením (*Opravuje*) a otevře ji jako koncept. Změňte její **Typ
výkazu** na opravný nebo následný a pak ji vypočítejte a exportujte jako
obvykle. Kopie začíná bez řádků a přepočítá se z aktuálního stavu účetnictví.

Opravné podání, které původní nahrazuje, vykáže **celé hlášení**. Pozdější
podání, které vykazuje jen změny — slovenský *dodatočný* výkaz, české
*následné* hlášení —, se při **Vypočítat** zúží na to, co se změnilo oproti
podáním zaznamenaným za období (podaným nebo historickým, v pořadí podání):
nové řádky tak, jak jsou, změněné opravené, zmizelé zrušené. Jak se řádek
ruší, určuje země: Slovensko ho podá s hodnotou 0, český tiskopis storno
řádkem, zobrazeným šedě se zaškrtnutým *Ruší podaný řádek*. Takové podání bez
zaznamenaného podání za své období se odmítne. Viz stránky zemí.

Hlášení převzaté z předchozího systému jako **historické podání** je záznamem
toho, co bylo podáno: nelze ho přepočítat, exportovat ani podat, ale lze k
němu vytvořit opravu. Tlačítko **Porovnání** se zobrazí u hlášení, které bylo
porovnáno s jiným základem, například s novým výpočtem.

## Ověření ve VIES s konzultačním číslem {#vies}

Kontrola popsaná výše ověřuje jen formát. S modulem
[module:l10n_cssk_vies](module:l10n_cssk_vies) se sám nainstaluje doplněk
[module:l10n_cssk_ec_summary_vies](module:l10n_cssk_ec_summary_vies), který při
exportu ověří každý řádek ve službě VIES Evropské komise — ovšem jen u
společností se zapnutou volbou **Použít přímé EU VIES (bez IAP)**
(*Účetnictví → Konfigurace → Nastavení*, u nastavení **Ověření DIČ**).

U každého řádku uloží *Platné ve VIES*, *Stav VIES*, *Konzultační číslo VIES*
vrácené službou VIES a *VIES ověřen dne* (ve výchozím stavu skryté), takže z
podaného hlášení je vidět, co a kdy bylo potvrzeno.

- DIČ, které VIES označí za **neplatné**, export zablokuje. Hlášení zobrazí
  trvalé upozornění a chatter vyjmenuje dotčené řádky; konzultační čísla
  získaná pro platné řádky se zachovají, takže se při dalším pokusu
  neztratí.
- Není-li **VIES dostupné**, řádek se označí jako *Porucha služby* a export
  pokračuje, aby výpadek nezpůsobil zmeškání lhůty. Chatter tyto řádky
  vyjmenuje; ověření zopakujete dalším exportem.
- Každý export se na VIES ptá znovu, jednou za každý řádek.

## Verze {#versions}

*Účetnictví → Konfigurace → CZ/SK lokalizace → Verze souhrnného hlášení*
obsahuje verze tiskopisu, které instalují moduly zemí: platnost, XML šablonu,
schéma a na kartě *Typy podání* typy výkazu s hodnotou, kterou každý zapíše do
XML. Hlášení nabízí jen verze, jejichž platnost pokrývá jeho období, včetně
archivovaných, takže archivací verze si seznam zpřehledníte, aniž by stará
období nešla podat. Běžně zde nic neměníte.

## Omezení {#limitations}

- Kód plnění se čte jen z daně (viz [Nastavení](#setup)).
- Stát řádku se bere z adresy odběratele. Předpony DIČ, které se liší od ISO
  kódu státu — **EL** pro Řecko, **XI** pro Severní Irsko — se neodvozují;
  odběratel ze Severního Irska s adresou ve Spojeném království neprojde
  kontrolou členství v EU.
- Příznaky *Povolit měsíční* / *Povolit čtvrtletní* na verzi odmítnou typ
  období, který tiskopis nemá; zda smíte podávat čtvrtletně, posuďte sami
  podle vnitrostátních pravidel.
- Oprava se porovnává jen s podáními zaznamenanými zde (viz
  [Opravy](#corrections)).
- Režim skladu (na Slovensku *režim call-off stock*) nepodporuje žádný z
  modulů zemí.
- Bez doplňku VIES je kontrola před exportem jen kontrolou formátu, nikoli
  platnosti.
