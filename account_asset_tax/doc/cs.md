---
title: Daňové odpisy (CZ/SK)
summary: Druhý, nikdy neúčtovaný odpisový plán ke každému majetku pro české a slovenské daňové odpisy vedle účetních, s ročním porovnáním účetních a daňových odpisů, odloženou daní a registrem daňových odpisů.
verified: 19.0.1.11.0
---

## K čemu slouží {#purpose}

České a slovenské společnosti odepisují každý dlouhodobý majetek **dvakrát**:

- **Účetní odpisy** se řídí vlastním odpisovým plánem účetní jednotky a
  účtují se do hlavní knihy (účet 551).
- **Daňové odpisy** se řídí odpisovými skupinami a způsoby odpisování zákona o
  daních z příjmů. **Neúčtují se** — daňové přiznání je uplatní místo účetních
  odpisů, takže rozdíl mezi nimi upravuje základ daně.

Registry majetku v Odoo — *Majetek* v Enterprise a registr OCA
`account_asset_management` v Community — vedou jen první z nich. Tento modul
přidává druhé: daňový odpisový plán u každého majetku, vypočtený podle
zákona, a roční nástroje, které z obou plánů připraví údaje pro daňové
přiznání.

Funguje jako skupina modulů. Nainstalujte:

| Modul | Co přináší |
|---|---|
| tento modul | výpočet, číselník odpisových skupin, průvodce a sestavy |
| **jeden** most k registru majetku: [module:account_asset_tax_oca](module:account_asset_tax_oca) (Community, registr OCA) nebo [module:account_asset_tax_ee](module:account_asset_tax_ee) (*Majetek* v Enterprise) | záložku *Daňové odpisy* na kartě majetku; viz [Community](#oca) a [Enterprise](#ee) |
| údaje státu: [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax) a/nebo [module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) | zákonné odpisové skupiny s dobou odpisování, sazbami a koeficienty |

Samotný tento modul na majetku nic nezobrazí; potřebuje most.

## Právní rámec {#legal}

**Česká republika** — [zákon č. 586/1992 Sb., o daních z příjmů](law:cz/1992/586):

- **Odpisové skupiny a minimální doba odpisování**: šest skupin, 1 až 6, od
  3 do 50 let (§ 30 odst. 1); rovnoměrné (§ 31) nebo zrychlené (§ 32)
  odpisování, které odpisovatel stanoví pro každý nově pořízený majetek a
  nelze je změnit po celou dobu odpisování (§ 30 odst. 2).
- **Rovnoměrné odpisování**: sazba pro první rok a pro další roky, obě ze
  vstupní ceny, bez krácení podle měsíců; zvýšené sazby v prvním roce (+10,
  +15, +20 %) podle § 31 odst. 1 písm. b) až d) v případech podle § 31 odst. 2
  až 4; sazba pro zvýšenou vstupní cenu po technickém zhodnocení
  (§ 31 odst. 8).
- **Zrychlené odpisování**: v prvním roce vstupní cena ÷ koeficient, dále
  dvojnásobek zůstatkové ceny ÷ (koeficient − počet let, po které byl majetek
  již odpisován) (§ 32 odst. 2); první odpisovatel může první odpis zvýšit o
  20, 15 nebo 10 % vstupní ceny ve stejných případech jako u rovnoměrného
  odpisování (§ 32 odst. 2 písm. a)); po technickém zhodnocení koeficient pro
  zvýšenou zůstatkovou cenu (§ 32 odst. 3).
- **Mimořádné odpisy** bezemisních vozidel pořízených od 1. 1. 2024 do
  31. 12. 2028 prvním odpisovatelem: 60 % za prvních 12 měsíců a 40 % za
  dalších 12, s přesností na celé měsíce od měsíce následujícího po splnění
  podmínek (§ 30a).
- **Vyřazení**: v roce vyřazení jen polovina ročního odpisu, a to jen u
  majetku evidovaného na počátku zdaňovacího období (§ 26 odst. 7); majetek
  zařazený a vyřazený v témže roce nedostane nic.
- **Přerušení** odpisování je možné; pokračuje se, jako by přerušeno nebylo
  (§ 26 odst. 8).
- **Vozidla kategorie M1**: do výdajů jde jen poměrná část odpisu podle poměru
  2 000 000 Kč ke vstupní ceně (§ 30e).
- Odpisy se zaokrouhlují **na celé koruny nahoru** (§ 31 odst. 9,
  § 32 odst. 5, § 30a odst. 2).

**Slovensko** — [zákon č. 595/2003 Z. z. o dani z príjmov](law:sk/2003/595):

- **Odpisové skupiny a doba odpisování**: sedm skupin, 0 až 6, od 2 do 40
  let — [§ 26 ods. 1](law:sk/2003/595#paragraf-26.odsek-1).
- **Způsob odpisování**: rovnoměrné ve všech skupinách, zrychlené jen ve
  skupinách 2 a 3; zvolený způsob *„nemožno ho zmeniť po celú dobu jeho
  odpisovania“* — [§ 26 ods. 3](law:sk/2003/595#paragraf-26.odsek-3).
- **Rovnoměrné odpisování**: roční odpis je podíl vstupní ceny a doby
  odpisování; v prvním roce jen poměrná část podle počtu měsíců od měsíce
  zařazení do užívání a neuplatněná část se uplatní v roce následujícím po
  uplynutí doby odpisování —
  [§ 27 ods. 1 a 2](law:sk/2003/595#paragraf-27.odsek-2).
- **Zrychlené odpisování**: koeficienty 6/7/6 (skupina 2) a 8/9/8
  (skupina 3), poměrný první rok a zůstatková cena pro druhý rok určená, jako
  by byl uplatněn celý odpis prvního roku —
  [§ 28 ods. 1 a 2](law:sk/2003/595#paragraf-28.odsek-2); po technickém
  zhodnocení [§ 28 ods. 3](law:sk/2003/595#paragraf-28.odsek-3).
- **Technické zhodnocení** a prodloužení doby odpisování —
  [§ 26 ods. 5](law:sk/2003/595#paragraf-26.odsek-5).
- **Přerušení odpisování** na celá zdaňovací období s prodloužením doby
  odpisování — [§ 22 ods. 9](law:sk/2003/595#paragraf-22.odsek-9).
- **Vyřazení.** Roční odpis lze uplatnit jen z majetku účtovaného k
  poslednímu dni zdaňovacího období —
  [§ 22 ods. 11](law:sk/2003/595#paragraf-22.odsek-11) —, takže v roce
  vyřazení se daňový odpis neuplatní a daňovým výdajem je zůstatková cena
  podle [§ 19 ods. 3 písm. b)](law:sk/2003/595#paragraf-19.odsek-3.pismeno-b)
  (u osobních automobilů a dalšího majetku z jeho prvního bodu jen do výše
  příjmů z prodeje). Odpis za celé měsíce zůstává jen majetku podle
  [§ 22 ods. 12](law:sk/2003/595#paragraf-22.odsek-12): odpisovanému podle
  § 26 ods. 6 a 7 a — od roku 2016, rozhodne-li se tak poplatník — majetku,
  jehož zůstatková cena je výdajem jen do výše příjmů z prodeje.
- **Osobní automobily od 48 000 eur**: základ daně se zvýší o rozdíl oproti
  rovnoměrným odpisům ze vstupní ceny 48 000 eur, ale jen je-li základ daně
  nižší než stanovená hranice —
  [§ 17 ods. 34](law:sk/2003/595#paragraf-17.odsek-34). Samotné odpisy se
  neomezují.
- Přepočty se zaokrouhlují na eurocenty — [§ 47](law:sk/2003/595#paragraf-47).

Účetní odpisy upravují zvlášť zákony o účetnictví:
[§ 28 zákona č. 563/1991 Sb.](law:cz/1991/563) a
[§ 28 ods. 1 zákona č. 431/2002 Z. z.](law:sk/2002/431#paragraf-28.odsek-1) —
účetní jednotka odepisuje v souladu se svými účetními metodami. Tento plán je
odpisový plán registru majetku a tento modul do něj nezasahuje.

## Nastavení {#setup}

1. Nainstalujte tento modul, most pro svou edici a modul s údaji státu.
   Odpisové skupiny najdete v *Účetnictví → Konfigurace → Daňové odpisové
   skupiny*.
2. **Nastavení společnosti** na kartě společnosti (*Nastavení →
   Společnosti*), u měny — potřebné jen pro uvedené funkce:

   | Pole | Použití |
   |---|---|
   | Limit daňového odpisu vozidla | Zákonný limit pro vozidla se zaškrtnutým *Uplatnit limit odpisu vozidla*, v měně společnosti: 2 000 000 Kč u české společnosti, 48 000 € u slovenské. 0 = bez limitu. Co s ním dělá který stát, viz stejnojmenné pole na majetku. |
   | Deník odložené daně | Interní deník pro zápis odložené daně z [porovnání](#reconciliation). |
   | Účet odložené daně (481) | Rozvahový účet odložené daně. Použijte účet, na kterém je jen odložená daň z odpisů (například analytický účet 481): porovnání dorovnává celý jeho zůstatek. |
   | Výsledkový účet odložené daně (592) | Výsledkový účet odložené daně. |

3. **Výchozí hodnoty podle druhu majetku.** *Sledovat daňové odpisy*,
   skupinu, metodu a zvýšený odpis v 1. roce nastavte na profilu majetku
   (Community) nebo na odpisovacím modelu (Enterprise); nový majetek vytvořený
   z nich je převezme. Viz části o mostech níže.

Nabídky této skupiny modulů vidí jen **administrátoři** účetnictví. Cesty v
nabídce zde začínají v *Účetnictví*; v Community bez účetnictví Enterprise se
tatáž hlavní nabídka jmenuje *Fakturace*.

## Odpisové skupiny {#groups}

*Účetnictví → Konfigurace → Daňové odpisové skupiny* obsahuje zákonné skupiny
nahrané moduly jednotlivých států. Každá skupina má:

- **Zemi**, číslo **Skupiny**, **Dobu odpisování (roky)**;
- povolené způsoby — *Umožňuje rovnoměrné*, *Umožňuje zrychlené*, *Umožňuje
  mimořádné (§30a)*;
- české sazby rovnoměrného odpisování (1. rok, další roky, zvýšená vstupní
  cena) a koeficienty zrychleného odpisování (1. rok, další roky, zvýšená
  zůstatková cena).

Hodnoty pocházejí ze zákona a při aktualizaci modulu státu se nahrají znovu,
proto je kvůli jednomu majetku neupravujte. Tabulky jsou na stránkách modulů
[module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax) a
[module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax).

Do které skupiny majetek patří, určuje to, čím majetek je (příloha zákona jej
třídí podle klasifikace produkce a stavebních děl), nikoli účet. Rozhoduje o
tom účetní.

## Nastavení majetku {#usage}

Otevřete majetek a záložku **Daňové odpisy**:

| Pole | Význam |
|---|---|
| Sledovat daňové odpisy | Vést u majetku daňový odpisový plán. |
| Daňová odpisová skupina | Nabídnou se jen skupiny státu společnosti. |
| Daňová metoda | Rovnoměrné, zrychlené nebo (CZ skupina 2) mimořádné — přijmou se jen způsoby, které skupina povoluje. |
| Zvýšený odpis v 1. roce | CZ, rovnoměrné i zrychlené, skupiny 1–3, jen první odpisovatel: +10 % u každého takového majetku, +15 % jen u zařízení pro čištění a úpravu vod a pro zhodnocení druhotných surovin podle § 31 odst. 3, +20 % jen u strojů pro zemědělství a lesnictví poplatníka s převážně zemědělskou a lesní výrobou (§ 31 odst. 2); nikdy u majetku podle § 31 odst. 5. Podmínky vyjmenovává nápověda pole. Rovnoměrné odpisování použije tabulku zvýšených sazeb, zrychlené přičte procento ze vstupní ceny k prvnímu odpisu. Mimo českých skupin 1–3 se odmítne. |
| Daňová metoda uzamčena | Zaškrtne se samo po uzavření prvního roku (viz [Uzavření daňového roku](#year-close)); způsob ani skupinu pak už změnit nelze. |
| Daňová vstupní cena | Vstupní cena pro daňové účely. Při zapnutí sledování se vyplní z účetní pořizovací ceny; změňte ji, je-li daňová vstupní cena jiná. |
| Uplatnit limit odpisu vozidla | Osobní vozidlo podléhající *Limitu daňového odpisu vozidla* společnosti. **CZ** (§ 30e): plán se počítá z limitu, což je daňově uznaná část každého odpisu. **SK** (§ 17 ods. 34): plán ponechá odpisy v plné výši a jeho skrytý sloupec *Připočtení za vozidlo (SK § 17 ods. 34)* ukáže za každý rok částku nad rovnoměrným odpisem ze 48 000 € — viz [Roční porovnání](#reconciliation). |
| Odpis za celé měsíce v roce vyřazení | Jen SK (§ 22 ods. 12): ponechat odpis za celé měsíce, po které se majetek v roce vyřazení účtoval. Zaškrtněte u majetku odpisovaného podle § 26 ods. 6 a 7 a podle vlastního rozhodnutí u majetku, jehož zůstatková cena je výdajem jen do výše příjmů z prodeje (osobní automobily, čluny, letadla, motocykly, prodané budovy skupiny 6 …). Bez zaškrtnutí se v roce vyřazení neodepisuje. |
| Datum zařazení (daňové) | Datum zařazení do užívání pro daňové účely. Prázdné = datum zahájení účetního odpisování. |
| Daňově odepsáno / Daňová zůstatková cena | Součet uzavřených řádků plánu a součet řádků dosud neuzavřených. |

Pak klikněte na **Vypočítat daňový odpisový plán**. Plán se pokaždé přepočítá
z těchto polí; již uzavřené roky zůstanou beze změny.

Chcete-li přepočítat mnoho majetku najednou, označte jej v seznamu majetku a
zvolte *Akce → Vypočítat daňové odpisy*, nebo spusťte
*Účetnictví → Konfigurace → Vypočítat daňové odpisy* pro veškerý majetek,
který sleduje daňové odpisy. I zde zůstanou uzavřené roky beze změny.

## Daňový odpisový plán {#board}

Jeden řádek za každý daňový rok (u českých mimořádných odpisů za každý
měsíc): odpis roku, kumulované odpisy, daňová zůstatková cena, poznámka ke
způsobu výpočtu a příznak *Podáno*. Další dva sloupce k němu přiřazují účetní
odpisy téhož kalendářního roku: **Účetní odpis** a **Rozdíl (účetní −
daňový)**. Počítají se v nich všechny účetní odpisy roku, zaúčtované i
plánované. U měsíčního plánu (§ 30a) se účetní částky roku zobrazí jednou, na
posledním řádku roku.

Jak se řádky počítají:

| | Česká republika | Slovensko |
|---|---|---|
| Rovnoměrné, první rok | celá sazba pro první rok bez ohledu na měsíc | roční odpis × měsíce od měsíce zařazení ÷ 12 |
| Rovnoměrné, další roky | sazba pro další roky | vstupní cena ÷ doba odpisování |
| Neuplatněná část prvního roku | — | samostatný řádek v roce po uplynutí doby odpisování |
| Zrychlené | § 32: vstupní cena ÷ k₁ (+ zvolených 10/15/20 % vstupní ceny), dále 2 × ZC ÷ (k − n) | § 28: poměrný první rok, další roky ze zůstatkové ceny bez krácení |
| Mimořádné | § 30a: 24 měsíčních řádků od měsíce po zařazení, 60 % a pak 40 % | — |

Příklady:

- **CZ**, stroj, skupina 2, rovnoměrně, 300 000 Kč: 33 000 Kč (11 %), pak
  čtyři roky po 66 750 Kč (22,25 %).
- **SK**, stroj, skupina 1 (4 roky), vstupní cena 12 000 €, zařazen v říjnu:
  750 € (3/12), pak tři roky po 3 000 €, v pátém roce 2 250 €.

České odpisy se zaokrouhlují na celé koruny nahoru a zůstatková cena dalšího
roku je to, co zbude po zaokrouhlených odpisech. Poslední řádek každého plánu
se upraví tak, aby plán přesně odpovídal odpisované ceně; u plánu podle § 30a
se i dvanáctý měsíc zastaví na 60 %.

## Technické zhodnocení, přerušení, vyřazení {#events}

Události mění plán od určitého data. Zadejte je tlačítky pod **Události
životního cyklu** na záložce — *Technické zhodnocení*, *Přerušení
odpisování*, *Vyřazení* — s datem (a částkou nebo počtem let). Plán se hned
přepočítá a událost se uloží, takže každý další výpočet ji zopakuje.

- **Technické zhodnocení**: od jeho roku plán pokračuje ze zvýšené ceny — CZ
  rovnoměrně sazbou pro zvýšenou vstupní cenu, SK rovnoměrně zvýšenou cenou ÷
  doba odpisování, zrychleně koeficientem pro zvýšenou zůstatkovou cenu. Pole
  *Daňová vstupní cena* si ponechá původní cenu; zvýšení nese událost.
- **Přerušení**: zvolené roky dostanou nulový řádek a zbytek plánu se posune o
  stejný počet let.
- **Vyřazení**: plán skončí. CZ: polovina ročního odpisu v roce vyřazení,
  zaokrouhlená nahoru — nic, byl-li majetek v témže roce zařazen. SK: v roce
  vyřazení se neodepisuje, celá zbývající daňová zůstatková cena je výdajem
  podle § 19 ods. 3 písm. b); se zaškrtnutým *Odpis za celé měsíce v roce
  vyřazení* roční odpis × celé měsíce ÷ 12 (měsíc vyřazení se nezapočítá).
  Vyřazení majetku přímo v registru tuto událost
  zapíše samo (*Vyřadit* v OCA, *Zlikvidovat* / *Prodat* v Enterprise).

Odmítne se: událost s datem v posledním uzavřeném roce nebo před ním,
technické zhodnocení majetku odpisovaného podle § 30a (odpisuje se jako
samostatný majetek, § 30a odst. 3 — založte nový majetek) a přerušení
odpisování majetku podle § 30a.

## Majetek, který se již odpisuje {#migration}

U majetku, jehož daňové odpisování začalo před Odoo, klikněte na záložce na
**Doplnit (migrace)**. Zadejte skupinu, způsob, daňovou vstupní cenu, datum
zařazení a **Podáno do roku** — poslední rok již uplatněný v podaném přiznání.
Volitelně zadejte **Očekávanou daňovou ZC** z dosavadní evidence: liší-li se
vypočtená zůstatková cena na konci tohoto roku, nic se nezapíše a průvodce vás
na to upozorní. Kontrola přehraje události, které již jsou u majetku
zaznamenány, přesně tak, jak je přehraje plán.

Způsobuje-li rozdíl technické zhodnocení nebo přerušení, které ještě není
zaznamenáno, zaznamenejte je jako událost a spusťte průvodce znovu. Do roku,
který je již podán, událost zaznamenat nelze; u majetku s podanými roky
nejprve spusťte průvodce bez očekávané ZC a s polem *Podáno do roku*
nastaveným na rok před událostí, zaznamenejte událost a poté spusťte průvodce
znovu se skutečným podaným rokem a očekávanou ZC.

Průvodce vypočte celý zákonný plán, všechny roky do zadaného roku označí jako
podané a uzamkne způsob odpisování. Je to také jediný dovolený způsob, jak
opravit daňové parametry majetku, jehož uzavřené roky jsou zmrazené.

## Uzavření daňového roku {#year-close}

Po podání daňového přiznání za rok spusťte *Účetnictví → Konfigurace →
Uzavřít rok daňových odpisů*, zvolte rok (výchozí je minulý) a klikněte na
**Uzavřít rok**. U každého majetku společnosti se sledováním daňových odpisů
se všechny řádky plánu do zvoleného roku včetně označí jako **Podáno** a
způsob odpisování se uzamkne.

Od té chvíle:

- přepočet plánu podaný řádek nikdy nezmění — pokud by ho změnil změněný
  parametr, výpočet se odmítne;
- daňovou vstupní cenu, datum zařazení, zvýšený odpis v 1. roce a limit
  vozidla nelze měnit;
- podané řádky nelze upravovat.

Uzavřené roky otevře jen průvodce *Doplnit (migrace)*.

## Roční porovnání a odložená daň {#reconciliation}

*Účetnictví → Výkazy → Rekonciliace daňových odpisů*. Zvolte období (výchozí je
aktuální kalendářní rok), zkontrolujte **Sazbu daně z příjmů (%)** (výchozí 21)
a klikněte na **Vypočítat**. Jeden řádek za každý sledovaný majetek:

| Sloupec | Obsah |
|---|---|
| Účetní odpis | zaúčtované účetní odpisy v období |
| Daňové odpisy | řádky daňového plánu začínající v období |
| Připočet | účetní − daňové, je-li kladné |
| Odpočet | daňové − účetní, je-li kladné |
| Účetní ZC, Daňová ZC (výchozí skryté) | obě zůstatkové ceny ke konci období |
| Přechodný rozdíl | účetní ZC − daňová ZC |
| Odložená daň | přechodný rozdíl × sazba: kladná = závazek, záporná = pohledávka |
| Připočtení za vozidlo (SK § 17 ods. 34) (výchozí skryté) | u slovenských automobilů se zaškrtnutým *Uplatnit limit odpisu vozidla*: odpisy období nad rovnoměrným odpisem ze 48 000 € |

Řádky přiznání se řídí státem společnosti a zobrazí se u součtů i v záhlaví
PDF a XLSX: **Česká republika** ř. 50 (účetní odpisy převyšují daňové) a
ř. 150 (daňové převyšují účetní), **Slovensko** r. 150 (pripočítateľná) a
r. 250 (odpočítateľná položka).

**Připočtení za vozidlo** záměrně není ve sloupci připočtu: § 17 ods. 34 jej
připočte k základu daně, jen je-li základ nižší než počet takových automobilů
× roční rovnoměrný odpis ze 48 000 €, a pronajímatel automobilu pronajatého
bez sjednaného práva koupě jej nepřipočte nikdy. Zda se uplatní, se rozhoduje
v přiznání; průvodce ukazuje částku.

V průvodci:

- **Zaúčtovat odloženou daň (návrh)** vytvoří doklad v *Deníku odložené daně*
  k poslednímu dni období, který dorovná zaúčtovaný zůstatek účtu 481 **ke
  konci období** na vypočtenou odloženou daň, se souvztažným účtem 592.
  Doklady s datem po konci období se nezapočítají. Zůstane jako návrh,
  není-li zaškrtnuto *Zaúčtovat odloženou daň ihned*.
- **Export XLSX** a **Tisk PDF** dají tabulku jako sešit nebo PDF.

Slovenské přiznání právnické osoby v modulu
[module:l10n_sk_dppo](module:l10n_sk_dppo) si řádky 150 a 250 načte z tohoto
modulu samo (připočtení za vozidlo ne — to zadáte sami, uplatní-li se), a to jako **souhrn za společnost**, kdežto průvodce ukazuje
připočitatelné a odečitatelné částky po jednotlivých majetcích. Český modul
přiznání tyto řádky z tohoto modulu nenačítá.

## Registr a analýza {#register}

- **Registr daňových odpisů** (*Účetnictví → Výkazy*): zvolte rok a klikněte
  na **Tisk registru**. PDF podle odpisových skupin: vstupní cena, počáteční
  zůstatková cena, odpis roku, oprávky, konečná zůstatková cena, způsob
  odpisování a účetní odpis s rozdílem, se součty za skupiny a celkovým
  součtem. Majetek s měsíčním plánem (§ 30a) je v něm jednou, se sečtenými
  měsíci roku. Záhlaví sloupců jsou slovensky a anglicky.
- **Účetní vs. daňové odpisy** (*Účetnictví → Výkazy*): kontingenční tabulka,
  graf a seznam účetních a daňových odpisů podle majetku, roku a skupiny.
  *Účetní odpis* počítá všechny účetní odpisy roku, *Účetní odpis
  (zaúčtovaný)* jen zaúčtované; filtr *Podáno* ukáže zmrazené roky.

## V Community — registr OCA {#oca}

[module:account_asset_tax_oca](module:account_asset_tax_oca) připojuje daňový
plán k registru OCA `account_asset_management`:

- záložka **Daňové odpisy** na kartě majetku; vstupní cena = pořizovací
  hodnota majetku, datum zařazení = datum zahájení odpisování;
- blok **Výchozí nastavení daňových odpisů** na profilu majetku (*Sledovat
  daňové odpisy*, skupina, způsob, zvýšený odpis v 1. roce), který se přenese
  na majetek založený s tímto profilem, nemá-li vlastní skupinu;
- vyřazení majetku průvodcem *Vyřadit* v registru zapíše daňové vyřazení k
  datu vyřazení;
- účetní odpisy = řádky odpisového plánu registru (zaúčtované = ty s účetním
  dokladem);
- na kartě majetku přejmenuje pole registru *Number of Years* na *Počet let*
  nebo *Počet období* podle metody času a vedle něj zobrazí délku období.

## V Enterprise — Majetek Odoo {#ee}

[module:account_asset_tax_ee](module:account_asset_tax_ee) připojuje daňový
plán k modulu *Majetek* v Odoo Enterprise:

- záložka **Daňové odpisy** za odpisovým plánem; vstupní cena = původní
  hodnota majetku, datum zařazení = datum prvního odpisu (jinak datum
  pořízení);
- výchozí daňové hodnoty na **odpisovacím modelu** se přenesou na majetek z
  něj založený, nemá-li vlastní skupinu;
- likvidace nebo prodej majetku zapíše daňové vyřazení k datu vyřazení;
- účetní odpisy = odpisové doklady majetku (zaúčtované = zaúčtované doklady;
  zrušené se nepočítají).

Nainstalovat lze jen jeden most, protože nainstalovaný může být jen jeden z
obou registrů majetku.

## Omezení {#limitations}

- **Plány uzavřené před verzí 19.0.1.10.0 si ponechají původní částky.** Do
  této verze plán zaokrouhloval české odpisy na haléře, majetku vyřazenému v
  prvním roce dal polovinu odpisu, každému slovenskému majetku dal v roce
  vyřazení poměrný odpis a slovenské automobily od 48 000 € odepisoval jen z
  této částky. Uzavřené roky jsou zmrazené, takže přepočet takového majetku
  se odmítne; byly-li uzavřené částky nesprávné, opravte je přes *Doplnit
  (migrace)*. Neuzavřené roky opraví **Vypočítat daňový odpisový plán**.
- **Zaokrouhlování podle § 30a** se uplatní na každý měsíční odpis (nahoru,
  dvanáctý měsíc se zastaví na 60 % v celých korunách). § 30a odst. 2
  neříká, zda se zaokrouhluje po měsících, nebo za zdaňovací období; roční
  součet se může od zaokrouhlení za rok lišit o několik korun.
- *Odpis za celé měsíce v roce vyřazení* se vůči majetku nekontroluje: zda
  jde o majetek podle § 26 ods. 6 a 7, nebo o majetek se zůstatkovou cenou
  omezenou příjmy z prodeje, i začátek druhého případu v roce 2016, ověřujete
  vy. Měsíc vyřazení se nikdy nepočítá jako celý měsíc.
- **Připočtení za vozidlo** porovnává odpisy s rovnoměrným odpisem ze
  48 000 € rok po roce v pořadí; po technickém zhodnocení, které dobu
  odpisování prodlouží, se roky navíc připočtou celé. Zda se připočtení
  vůbec uplatní, se nevyhodnocuje.
- **Podmínky se nekontrolují**: Odoo neví, zda jste první odpisovatel
  (§ 31 odst. 6), ani zda jde o majetek, který smí mít +15 % nebo +20 %
  (§ 31 odst. 2 a 3), nebo žádné zvýšení (§ 31 odst. 5), proto každý český
  majetek skupin 1–3 nabízí všechna tři zvýšení; podmínky musíte ověřit sami.
  Stejně tak podmínky § 30a (bezemisní vozidlo, pořízení 2024–2028, první
  odpisovatel).
- Technické zhodnocení dokončené v prvním roce se zpracuje jako událost, ne
  jako součást vstupní ceny; chce-li to účetní jinak, zahrňte je do *Daňové
  vstupní ceny*.
- Není pokryt nehmotný majetek, slovenské odpisování mikrodaňovníka (§ 26
  ods. 12), majetek odpisovaný podle doby trvání nebo výkonu (CZ § 30 odst. 4
  a 5, SK § 26 ods. 6 a 7), nižší než maximální české sazby, povinné přerušení
  (modul neví, kdy se majetek nepoužíval) ani hranice vstupní ceny
  (80 000 Kč / 1 700 €) — zda se majetek daňově odpisuje, rozhodujete vy.
- Porovnání zahrnuje jen odpisy. Rozdíl mezi účetní a daňovou zůstatkovou
  cenou vyřazeného majetku se nepočítá.
- Doklad odložené daně dorovnává **celý zaúčtovaný zůstatek** účtu 481 ke
  konci období, a to jen na rozdíl z odpisů. Použijte jej, jen pokud na tom
  účtu není nic jiného.
- Roky jsou kalendářní: společnost s hospodářským rokem odlišným od
  kalendářního dostane plány po kalendářních letech.
- Záhlaví registru jsou slovensko-anglická i pro české společnosti.
