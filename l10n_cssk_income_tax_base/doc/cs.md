---
title: Přiznání k dani z příjmů PO (CZ/SK)
summary: Obrazovka, na které se připravuje přiznání k dani z příjmů právnických osob — výsledek hospodaření z účetnictví, úpravy účetní, výpočet daně, XML ověřené proti schématu a zaúčtování splatné daně.
verified: 19.0.1.5.8
---

## K čemu slouží {#purpose}

Přiznání právnické osoby vychází z výsledku hospodaření v účetnictví a ten se
pak upravuje na základ daně: přičtou se náklady, které zákon neuznává,
odečtou se výnosy, které se nedaní, odečte se daňová ztráta z minulých let a
teprve potom se vypočte daň. Modul pro tuto práci vytvoří za každé zdaňovací
období jeden záznam — **daňové přiznání** — a udělá za vás to, co je číslo a
vzorec:

- **výsledek hospodaření** před zdaněním sečte ze zaúčtovaných položek
  deníku za období;
- **úpravy** zadává účetní po řádcích;
- řádky, které jsou jen výpočtem z jiných řádků, se přepočítají;
- přiznání se exportuje do XML, ověří proti oficiálnímu schématu tiskopisu a
  označí jako podané.

Tento modul je společná část. Vlastní tiskopis nemá: řádky, pravidla a
strukturu XML dodává národní modul —
[module:l10n_cz_dppo](module:l10n_cz_dppo) pro české přiznání k dani z
příjmů právnických osob (DPPDP9) a
[module:l10n_sk_dppo](module:l10n_sk_dppo) pro slovenské *daňové priznanie k
dani z príjmov právnických osôb*. Nainstalujte jeden z nich, tento modul se
nainstaluje s ním. Bez národního modulu nabídka existuje, ale není z čeho
vybrat verzi tiskopisu.

## Přiznání krok za krokem {#usage}

*Účetnictví → Výkazy → Zákonné výkazy → Daň z příjmů (DPPO)*, potom *Nový*.

1. **Záhlaví.** Zvolte období (*Datum od*, *Datum do*), potom **Verzi** —
   vydání tiskopisu. Nabídnou se jen verze státu, ve kterém je společnost
   daňově usazena, platné alespoň pro část období. Potom **Typ výkazu**:
   řádné, opravné nebo dodatečné přiznání, jak je pojmenovává národní modul.
   Uložte. Pokud období nepokrývá žádná verze — zpravidla proto, že správce
   daně tiskopis pro daný rok ještě nezveřejnil — upozornění to oznámí hned po
   zadání dat a přiznání nelze uložit.
2. **Vypočítat.** Vyplní kartu *Řádky* a přesune přiznání do stavu
   *Náhled*. U každého řádku je uveden jeho druh:

   | Druh | Odkud se hodnota bere |
   |---|---|
   | Výsledek hospodaření (VZZ) | Zůstatek uvedených účtů za období, jen ze zaúčtovaných dokladů. |
   | Rozdíl účetních a daňových odpisů majetku | Rozdíl účetních a daňových odpisů za období z modulu daňových odpisů `account_asset_tax`, je-li nainstalován; jinak 0. |
   | Souhrn | Vzorec z jiných řádků, přepočítá se vždy. |
   | Ruční | Zadáváte vy. |

3. **Zadejte úpravy.** V řádku zaškrtněte **Přepis** a částku napište do
   sloupce *Ruční hodnota*. Stejně opravíte i vypočtený řádek. Potom znovu
   klikněte na **Vypočítat**: přepsané řádky si vaši částku ponechají a
   všechny řádky, které z nich vycházejí, se z ní přepočítají. Ruční řádek
   bez přepisu se při každém výpočtu vynuluje, proto políčko zaškrtněte vždy.
4. **Zkontrolujte čísla.** U řádku počítaného z účtů ukáže tlačítko s lupou
   **Doklady** položky deníku, ze kterých vznikl, seskupené podle účtů, a
   sloupec ✓ říká, zda s řádkem stále souhlasí. Pokud ne — obvykle proto, že
   se po posledním výpočtu zaúčtovaly další doklady — záhlaví ukáže červené
   tlačítko **Nesouhlasící řádky**; když vše sedí, zelené **Řádky
   souhlasí**. Sloupec *Odvození* ukazuje vzorec vypočteného řádku, u
   ručního *manual input*.
5. **Exportovat XML.** Vytvoří soubor, ověří ho proti oficiálnímu schématu
   (XSD) uloženému u verze tiskopisu a připojí ho k přiznání; stav se změní
   na *Exportováno*. Pokud schéma soubor odmítne nebo společnost nemá
   vyplněné DIČ, nic se nepřipojí a hlášení řekne proč. Verze bez schématu
   export odmítne vždy.
6. **Podejte přiznání** přes daňový portál a potom klikněte na **Označit
   jako podané**. Exportovaný soubor se uloží jako podaný exemplář, zaznamená
   se datum a stav se změní na *Podáno*. Tlačítko **Podat** otevře záznam o
   doručení podání, kde se uchová potvrzení o podání; při označení jako
   podané se takový záznam otevře automaticky.

Podané přiznání nelze smazat. **Vrátit do konceptu** ho znovu otevře — smí
to jen uživatel s právem *Účetnictví / Administrátor* — a všechny podané
exempláře zůstanou zachovány: každý podaný soubor zůstane u přiznání, i když
ho nahradí nový.

## Opravné a dodatečné přiznání {#amendments}

U podaného přiznání vytvoří tlačítko **Dodatečné / opravné** nové přiznání v
konceptu, propojené s původním (*Opravuje*), se zkopírovanými řádky a vašimi
přepisy jako výchozím stavem. Změňte mu *Typ výkazu* na opravné nebo
dodatečné, opravte, co se změnilo, a znovu ho vypočtěte. Řádky, které obě
přiznání porovnávají, vyplní národní modul, pokud je jeho tiskopis má.

## Zaúčtování splatné daně {#provision}

Po výpočtu přiznání ukáže blok **Splatná daň z příjmů (591/341)** daň z
řádku, který verze tiskopisu určuje jako daň k zaúčtování (v českém
přiznání ř. 340, ve slovenském r. 1050), a tlačítko **Zaúčtovat splatnou daň**
ji zaúčtuje:

- na vrub účtu daně z příjmů splatné (první účet, jehož kód začíná na
  **591**) a ve prospěch účtu daně z příjmů (první začínající na **341**);
- k poslednímu dni období, v deníku zvoleném v bloku, jinak v prvním deníku
  typu *Ostatní*. Účty lze v bloku zvolit i ručně (*Účet daňového nákladu*,
  *Účet daňového závazku*), pokud je osnova pod 591 a 341 nemá.

Nejde o rezervu na daň z příjmů (účet 453), ale o splatnou daň, kterou se
uzavírá výkaz zisku a ztráty a rozvaha za rok. **Stornovat splatnou daň** ji zruší opačným zápisem. Tlačítko se zobrazí, jen je-li
daň vyšší než nula, a jen u verzí tiskopisu, které řádek daně určují.

**Upozornění exportu.** Kontroly, které export nezastaví, se zobrazí ve
žlutém pruhu nahoře na formuláři a v chatteru až do dalšího exportu.

## Omezení {#limitations}

- **Daňové úpravy jsou na vás.** Modul vypočte výsledek hospodaření a
  aritmetiku; nerozhoduje, které náklady jsou daňově neuznatelné ani které
  výnosy jsou osvobozené.
- Výsledek hospodaření počítá jen **zaúčtované** doklady. Po zaúčtování
  posledních závěrkových zápisů přiznání přepočtěte.
- Zaúčtuje se **celá** daň z přiznání. U dodatečného přiznání zaúčtujte
  rozdíl sami: další zaúčtování by daň započetlo dvakrát.
- Účty pro zaúčtování daně se hledají podle začátku kódu (591, 341). Pokud
  je účtová osnova nemá, zvolte je v bloku splatné daně.
- Verze tiskopisu, jejich řádky ani sazby nemají vlastní obrazovku. Změnit
  je může jen správce s technickým přístupem.
- Samotné podání probíhá přes daňový portál; *Označit jako podané* ho jen
  zaznamená.
