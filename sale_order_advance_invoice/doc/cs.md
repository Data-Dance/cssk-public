---
title: Zálohové faktury (prodej)
summary: Zálohová faktura jako samostatný doklad, daňový doklad ke každé přijaté platbě a odečtení zálohy na vyúčtovací faktuře.
verified: 19.0.2.8.0
---

## K čemu slouží {#purpose}

Záloha se v české i slovenské praxi řeší třemi doklady:

1. **zálohová faktura** — výzva k platbě; není účetním ani daňovým dokladem
   a neúčtuje se;
2. **daňový doklad k přijaté platbě** (na Slovensku *faktúra k prijatej
   platbe*) — vystavuje se po přijetí peněz, protože povinnost přiznat daň
   vzniká dnem přijetí úplaty;
3. **vyúčtovací (konečná) faktura** — celé plnění, od kterého se odečte
   záloha i daň z ní již přiznaná, takže se DPH odvede jen jednou.

Zálohy ve standardním Odoo zaúčtují fakturu za zálohu okamžitě. Tento modul
místo toho vede zálohovou fakturu jako samostatný doklad podobný nabídce
s čísly `ADV00001`, `ADV00002`…, který zákazník uhradí QR kódem, přes
zákaznický portál nebo převodem. Do účetnictví se dostane až platba
a daňový doklad k ní.

Modul je nezávislý na zemi. České a slovenské účty nastaví lokalizační
doplňky popsané v části [Lokalizační doplňky](#localization). Stranu
dodavatele řeší modul
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice).

## Právní rámec {#legal}

**Česko** — [zákon č. 235/2004 Sb., o dani z přidané hodnoty](law:cz/2004/235):

- § 20a odst. 2: je-li před uskutečněním zdanitelného plnění přijata úplata,
  vzniká povinnost přiznat daň z této úplaty ke dni jejího přijetí — to
  neplatí, není-li plnění ke dni přijetí úplaty známo dostatečně určitě.
  Podle § 20a odst. 3 musí být známo alespoň zboží nebo služba, sazba daně
  a místo plnění.
- § 28 odst. 1 písm. d) ukládá vystavit daňový doklad při přijetí takové
  úplaty a § 28 odst. 8 lhůtu: do 15 dnů ode dne, kdy vznikla povinnost
  přiznat daň.
- § 36 odst. 2: základem daně je přijatá úplata snížená o daň.
- § 37a: při uskutečnění plnění je základem daně rozdíl mezi základem za celé
  plnění a souhrnem základů ze záloh; je-li záporný, uplatní se sazba a kurz
  použité při přiznání daně ze záloh.

**Slovensko** — [zákon o DPH](law:sk/2004/222):

- Daňová povinnost z platby prijatej pred dodaním vzniká dňom jej prijatia —
  [§ 19 ods. 4](law:sk/2004/222#paragraf-19.odsek-4).
- Faktúru k prijatej platbe je platiteľ povinný vyhotoviť pri dodaní inej
  zdaniteľnej osobe alebo právnickej osobe —
  [§ 72 ods. 1 písm. f)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-f) a
  [písm. g)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-g) — do 15 dní odo
  dňa prijatia platby **alebo** do konca kalendárneho mesiaca, v ktorom bola
  platba prijatá —
  [§ 73 ods. 1 písm. b)](law:sk/2004/222#paragraf-73.odsek-1.pismeno-b).
- Faktúra uvádza dátum prijatia platby, ak sa líši od dátumu vyhotovenia —
  [§ 74 ods. 1 písm. d)](law:sk/2004/222#paragraf-74.odsek-1.pismeno-d).

## Nastavení {#setup}

*Prodej → Konfigurace → Nastavení*, blok **Fakturace**:

| Nastavení | Účel |
|---|---|
| Deník daňových dokladů k zálohám | Deník pro daňové doklady k přijatým platbám. Při instalaci modul vytvoří pro aktuální společnost obecný deník **TDADV** a nastaví ho. |
| Zúčtovací účet záloh | Párovatelný účet, na kterém se setká platba s daňovým dokladem, např. 324001. |
| Účet přijatých záloh (krátkodobé) | Nese zálohu bez DPH až do vyúčtování, např. 324000. |
| Účet přijatých záloh (dlouhodobé) | Totéž pro zálohy označené jako *Dlouhodobá záloha*, např. 475000. |

Bez lokalizačního doplňku vyplňte tři účty sami.

Před první zálohou zkontrolujte také:

- **Bankovní účet společnosti** — zálohová faktura vytiskne bankovní účet
  společnosti, přednostně v měně objednávky, a jsou-li v nastavení fakturace
  zapnuté QR kódy, i platební QR kód.
- **Produkt *Advance*** (v překladu *Záloha*) — vznikne při první záloze
  a je produktem všech řádků zálohy, pokud nezvolíte *Zahrnout objednané
  položky* (viz [níže](#create)). Jeho daně z prodeje určují DPH takových
  záloh.

### Lokalizační doplňky {#localization}

[module:l10n_cz_sale_order_advance_invoice](module:l10n_cz_sale_order_advance_invoice)
a
[module:l10n_sk_sale_order_advance_invoice](module:l10n_sk_sale_order_advance_invoice)
vyplní uvedená nastavení každé společnosti s českou nebo slovenskou účtovou
osnovou — při instalaci a znovu pokaždé, když se osnova načte později,
například pro novou společnost:

| Role | Účet | Český název | Slovenský název |
|---|---|---|---|
| Zúčtovací účet (vytvoří ho doplněk, párovatelný) | 324001 | Přijaté zálohy – zúčtování (daňový doklad) | Prijaté preddavky – zúčtovanie (daňový doklad) |
| Přijaté zálohy, krátkodobé | 324000 | Přijaté provozní zálohy | Prijaté preddavky |
| Přijaté zálohy, dlouhodobé | 475000 | Dlouhodobé přijaté zálohy | Dlhodobé prijaté preddavky |
| Deník TDADV | — | Daňové doklady k přijatým platbám | Faktúry k prijatým platbám |

Vyplní se jen prázdná nastavení; účty, které jste zvolili sami, zůstanou.

## Vystavení zálohové faktury {#create}

Na potvrzené objednávce klikněte na **Vytvořit zálohovou fakturu** a zvolte:

| Možnost | Výsledek |
|---|---|
| Plná suma | jeden řádek *Advance* za každý řádek objednávky ve výši jeho mezisoučtu |
| Procento z celé částky | jeden řádek *Advance* na dané procento z částky bez DPH |
| Pevná částka | jeden řádek *Advance* na zadanou částku bez DPH |
| **Zahrnout objednané položky** | místo řádků *Advance* produkty, množství a sazby DPH z objednávky; u procenta nebo pevné částky se poměrně sníží jednotkové ceny, množství zůstanou |

**Volbu *Zahrnout objednané položky* použijte vždy, když má objednávka jinou
sazbu DPH než produkt *Advance* nebo když kombinuje sazby.** Bez ní má každý
řádek zálohy daně produktu *Advance* a stejně tak daňový doklad k platbě.
Vyúčtovací faktura rozdíl vyrovná, takže se DPH neztratí ani nezaplatí
dvakrát, ale daň z přijaté úplaty byla přiznána ve špatné sazbě.

Zálohová faktura se otevře jako nový doklad navázaný na objednávku. Na ní:

- **Datum splatnosti** se řídí platebními podmínkami; **Číslo účtu**
  a **Platební QR-kód** určují, co se vytiskne.
- **Dlouhodobá záloha** pošle zálohu bez DPH na dlouhodobý účet. Označte ji
  před potvrzením zálohy.
- *Odeslat e-mailem* a *Tisk* vytvoří „Zálohovou fakturu“ s datem vystavení
  a splatnosti, s částkami včetně DPH bez rozpisu daně a s bankovním účtem,
  číslem zálohy jako referencí platby a QR kódem.

Objednávka dostane sekci *Zálohové faktury* s řádkem s nulovým množstvím za
každou zálohu, který průběžně ukazuje její stav, datum úhrady a daňový
doklad, a tlačítko **Zálohové faktury**. Zálohové faktury se nezobrazují
v *Nabídkách* ani v *Objednávkách*. Mají vlastní nabídku *Prodej →
Objednávky → Zálohové faktury* a *Účetnictví → Zákazníci → Zálohové
faktury*, kde lze vystavit i zálohovou fakturu bez objednávky (viz
[Zálohy bez objednávky](#standalone)).

Potvrzení zálohy nikdy nevytvoří dodávku: zboží se dodává z původní
objednávky.

## Přijetí platby {#payment}

**Stav platby** zálohy (*Nezaplaceno*, *Částečně zaplaceno*, *Zaplaceno*,
*Přeplaceno*) se řídí platbami, které jsou s ní provázané. Obě tlačítka
uvedená níže se zobrazí, jakmile je záloha odeslaná nebo potvrzená a část
ještě není uhrazená. Platba může přijít čtyřmi způsoby:

- **Online** přes zákaznický portál, je-li nastaven poskytovatel plateb —
  záloha vyžaduje platbu jako online nabídka. Platba se zaúčtuje **na
  zúčtovací účet**.
- **Registrovat platbu** — zaznamená platbu v bankovním nebo pokladním
  deníku, zaúčtovanou **na zúčtovací účet**, a byla-li záloha ještě
  nabídkou, potvrdí ji. Částka nesmí převýšit nezaplacenou část.
- **Provázat platbu** (*Link Manual Transfer*) — připojí existující přijatou
  platbu téhož zákazníka, která není spárovaná s žádnou fakturou. Byla-li
  zaúčtována na pohledávku zákazníka, přesune ji převodní zápis v deníku
  ostatních operací na **zúčtovací účet**.
- **Z bankovního výpisu**, automaticky nebo průvodcem, s modulem
  [module:sale_order_advance_invoice_payment_match](module:sale_order_advance_invoice_payment_match).

## Daňový doklad k přijaté platbě {#tax-document}

Jakmile je záloha alespoň částečně zaplacena, **Účetní stav** se změní
z *Nic k zaúčtování* na **Čeká** a v záhlaví se objeví **Vytvořit fakturu**.
Tlačítko vytvoří koncept daňového dokladu na zaplacenou částku, kterou ještě
nepokrývá dřívější daňový doklad. Každá splátka částečně zaplacené zálohy
tak může mít vlastní.

Daňový doklad k přijaté platbě:

- je fakturou zákazníkovi v deníku TDADV, rozdělenou podle sazeb DPH
  v poměru řádků zálohy;
- má jako DUZP **den přijetí platby** a řádek „Přijatá platba pro Zálohovou
  fakturu ADV00042 ze dne …“;
- účtuje částku bez DPH na účet přijatých záloh (324000, u dlouhodobé zálohy
  475000) a pohledávku na **zúčtovací účet**;
- tiskne se jako **Daňový doklad** s *Datem vystavení*, *Datem přijetí
  platby* místo DUZP a bez splatnosti, platebních údajů a QR kódu.

Zkontrolujte ho a zaúčtujte. Zaúčtování ho na zúčtovacím účtu spáruje
s platbami zálohy a stav se změní na **Zaúčtováno**.

Seznam záloh ukazuje lhůtu ve sloupci *Poslední datum zaúčtovaní*, po jejím
uplynutí červeně. Řídí se zemí společnosti (viz [Právní rámec](#legal)):

| Země | Lhůta |
|---|---|
| Česko | 15 dnů po platbě |
| Slovensko | 15 dnů po platbě nebo poslední den měsíce platby, podle toho, co nastane později (u plateb před rokem 2016 15 dnů) |
| jiná | 15 dnů po platbě |

## Vyúčtování {#final-invoice}

Objednávku vyfakturujte jako obvykle (*Vytvořit fakturu* na objednávce).
Každá zaplacená záloha se přidá pod běžné řádky do sekce *Zálohové faktury*
jako záporný řádek:

- **Část pokrytá zaúčtovanými daňovými doklady**: částka bez DPH, kterou tyto
  doklady přiznaly, na účtu přijatých záloh s jejich DPH, takže se daň
  přiznaná z platby vrátí. Doklady v několika sazbách se odečtou po řádku za
  každou sazbu.
- **Přijatá část, kterou nepokrývá zaúčtovaný daňový doklad**: částka včetně
  DPH, bez daně, na výnosový účet produktu *Advance*. DPH z této části pak
  vyměří sama vyúčtovací faktura.

Odečte se jen to, co bylo **přijato**: částečně zaplacená záloha se odečte
v zaplacené výši, ne v plné. Daňový doklad v konceptu nepokrývá nic.
Záloha se odečte, až když je na ní něco zaplaceno, a jen spolu s běžnými
řádky připravenými k fakturaci. Nelze-li zatím fakturovat nic jiného,
například proto, že nic nebylo dodáno, Odoo oznámí, že není co fakturovat.

**Cizí měna.** Odpočet se přepočte kurzem, kterým byly přiznány jeho daňové
doklady, a stejně tak část plnění, kterou záloha uhradila. Jen zbytek plnění
se přepočte kurzem vyúčtovací faktury. Plně předplacené plnění tak vyjde
s nulovou DPH a na pohledávce nic nezůstane, jak vyžaduje § 37a.

## Zálohy bez objednávky {#standalone}

Zálohová faktura vystavená přímo z nabídky *Zálohové faktury* nemá
objednávku. K jejímu vyúčtování otevřete vyúčtovací fakturu zákazníkovi,
dokud je konceptem, a klikněte na **Přepojit zálohové faktury**. Nabídnou se
potvrzené zálohy téhož zákazníka, na kterých je něco zaplaceno a které
neodečítá jiná faktura. Každá se přidá přesně jako na vyúčtování objednávky:
část pokrytá zaúčtovanými daňovými doklady bez DPH se stornem daně, po řádku
za každou sazbu, a zbytek přijaté částky včetně DPH bez daně.

## Omezení {#limitations}

- Daňový doklad nevznikne po zaplacení sám: klikněte na **Vytvořit fakturu**,
  nebo ho nechte vytvořit doplněk pro párování výpisů.
- Platba připojená přes *Provázat platbu* se přesune na zúčtovací účet, jen
  dokud je její řádek pohledávky otevřený a společnost má deník ostatních
  operací jiný než deník daňových dokladů. Jinak řádek daňového dokladu na
  zúčtovacím účtu spárujte s platbou sami.
- Bez daňového dokladu se odpočet zúčtovacího účtu nedotkne a platba na něm
  zůstane, dokud ji nevyrovnáte ručním zápisem. Povinnost přiznat daň přitom
  v obou zemích vzniká přijetím úplaty (v Česku s výjimkou podle § 20a
  odst. 2 pro plnění, které ještě není známo dostatečně určitě).
- Bez volby *Zahrnout objednané položky* mají záloha i daňový doklad sazbu
  DPH produktu *Advance*, ne objednávky.
- Přenesení daňové povinnosti a plnění do jiného členského státu nemají
  zvláštní zpracování: nevystavujte daňový doklad tam, kde přijetí úplaty
  nezakládá povinnost přiznat daň.
