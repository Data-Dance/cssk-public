---
title: Přiznání k DPH OSS CZ/SK (režim Unie)
summary: Čtvrtletní přiznání ve zvláštním režimu jednoho správního místa pro prodej zboží na dálku a služby spotřebitelům v jiných státech EU — z daní OSS v Odoo, přepočtené na eura kurzem ECB, s opravami předchozích čtvrtletí.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Prodejce registrovaný ve **zvláštním režimu jednoho správního místa, režimu
Evropské unie** (One-Stop-Shop, OSS) uplatňuje u prodeje zboží na dálku a u
služeb spotřebitelům v jiných státech EU daň státu zákazníka a celou ji přiznává
v jednom čtvrtletním přiznání podaném doma: v Česku je to *daňové přiznání ve
zvláštním režimu jednoho správního místa — režim Evropské unie*, na Slovensku
*daňové priznanie k DPH — osobitná úprava pre Úniu*.

Standardní modul Odoo `l10n_eu_oss` už vytváří vše potřebné k *fakturaci* této
daně: fiskální pozici *OSS B2C* pro každý členský stát a daně se sazbou státu
určení, všechny označené štítkem `OSS`. Co Odoo pro Česko a Slovensko
nevytvoří, je samotné *přiznání*. Tento modul ho spočítá z označených
účetních položek:

- jeden řádek za každou kombinaci **stát spotřeby × zboží/služby × sazba
  daně**, v eurech;
- **opravy předchozích čtvrtletí** za každý členský stát;
- saldo za každý členský stát a celkovou splatnou daň.

Úřední XML vytvoří národní modul, který nainstalujete spolu s tímto:

| Stát identifikace | Modul | Formulář |
|---|---|---|
| Česko | [module:l10n_cz_oss](module:l10n_cz_oss) | formulář EPO OSSEI1 |
| Slovensko | [module:l10n_sk_oss](module:l10n_sk_oss) | eFormulár DPOSS_EUv01 |

Modul také doplňuje do mapování daní OSS v Odoo chybějící slovenskou sazbu 5 %
— viz [Slovenská sazba 5 %](#tax-mapping). Funguje v edici Community
i Enterprise: vlastní výkaz OSS v Enterprise exportuje jen Belgii a Lucembursko.

## Právní rámec {#legal}

Oba státy přebírají stejná pravidla EU a modul se jimi řídí tam, kde se shodují:

- **Čtvrtletní přiznání do konce následujícího měsíce**, podává se i tehdy,
  když nebylo uskutečněno žádné plnění — CZ
  [§ 110zb a § 110zc zákona o DPH](law:cz/2004/235); SK
  [§ 68b ods. 12](law:sk/2004/222#paragraf-68b.odsek-12). Podle obou zákonů se
  lhůta neposouvá, připadne-li na sobotu, neděli nebo svátek.
- **Částky v eurech.** Částky fakturované v jiné měně se přepočtou kurzem
  Evropské centrální banky zveřejněným pro poslední den zdaňovacího období,
  nebo pro nejbližší následující den, není-li pro poslední den kurz zveřejněn —
  CZ [§ 110ze odst. 2 písm. a)](law:cz/2004/235); SK
  [§ 68b ods. 17](law:sk/2004/222#paragraf-68b.odsek-17) (který připouští
  i kurz vyhlášený Národnou bankou Slovenska).
- **Opravy se uvádějí v pozdějším přiznání** s uvedením státu spotřeby,
  zdaňovacího období a částky daně, nejpozději do tří let ode dne, kdy uplynula
  lhůta pro podání původního přiznání, kurzem použitým u původního plnění — CZ
  [§ 110zd a § 110ze odst. 2 písm. b)](law:cz/2004/235); SK
  [§ 68b ods. 19](law:sk/2004/222#paragraf-68b.odsek-19).

Registraci, podání a samotné formuláře popisují národní návody.

## Nastavení {#setup}

1. **Mapování OSS v Odoo.** *Účetnictví → Konfigurace → Nastavení*, blok
   **Prodej na dálku v rámci Evropské unie**, tlačítko **Mapování daní OSS**.
   Vytvoří fiskální pozice a daně OSS. Zkontrolujte je podle toho, co skutečně
   prodáváte, jak doporučuje i Odoo.
2. **Typ produktu.** Každý řádek se dělí na zboží a služby podle produktu na
   řádku faktury: produkt typu *Služba* je služba, vše ostatní — i řádek bez
   produktu — se počítá jako zboží. Kdo prodává elektronické nebo jiné služby,
   ať má na řádcích produkty.
3. **Kurzy.** Fakturujete-li v jiné měně než v eurech, udržujte kurzovní lístek
   společnosti aktuální: přiznání z něj navrhuje kurzy.
4. **Verze formuláře.** Nainstaluje ji národní modul. Najdete ji v
   *Účetnictví → Konfigurace → CZ/SK lokalizace → Verze přiznání OSS* s kódem
   formuláře, platností, šablonou a úředním XSD; zpravidla v ní není co měnit.

## Příprava přiznání {#usage}

*Účetnictví → Výkazy → Zákonné výkazy → Přiznání k DPH OSS*, potom *Nový*.

1. **Rok** a **Čtvrtletí** a verze formuláře pro vaši zemi (pole nabízí jen
   verze státu společnosti platné pro dané čtvrtletí). Přiznání lze sestavit od
   třetího čtvrtletí 2021, kdy se režim Unie začal používat.
2. **Registrován od / Registrován do** vyplňte, jen pokud registrace začala
   nebo skončila během čtvrtletí. Data se zapíší do formuláře jako začátek
   nebo konec období a přiznání vezme jen doklady s datem mezi nimi. Obě musí
   ležet ve čtvrtletí.
3. Klikněte na **Vypočítat**. Modul vezme každou zaúčtovanou účetní položku se
   štítkem `OSS`:
   - faktura patří do čtvrtletí podle data uskutečnění zdanitelného plnění,
     a není-li vyplněno, podle data faktury;
   - opravný daňový doklad patří do čtvrtletí, ve kterém byl **vystaven** — kdy
     se změna zjistila;
   - stát spotřeby se určí podle daně OSS (každá daň OSS patří jednomu státu
     určení), jinak podle fiskální pozice dokladu a nakonec podle dodací adresy.
4. Zkontrolujte tři záložky:
   - **Plnění** — řádky se základem daně a daní v eurech. Daň řádku se spočítá
     jako základ × sazba. Lupa otevře účetní položky, ze kterých řádek vznikl.
   - **Opravy předchozích čtvrtletí** — viz [Opravy](#corrections).
   - **Směnné kurzy** — viz [Směnné kurzy](#rates).
5. *Zaúčtovaná daň (EUR)* ukazuje daň OSS skutečně zaúčtovanou na dokladech,
   přepočtenou stejně, vedle spočtených součtů. Porovnejte je.

Dokud je přiznání v konceptu, lze řádky a opravy přidávat a upravovat ručně.
Řádek, který přidáte, je *Ruční* už sám; zaškrtněte *Ruční* i u spočteného
řádku, který změníte. **Vypočítat** ruční řádky ponechá a ostatní nahradí, takže
úprava nezaškrtnutého spočteného řádku se při dalším výpočtu ztratí. Na ručním řádku zadáváte základ i daň.

Zboží odeslané ze skladu v jiném členském státě nebo služby poskytnuté
z provozovny v jiném státě se vykazují zvlášť za tento stát. Na běžné faktuře
Odoo není zaznamenáno, odkud bylo zboží odesláno, proto se takové řádky
**nespočítají**: zadejte je ručně s polem *Dodáno ze státu* a, máte-li ho,
*DIČ v tomto státě*.

## Opravy předchozích čtvrtletí {#corrections}

Opravný daňový doklad (dobropis nebo vrubopis), který odkazuje na původní
fakturu z některého předchozího čtvrtletí, nesnižuje řádky tohoto čtvrtletí.
Stane se opravou původního čtvrtletí za daný stát spotřeby, přepočtenou kurzem
původního čtvrtletí. Dobropis k faktuře ze stejného čtvrtletí se od řádku
prostě odečte.

Dobropis bez odkazu na původní fakturu zůstane v tomto čtvrtletí. Vznikne-li
tím záporný řádek, export přiznání odmítne — žádný z formulářů záporný řádek
nepřipouští. Propojte dobropis s fakturou, nebo opravu zadejte ručně.

Před exportem modul ověří, že se každá oprava týká čtvrtletí od 3. čtvrtletí
2021 po čtvrtletí před tímto přiznáním, a odmítne opravu, jejíž tříletá lhůta
uplynula — takovou opravu je třeba provést přímo vůči státu spotřeby.

## Směnné kurzy {#rates}

Částky fakturované v eurech se přebírají tak, jak byly fakturovány. Pro každou
jinou měnu potřebuje přiznání jeden kurz za měnu a referenční datum: poslední
den tohoto čtvrtletí a poslední den každého čtvrtletí, kterého se týká oprava.

**Vypočítat** navrhne každý kurz z kurzovního lístku společnosti — první kurz
s datem v referenční den nebo později, tedy pravidlo „nejbližšího následujícího
dne“. Lístek může obsahovat kurzy ČNB nebo banky místo kurzů ECB a nic v něm
neříká které, proto je navržený kurz označen *Kurzovní lístek společnosti
(k potvrzení)* a zobrazen červeně. Každý kurz porovnejte s referenčním kurzem
ECB, případně ho opravte (kurz se zadává jako *jednotek měny za 1 EUR*)
a klikněte na **Potvrdit kurzy ECB**. Export odmítne přiznání s chybějícím nebo
nepotvrzeným kurzem. Potvrzený nebo zadaný kurz se při dalším výpočtu zachová.

## Export a podání {#export}

**Exportovat XML** postupně:

1. zkontroluje údaje společnosti — společnost musí mít DIČ v podobě, kterou
   vyžaduje národní modul;
2. zkontroluje obsah: chybějící nebo nepotvrzené kurzy, záporné řádky, stát
   mimo EU, plnění do státu, ze kterého se dodává, řádek, u kterého nelze určit
   typ sazby (základní nebo snížená), a opravy mimo období nebo po lhůtě;
3. vytvoří národní formulář a ověří ho proti úřednímu XSD uloženému ve verzi
   formuláře.

Každá chyba export zastaví s uvedením důvodu. Platný soubor se připojí
k přiznání, které přejde do stavu *Exportováno*.

XML podejte podle národního návodu a potom klikněte na **Označit jako podané**.
Podaný soubor se tím uchová jako podaná kopie a přiznání se uzamkne. **Podat**
otevře záznam podání, který sleduje doručení a uchovává potvrzení (viz
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base)).
**Vrátit do konceptu** — jen pro administrátory účetnictví — znovu otevře podané
přiznání a podanou kopii zachová.

Typ sazby každého řádku se určí z tabulky základních sazeb členských států
s datem jejich účinnosti: sazba rovná základní sazbě platné poslední den
čtvrtletí je *základní*, každá jiná *snížená*.

## Slovenská sazba 5 % {#tax-mapping}

Mapování daní OSS v Odoo nezná slovenskou sazbu 5 % ani v jednom směru, ačkoli
ji [§ 27 ods. 3 slovenského zákona o DPH](law:sk/2004/222#paragraf-27.odsek-3)
od 1. 1. 2025 uplatňuje i na část toho, co se do roku 2024 zdaňovalo sazbou
10 %. Bez mapování by si prodej OSS s touto daní ponechal tuzemskou sazbu.
Modul chybějící položky doplní vždy, když mapování Odoo běží, bez zásahu do
Odoo:

- **Slovenská 5 % → jiný členský stát**: zahraniční sazba, kterou Odoo používá
  pro původní slovenskou 10 %.
- **Jiný členský stát → slovenská 5 %**, pro prodejce z jiného státu, který
  prodává na Slovensko: nejnižší snížená sazba daného státu a navíc česká
  sazba 12 %.

Odoo 19 propojí tuzemskou daň s daní OSS jen tehdy, když daň OSS vytváří, takže
druhá tuzemská daň se stejnou sazbou ve státě určení — například slovenská 5 %
vedle 19 % — by zůstala nenamapovaná. Modul propojí každou takovou tuzemskou daň
s existující daní OSS. Jen přidává propojení; nikdy nevytváří daně ani nemění
mapování, které už na fiskální pozici je.

Při instalaci se mapování doplní každé společnosti, která už daně OSS má.
Společnosti, které OSS nikdy nepoužily, zůstanou beze změny. Mapování je návrh,
stejně jako v samotném Odoo: zkontrolujte ho podle zboží, které prodáváte.

## Omezení {#limitations}

- Jen **režim Evropské unie**. Režim mimo Evropskou unii a dovozní režim (IOSS)
  pokryty nejsou — Odoo pro ně nemá daně.
- Plnění odeslaná z jiného členského státu nebo z provozovny v jiném státě se
  nerozpoznají; zadejte je jako ruční řádky.
- Zboží a služby se rozlišují jen podle typu produktu; řádek bez produktu se
  počítá jako zboží.
- Porovnání *zaúčtované daně* se spočtenou a upozornění, že opravu je třeba
  podat dříve, aby se stihla tříletá lhůta, se zapisují jen do záznamu serveru;
  formulář je nezobrazí. *Zaúčtovanou daň* porovnejte s *Daní z plnění*
  a *Opravami* sami.
- Daň řádku se zaokrouhlí na centy ze základu řádku, nesčítá se z faktur.
  Český zákon přitom žádá vyčíslení na dvě desetinná místa bez zaokrouhlování —
  viz [návod k českému formuláři](module:l10n_cz_oss#limitations).
- Navržené kurzy pocházejí z kurzovního lístku společnosti a musí je
  zkontrolovat člověk.
- Tabulka typů sazeb a mapování 5 % odpovídají sazbám známým při vydání modulu.
  Pozdější změna základní sazby vyžaduje aktualizaci modulu.
