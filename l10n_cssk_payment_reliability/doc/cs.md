---
title: CZ/SK kontrola spolehlivosti dodavatele
summary: Před úhradou dodavateli ověří v registrech správce daně jeho spolehlivost a bankovní účet, na který platíte, a výsledek ponechá na faktuře a platbě jako doklad.
verified: 19.0.1.3.0
---

## K čemu slouží {#purpose}

V obou zemích může plátce, který nakupuje od dodavatele, zaplatit daň, kterou
dodavatel neodvedl — v Česku jde o **ručení za nezaplacenou daň**, na
Slovensku o *ručenie za daň*. Dvě okolnosti, které ručení zakládají, lze před
úhradou ověřit ve veřejných registrech:

- zda správce daně dodavatele neoznačil (CZ: **nespolehlivý plátce**; SK:
  seznam plátců, u nichž nastaly důvody pro zrušení registrace);
- zda je bankovní účet, na který platíte, **zveřejněný** správcem daně.

Modul se registrů zeptá při zaúčtování přijaté faktury nebo platby
dodavateli, odpověď s časovým razítkem zapíše na doklad a při riziku zobrazí
upozornění. Zaúčtování ani platbu **nikdy nezablokuje**: rozhodnutí zůstává
na vás a záznam ukazuje, co register v tu chvíli uváděl.

Sám modul žádné napojení na register nemá. Údaje dodává modul pro danou
zemi:

| Dodavatel | Modul | Register |
|---|---|---|
| český | [module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) | webová služba ADIS Ministerstva financí (registr plátců DPH) |
| slovenský | [module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability) | otevřená data Finančnej správy SR |

Bez modulu pro zemi dodavatele skončí každá kontrola stavem *Neověřeno /
nedostupné*, bez upozornění.

## Právní rámec {#legal}

**Česko** — [zákon o DPH, § 106a, § 109, § 109a](law:cz/2004/235):

- § 106a: správce daně rozhodne, že plátce, který závažným způsobem porušil
  své povinnosti vztahující se ke správě daně, je **nespolehlivým plátcem**.
- § 109 odst. 2: má se za to, že příjemce zdanitelného plnění věděl nebo
  vědět měl a mohl, že daň nebude úmyslně uhrazena — a ručí za ni —, mimo
  jiné pokud je o poskytovateli zveřejněno, že je nespolehlivým plátcem
  (písm. a)), nebo pokud je úplata poskytnuta bezhotovostním převodem na
  **jiný účet než účet poskytovatele zveřejněný správcem daně** (písm. c)
  bod 2).
- § 98 písm. d): zveřejňuje se číslo účtu, které plátce v přihlášce k
  registraci určil ke zveřejnění.
- § 109a: příjemce může daň za poskytovatele uhradit přímo jeho správci daně
  (zvláštní způsob zajištění daně).

**Slovensko** — [zákon o DPH](law:sk/2004/222):

- Podle [§ 69 ods. 13](law:sk/2004/222#paragraf-69.odsek-13) ručí platiteľ,
  kterému je dodáno zboží nebo služba, za daň z faktury, kterou dodavatel
  nezaplatil, pokud věděl nebo vědět měl a mohl, že daň nebude zaplacena.
  Dostatečným důvodem je podle
  [písm. c)](law:sk/2004/222#paragraf-69.odsek-13.pismeno-c) i platba na jiný
  účet, než je účet dodavatele, který byl **v den platby zveřejněn** v seznamu
  bankovních účtů; dnem platby je den zadání platebního příkazu bance.
- Seznam bankovních účtů zveřejňuje finanční ředitelství podle
  [§ 6 ods. 6](law:sk/2004/222#paragraf-6.odsek-6).
- Podle [§ 69 ods. 14](law:sk/2004/222#paragraf-69.odsek-14) se zveřejňují
  plátci, u nichž nastaly důvody pro zrušení registrace podle § 81 ods. 3
  písm. b) druhého bodu.
- Ručení se uplatňuje podle [§ 69b](law:sk/2004/222#paragraf-69b);
  [§ 69c](law:sk/2004/222#paragraf-69c) umožňuje odběrateli zaplatit daň z
  faktury přímo na účet správce daně vedený pro dodavatele.
- **Index daňovej spoľahlivosti** (vysoko spoľahlivý / spoľahlivý / menej
  spoľahlivý) určuje daňový úřad podle
  [§ 53d daňového poriadku](law:sk/2009/563#paragraf-53d) a zveřejňuje se
  podle [§ 52 ods. 17](law:sk/2009/563#paragraf-52.odsek-17). Nepatří mezi
  důvody podle § 69 ods. 13; modul jej zobrazuje jako doplňující informaci.

## Nastavení {#setup}

*Účetnictví → Konfigurace → Nastavení*, blok **Přijaté faktury**, nastavení
**Kontrola spolehlivosti dodavatele (CZ/SK)**. Ve výchozím stavu je zapnuté
pro každou společnost; chcete-li kontrolovat jen ručně, vypněte je pro danou
společnost.

Kontrola běží jen ve společnostech, jejichž daňovou zemí je Česko nebo
Slovensko. Nainstalujte modul pro každou zemi, odkud máte dodavatele;
slovenský potřebuje i API klíč (viz [níže](#sk-provider)).

Dodavatel musí mít údaj, podle kterého register vyhledává:

| Dodavatel | Potřebné na kontaktu |
|---|---|
| český | země Česko a *DIČ* (`CZ12345678`) |
| slovenský | země Slovensko (nebo *DIČ* začínající `SK`), *DIČ* = IČ DPH pro účty a seznam ke zrušení registrace, *IČO* pro index spolehlivosti |

Účet, na který platíte, se se seznamem z registru porovnává jako **IBAN**. Účet
českého dodavatele může být zadán i v tuzemském tvaru (`19-2000145399/0800`);
český poskytovatel ho nejprve převede na IBAN.

## Kdy se kontroluje {#checks}

- **Při zaúčtování přijaté faktury nebo dobropisu od dodavatele** —
  automaticky, je-li nastavení zapnuté.
- **Při zaúčtování odchozí platby dodavateli** — automaticky, vůči účtu, na
  který platba skutečně jde. Právě na platbě ručení závisí a mezi fakturou a
  platbou mohou uběhnout týdny.
- **Denně** — naplánovaná akce *Supplier reliability: re-check unpaid bills
  (CZ/SK)* znovu ověří zaúčtované faktury, které ještě nejsou uhrazené (nebo
  jsou uhrazené jen částečně) a naposledy byly ověřeny před více než 7 dny,
  nejvýše 200 najednou, od nejstarších.
- **Ručně** — tlačítko **Zkontrolovat spolehlivost dodavatele** pod bankovním
  účtem příjemce na přijaté faktuře a pod bankovním účtem dodavatele na
  platbě. Funguje v každém stavu dokladu včetně konceptu, i když je
  automatická kontrola vypnutá.
- **Na kontaktu** — *Akce → Check tax reliability* v seznamu nebo na
  formuláři kontaktu zjistí jen hodnocení, pro společnost každého označeného
  kontaktu.

Každá kontrola, která hodnocení získá, ho zapíše i na kontakt dodavatele jako
**Daňová spolehlivost** s časem kontroly, vedle jeho *DIČ*.

Register, který neodpoví, zaúčtování nikdy nezastaví; doklad pak ukáže
*Neověřeno / nedostupné*.

## Co uvidíte {#results}

Na přijaté faktuře (a na platbě) u bankovního účtu:

| Pole | Význam |
|---|---|
| Kontrola bankovního účtu | *Účet pro platbu je zveřejněný*, *Účet pro platbu NENÍ zveřejněný*, *Není nastaven bankovní účet* nebo *Neověřeno / nedostupné* |
| Spolehlivost dodavatele | hodnocení z registru, viz moduly pro jednotlivé země níže |
| Seznam ke zrušení registrace (*VAT Deregistration Listing*) | vyplněno, je-li dodavatel na seznamu plátců, u nichž nastaly důvody pro zrušení registrace (Slovensko) |
| Registrované účty (při kontrole) | účty, které register v tu chvíli uváděl (jen na faktuře) |
| Spolehlivost ověřena dne | kdy byl záznam pořízen |

V horní části dokladu se zobrazí upozornění a stejný text se zapíše do
chatteru, pokud:

- účet, na který platíte, **není** mezi zveřejněnými účty — se zvláštním
  zněním, pokud dodavatel nezveřejnil žádný účet;
- hodnocení je *Méně spolehlivý* nebo *Nespolehlivý*;
- dodavatel je na seznamu ke zrušení registrace.

Každá nová kontrola záznam na dokladu přepíše; dřívější upozornění zůstávají
v chatteru. Pole záznamu nelze upravovat a při duplikaci faktury se
nepřenášejí.

Jak s upozorněním naložíte, je na vás: zaplaťte na zveřejněný účet, nebo
uhraďte daň přímo správci daně dodavatele (§ 109a CZ / § 69c SK) a zbytek
dodavateli.

## Český registr (ADIS) {#cz-provider}

[module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) se
ptá webové služby Ministerstva financí *rozhraní CRP DPH* (veřejná část
registru plátců DPH) na dodavatele se zemí Česko. Nepotřebuje účet ani klíč.
Jeden dotaz odpoví na obě otázky:

| Odpověď ADIS | Spolehlivost dodavatele |
|---|---|
| nespolehlivý plátce = ANO | Nespolehlivý (upozornění) |
| nespolehlivý plátce = NE | Spolehlivý |
| nenalezen (není plátce) | Není plátce DPH; bankovní účet je *Dodavatel není plátce DPH*, bez upozornění, protože neplátce účty nezveřejňuje a § 109 se na něj nevztahuje |

Zveřejněné účty přicházejí v tuzemském tvaru (předčíslí–číslo/kód banky);
modul je, stejně jako účet zadaný na faktuře v tomto tvaru, před porovnáním
převede na IBAN. Účty zveřejněné v jiném tvaru
(zahraniční IBAN) se porovnávají tak, jak jsou zveřejněny. Český registr
seznam ke zrušení registrace nevede, takže toto pole u českých dodavatelů
zůstává prázdné.

## Slovenský registr (otevřená data FS SR) {#sk-provider}

[module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability)
používá službu otevřených dat slovenské Finančnej správy
(`opendata.financnasprava.sk`), která vyžaduje bezplatný API klíč. Požádejte
o něj tam a zadejte jej v *Účetnictví → Konfigurace → Nastavení* u nastavení
**Kontrola spolehlivosti dodavatele (CZ/SK)** do pole *FS open-data API key*
(popisek je v této verzi anglicky). Klíč je společný pro všechny společnosti
databáze. Bez něj je každá kontrola slovenského dodavatele *Neověřeno /
nedostupné*.

| Otázka | Datová sada | Hledá se podle |
|---|---|---|
| zveřejněné bankovní účty | `ds_dph_iban` (seznam bankovních účtů plátců DPH) | IČ DPH (*DIČ*) |
| spolehlivost | `ds_iz_ran` (index daňovej spoľahlivosti) | IČO |
| seznam ke zrušení registrace | `ds_dphz` | IČ DPH |

| Index daňovej spoľahlivosti | Spolehlivost dodavatele |
|---|---|
| vysoko spoľahlivý | Vysoce spolehlivý |
| spoľahlivý | Spolehlivý |
| menej spoľahlivý | Méně spolehlivý (upozornění) |
| není v indexu | Neznámé / nezkontrolováno |

Před hledáním v seznamu ke zrušení registrace se modul služby zeptá, zda lze
v této datové sadě hledat podle IČ DPH. Pokud ne, pole zůstane prázdné a
kontrola se považuje za nedostupnou, ne za čistý výsledek.

## Omezení {#limitations}

- **Jen upozorňuje, nikdy neblokuje.** Nic vám nebrání zaúčtovat ani
  zaplatit na nezveřejněný účet.
- **Prázdný slovenský seznam vede k upozornění.** Neuvádí-li slovenský seznam
  pro IČ DPH na kontaktu žádný účet, upozornění řekne, že dodavatel žádný
  nezveřejnil. U plátce je to právě případ ručení; datová sada ale nerozliší
  plátce bez účtu od subjektu, který plátcem není. Než se na upozornění
  spolehnete, ověřte registraci dodavatele. Českého dodavatele, kterého ADIS
  nevede jako plátce, modul označí *Neověřeno / nedostupné*.
- **Tuzemský tvar účtu** rozpozná jen u českých dodavatelů. Slovenský účet
  zadejte jako IBAN.
- **Den platby.** Zákon hledí na zveřejnění v okamžiku platby. Modul
  kontroluje při zaúčtování platby v Odoo; pokud příkaz bance odešlete
  později, zkontrolujte znovu.
- **Dodavatelé z jiných zemí** se nekontrolují. Dodavatel bez země (český
  registr) nebo bez údaje, který registr potřebuje, skončí stavem *Neověřeno /
  nedostupné*, bez upozornění.
- **Daňová spolehlivost** na kontaktu je poslední hodnocení, které některá
  kontrola získala; záznamem o tom, co registr uváděl v dané chvíli, zůstává
  stav na faktuře a platbě.
- Název slovenské datové sady pro seznam ke zrušení registrace (`ds_dphz`)
  nebyl ověřen vůči živé službě; je-li nesprávný, pole prostě zůstane
  prázdné.
- Kontrola zaznamenává, co uváděl registr; neprokazuje, že dodavatel daň
  zaplatí, ani že jste o riziku nemohli vědět jinak.
