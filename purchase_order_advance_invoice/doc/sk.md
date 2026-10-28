---
title: Prijaté zálohové faktúry (nákup)
summary: Zálohová faktúra od dodávateľa ako nákupný doklad, jej úhrada, faktúra dodávateľa k prijatej platbe a odpočet preddavku na konečnej faktúre.
verified: 19.0.1.2.0
---

## Na čo slúži {#purpose}

Je to strana dodávateľa k modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice). Keď
dodávateľ žiada preddavok, rieši sa:

1. **prijatá zálohová (preddavková) faktúra** — výzva na platbu, nikdy sa
   neúčtuje;
2. **vaša úhrada** preddavku;
3. **faktúra dodávateľa k prijatej platbe** (v praxi aj *daňový doklad k
   prijatej platbe*) — doklad, na základe ktorého môžete odpočítať DPH z
   preddavku;
4. **konečná faktúra**, od ktorej sa preddavok aj jeho DPH odpočíta.

Modul eviduje prijatú zálohovú faktúru ako samostatnú nákupnú objednávku s
číslami `PADV00001`, `PADV00002`… a účtuje len platbu a faktúru k platbe.

## Právny rámec {#legal}

- **Strana dodávateľa.** Platba prijatá pred dodaním sa zdaňuje dňom jej
  prijatia — na Slovensku
  [§ 19 ods. 4 zákona o DPH](law:sk/2004/222#paragraf-19.odsek-4), v Česku
  [§ 20a odst. 2 zákona o DPH](law:cz/2004/235). Dodávateľ musí faktúru
  vyhotoviť na Slovensku do 15 dní od prijatia platby alebo do konca
  mesiaca, v ktorom ju prijal
  ([§ 73 ods. 1 písm. b)](law:sk/2004/222#paragraf-73.odsek-1.pismeno-b)),
  v Česku do 15 dní (§ 28 odst. 8).
- **Váš odpočet.** Na odpočítanie dane musíte mať faktúru dodávateľa — na
  Slovensku
  [§ 51 ods. 1 písm. a)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a),
  v Česku § 73 odst. 1 písm. a). Na Slovensku sa odpočítanie vykoná najskôr
  v zdaňovacom období, v ktorom právo vzniklo, a najneskôr v poslednom
  zdaňovacom období toho kalendárneho roka, ak máte doklad do uplynutia
  lehoty na podanie priznania za obdobie, v ktorom odpočet uplatňujete; ak
  ho nemáte do uplynutia lehoty na podanie priznania za posledné obdobie
  roka, odpočítate daň v tom období, v ktorom doklad dostanete
  ([§ 51 ods. 2](law:sk/2004/222#paragraf-51.odsek-2)). V Česku možno
  nárok uplatniť najskôr za obdobie, v ktorom sú splnené podmienky
  (§ 73 odst. 2). Preto je dátum účtovania faktúry k platbe na vás (pozri
  [nižšie](#tax-document)).

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Prijaté zálohové
faktúry**:

| Nastavenie | Účel |
|---|---|
| Denník daňových dokladov | Nákupný denník pre faktúry dodávateľov k prijatým platbám, napr. PDADV. |
| Zúčtovací účet | Párovateľný účet typu **záväzok**, na ktorom sa stretne vaša platba s faktúrou k nej, napr. 314001. |
| Účet poskytnutých preddavkov | Preddavok bez DPH až do konečnej faktúry, napr. 314000, voliteľne aj s dlhodobým variantom. |

Bez lokalizačného doplnku ich vyplňte sami.

### Lokalizačné doplnky {#localization}

[module:l10n_cz_purchase_order_advance_invoice](module:l10n_cz_purchase_order_advance_invoice)
a
[module:l10n_sk_purchase_order_advance_invoice](module:l10n_sk_purchase_order_advance_invoice)
vyplnia uvedené nastavenia každej spoločnosti s českou alebo slovenskou
účtovou osnovou — pri inštalácii a znova vždy, keď sa osnova načíta neskôr,
napríklad pre novú spoločnosť:

| Úloha | Účet | Slovenský názov | Český názov |
|---|---|---|---|
| Zúčtovací účet (vytvorí ho doplnok, záväzok, párovateľný) | 314001 | Poskytnuté preddavky – zúčtovanie (daňový doklad) | Poskytnuté zálohy – zúčtování (daňový doklad) |
| Poskytnuté preddavky | 314000 | Poskytnuté preddavky | Poskytnuté provozní zálohy |
| Poskytnuté preddavky, dlhodobé | — (ostane prázdne) | | |
| Denník PDADV (nákupný) | — | Faktúry k odoslaným platbám | Daňové doklady k odeslaným platbám |

Vyplnia sa len prázdne nastavenia, takže účty, ktoré ste si zvolili sami,
ostanú.

## Zaevidovanie prijatej zálohovej faktúry {#register}

*Nákup → Objednávky → Prijaté zálohové faktúry* (aj *Účtovníctvo →
Dodávatelia → Prijaté zálohové faktúry*), potom *Nové*. Zadajte dodávateľa a
riadky podľa zálohovej faktúry dodávateľa, so sadzbami DPH, ktoré uvádza.
Voliteľne zvoľte **Nadradenú objednávku**, ku ktorej patrí, a označte
**Dlhodobý preddavok**, ak sa má použiť dlhodobý účet (ak je nastavený).

Nákupná objednávka s preddavkami má tlačidlo **Preddavky**.

**So Skladom.** Tovar sa prijíma na nadradenej objednávke, nikdy na
preddavku: s modulom
[module:purchase_order_advance_invoice_stock](module:purchase_order_advance_invoice_stock),
ktorý sa nainštaluje sám, keď je Sklad nainštalovaný, potvrdenie ani úhrada
preddavku nevytvorí príjemku, ani keď sú na ňom skladované produkty.

## Úhrada {#payment}

Na preddavku:

- **Zaevidovať platbu** — vytvorí a zaúčtuje platbu dodávateľovi z bankového
  alebo pokladničného denníka **na zúčtovací účet** a preddavok potvrdí. Suma
  nesmie prevýšiť neuhradenú časť.
- **Prepojiť platbu** — pripojí existujúcu platbu toho istého dodávateľa,
  ktorá nie je prepojená s iným preddavkom.

**Stav úhrady** (*Neuhradené*, *Čiastočne uhradené*, *Plne uhradené*,
*Preplatené*), **Uhradená suma** a **Dátum úhrady** sa riadia prepojenými
platbami.

## Zaevidovanie faktúry dodávateľa k platbe {#tax-document}

Keď je niečo uhradené, **Stav zaúčtovania** sa zmení na **Čaká sa na daňový
doklad** a pole **Daňový doklad očakávaný do** ukáže lehotu. Keď faktúra
dodávateľa k platbe príde, kliknite na **Zaevidovať prijatý daňový doklad**:

| Pole | Význam |
|---|---|
| Číslo dokladu dodávateľa | číslo presne tak, ako ho dodávateľ uviedol (povinné) — je referenciou faktúry |
| Dátum dokladu | dátum vyhotovenia |
| Dátum účtovania | obdobie, v ktorom uplatňujete odpočet; predvolene dátum dokladu (pozri [Právny rámec](#legal)) |
| Deň dodania | deň, keď dodávateľ prijal platbu; predvolene dátum vašej platby |
| Suma (s DPH) | suma dokladu s DPH; predvolene uhradená suma, ktorú ešte nepokrýva faktúra k platbe |

Vznikne **koncept dodávateľskej faktúry** v denníku daňových dokladov,
rozdelený podľa sadzieb DPH v pomere riadkov preddavku, so sumou bez DPH na
účte poskytnutých preddavkov a záväzkom na **zúčtovacom účte**. Porovnajte ho
s papierovým dokladom a zaúčtujte. Zaúčtovanie ho na zúčtovacom účte spáruje
s platbami preddavku a keď faktúry k platbe pokrývajú celú uhradenú sumu,
stav sa zmení na **Zaúčtované**.

Tlačidlo **Daňové doklady** ich zobrazí.

## Odpočet na konečnej faktúre {#deduction}

- **Z nadradenej objednávky**: *Vytvoriť prijaté faktúry* pridá na najnovší
  koncept faktúry odpočet každého uhradeného preddavku, ktorý ešte nie je
  celý odpočítaný.
- **Na ktoromkoľvek koncepte dodávateľskej faktúry**: **Odpočítať zálohové
  faktúry** ponúkne preddavky dodávateľa, z ktorých ostáva čo odpočítať.

Odpočet je:

- **za časť pokrytú zaúčtovanými faktúrami k platbe** — záporná kópia každého
  riadku faktúr k platbe: suma bez DPH na účte poskytnutých preddavkov s
  rovnakou DPH, takže sa odpočet dane z preddavku stornuje;
- **za uhradenú časť, ktorú zaúčtovaná faktúra k platbe nepokrýva** — jeden
  záporný riadok na túto sumu na účte poskytnutých preddavkov, bez DPH.

Odpočíta sa len to, čo ešte ostáva. Faktúra po skoršom odpočte berie najprv
pokrytú časť a riadky faktúr k platbe kopíruje len v ich zostávajúcej výške.

## Urgovanie dodávateľa {#chasing}

Plánovaná akcia *Prijaté zálohové faktúry: urgovať daňové doklady po
termíne* beží denne. Pre každý preddavok, ktorý po dátume **Daňový doklad
očakávaný do** stále čaká na faktúru k platbe, naplánuje (raz) aktivitu
„Daňový doklad k preddavku je po termíne — urgovať dodávateľa …“. Zoznam má
filtre **Čaká sa na daňový doklad**, **Daňový doklad po termíne** a
**Neuhradené**.

Očakávaný dátum sa riadi krajinou spoločnosti (pozri
[Právny rámec](#legal)): v Česku 15 dní po vašej platbe; na Slovensku 15 dní
po platbe alebo koniec toho mesiaca, podľa toho, čo nastane neskôr (pri
platbách pred rokom 2016 15 dní); inde 15 dní. Aktivita má vlastný typ
*Urgovať daňový doklad k preddavku*, takže sa naplánuje raz bez ohľadu na
jazyk, v ktorom plánovaná akcia beží.

## Obmedzenia {#limitations}

- Preddavok je v skutočnosti obyčajná nákupná objednávka. Nepoužívajte na
  ňom *Vytvoriť prijaté faktúry*.
- **Prepojiť platbu** nekontroluje, na aký účet bola platba zaúčtovaná. S
  faktúrou k platbe sa automaticky spáruje len platba zaúčtovaná na zúčtovací
  účet.
- Bez faktúry k platbe ide odpočet na účet poskytnutých preddavkov, kým
  platba je na zúčtovacom účte. Vyrovnajte ich ručným zápisom.
- Preddavky s prenesením daňovej povinnosti a v rámci EÚ sú mimo rozsahu:
  platba tam daňovú povinnosť nezakladá, preto k nim faktúru k platbe
  neevidujte.
