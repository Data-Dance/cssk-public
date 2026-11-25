---
title: CZ přiznání k dani z příjmů PO (DPPDP9)
summary: České přiznání k dani z příjmů právnických osob — ř. 10 z účetnictví, úpravy účetní, výpočet daně ve II. oddílu a soubor pro EPO ověřený proti schématu Finanční správy, včetně rozvahy a výkazu zisku a ztráty podaných uvnitř přiznání.
verified: 19.0.1.8.0
---

## K čemu slouží {#purpose}

Česká obchodní korporace podává jednou ročně přiznání k dani z příjmů
právnických osob (tiskopis DPPDP9). Tento modul dodává tiskopis na obrazovku
daňového přiznání z modulu
[module:l10n_cssk_income_tax_base](module:l10n_cssk_income_tax_base), jehož
návod popisuje společný postup — vytvoření přiznání, výpočet, přepis
řádků, export, označení jako podané a zaúčtování daně. Tato stránka popisuje
to, co je české:

- řádky **II. oddílu** (výpočet daně) od ř. 10 po ř. 340;
- **ř. 10**, výsledek hospodaření před zdaněním, vypočtený z účetnictví;
- záhlaví přiznání — typ přiznání, zdaňovací období, typ poplatníka;
- **rozvahu** a **výkaz zisku a ztráty** podané uvnitř přiznání, převzaté z
  modulu [module:l10n_cz_fs](module:l10n_cz_fs);
- soubor XML pro EPO ověřený proti oficiálnímu schématu.

## Právní rámec {#legal}

Odkazy jsou na [zákon o daních z příjmů](law:cz/1992/586), není-li uvedeno
jinak.

- **Východisko.** Poplatník, který vede účetnictví, vychází z výsledku
  hospodaření (zisku nebo ztráty) — [§ 23 odst. 2 písm. a)](law:cz/1992/586).
  To je ř. 10.
- **Sazba a zaokrouhlení.** Sazba daně činí **21 %** za období započatá od
  1. 1. 2024 a **19 %** za dřívější — sazba platná k prvnímu dni období
  (zákon č. 349/2023 Sb., čl. XVI bod 1) — a daň se vypočte jako
  součin sazby a základu daně sníženého o položky snižující základ daně a o
  odčitatelné položky, zaokrouhleného na celé tisíce Kč dolů —
  [§ 21 odst. 1](law:cz/1992/586); zaokrouhlení stanoví i
  [§ 20 odst. 11](law:cz/1992/586).
- **Daňová ztráta.** Odečíst ji lze v pěti zdaňovacích obdobích
  bezprostředně následujících po období, za které byla stanovena, nebo ve
  dvou obdobích předcházejících — [§ 34 odst. 1](law:cz/1992/586).
- **Bezúplatná plnění (dary).** Odečítají se od základu daně již sníženého
  podle § 34 — [§ 20 odst. 8](law:cz/1992/586).
- **Zdaňovací období.** [§ 21a](law:cz/1992/586) zná čtyři: a) kalendářní
  rok, b) hospodářský rok, c) období od rozhodného dne fúze nebo rozdělení,
  d) účetní období delší než 12 měsíců.
- **Výkazy podávané s přiznáním.** Ve zkráceném rozsahu mohou sestavit
  účetní závěrku účetní jednotky, které nejsou povinny mít ji ověřenou
  auditorem — [§ 18 odst. 4 zákona o účetnictví](law:cz/1991/563). Měnou
  účetnictví může být česká měna, nebo jako funkční měna euro, americký
  dolar či britská libra — [§ 24a zákona o účetnictví](law:cz/1991/563).

## Nastavení {#setup}

Modul nemá nastavení. Před prvním přiznáním zkontrolujte údaje společnosti,
protože z nich se vyplňuje záhlaví souboru:

| Pole společnosti | Kam jde |
|---|---|
| *DIČ* (bez předpony `CZ`) | DIČ |
| Název společnosti | zkrácený název (prvních 20 znaků) |
| *Finanční úřad* (z modulu [module:l10n_cz_statutory](module:l10n_cz_statutory)) — jeho kód pro podání | finanční úřad, kterému je přiznání určeno |
| *Finanční Úřad (CZ)* — kód územního pracoviště | územní pracoviště |
| *NACE (main activity)* (z modulu [module:partner_nace](module:partner_nace)) | CZ-NACE |

## Přiznání {#usage}

Při vytváření přiznání je jedinou **Verzí** *DPPDP9*, platná od 1. 1. 2021
bez konce platnosti: finanční správa přijímá každé období v aktuální
struktuře, která přijímá období od roku 2021. **Typ výkazu** je *Řádné*, *Opravné*,
*Dodatečné* nebo *Dodatečné-opravné*.

**Záhlaví** (blok *Druh přiznání*, upravitelný až do exportu):

| Pole | Význam |
|---|---|
| Typ daňového přiznání | Proč se přiznání podává: *A – za zdaňovací období* (výchozí) nebo jeden ze zvláštních případů — vstup do likvidace, před fúzí, před změnou zdaňovacího období a další. |
| Zdaňovací období (§ 21a) | Vyplní se podle dat: kalendářní rok je a), jiných dvanáct měsíců b), delší období d). Písmeno c) pro období od rozhodného dne fúze nastavte sami; kratší období ponechá, co nastavíte. |
| Typ poplatníka | Výchozí *1 – ostatní*; změňte u daňového nerezidenta, veřejně prospěšného poplatníka, investičního fondu apod. |
| Důvody zjištěny dne | Zobrazí se a je povinné u přiznání *Dodatečné* nebo *Dodatečné-opravné*: den, kdy byly zjištěny důvody pro jeho podání. |

**Řádky:**

| Řádek | Druh | Výpočet |
|---|---|---|
| ř. 10 Výsledek hospodaření před zdaněním | z účtů | třída 6 minus třída 5, bez účtů 591, 592, 593, 595, 599 (daně z příjmů) a 596 (převod podílu společníkům) |
| ř. 50 Rozdíl, o který účetní odpisy převyšují daňové | z evidence majetku | účetní odpisy minus daňové odpisy roku, je-li rozdíl kladný; viz [níže](#depreciation) |
| ř. 20–63 bez ř. 50 (ostatní položky) | zadáváte | ostatní položky zvyšující výsledek hospodaření jednou částkou |
| ř. 70 Mezisoučet — zvýšení VH | výpočet | předchozí řádek + ř. 50 |
| ř. 150 Rozdíl, o který daňové odpisy převyšují účetní | z evidence majetku | daňové odpisy minus účetní odpisy roku, je-li rozdíl kladný |
| ř. 100–162 bez ř. 150 (ostatní položky) | zadáváte | ostatní položky snižující výsledek hospodaření jednou částkou |
| ř. 170 Mezisoučet — snížení VH | výpočet | předchozí řádek + ř. 150 |
| ř. 200 Základ daně | výpočet | ř. 10 + ř. 70 − ř. 170 |
| ř. 230 Odečet daňové ztráty | zadáváte | odečítaná daňová ztráta |
| ř. 240 Odečet podle § 34 ve znění do 31. 12. 2004 | zadáváte | dřívější odpočty podle § 34 odst. 3 až 10 a 12; obvykle prázdný |
| ř. 242 Odečet na podporu výzkumu a vývoje | zadáváte | § 34 odst. 4, § 34a až 34e |
| ř. 243 Odečet na podporu odborného vzdělávání | zadáváte | § 34 odst. 4, § 34f až 34h |
| ř. 250 Základ daně snížený o položky podle § 34 | výpočet | ř. 200 − ř. 230 − ř. 240 − ř. 242 − ř. 243, nejméně 0 |
| ř. 260 Odečet bezúplatných plnění (§ 20 odst. 8) | zadáváte | skutečně uplatněné dary v zákonném limitu |
| ř. 270 Základ daně zaokrouhlený | výpočet | ř. 250 − ř. 260, zaokrouhlený na celé tisíce Kč dolů |
| ř. 280 Sazba daně | výpočet | 21 (19 za období započaté před rokem 2024), je-li ř. 270 vyšší než 0 |
| ř. 290 Daň | výpočet | ř. 270 × ř. 280 % |
| ř. 300 Slevy na dani (§ 35) | zadáváte | slevy na dani |
| ř. 310 Daň po slevách | výpočet | ř. 290 − ř. 300 |
| ř. 340 Celková daňová povinnost | výpočet | ř. 310 |

Kromě ř. 50 a ř. 150 zadáváte položky ř. 20 – 63 a ř. 100 – 162 vždy jednou
částkou; jednotlivé položky za nimi na obrazovce nejsou a nepodávají se. Zaúčtování daně popsané v
[návodu ke společnému modulu](module:l10n_cssk_income_tax_base#provision)
účtuje ř. 340.

## Rozvaha a výkaz zisku a ztráty {#statements}

Přiznání může nést účetní závěrku přímo v souboru, jak tiskopis umožňuje.
Nejdřív vypočtěte a zkontrolujte *Rozvahu* a *Výkaz zisku a ztráty* za
stejné období (*Účetnictví → Výkazy → Zákonné výkazy → Rozvaha* a *Výkaz
zisku a ztráty*, z modulu [module:l10n_cz_fs](module:l10n_cz_fs)). Potom je v
bloku přiznání *Financial statements filed with the return* (popisek je v
této verzi anglicky) propojte obě:

- **Rozvaha** — rozvaha společnosti se stejným koncovým datem;
- **Výkaz zisku a ztráty** — výkaz se stejným obdobím.

Export je pak podá v rozsahu propojených výkazů — v plném (`uv_rozsah` P),
jsou-li oba ve verzi plného rozsahu, ve zkráceném (Z), jsou-li oba zkrácené —
podle vyhlášky č. 500/2002 Sb., v
tisících Kč (zaokrouhleno matematicky) a se sloupcem minulého období: aktiva
s hodnotami brutto, korekce a netto, pasiva a výkaz zisku a ztráty v
druhovém členění s běžným a minulým obdobím. Každý řádek podávaného rozsahu
se vyplní z řádku výkazu se stejným označením; přiřazení účtů je to z
`l10n_cz_fs`, žádné druhé.

Export odmítne, s hlášením, které problém pojmenuje:

- propojený jen jeden z obou výkazů — propojte oba, nebo žádný;
- jeden výkaz v plném a druhý ve zkráceném rozsahu — tiskopis uvádí jeden
  rozsah pro oba, proto oba vypočtěte v plném rozsahu (ten je přípustný
  vždy), nebo oba ve zkráceném;
- výkaz jiné společnosti, jiného druhu nebo jiného období;
- výkaz dosud nevypočtený nebo vypočtený na verzi, které chybí řádek, jenž
  tiskopis potřebuje;
- verzi rozvahy, která korekce nevede zvlášť, nebo řádek se zápornou
  korekcí (debetní zůstatek na účtu oprávek nebo opravných položek — opravte
  zaúčtování);
- měnu účetnictví jinou než CZK, EUR, USD nebo GBP.

Bez propojených výkazů se přiznání exportuje bez nich a poznámka v
chatteru připomene, že účetní závěrku je pak třeba přiložit k podání jako
E-přílohu.

## Předání účetní závěrky do sbírky listin {#registry}

Obchodní korporace může účetní závěrku předat do sbírky listin veřejného
rejstříku prostřednictvím přiznání k dani z příjmů, místo podání
u rejstříkového soudu: [§ 21b zákona o účetnictví](law:cz/1991/563). Správce
daně ji předá soudu a povinnost zveřejnění je splněna okamžikem podání
přiznání (§ 21b odst. 6). Žádostí je tiskopis *Žádost o předání účetní
závěrky do sbírky listin veřejného rejstříku* (25 5404/I), v souboru věta
`VetaUZ`.

Na přiznání, skupina **Sbírka listin (§ 21b zákona o účetnictví)**:

| Pole | Co dělá |
|---|---|
| Účetní závěrka nebyla schválena / nebyla ověřena auditorem | Zaškrtněte, pokud údaje vycházejí ze závěrky, kterou valná hromada ještě neschválila nebo auditor ještě neověřil. Podává se v záhlaví bez ohledu na žádost. |
| Předat účetní závěrku do sbírky listin | Přidá do souboru žádost. |
| Předat Rozvahu, Předat Výkaz zisku a ztráty | Rozsah žádosti (§ 21b odst. 3). Obojí je ve výchozím stavu zaškrtnuto; Výkaz zisku a ztráty odškrtněte, pokud ho společnost nezveřejňuje (malá nebo mikro účetní jednotka bez povinnosti auditu, § 21a odst. 9). Předávají se výkazy [připojené k přiznání](#statements). |
| E-mail pro potvrzení | Kam správce daně potvrdí předání. Nepovinné. |
| Příloha účetní závěrky, Přehled o peněžních tocích, Přehled o změnách vlastního kapitálu | Soubory, které nahrajete; každý jde do přiznání jako předepsaná e-příloha a je součástí žádosti. |

Nahrané soubory se podají s přiznáním i bez žádosti: příloha je součástí
účetní závěrky přikládané ke každému přiznání.

Export odmítne žádost, kterou by správce daně nepředal: žádost jmenující
Rozvahu nebo Výkaz zisku a ztráty, když k přiznání nejsou připojeny výkazy,
žádost bez jakéhokoli rozsahu, chybný e-mail, soubor typu, který EPO
nepřijímá (DOC, DOCX, RTF, XLS, XLSX, PDF, JPG, JPEG, TXT, CSV nebo jeden
z nich podepsaný či zabalený do ZIP), a soubory o celkové velikosti nad
10 240 kB. Žádost bez přílohy účetní závěrky se exportuje a v historii
přiznání zůstane upozornění.

## Porovnání s účetní závěrkou {#compare}

Přiznání vychází z účetního výsledku: ř. 10 (výsledek hospodaření před
zdaněním) je stejné číslo jako řádek *\*\* Výsledek hospodaření před
zdaněním* Výkazu zisku a ztráty. Jakmile je přiznání vypočteno, ověří to
tlačítko **Porovnat s účetní závěrkou**.

Použije výkaz zisku a ztráty připojený k přiznání; není-li žádný připojen,
vypočtený výkaz společnosti za přesně stejné období (nejnovější, koncepty
a zrušené výkazy se neberou). Obrazovka porovnání pak ukáže ř. 10, částku
z výkazu a rozdíl. Rozdíl znamená, že se obě podání neshodují na účetním
výsledku. Obvyklé příčiny: ř. 10 zadaný ručně, zápis zaúčtovaný až po
výpočtu výkazu (přepočtěte ho), nebo řádek výkazu s upravenými účty.

Tlačítko pouze hlásí; export nezastaví.

## Účetní a daňové odpisy: ř. 50 a ř. 150 {#depreciation}

Přiznání uvádí rozdíl mezi odpisy hmotného a nehmotného majetku uplatněnými
v účetnictví a odpisy podle § 26 až 33 zákona o daních z příjmů na jednom ze
dvou řádků: na ř. 50, jsou-li účetní odpisy vyšší (rozdíl zvyšuje výsledek
hospodaření), na ř. 150, jsou-li vyšší daňové odpisy (rozdíl ho snižuje).
Nikdy na obou. Tak zní pokyn k oběma řádkům v *Pokynech* Finanční správy
25 5404/1 i ve schématu EPO.

Je-li nainstalována evidence daňových odpisů
([module:account_asset_tax](module:account_asset_tax) s
[module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax)),
vyplní se oba řádky při výpočtu přiznání:

- **daňové odpisy** jsou částky daňového odpisového plánu za kalendářní rok
  u každého majetku společnosti, který plán má;
- **účetní odpisy** jsou odpisy téhož majetku zaúčtované v období.
  Nezaúčtované odpisové doklady se nepočítají, proto nejdřív zaúčtujte
  odpisy roku.

Oba řádky se podávají (`kc_ii60_50`, `kc_ii170_150`) a jsou součástí
mezisoučtů ř. 70 a ř. 170. Chcete-li podat jinou částku, zaškrtněte na řádku
*Override* a částku zadejte. Bez evidence jsou oba řádky nulové a rozdíl
zadáte stejným způsobem.

Přiznání vypočtená před verzí 19.0.1.7.0 si ponechávají mezisoučet, který
jste na ř. 70 nebo ř. 170 zadali ručně: aktualizací modulu se základ daně
nezmění. Takové přiznání má v historii poznámku. Zkontrolujte, zda ručně
zadaný mezisoučet rozdíl odpisů už obsahuje; chcete-li mezisoučet nechat
počítat, zrušte na ř. 70 / ř. 170 *Override*, zbývající položky zadejte na
řádek *ostatní položky* a přiznání přepočítejte.

## Omezení {#limitations}

- **Žádost o předání do sbírky listin odtud portál EPO nekontroluje.**
  Soubor odpovídá schématu; vlastní kontroly portálu proběhnou až při
  načtení. Žádost je určena společnostem účtujícím podle vyhlášky
  č. 500/2002 Sb., které nezveřejňují prostřednictvím České národní banky;
  závěrka podle mezinárodních účetních standardů (`pr11_uzmus`) se nepodává.
  Přílohu, přehled o peněžních tocích a přehled o změnách vlastního kapitálu
  připravujete mimo Odoo.
- **ř. 50 a ř. 150 se počítají jen za období shodné s kalendářním rokem.**
  Daňový odpisový plán se vede po kalendářních letech, proto u hospodářského
  roku a u každého období přecházejícího přes konec roku zůstávají oba řádky
  nulové, přiznání to uvede v historii a rozdíl zadáte ručně.
- **Počítá se jen majetek s daňovým plánem.** Účetní odpisy majetku bez
  daňového plánu (například odpisovaného jen účetně) v ř. 50 nejsou;
  přidejte je na řádek *ostatní položky*, nebo ř. 50 přepište.
- Mezisoučet zadaný ručně na ř. 70 nebo ř. 170 se musí rovnat součtu svých
  řádků (řádek *ostatní položky* plus ř. 50 nebo ř. 150); export jiný
  mezisoučet odmítne, protože by soubor nesl řádky, které nedávají součet.
- Rozdíl daňové a účetní zůstatkové ceny prodaného nebo vyřazeného majetku
  (ř. 40 / ř. 160) se nepočítá.

- **Limit darů se nehlídá.** Na ř. 260 zadejte skutečně uplatněnou částku:
  nejvýše 10 % z ř. 250, za zdaňovací období skončená od 1. 3. 2022 do
  28. 2. 2027 nejvýše 30 % (jak uvádí pokyn k řádku ve schématu EPO Finanční správy). Modul odečte,
  co zadáte.
- **Částky zadané na ř. 240 před verzí 19.0.1.3.1 se nepřesouvají.** Řádek
  dříve zahrnoval výzkum a vývoj, odborné vzdělávání i dary dohromady;
  takovou částku rozdělte na ř. 242, ř. 243 nebo ř. 260 a přepočítejte.
- Vytváří se jen II. oddíl, a jen řádky výše. Jeho další řádky (například
  201, 210, 220, 241 a 251) ani žádná příloha tiskopisu (odpisy po skupinách
  v tabulce B přílohy č. 1, daňová ztráta,
  slevy, daň zaplacená v zahraničí atd.) se nevytvářejí; schéma soubor bez
  nich přijme.
- Období započatá před rokem 2021 zadat nelze; struktura je nepřijímá. Za
  roky 2021–2024 se podávají řádky uvedené výše tak, jak jsou; řádek, který
  se ve starším znění tiskopisu lišil, si zkontrolujte.
- Rozsah pro mikro účetní jednotky (M) se nepodává; mikro jednotka může
  propojit výkazy ve zkráceném rozsahu. Nepodává se ani časové rozlišení v
  položkách C.II.3. / C.III.: výkazy používají D.
- Každý řádek se zaokrouhluje na tisíce samostatně, takže u mnoha drobných
  položek se součet může od součtu zaokrouhlených položek lišit o tisíc či
  dva; takové součty před podáním zkontrolujte.
- Kódy záhlaví (typ přiznání, typ poplatníka) a úplnou sadu úprav je třeba
  před prvním podáním potvrdit s vaší účetní.
