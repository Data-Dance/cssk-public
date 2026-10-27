---
title: Odpisový plán majetku — přehled odpisů
summary: Interaktivní přehled pohybů dlouhodobého majetku a kontingenční analýza účetních odpisů pro evidenci majetku v Community (OCA account_asset_management).
verified: 19.0.1.0.2
---

## K čemu slouží {#purpose}

Evidence majetku v Community, OCA
[module:account_asset_management](module:account_asset_management), vede
odpisový plán každého majetku zvlášť, ale za celou evidenci nabízí jen
statickou sestavu v XLSX. Tento modul přidává dvě obrazovky pro kontrolu
**účetních odpisů** za celý majetek:

- **Odpisový plán (dynamický)** — přehled pohybů dlouhodobého majetku za
  libovolné období: pořizovací cena, oprávky na počátku, odpisy za období,
  vyřazení, oprávky na konci a zůstatková cena, po jednotlivých položkách
  majetku i po profilech majetku.
- **Analýza odpisů** — odpisové řádky v kontingenční tabulce a v grafu, podle
  majetku, profilu a roku.

Obě obrazovky čtou odpisové plány, nic neúčtují a nic nemění. Daňové odpisy
jsou samostatný, neúčtovaný odpisový plán s vlastními sestavami — viz
[module:account_asset_tax](module:account_asset_tax).

## Nastavení {#setup}

Nic se nenastavuje. Obě obrazovky jsou v nabídce *Fakturace → Majetky*
(*Účetnictví → Majetky*, je-li nainstalováno Účetnictví z Odoo Enterprise) jen pro uživatele se
skupinou *Zobrazit kompletní účetní funkcionality*
(`account.group_account_user`, přiděluje se na kartě uživatele); ostatní
uživatelé evidence majetku je nevidí.

Čísla jsou jen tak dobrá jako odpisové plány za nimi: majetek se zobrazí, až
je potvrzený a jeho odpisový plán spočítaný.

## Odpisový plán (dynamický) {#schedule}

*Majetky → Odpisový plán (dynamický)*. Nahoře zvolte **Od** a **Do**; výchozí
je aktuální účetní období aktivní společnosti. Přehled se přepočítá hned po
změně data.

Jeden řádek na položku majetku, seskupené podle **profilu majetku**, s
mezisoučtem za profil a řádkem **Celkem**. Kliknutím na řádek profilu jej
sbalíte nebo rozbalíte, kliknutím na majetek otevřete jeho kartu.

| Sloupec | Obsah |
|---|---|
| Majetek | Označení a název majetku. |
| Pořizovací cena | *Pořizovací cena* (*Purchase Value*) z karty majetku. |
| Oprávky k počátku období | Odpisové řádky s datem **před** *Od*. Patří sem i řádky označené jako *Počáteční zůstatkový zápis* (odpisy převzaté z předchozího systému). |
| + Odpisy | Odpisové řádky s datem od *Od* do *Do*. |
| Vyřazení / úbytky | U majetku vyřazeného v období zůstatková cena, která z evidence odešla — pořizovací cena − oprávky ke konci období. To je zůstatková hodnota odepsaná průvodcem vyřazení (*Vyřadit*) plus případná zbytková hodnota na konci životnosti. |
| Oprávky ke konci období | Oprávky na počátku + odpisy za období. |
| Zůstatková cena na konci | Pořizovací cena − oprávky ke konci období − vyřazení: zůstatková cena k datu *Do* včetně zbytkové hodnoty na konci životnosti; u majetku vyřazeného v období nula. |

**Zaúčtované i plánované řádky se počítají stejně.** Přehled ukazuje odpisový
plán, nejen to, co je v hlavní knize: období, které ještě nebylo zaúčtováno,
ukazuje plánované odpisy. Co je skutečně zaúčtováno, zjistíte v analýze níže
s filtrem *Zaúčtované*.

Zahrnut je majetek ve stavu *Běžící*, plně odepsaný (stav, který se v českém
překladu zobrazuje jako *Zavřít*) a vyřazený majetek s datem zahájení nejpozději
v den *Do*. Vyřazený majetek vypadne, je-li datum vyřazení před *Od*. Majetek
ve stavu *Návrh* se nezobrazuje. Plně odepsaný majetek, který společnost stále
drží, se zobrazuje dál, bez pohybu v období.

## Analýza odpisů {#analysis}

*Majetky → Analýza odpisů* otevře odpisové řádky (jen řádky typu *Odpis*, ne
řádky pořízení ani vyřazení, a žádné řádky majetku ve stavu *Návrh*) v
kontingenční tabulce: majetek v řádcích, roky ve
sloupcích, míra *Částka*. Graf zobrazí roční odpisy jako skládané sloupce.

Filtry a seskupení ve vyhledávání:

- **Zaúčtované** — řádky s účetním zápisem; **Plánované** — řádky dosud
  nezaúčtované;
- seskupení podle **Majetek**, **Profil majetku** nebo **Rok**.

*Částka* je jediná míra. Pole OCA *Odpis příštího období*, které navzdory
názvu obsahuje zůstatkovou hodnotu po daném řádku, je zůstatek: jeho součet
za řádky roku nedával smysl, proto se nenabízí.

## Omezení {#limitations}

- Přehled zobrazuje **jen aktivní společnost** v její měně, i když je zvoleno
  více společností. Analýza se řídí běžným výběrem společností a může je
  míchat.
- Přehled nelze vytisknout ani exportovat; použijte export z kontingenční
  tabulky nebo sestavu OCA *Výkaz finančního majetku* v nabídce *Výkazy*.
- Jen účetní odpisy. Daňové odpisy a rozdíl mezi oběma vykazuje
  [module:account_asset_tax](module:account_asset_tax).
- Jen pro evidenci majetku v Community. Odoo Enterprise má pro svou evidenci
  `account_asset` vlastní odpisový přehled.
