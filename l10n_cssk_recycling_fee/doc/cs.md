---
title: Recyklační příspěvek CZ/SK (recyklační příspěvek / recyklačný poplatok)
summary: Příspěvek na zpětný odběr elektrozařízení a baterií podle platného ceníku kolektivního systému, uvedený u každého řádku faktury, jak vyžaduje zákon, a sečtený po kategoriích pro výkaz kolektivnímu systému.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Výrobce, distributor nebo prodejce elektrozařízení platí kolektivnímu
systému (na Slovensku organizaci odpovědnosti výrobců) příspěvek za každý
kus nebo kilogram uvedený na trh a oba státy vyžadují, aby jej při prodeji
uváděl. U přenosných baterií platí opak: náklady na zpětný odběr se odděleně
uvádět **nesmějí**.

Modul to doplňuje do Odoo nad modulem OCA `account_ecotax`, který už zná
klasifikace ekologického poplatku, více klasifikací na produkt a podřízený
řádek poplatku ke každému řádku faktury. Přidává to, co je české a
slovenské:

- **sazby s platností od – do** pro každou klasifikaci, v měně kolektivního
  systému (Kč nebo EUR), vybírané podle data faktury;
- klasifikaci vázanou na **trh** (CZ nebo SK), kterou použijí jen
  společnosti z daného státu;
- příspěvek **vytištěný pod každým řádkem faktury** v zákonném znění a
  součet za doklad;
- **přenosné baterie** se spočítají a vykážou, ale nikdy nevytisknou;
- **přehled za období** po kategoriích pro výkaz kolektivnímu systému.

Strana objednávek je popsána v části [Prodejní objednávky](#sales-orders).

## Právní rámec {#legal}

**Česko** — [zákon č. 542/2020 Sb., o výrobcích s ukončenou
životností](law:cz/2020/542):

- **§ 73 odst. 1**: výrobce elektrozařízení, distributor a poslední prodejce
  jsou povinni při prodeji nového elektrozařízení uvádět náklady na zpětný
  odběr, zpracování, využití a odstranění připadající na jeden kus nebo
  jeden kilogram **odděleně od ceny**, *„a to zejména formou samostatného
  údaje na daňovém dokladu“*. **§ 99 odst. 1** ukládá totéž u pneumatik.
- **§ 73 odst. 2**: odděleně uváděné náklady nesmějí převýšit náklady známé
  výrobci v okamžiku uvedení na trh; plní-li výrobce povinnosti v
  kolektivním systému, určí se podle příspěvku, který provozovateli platí.
  Proto se sazba bere z ceníku kolektivního systému.
- **§ 73 odst. 3**: povinnosti posledního prodejce podle cenových předpisů
  nejsou dotčeny.
- **§ 85 odst. 3**: náklady na zpětný odběr, zpracování a recyklaci
  přenosných baterií *„nesmějí být při prodeji nových přenosných baterií
  nebo akumulátorů uváděny odděleně“*.
- **§ 125 odst. 2 písm. i) a l)**: neuvedení nákladů, jejich uvedení v
  rozporu s § 73 odst. 2 nebo jejich uvedení u přenosných baterií je
  přestupkem.
- Metodický pokyn MŽP k odděleně uváděným nákladům podle § 73 a § 99
  (revize z 26. 10. 2021) požaduje příspěvek u každé položky daňového
  dokladu a ve vzorových fakturách jej zahrnuje do jednotkové ceny; modul
  se tímto způsobem řídí.

**Slovensko** — [zákon č. 79/2015 Z. z. o odpadoch](law:sk/2015/79):

- [§ 34 ods. 1 písm. d)](law:sk/2015/79#paragraf-34.odsek-1.pismeno-d):
  výrobce uvádí *„na jeho obale alebo etikete alebo na daňovom či inom
  obdobnom doklade vyhotovenom pri jeho predaji výšku recyklačného
  poplatku“* za elektroodpad z domácností.
- [§ 37 ods. 1 písm. a)](law:sk/2015/79#paragraf-37.odsek-1.pismeno-a):
  distributor uvádí recyklační poplatek, uvedl-li jej výrobce.
- [§ 46 ods. 2](law:sk/2015/79#paragraf-46.odsek-2) a
  [§ 48 ods. 1 písm. d)](law:sk/2015/79#paragraf-48.odsek-1.pismeno-d): u
  přenosných baterií se náklady nesmějí uvádět odděleně.

Žádný z obou zákonů nepředepisuje samostatný řádek faktury, proto modul
nabízí obojí: příspěvek **zahrnutý** v ceně s uvedením u řádku (výchozí),
nebo **navíc** jako samostatný řádek.

## Nastavení {#setup}

1. **Klasifikace** — *Účetnictví → Konfigurace → Ecotax → Classification*,
   jedna za každou položku ceníku vašeho kolektivního systému. Popisky jsou
   anglicky (modul zatím nemá český překlad):
   - **Scheme Country** (stát systému) — CZ nebo SK. Za zákonný recyklační
     příspěvek se považuje jen klasifikace se státem; bez něj se chová
     přesně jako v modulu OCA.
   - **Ecotax Type** (způsob výpočtu) — *Fixed* (za kus) nebo *Weight
     based* (za kg); **Category** (kategorie), **Ecotax collector**
     (kolektivní systém), **Product Status** (*Domestic* = z domácností,
     *Professional* = jiné než z domácností).
   - **Dated Rates** (sazby) — *Valid From*, *Valid To* (prázdné pro
     platnou sazbu) a *Rate* bez DPH v měně klasifikace (doplní se podle
     státu: Kč, EUR). Dvě sazby jedné klasifikace se nesmějí překrývat.
     Původní pole OCA s jednou částkou jsou jen pro čtení a ukazují dnešní
     sazbu; denní plánovaná akce je přepne, jakmile začne platit nová.
   - **Show on Documents** (uvádět na dokladech) — u **přenosných baterií**
     odškrtněte.
2. **Produkty** — na záložce *Účetnictví* přidejte klasifikaci (klasifikace);
   produkt prodávaný v obou státech může mít českou i slovenskou a každá
   společnost použije jen svou. U klasifikace za kg vyplňte **hmotnost** v
   kg. Distributor může na řádku klasifikace produktu zadat **pevnou
   částku** — příspěvek, který skutečně zaplatil jeho dodavatel, v měně
   klasifikace; ta pak nahradí ceník.
3. **Způsob uvádění** — *Účetnictví → Konfigurace → Nastavení*, blok
   **Recycling Fee**: *Included in the price* (zahrnutý v ceně, výchozí) nebo
   *Separate line on top of the price* (samostatný řádek navíc).

Modul vytvoří **kategorie** ekologického poplatku — šest skupin
elektrozařízení (EEE1 – EEE6) a pět kategorií baterií (přenosné, LMT,
automobilové SLI, průmyslové, do elektrických vozidel). **Ceníky
nedodává**: jsou věcí každého kolektivního systému.

## Na faktuře {#invoice}

Každý řádek vydané faktury dostane příspěvek podle:

- sazby platné ke **dni vystavení faktury** (dokud není vyplněn, podle data
  zaúčtování);
- množství přepočteného na vlastní měrnou jednotku produktu (řádek
  prodávaný po tuctech znamená dvanáct kusů);
- u klasifikace za kg hmotnosti produktu; příspěvek za kus se zaokrouhlí na
  dvě desetinná místa měny;
- přepočtu kurzem ke dni faktury, je-li faktura v jiné měně než sazba.

Pod popisem řádku uvede vytištěná faktura v národním znění podle státu
klasifikace:

    z toho recyklační příspěvek 100,00 Kč (0,50 Kč/kg × 2,000 kg = 1,00 Kč/ks)
    z toho recyklačný poplatok 3,60 € (0,90 €/ks)

dále *bez DPH*, obsahuje-li cena řádku DPH, a u faktury v jiné měně původní
částku s kurzem. Doklad uzavírá řádek *Recyklační příspěvek celkem bez DPH*
/ *Recyklačný poplatok spolu bez DPH*. Anglický sloupec a součet *Eco Part*
z modulu OCA se na takových dokladech skryjí. Příspěvky klasifikací s
odškrtnutým *Show on Documents* se nevytisknou ani nezapočtou do součtu.

**Zaúčtování.** Při zaúčtování se příspěvek ještě jednou spočítá ke
konečnému datu faktury a vydaná faktura nebo dobropis, jehož klasifikace
**nemá k tomuto datu platnou sazbu**, se odmítne (nejde-li o pevnou
částku). Po zaúčtování je příspěvek zmrazen: pozdější změna ceníku nebo
hmotnosti jej nepřepíše; vrácení faktury do konceptu jej spočítá znovu.

## Přehled pro kolektivní systém {#report}

*Účetnictví → Výkazy → Správa → Recycling Fees* ukazuje kusy, kilogramy a
příspěvek ze **zaúčtovaných vydaných faktur a dobropisů** (dobropisy se
záporným znaménkem) podle státu, kategorie, klasifikace, kolektivního
systému a období, v měně systému bez ohledu na měnu faktury. K dispozici je
kontingenční tabulka, seznam a graf; filtry pro CZ, SK, z domácností a
profesionální. Přenosné baterie jsou zahrnuty.

*Tisk → Recycling Fees (XLSX)* vyexportuje vybrané řádky: souhrnný list
podle státu, systému, kategorie, klasifikace, druhu (z domácností /
profesionální) a způsobu výpočtu a druhý list s řádky faktur.

## Prodejní objednávky {#sales-orders}

S aplikací Prodej a modulem OCA `account_ecotax_sale` se sám nainstaluje
[module:l10n_cssk_recycling_fee_sale](module:l10n_cssk_recycling_fee_sale) a
přidá:

- **Příspěvky na řádcích objednávky**, spočítané podle sazby platné ke **dni
  objednávky**, se stejným výběrem trhu a přepočtem jednotek. Faktura je
  spočítá znovu ke svému datu, protože zákon mluví o daňovém dokladu.
- **Pevná částka** z produktu se přenese z objednávky na fakturu.
- **Režim „navíc“.** Je-li zvoleno *Separate line on top of the price*,
  nastavte ve stejném bloku **Recycling Fee Product** (produkt typu služba).
  Tlačítko **Update Recycling Fee** na objednávce přidá jeden řádek za každou
  klasifikaci a sazbu DPH, s cenou rovnou součtu příspěvků a s DPH zboží, k
  němuž patří (daň zahrnutá v ceně se dopočítá navrch, protože ceník je bez
  DPH). Použije se výnosový účet produktu příspěvku, jeho daně ne. Opakovaným
  stisknutím se řádky vytvoří znovu; po jejich vyfakturování tlačítko
  odmítne. Přenosné baterie řádek nedostanou.

## Omezení {#limitations}

- Sazba se vybírá podle **data faktury**, zatímco § 73 odst. 2 váže částku
  na okamžik uvedení na trh. Distributor, který prodává starší zboží přes
  změnu ceníku, by měl použít pevnou částku na produktu.
- Ceníky se nedodávají; zadejte ceník svého kolektivního systému.
- Přehled vychází z vydaných faktur. Je-li zboží dodáno v jednom období a
  fakturováno v jiném, srovnejte to ve výkazu. Dodání do jiných členských
  států a vývoz jsou zahrnuty a je třeba je vyloučit, pokud je kolektivní
  systém nezapočítává.
- V režimu „navíc“ vznikají samostatné řádky příspěvku jen z **prodejní
  objednávky**; faktura vytvořená bez objednávky uvede příspěvek u řádku,
  ale řádek příspěvku nemá, takže se navíc neúčtuje.
- Nabídky a objednávky uvedení u řádku netisknou; tiskne jej faktura.
- Kategorie pneumatik se nedodává; pneumatiky (§ 99) lze nastavit stejně.
- Uživatelské rozhraní je anglicky; zákonné texty na faktuře jsou česky
  nebo slovensky.
