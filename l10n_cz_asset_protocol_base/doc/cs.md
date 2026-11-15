---
title: CZ Protokoly o zařazení a vyřazení majetku
summary: Protokol o zařazení dlouhodobého majetku do užívání a protokol o jeho vyřazení, tištěné z evidence majetku v kterékoli edici Odoo.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Ke každému dlouhodobému majetku vyhotovuje účetní dva interní doklady:

- **Protokol o zařazení dlouhodobého majetku do užívání** — inventární
  číslo, ocenění (zpravidla pořizovací cena), datum uvedení do užívání, místo
  umístění a odpovědná osoba;
- **Protokol o vyřazení dlouhodobého majetku** — důvod a způsob vyřazení a
  hodnoty majetku v tom okamžiku.

Modul doplňuje údaje, které protokol potřebuje a evidence majetku je nemá, a
obě tiskové sestavy. Pracuje s tou evidencí majetku, která je nainstalována:

| Edice | Evidence majetku | Propojení (nainstaluje se samo) |
|---|---|---|
| Community | OCA `account_asset_management` | [module:l10n_cz_asset_protocol_oca](module:l10n_cz_asset_protocol_oca) — viz [Community](#community) |
| Enterprise | Odoo `account_asset` | [module:l10n_cz_asset_protocol_ee](module:l10n_cz_asset_protocol_ee) — viz [Enterprise](#enterprise) |

Nainstalujte tento modul, příslušné propojení se doinstaluje samo. Bez
evidence majetku se modul nainstaluje, ale nic nezobrazí.

## Právní rámec {#legal}

Ani jeden protokol nemá předepsaný vzor. Oba jsou interními účetními doklady
a účetní doklad musí podle
[§ 11 odst. 1 zákona o účetnictví](law:cz/1991/563) obsahovat:

- a) označení účetního dokladu,
- b) obsah účetního případu a jeho účastníky,
- c) peněžní částku nebo informaci o ceně za měrnou jednotku a vyjádření
  množství,
- d) okamžik vyhotovení účetního dokladu,
- e) okamžik uskutečnění účetního případu, není-li shodný s okamžikem podle
  písmene d),
- f) podpisový záznam osoby odpovědné za účetní případ a podpisový záznam
  osoby odpovědné za jeho zaúčtování.

Výstupy obsahují označení dokladu a datum vyhotovení, účetní jednotku se
sídlem a IČO, majetek a jeho hodnoty, datum uvedení do užívání nebo vyřazení
a řádky pro podpisy — včetně obou, které požaduje písmeno f). Další obsah
protokolů určuje vnitřní předpis účetní jednotky; šablony berte jako
východisko.

Obsah vychází ještě ze tří pramenů:

- Dlouhodobým majetkem se věc stává uvedením do stavu způsobilého k užívání
  ([§ 7 odst. 11 vyhlášky č. 500/2002 Sb.](law:cz/2002/500)); toto datum
  protokol o zařazení uvádí. Majetek se odpisuje podle odpisového plánu
  ([§ 28 odst. 6 zákona o účetnictví](law:cz/1991/563),
  [§ 56 odst. 4 vyhlášky](law:cz/2002/500)), proto protokol plán jmenuje.
- Český účetní standard pro podnikatele č. 013 (Dlouhodobý nehmotný a hmotný
  majetek) vyjmenovává způsoby vyřazení majetku (bod 5.4) — to jsou možnosti
  pole *Způsob vyřazení* níže — a zůstatkovou cenu vymezuje jako rozdíl mezi
  oceněním majetku a oprávkami (bod 4.4).
- Pro daňové účely se hmotný majetek v prvním roce odpisování zatřídí do
  odpisové skupiny a odpisuje se rovnoměrně nebo zrychleně
  ([§ 30 odst. 1 a 2 zákona o daních z příjmů](law:cz/1992/586)). V praxi se
  obojí uvádí už na protokolu o zařazení, viz [Tisk](#printing).

## Údaje pro protokoly {#usage}

Otevřete majetek a záložku **Protokoly (CZ)**:

| Blok | Pole | Význam |
|---|---|---|
| Zařazení | Inventární číslo (*Inventory number*) | Číslo v evidenci majetku. Je-li prázdné, protokoly vytisknou vlastní označení z evidence (viz propojení). |
| | Místo umístění (*Location*) | Kde se majetek nachází. |
| | Odpovědná osoba (*Responsible person*) | Kontakt. |
| | Poznámka k zařazení (*Commissioning note*) | Technický stav, příslušenství, doklady tvořící přílohu. |
| | Datum vyhotovení protokolu o zařazení (*Commissioning protocol date*) | Kdy byl protokol vyhotoven. Prázdné: protokol uvede den tisku; vyplňte je, aby byl i pozdější tisk stejný. |
| Vyřazení | Způsob vyřazení (*Disposal method*) | Prodej, likvidace, dar nebo jiný bezúplatný převod, vklad do jiné obchodní korporace, převod na základě právních předpisů, škoda nebo manko, převod z podnikání do osobního užívání, jiný. |
| | Důvod vyřazení (*Disposal reason*) | Volný text. |
| | Datum vyhotovení protokolu o vyřazení (*Disposal protocol date*) | Jako u protokolu o zařazení. |

Způsob vyřazení se eviduje jen pro protokol: majetek nevyřadí a nic
nezaúčtuje. Vyřazení proveďte funkcí samotné evidence majetku.

## Tisk {#printing}

Na majetku *Tisk*:

Oba protokoly začínají označením dokladu — **ZP-** (zařazení) nebo **VP-**
(vyřazení) a inventární číslo — datem vyhotovení a názvem, sídlem a IČO
účetní jednotky.

- **Protokol o zařazení majetku** — datum uvedení do užívání, název majetku,
  inventární číslo, ocenění (pořizovací cena), účetní odpisový plán (profil
  nebo model majetku), místo umístění, odpovědná osoba, poznámka a řádky pro
  podpis *Majetek předal* / *Majetek převzal*.
- **Protokol o vyřazení majetku** — datum vyřazení, název majetku, inventární
  číslo, datum uvedení do užívání, ocenění (pořizovací cena), oprávky,
  zůstatková cena, způsob a důvod vyřazení, upozornění, že přílohy dokládající
  způsob vyřazení jsou nedílnou součástí protokolu, a řádky pro podpis
  *Vyřazení navrhl* / *Vyřazení schválil*.

Oba končí dvěma podpisovými řádky podle § 11 odst. 1 písm. f): *Osoba
odpovědná za účetní případ* a *Osoba odpovědná za zaúčtování*.

Je-li nainstalován [module:account_asset_tax](module:account_asset_tax) a
majetek má zapnuté daňové odpisy s českou odpisovou skupinou, přibudou na
protokolu o zařazení dva řádky: *Odpisová skupina (daňové odpisy)* a *Způsob
daňového odpisování* (rovnoměrné, zrychlené nebo mimořádné). Bez tohoto
modulu se řádky netisknou.

Hodnoty na sebe vždy navazují: ocenění − oprávky = zůstatková cena, tedy
účetní zůstatková cena včetně zbytkové hodnoty, kterou odpisový plán
neodepisuje. Oprávky jsou jen zaúčtované odpisy; na protokolu o vyřazení již
vyřazeného majetku neobsahují odepsanou zůstatkovou cenu, ta je v řádku
*Zůstatková cena*.

Výstupy jsou vždy česky, včetně způsobu vyřazení; data se tisknou ve formátu
jazyka uživatele. Oba lze vytisknout kdykoli; protokol o vyřazení majetku,
který ještě vyřazen není, má prázdné datum vyřazení.

## Community: evidence majetku OCA {#community}

[module:l10n_cz_asset_protocol_oca](module:l10n_cz_asset_protocol_oca) se
nainstaluje sám, je-li nainstalován tento modul i OCA
`account_asset_management`. Majetek je v nabídce *Účetnictví → Majetky →
Majetky* (nabídka modulu OCA). Protokoly berou:

| Na protokolu | Z majetku OCA |
|---|---|
| Datum uvedení do užívání | *Datum zahájení majetku* (Asset Start Date) |
| Ocenění (pořizovací cena) | *Pořizovací cena* (Purchase Value) |
| Oprávky | zaúčtované řádky odpisů (ne řádek vyřazení) |
| Zůstatková cena | *Pořizovací cena* − oprávky (včetně neodepsatelné hodnoty) |
| Účetní odpisový plán | *Profil majetku* (Asset Profile) |
| Datum vyřazení | *Datum vyřazení majetku* (Asset Removal Date), které nastaví průvodce vyřazením |
| Inventární číslo, je-li prázdné | *Odkaz* (Reference) |

## Enterprise: evidence majetku Odoo {#enterprise}

[module:l10n_cz_asset_protocol_ee](module:l10n_cz_asset_protocol_ee) se
nainstaluje sám, je-li nainstalován tento modul i `account_asset` z Odoo
Enterprise. Majetek je v nabídce *Účetnictví → Účetnictví → Aktiva a pasiva →
Majetek*. Protokoly berou:

| Na protokolu | Z majetku Enterprise |
|---|---|
| Datum uvedení do užívání | *Datum pořízení* |
| Ocenění (pořizovací cena) | *Původní hodnota* majetku a jeho zvýšení hodnoty (podřízený majetek) |
| Oprávky | zaúčtované odpisy majetku a jeho zvýšení hodnoty včetně odpisů importovaných jako již provedené; ne zápis vyřazení ani prodeje |
| Zůstatková cena | ocenění − oprávky (včetně neodepsatelné hodnoty) |
| Účetní odpisový plán | *Odpisovací model* |
| Datum vyřazení | *Datum likvidace*, nastavené při vyřazení nebo prodeji |
| Inventární číslo, je-li prázdné | název majetku |

Obě propojení současně nainstalovat nelze, protože se obě evidence majetku
navzájem vylučují.

## Omezení {#limitations}

- Označení dokladu se odvozuje z inventárního čísla (nebo z označení v
  evidenci); jedinečnost inventárních čísel Odoo nekontroluje.
- Řádek se jmenuje *Ocenění (pořizovací cena)* bez ohledu na způsob ocenění;
  u majetku oceněného reprodukční pořizovací cenou nebo vlastními náklady
  šablonu upravte.
- Datem uvedení do užívání je datum zahájení, resp. pořízení z evidence;
  samostatné datum pořízení protokoly nevedou.
- Protokoly netisknou daňovou vstupní cenu ani daňovou zůstatkovou cenu; ty
  vede [module:account_asset_tax](module:account_asset_tax).
- Odpovědná osoba je libovolný kontakt, nijak nesouvisí se zaměstnancem ani
  s hmotně odpovědnou osobou při inventarizaci.
- Podpisové řádky jsou určeny pro vlastnoruční podpis; elektronické podpisové
  záznamy modul nevytváří.
