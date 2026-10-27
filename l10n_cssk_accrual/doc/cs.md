---
title: Dohadné položky CZ/SK
summary: Zaúčtování odhadu nákladu nebo výnosu, ke kterému do konce období nepřišla faktura, a jeho vyrovnání se skutečnou fakturou tak, aby v novém období zůstal jen rozdíl.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Ke konci období jsou některé náklady už spotřebované, ale ještě
nevyfakturované: elektřina za prosinec, služba poskytnutá v prosinci a
fakturovaná v lednu, odměna auditora za uzavíraný rok. V Česku se takové
položky účtují na **dohadných účtech** (388 aktivní, 389 pasivní); na
Slovensku na účtu **326** *Nevyfaktúrované dodávky*, případně jako rezerva,
není-li výše jistá (viz [Právní rámec](#legal)).

Odoo takový doklad nemá. Modul přidává **dohadnou položku**: odhad zadáte a
zaúčtujete ke konci období, a když dorazí faktura, propojíte ji a dohadnou
položku vyrovnáte. Vyrovnání zaúčtuje storno odhadu k datu faktury, takže se
dohadný účet vynuluje a do nového období připadne jen rozdíl mezi odhadem a
fakturou.

Dohadná položka není časové rozlišení: to rozkládá **známou** částku do více
období a řeší ho moduly
[module:l10n_cz_account_cutoff](module:l10n_cz_account_cutoff) a
[module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff).

Modul funguje s jakoukoli účtovou osnovou: účty a deník vybíráte u každé
dohadné položky. Potřebuje jen modul `account` a
[module:l10n_cssk_core](module:l10n_cssk_core), takže běží v edici Community
i Enterprise.

## Právní rámec {#legal}

Oba zákony o účetnictví požadují účtovat o skutečnostech v období, s nímž
časově a věcně souvisejí — [§ 3 odst. 1 zákona o účetnictví](law:cz/1991/563)
a [§ 3 ods. 1 slovenského zákona o účtovníctve](law:sk/2002/431#paragraf-3.odsek-1).
Způsob zachycení nevyfakturované položky se liší:

- **Česko.** [Vyhláška č. 500/2002 Sb.](law:cz/2002/500) (§ 10 odst. 7,
  § 17 odst. 6 a příloha č. 1) vymezuje *dohadné účty aktivní* a *dohadné
  účty pasivní* jako částky stanovené například podle smluv, které nejsou
  doloženy veškerými potřebnými doklady, a tedy není známa jejich přesná
  výše. Jde o účty 388 a 389.
- **Slovensko.** [Opatrenie 740/2002 Z. z.](law:sk/2002/740) dohadné účty
  nezná. Na účet **326** *Nevyfaktúrované dodávky* se účtují položky, jejichž
  výši účetní jednotka **zná** ze smlouvy, dodacího listu nebo jiného dokladu
  ([§ 50 ods. 6](law:sk/2002/740#paragraf-50.odsek-6)); je-li neurčité
  časové vymezení nebo výše závazku, tvoří se krátkodobá rezerva na účtu 323
  ([§ 50 ods. 3](law:sk/2002/740#paragraf-50.odsek-3)). Nevyfakturovaná
  pohledávka se účtuje na příslušném účtu pohledávek na samostatném
  analytickém účtu ([§ 48 ods. 3](law:sk/2002/740#paragraf-48.odsek-3)).

Modul zaúčtuje na účty, které mu zadáte. Který účet se na danou položku
použije — a na Slovensku, zda jde o nevyfakturovanou dodávku, nebo o
rezervu — rozhoduje vaše účetní.

## Nastavení {#setup}

Modul nemá žádná nastavení. Před první dohadnou položkou:

- **Povolte párování na dohadném účtu.** Při vyrovnání se odhad páruje se
  stornem právě na tomto účtu, proto modul odmítne zaúčtovat, nemá-li účet
  zaškrtnuto *Povolit párování plateb* (tak Odoo v češtině nazývá *Allow
  Reconciliation*). Česká osnova Odoo má účty 388000 a 389000 a slovenská
  účet 326000 **bez** něj: otevřete účet v *Účetnictví → Konfigurace →
  Účetnictví → Účtová osnova* a zaškrtněte ho.
- **Deník typu Ostatní.** Dohadné položky se účtují v deníku typu *Ostatní*.

Nabídka je v *Účetnictví → Účetnictví*; v edici Community se zobrazí, jen
jsou-li zapnuty úplné účetní funkce, a samotná aplikace se tam jmenuje
*Fakturace*.

## Zadání dohadné položky {#usage}

*Účetnictví → Účetnictví → Transakce → Dohadné položky*, potom *Nový*.

| Pole | Co vyplnit |
|---|---|
| Partner | Dodavatel (nebo odběratel), od něhož (nebo jemuž) se faktura očekává. Povinné. |
| Typ dohadné položky | **Odhadovaný závazek** — nevyfakturovaný náklad; nebo **Odhadovaná pohledávka** — nevyfakturovaný výnos. |
| Datum | Datum zaúčtování odhadu, obvykle poslední den období. |
| Částka | Odhadovaná částka v měně společnosti, bez DPH. Musí být kladná. |
| Popis | Vytiskne se na obou řádcích zápisu. |
| Deník | Deník společnosti typu *Ostatní*. |
| Účet dohadné položky | 389 / 388 (CZ). Na Slovensku 326 pro nevyfakturovanou dodávku, nebo samostatný analytický účet pohledávky pro nevyfakturovanou pohledávku — podle rozhodnutí účetní. |
| Protiúčet | Nákladový účet (u odhadovaného závazku) nebo výnosový účet (u odhadované pohledávky). |

Klikněte na **Zaúčtovat odhad**. Modul vytvoří a zaúčtuje jeden zápis,
číslovaný od `DOHAD/<rok>/0001`:

| Typ dohadné položky | MD | D |
|---|---|---|
| Odhadovaný závazek | protiúčet (náklad) | dohadný účet |
| Odhadovaná pohledávka | dohadný účet | protiúčet (výnos) |

Oba řádky nesou partnera. Zápis je bez DPH: odhad není daňový doklad.

## Vyrovnání se skutečnou fakturou {#settle}

Skutečnou fakturu zaúčtujte obvyklým způsobem na nákladový nebo výnosový
účet. Potom otevřete dohadnou položku:

1. V poli **Skutečná faktura** vyberte fakturu. Nabídnou se zaúčtované
   faktury a opravné daňové doklady téhož partnera a společnosti.
2. Klikněte na **Vyrovnat (propojit fakturu)**.

Modul zaúčtuje storno zápisu odhadu k **datu faktury** (nebo k datu odhadu,
je-li faktura datována dříve) a odhad se stornem spáruje na dohadném účtu.
Dohadný účet se pro tuto položku vynuluje, storno v novém období zruší
odhadovaný náklad a faktura zaúčtuje skutečný. V novém období zůstane přesně
rozdíl.

Příklad: odhad 1 000 za elektřinu za prosinec, lednová faktura 1 050 bez DPH.
V lednu storno zaúčtuje 1 000 ve prospěch nákladu a faktura 1 050 na vrub
nákladu — v lednu zůstane 50, v prosinci 1 000.

Dohadná položka přejde do stavu *Vyrovnáno*; pole *Účetní zápis odhadu* a
*Vyrovnávací / storno zápis* odkazují na oba zápisy.

## Zrušení dohadné položky {#cancel}

**Zrušit** u zaúčtované dohadné položky zaúčtuje storno k **dnešnímu datu**,
spáruje ho a položku nastaví na *Zrušeno*. Položka ve stavu koncept se jen
zruší.

**Nastavit na koncept** vrátí zrušenou položku do konceptu, aby ji šlo opravit
a znovu zaúčtovat. Zrušený zápis a jeho storno zůstanou v účetnictví (vzájemně
se vyruší) a chatter je uvede; nové zaúčtování vytvoří nový zápis.

Před každým stornem (při vyrovnání i zrušení) proběhnou dvě kontroly:

- Je-li řádek na dohadném účtu už spárován s něčím jiným, modul storno
  odmítne a uvede zápisy, s nimiž je spárován. Nejprve párování zrušte.
- Padne-li datum storna do uzamčeného období, modul ho odmítne a uvede, o
  který zámek jde. Upravte datum uzamčení nebo vyrovnejte proti faktuře s
  pozdějším datem.

## Omezení {#limitations}

- Modul odhad s fakturou neporovnává a fakturu s ničím nepáruje. Nekontroluje
  ani typ: propojit lze jakoukoli zaúčtovanou fakturu nebo opravný daňový
  doklad partnera.
- Jedna dohadná položka se vyrovná s jednou fakturou. Odhad za více faktur je
  třeba rozdělit na více položek, nebo ho vyrovnat s jednou z nich a ostatní
  zaúčtovat běžně.
- Částky jsou jen v měně společnosti; odhad v cizí měně ani analytické
  rozúčtování zápis nepodporuje.
- Zrušení stornuje k dnešnímu datu, ne k datu, které si zvolíte.
- Nic se neodhaduje automaticky a modul neupozorní na dohadné položky, které
  zůstaly otevřené i při další závěrce; filtrujte seznam podle stavu
  *Zaúčtováno*.
