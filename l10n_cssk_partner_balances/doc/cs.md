---
title: CZ/SK odsouhlasení zůstatků a zápočet (saldokonto)
summary: Odsouhlasení otevřených pohledávek a závazků partnera k datu s PDF k podpisu a zápočet, který vzájemné pohledávky a závazky vyrovná v účetnictví.
verified: 19.0.1.2.1
---

## K čemu slouží {#purpose}

Dva běžné doklady saldokonta v česko-slovenském účetnictví:

1. **Odsouhlasení zůstatků.** Uložený doklad se seznamem otevřených
   pohledávek a závazků partnera k zvolenému datu, který vytisknete, pošlete
   partnerovi a označíte jako odsouhlasený nebo sporný. Používá se hlavně ke
   konci roku jako podklad k inventarizaci pohledávek a závazků.
2. **Zápočet.** Dohoda nebo jednostranné prohlášení, kterým se to, co dluží
   partner vám, započte proti tomu, co dlužíte vy jemu. Při zaúčtování
   vytvoří zápočtový účetní zápis a spáruje faktury.

Modul potřebuje jen modul Odoo `account` a
[module:l10n_cssk_core](module:l10n_cssk_core), takže funguje v edici
Community i Enterprise. Pracovat s ním mohou uživatelé s oprávněním
*Zobrazit kompletní účetní funkcionality* nebo *Administrátor* účetnictví;
mazat doklady může jen administrátor.

## Právní rámec {#legal}

**Inventarizace.** Potvrzení od partnera nevyžaduje ani jeden zákon
o účetnictví, oba ale ukládají ověřit pohledávky a závazky k rozvahovému dni
a jejich skutečný stav se zjišťuje dokladovou inventurou:

- **Česko:** [§ 29 odst. 1 a § 30 odst. 1 písm. b) zákona
  o účetnictví](law:cz/1991/563) — periodická inventarizace k okamžiku,
  ke kterému se sestavuje účetní závěrka; u závazků a majetku, u kterého
  nelze vizuálně zjistit jeho existenci, se provádí dokladová inventura.
  Podle [§ 30 odst. 4 a 6](law:cz/1991/563) lze stanovit rozhodný den před
  rozvahovým dnem a inventuru ukončit nejpozději dva měsíce po rozvahovém dni.
- **Slovensko:** [§ 29 ods. 1 a 2](law:sk/2002/431#paragraf-29.odsek-1) a
  [§ 30 ods. 1](law:sk/2002/431#paragraf-30.odsek-1) zákona o účtovníctve —
  inventarizací účetní jednotka ověřuje, zda stav v účetnictví odpovídá
  skutečnosti, provádí ji ke dni sestavení účetní závěrky a u závazků
  a majetku, u kterého nelze provést fyzickou inventuru, se skutečný stav
  zjišťuje dokladovou inventurou.

Odsouhlasení zůstatků podepsané partnerem je běžným podkladem této dokladové
inventury.

**Zápočet.**

- **Česko:** podle [§ 1982 občanského zákoníku](law:cz/2012/89) může každá
  strana prohlásit, že svou pohledávku započítává proti pohledávce druhé
  strany, dluží-li si vzájemně plnění stejného druhu, a to jakmile může
  požadovat uspokojení vlastní pohledávky a plnit svůj dluh. Pohledávky se
  ruší v rozsahu, v jakém se kryjí, a tyto účinky nastávají *„k okamžiku, kdy
  se obě pohledávky staly způsobilými k započtení“*. [§ 1987](law:cz/2012/89)
  připouští jen pohledávky, které lze uplatnit před soudem a nejsou nejisté
  ani neurčité, a podle [§ 1991](law:cz/2012/89) zákaz jednostranného
  započtení nebrání stranám, aby si započtení ujednaly.
- **Slovensko:** podle [§ 580 Občianskeho zákonníka](law:sk/1964/40#paragraf-580)
  vzájemné pohledávky stejného druhu zaniknou započtením, pokud se kryjí,
  učiní-li některý z účastníků projev směřující k započtení, a to k okamžiku,
  kdy se setkaly. [§ 581 ods. 2](law:sk/1964/40#paragraf-581.odsek-2) mimo
  jiné vylučuje započtení promlčených pohledávek a nesplatné pohledávky proti
  splatné, [§ 581 ods. 3](law:sk/1964/40#paragraf-581.odsek-3) je dovoluje
  dohodou. Mezi podnikateli Obchodný zákonník doplňuje, že započíst lze jen
  pohledávky uplatnitelné u soudu ([§ 358](law:sk/1991/513#paragraf-358)),
  nesplatnou proti splatné jen vůči dlužníkovi, který není schopen plnit své
  peněžité závazky ([§ 359](law:sk/1991/513#paragraf-359)), a pohledávky
  v různých měnách jen tehdy, jsou-li volně směnitelné, kurzem dne, kdy se
  staly způsobilými k započtení ([§ 362](law:sk/1991/513#paragraf-362)).

Z toho vycházejí dva režimy modulu: **dvoustranná dohoda** o započtení,
kterou podepíší obě strany, a **jednostranný zápočet**, tedy prohlášení
doručené druhé straně, které lze použít jen u pohledávek splňujících zákonné
podmínky. Modul tyto podmínky nekontroluje.

## Odsouhlasení zůstatků {#confirmation}

*Účetnictví → Zákazníci → Odsouhlasení zůstatků*, potom *Nový*:

| Pole | Význam |
|---|---|
| Partner | Společnost (ne kontaktní osoba). Zahrnou se otevřené položky všech jejích kontaktů. |
| Kontakt | Osoba, které je odsouhlasení určeno. |
| K datu | Datum, ke kterému se zůstatek odsouhlasuje, obvykle 31. 12. |
| Typ potvrzení | *Pouze pohledávky*, *Pouze závazky* nebo *Pohledávky a závazky*. |

Klikněte na **Vypočítat**. Karta *Otevřené položky* se naplní všemi
zaúčtovanými položkami partnera na účtech pohledávek a závazků, které byly
otevřené **k zvolenému datu**: úhrada nebo spárování s pozdějším datem se
přičte zpět, takže odsouhlasení k 31. 12. sestavené v únoru ukáže i fakturu
uhrazenou v lednu, a to v plné částce, která byla otevřená k 31. 12.
*Pohledávky celkem*, *Závazky celkem* a *Čistý zůstatek* (kladný = partner
dluží vám) se počítají z řádků.

Řádky jsou **snímkem**: mají vlastní kopii čísla dokladu, dat a částky, takže
odsouhlasení zůstane takové, jaké jste odeslali, i když se účetnictví později
změní. Opětovným **Vypočítat** ho sestavíte znovu; to jde ve stavu *Koncept*
a *Odesláno*.

Postup:

1. **Tisk** (zobrazí se, když odsouhlasení není konceptem) vytvoří PDF
   *Odsouhlasení zůstatků (saldokonto)* s oběma společnostmi, seznamem
   položek, součty a dvěma podpisovými řádky. **Označit jako odeslané** změní
   stav na *Odesláno*; e-mail neodešle — PDF pošlete sami, například
   z chatteru.
2. Když partner odpoví, klikněte na **Dohodnuto** nebo **Sporné**.
3. Rozporuje-li partner jednotlivé položky, označte na těchto řádcích
   **Blokováno**. V PDF zůstanou, šedé a s poznámkou *(sporné)*, do součtů se
   ale nezapočítají.

**Vytvořit odsouhlasení zůstatků** (*Účetnictví → Zákazníci*) je vytvoří
hromadně: zvolte společnost, datum, typ a případně partnery — nevyberete-li
je, dostane je každý partner s otevřenou položkou k tomu dni — a vypočtená
odsouhlasení se otevřou v seznamu.

PDF je česky nebo slovensky podle země společnosti, s angličtinou, a strany
označuje neutrálně (*Účetní jednotka* a *Partner*), protože při odsouhlasení
závazků je vaše společnost dlužníkem.

Odsouhlasené nebo sporné odsouhlasení je zmrazené: řádky nelze měnit a doklad
nelze smazat, jen zrušit. **Nastavit na koncept** ho uvolní. Odsouhlasení se
číslují `SALDO/<rok>/0001`.

## Zápočet {#netting}

*Účetnictví → Dodavatelé → Dohody o zápočtu*, potom *Nový*:

1. Zvolte **Partnera**, **Datum dohody**, měnu (*Currency*) a **Režim
   zápočtu** — *Dvoustranná dohoda* nebo *Jednostranný zápočet*. Volitelně
   zvolte **Zúčtovací deník**; bez něj se použije první deník typu Ostatní
   společnosti.
2. Na kartách **Pohledávky** a **Závazky** přidejte otevřené účetní položky,
   které se mají započíst, a ve sloupci *Částka k zápočtu* kolik z každé.
   Započíst lze i část položky, ne však víc, než je její otevřená částka.
   Nabízejí se jen zaúčtované otevřené pohledávky a závazky partnera ze
   zápočtu.
3. Zaúčtovat lze, jen když se součet pohledávek rovná součtu závazků (*Je
   vyrovnáno*); tato částka je *Částka zápočtu*.

Položka patří na stranu podle toho, kdo komu dluží, ne podle účtu: otevřený
dobropis odběrateli je váš dluh vůči partnerovi a patří mezi závazky,
dobropis od dodavatele mezi pohledávky.

Postup se liší podle režimu:

| Režim | Kroky |
|---|---|
| Dvoustranná dohoda | Potvrdit → Označit jako odeslané → Odsouhlaseno protistranou → Zaúčtovat |
| Jednostranný zápočet | Potvrdit → Označit jako odeslané → Zaúčtovat (bez podpisu protistrany) |

**Vytvořit zápočet** (*Účetnictví → Dodavatelé*) zápočet navrhne: zvolte
partnera, datum a měnu a průvodce načte otevřené položky partnera a rozdělí
nejvyšší vyrovnanou částku, od nejstarších položek.

Řádky lze měnit jen ve stavu *Koncept*. PDF *Zápočet* z nabídky *Tisk* má
podle režimu nadpis dohody se dvěma podpisovými řádky, nebo oznámení
o jednostranném započtení s jedním.

**Zaúčtovat** nejprve ověří, zda je každá položka stále otevřená alespoň
v dohodnuté částce (mezitím mohla přijít úhrada), pak vytvoří účetní zápis
s datem dohody, který každou pohledávku zaúčtuje na stranu Dal a každý závazek
na stranu Má dáti v částce k zápočtu, a každou položku spáruje s jejím
vlastním řádkem zápočtu, takže částečné zápočty se zachovají přesně. Zápočty
se číslují `ZAP/<rok>/0001`.

**Cizí měna.** V měně společnosti lze započíst každou otevřenou položku v její
zaúčtované částce. V cizí měně jen položky v této měně; částky jsou v ní,
zápočtový zápis se zaúčtuje kurzem ke dni dohody a rozdíl oproti kurzu každé
faktury se při spárování zaúčtuje jako kurzový rozdíl.

**Zrušit storno-zápisem** u zaúčtovaného zápočtu zruší spárování a zápočtový
zápis stornuje, takže každá položka je znovu otevřená přesně jako předtím.
Zaúčtovaný zápočet nelze smazat.

## Omezení {#limitations}

- Modul nekontroluje zákonné podmínky jednostranného zápočtu (splatnost,
  uplatnitelnost u soudu, zákazy) ani souhlas partnera; to je na vás.
- Zápočtový zápis má datum dohody a v cizí měně kurz toho dne. Samotné
  pohledávky se ruší k okamžiku, kdy se staly způsobilými k započtení (§ 1982
  občanského zákoníku, na Slovensku § 580 Občianskeho zákonníka), což PDF
  uvádí; chce-li účetní zápis k tomuto dni, zvolte jej jako datum dohody.
- Obě PDF se řídí zemí společnosti — české znění a DIČ pro českou společnost,
  jinak slovenské znění a IČ DPH — s angličtinou vedle. Znění si před prvním
  použitím nechte zkontrolovat.
- PDF odsouhlasení ukazuje částky jen v měně společnosti.
- *Označit jako odeslané* jen změní stav; nic se neodešle e-mailem.
