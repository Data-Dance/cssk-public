---
title: Přijaté zálohové faktury (nákup)
summary: Zálohová faktura od dodavatele jako nákupní doklad, její úhrada, daňový doklad dodavatele k přijaté platbě a odečtení zálohy na konečné faktuře.
verified: 19.0.1.2.0
---

## K čemu slouží {#purpose}

Je to strana dodavatele k modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice). Když
dodavatel žádá zálohu, řeší se:

1. **přijatá zálohová faktura** — výzva k platbě, nikdy se neúčtuje;
2. **vaše úhrada** zálohy;
3. **daňový doklad dodavatele k přijaté platbě** — doklad, na jehož základě
   můžete uplatnit nárok na odpočet DPH ze zálohy;
4. **konečná faktura**, od které se záloha i její DPH odečte.

Modul eviduje přijatou zálohovou fakturu jako samostatnou nákupní objednávku
s čísly `PADV00001`, `PADV00002`… a účtuje jen platbu a daňový doklad k ní.

## Právní rámec {#legal}

- **Strana dodavatele.** Úplata přijatá před uskutečněním plnění se daní ke
  dni jejího přijetí — v Česku
  [§ 20a odst. 2 zákona o DPH](law:cz/2004/235), na Slovensku
  [§ 19 ods. 4 zákona o DPH](law:sk/2004/222#paragraf-19.odsek-4). Dodavatel
  musí daňový doklad vystavit v Česku do 15 dnů (§ 28 odst. 8), na Slovensku
  do 15 dní od přijetí platby nebo do konce měsíce, v němž ji přijal
  ([§ 73 ods. 1 písm. b)](law:sk/2004/222#paragraf-73.odsek-1.pismeno-b)).
- **Váš odpočet.** K uplatnění nároku na odpočet musíte mít daňový doklad
  dodavatele — v Česku § 73 odst. 1 písm. a), na Slovensku
  [§ 51 ods. 1 písm. a)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a).
  V Česku lze nárok uplatnit nejdříve za zdaňovací období, ve kterém jsou
  podmínky splněny (§ 73 odst. 2). Na Slovensku se odpočet provede nejdříve
  v období, kdy právo vzniklo, a nejpozději v posledním období téhož
  kalendářního roku, má-li plátce doklad do konce lhůty pro podání přiznání;
  nemá-li ho ani do lhůty pro přiznání za poslední období roku, odečte daň
  v období, kdy doklad obdrží
  ([§ 51 ods. 2](law:sk/2004/222#paragraf-51.odsek-2)). Proto je datum
  účtování daňového dokladu na vás (viz [níže](#tax-document)).

## Nastavení {#setup}

*Účetnictví → Konfigurace → Nastavení*, blok **Přijaté zálohové faktury**:

| Nastavení | Účel |
|---|---|
| Deník daňových dokladů | Nákupní deník pro daňové doklady dodavatelů k přijatým platbám, např. PDADV. |
| Zúčtovací účet | Párovatelný účet typu **závazek**, na kterém se setká vaše platba s daňovým dokladem, např. 314001. |
| Účet poskytnutých záloh | Záloha bez DPH až do konečné faktury, např. 314000, volitelně i s dlouhodobou variantou. |

Bez lokalizačního doplňku je vyplňte sami.

### Lokalizační doplňky {#localization}

[module:l10n_cz_purchase_order_advance_invoice](module:l10n_cz_purchase_order_advance_invoice)
a
[module:l10n_sk_purchase_order_advance_invoice](module:l10n_sk_purchase_order_advance_invoice)
vyplní uvedená nastavení každé společnosti s českou nebo slovenskou účtovou
osnovou — při instalaci a znovu pokaždé, když se osnova načte později,
například pro novou společnost:

| Role | Účet | Český název | Slovenský název |
|---|---|---|---|
| Zúčtovací účet (vytvoří ho doplněk, závazek, párovatelný) | 314001 | Poskytnuté zálohy – zúčtování (daňový doklad) | Poskytnuté preddavky – zúčtovanie (daňový doklad) |
| Poskytnuté zálohy | 314000 | Poskytnuté provozní zálohy | Poskytnuté preddavky |
| Poskytnuté zálohy, dlouhodobé | — (zůstane prázdné) | | |
| Deník PDADV (nákupní) | — | Daňové doklady k odeslaným platbám | Faktúry k odoslaným platbám |

Vyplní se jen prázdná nastavení, takže účty, které jste si zvolili sami,
zůstanou.

## Zaevidování přijaté zálohové faktury {#register}

*Nákup → Objednávky → Přijaté zálohové faktury* (také *Účetnictví →
Dodavatelé → Přijaté zálohové faktury*), pak *Nový*. Zadejte dodavatele
a řádky podle zálohové faktury dodavatele, se sazbami DPH, které uvádí.
Volitelně zvolte **Nadřazenou objednávku**, ke které patří, a označte
**Dlouhodobou zálohu**, má-li se použít dlouhodobý účet (je-li nastaven).

Nákupní objednávka se zálohami má tlačítko **Zálohy**.

**Se Skladem.** Zboží se přijímá na nadřazené objednávce, nikdy na záloze:
s modulem
[module:purchase_order_advance_invoice_stock](module:purchase_order_advance_invoice_stock),
který se nainstaluje sám, je-li nainstalován Sklad, potvrzení ani úhrada
zálohy nevytvoří příjemku, ani když jsou na ní skladované produkty.

## Úhrada {#payment}

Na záloze:

- **Zaevidovat platbu** — vytvoří a zaúčtuje platbu dodavateli z bankovního
  nebo pokladního deníku **na zúčtovací účet** a zálohu potvrdí. Částka
  nesmí převýšit nezaplacenou část.
- **Propojit platbu** — připojí existující platbu téhož dodavatele, která
  není propojená s jinou zálohou.

**Stav úhrady** (*Nezaplaceno*, *Částečně zaplaceno*, *Zaplaceno*,
*Přeplaceno*), **Uhrazená částka** a **Datum úhrady** se řídí propojenými
platbami.

## Zaevidování daňového dokladu dodavatele {#tax-document}

Jakmile je něco zaplaceno, **Stav zaúčtování** se změní na **Čeká se na
daňový doklad** a pole **Daňový doklad očekáván do** ukáže lhůtu. Až daňový
doklad dodavatele přijde, klikněte na **Zaevidovat přijatý daňový doklad**:

| Pole | Význam |
|---|---|
| Číslo dokladu dodavatele | číslo přesně tak, jak ho dodavatel uvedl (povinné) — je referencí faktury |
| Datum dokladu | datum vystavení |
| Datum účtování | období, ve kterém uplatňujete odpočet; výchozí je datum dokladu (viz [Právní rámec](#legal)) |
| Datum uskutečnění zdanitelného plnění | den, kdy dodavatel přijal platbu; výchozí je datum vaší platby |
| Částka (včetně DPH) | částka dokladu včetně DPH; výchozí je zaplacená částka, kterou ještě nepokrývá daňový doklad |

Vznikne **koncept přijaté faktury** v deníku daňových dokladů, rozdělený
podle sazeb DPH v poměru řádků zálohy, s částkou bez DPH na účtu
poskytnutých záloh a závazkem na **zúčtovacím účtu**. Porovnejte ho
s dokladem dodavatele a zaúčtujte. Zaúčtování ho na zúčtovacím účtu spáruje
s platbami zálohy, a jakmile daňové doklady pokrývají celou zaplacenou
částku, stav se změní na **Zaúčtováno**.

Tlačítko **Daňové doklady** je zobrazí.

## Odečtení na konečné faktuře {#deduction}

- **Z nadřazené objednávky**: *Vytvářejte přijaté faktury* (*Create Bills*)
  přidá na nejnovější koncept faktury odpočet každé zaplacené zálohy, která
  ještě není celá odečtená.
- **Na kterémkoli konceptu přijaté faktury**: **Odečíst zálohové faktury**
  nabídne zálohy dodavatele, ze kterých zbývá co odečíst.

Odpočet je:

- **za část pokrytou zaúčtovanými daňovými doklady** — záporná kopie každého
  řádku daňových dokladů: částka bez DPH na účtu poskytnutých záloh se stejnou
  DPH, takže se odpočet daně ze zálohy vrátí;
- **za zaplacenou část, kterou zaúčtovaný daňový doklad nepokrývá** — jeden
  záporný řádek na tuto částku na účtu poskytnutých záloh, bez DPH.

Odečte se jen to, co ještě zbývá. Faktura po dřívějším odpočtu bere nejprve
pokrytou část a řádky daňových dokladů kopíruje jen v jejich zbývající výši.

## Urgování dodavatele {#chasing}

Naplánovaná akce *Přijaté zálohové faktury: urgovat daňové doklady po
termínu* běží denně. Pro každou zálohu, která po datu **Daňový doklad
očekáván do** stále čeká na daňový doklad, naplánuje (jednou) aktivitu
„Daňový doklad k záloze je po termínu — urgovat dodavatele …“. Seznam má
filtry **Čeká se na daňový doklad**, **Daňový doklad po termínu**
a **Neuhrazeno**.

Očekávané datum se řídí zemí společnosti (viz [Právní rámec](#legal)):
v Česku 15 dnů po vaší platbě; na Slovensku 15 dnů po platbě nebo konec
téhož měsíce, podle toho, co nastane později (u plateb před rokem 2016
15 dnů); jinde 15 dnů. Aktivita má vlastní typ *Urgovat daňový doklad
k záloze*, takže se naplánuje jednou bez ohledu na jazyk, ve kterém
naplánovaná akce běží.

## Omezení {#limitations}

- Záloha je ve skutečnosti obyčejná nákupní objednávka. Nepoužívejte na ní
  *Vytvářejte přijaté faktury*.
- **Propojit platbu** nekontroluje, na jaký účet byla platba zaúčtována.
  S daňovým dokladem se automaticky spáruje jen platba zaúčtovaná na
  zúčtovací účet.
- Bez daňového dokladu jde odpočet na účet poskytnutých záloh, zatímco platba
  je na zúčtovacím účtu. Vyrovnejte je ručním zápisem.
- Zálohy v režimu přenesení daňové povinnosti a v rámci EU jsou mimo rozsah:
  přijetí úplaty tam nezakládá povinnost přiznat daň, proto k nim daňový
  doklad neevidujte.
