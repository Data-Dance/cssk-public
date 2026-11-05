---
title: Česká EET 2.0 (elektronická evidence tržeb)
summary: Eviduje kontaktní platby přijaté mimo pokladnu — hotovost, kartu nebo QR kód zaplacený u pultu — v českém systému EET 2.0, uchovává každou datovou zprávu s potvrzovacím kódem, opakuje odeslání, dokud ji správce daně nepřijme, a sám obnovuje pokladní certifikát.
verified: 19.0.1.3.1
---

## K čemu slouží {#purpose}

Od **1. ledna 2027** musí každý český podnikatel, který přijímá **kontaktní
platby** — peníze přijaté v osobním kontaktu se zákazníkem nebo ve své
provozovně, ať hotově, kartou na terminálu nebo QR kódem načteným u pultu —
oznámit každou takovou tržbu Finanční správě v okamžiku, kdy nastane. To je
**EET 2.0**, druhé vydání elektronické evidence tržeb.

Tento modul je její odooovská strana. Drží **pokladní certifikát** vydaný
Finanční správou, sestaví a podepíše datovou zprávu o každé tržbě, odešle ji na
bránu EET 2.0 a uloží **potvrzovací kód** (*POK*), který se vrátí. Tržby
z pokladny modulu Místo prodeje eviduje
[module:l10n_cz_eet2_pos](module:l10n_cz_eet2_pos); tento modul eviduje
kontaktní platby zaúčtované v účetnictví — zákazník platící fakturu hotově
v kanceláři, kartu přijatou u pultu, QR kód načtený v prodejně.

## Právní rámec {#legal}

[Zákon o evidenci tržeb](law:cz/2026/180), č. 180/2026 Sb., účinný od
1. ledna 2027. Certifikáty a evidenční jednotky lze v daňovém portálu zřídit od
1. listopadu 2026 a produkční brána od tohoto dne přijímá zprávy v přechodném
režimu.

- **Evidovanou tržbou** je platba přijatá v osobním kontaktu s podnikatelem,
  nebo v jeho provozovně či dopravním prostředku v souvislosti se zbožím nebo
  službou (§ 5 a § 6). Na způsobu platby nezáleží: hotovost, karta, bankovní
  převod, QR kód, poukázky, žetony i kryptoaktiva se počítají, jsou-li přijaty
  tímto způsobem. Tentýž QR kód zaplacený z domova kontaktní platbou **není**.
- Tržba se eviduje **nejpozději při jejím uskutečnění**. U platby kartou nebo
  QR kódem je tím okamžikem **vydání příkazu k platbě**, nikoli připsání peněz
  (§ 16 odst. 2).
- Zpráva nese jen EIČ poplatníka, evidenční jednotku, pokladní zařízení,
  pořadové číslo, datum a čas a **celkovou částku v Kč** (§ 17). Žádné položky,
  žádný rozpis DPH, žádné údaje o zákazníkovi, žádný způsob platby.
- Podnikatel si nastaví **mezní dobu odezvy** nejméně 2 sekundy (§ 19). Když
  brána neodpoví včas, tržba se přesto uskuteční a zpráva se odešle hned po
  pominutí příčiny, **nejpozději do 48 hodin**; po jejich uplynutí povinnost
  nezaniká (§ 20).
- Vrácení nebo oprava se eviduje jako **záporná tržba** (§ 8).
- Nabití a čerpání dárkových karet, elektronických peněženek a podobných
  prostředků použitelných jen v omezené síti se eviduje ve dvou zvláštních
  položkách (§ 17 odst. 2); viz
  [module:l10n_cz_eet2_pos_loyalty](module:l10n_cz_eet2_pos_loyalty).
- Zákon **nevyžaduje účtenku**. Tisk POK na účtence je dobrovolný.
- EIČ je DIČ poplatníka (§ 18). Certifikát platí jeden rok.

Zda je určitá platba kontaktní, je úsudek váš a vašeho poradce; modul eviduje,
co označíte, nerozhoduje za vás.

## Nastavení {#setup}

### 1. V daňovém portálu {#portal}

V **MOJE daně → DIS+** oznamte své **evidenční jednotky** (každou provozovnu,
dopravní prostředek nebo činnost „mimo provozovnu“). Každá dostane číslo o dvou
až devíti číslicích končící 1 až 4. Poté vygenerujte jeden nebo více
**pokladních certifikátů** a každý stáhněte jako soubor `.p12` s heslem.

### 2. Nastavení společnosti {#settings}

*Účetnictví → Konfigurace → Nastavení*, blok **Czech EET 2.0**, zaškrtněte
**Enable EET 2.0**:

| Nastavení | Co dělá |
|---|---|
| EET 2.0 Environment | *Playground* pro zkoušení, *Production* pro skutečné tržby. Potvrzovací kód z playgroundu končí na `-ff` a žádnou zákonnou povinnost neplní. |
| EET 2.0 Taxpayer EIC | Vaše EIČ, `CZ` a 8 až 10 číslic. Předvyplní se z DIČ společnosti, má-li správný tvar. |
| EET 2.0 Default Unit ID | Číslo evidenční jednotky z DIS+ použité tam, kde ji deník ani pokladna neuvádí. |
| EET 2.0 Certificate | Certifikát, kterým se zprávy podepisují; viz níže. |
| EET 2.0 Response Time Limit (s) | Jak dlouho pokladna čeká na bránu, než tržbu pustí dál; nejméně 2 sekundy, výchozí 5. |
| EET 2.0 Warn After Attempts | Po tolika neúspěšných pokusech se zapíše varování. Odesílání samo nikdy nepřestane. |
| EET 2.0 Renew Certificate (days before expiry) | Kolik dní před vypršením certifikátu se sama spustí jeho obnova; 0 obnovu vypne. |

### 3. Certifikáty {#certificates}

*EET 2.0 → Configuration → Certificates*: založte záznam pro každý certifikát,
zvolte prostředí, nahrajte `.p12` a zadejte heslo. EIČ v certifikátu a jeho
platnost se načtou ze souboru. **Test certificate** odešle zprávu
v *ověřovacím módu*: brána vše zkontroluje a odpoví, aniž by tržbu zaevidovala,
takže certifikát i spojení ověříte na produkční bráně, aniž byste cokoli
evidovali. Playgroundový certifikát lze použít jen proti playgroundu a naopak.

### 4. Které platby se evidují {#scope}

Na každém bankovním či pokladním deníku, záložka *Pokročilá nastavení*, blok
**Czech EET 2.0**:

| Pole | Co dělá |
|---|---|
| EET 2.0 Contact Payments | Nové přijaté platby od zákazníků v tomto deníku se navrhnou jako kontaktní. |
| EET 2.0 PoS ID (id_pokl) | Označení pokladního zařízení odesílané za tento deník, nejvýše 20 znaků; při prázdném poli kód deníku. |
| EET 2.0 Unit ID (id_jednotky) | Evidenční jednotka tohoto deníku; při prázdném poli výchozí jednotka společnosti. |

Každá platba od zákazníka pak nese vlastní příznak **EET 2.0 Contact
Payment**, navržený z deníku a upravitelný, dokud není tržba přijata. Zde
rozlišíte dva případy, které zákon posuzuje různě a které dopadnou na tentýž
bankovní účet: QR kód načtený u pultu (zaškrtnout) a tentýž kód zaplacený
z domova (odškrtnout). Platby od dodavatelů se neevidují nikdy, stejně jako
platby, které Odoo zaúčtuje při uzavření pokladní relace Místa prodeje — ty
objednávky už zaevidovala pokladna.

## Jak se tržba eviduje {#flow}

Při zaúčtování označené platby Odoo zařadí **zprávu** do fronty a naplánovaná
úloha ji do zhruba dvou minut odešle. *EET 2.0 → Messages* je vypisuje všechny
a každá platba ukazuje svůj **EET 2.0 Status**, **EET 2.0 POK** a tlačítko
*EET 2.0*, které otevře její zprávy.

| Stav | Význam |
|---|---|
| To Send, Retry Scheduled | Čeká na další pokus. |
| Accepted | Brána vydala POK. Hotovo. |
| Verified | Test v ověřovacím módu uspěl; žádná tržba nebyla zaevidována. |
| Rejected | Brána zprávu odmítla natrvalo (neplatný podpis, chybné EIČ, chyba schématu). Odstraňte příčinu a stiskněte **Requeue**. |
| Error | Zprávu nebylo možné sestavit, obvykle proto, že nebyl k dispozici platný certifikát. Zkouší se každou hodinu a po nahrání nebo výběru certifikátu se zařadí znovu sama. |

Co se děje při nedostupné bráně, se řídí zákonem: pokusy se opakují
s rostoucími rozestupy do 48 hodin od tržby, poté **každou hodinu, dokud je
třeba**. Zpráva, která hranici 48 hodin překročí, dostane příznak **Past 48 h**
a správci EET 2.0 se založí aktivita, takže nevyřízené zprávy nikdy nestárnou
potichu. Každý pokus je novou zprávou s novým identifikátorem, jak vyžaduje
metodika Finanční správy; dřívější identifikátory zůstávají na záznamu
v záložce *Previous attempts* a XML požadavku i odpovědi se uchovává pro
podporu.

**Vrácení a storna.** Vrácení zaúčtované platby do návrhu nebo její zrušení
zaeviduje **zápornou tržbu** ve stejné výši, k okamžiku storna, ve stejném
pokladním zařízení a řadě. Opětovné zaúčtování platby zaeviduje novou tržbu.
Vratka zákazníkovi vyplacená z označeného deníku se eviduje jako záporná
tržba rovněž.

**Částky.** Zpráva je vždy v Kč. Platba v jiné měně se přepočte kurzem
společnosti ke dni tržby a původní částka i měna zůstávají na zprávě.

## Obnova certifikátu {#renewal}

Pokladní certifikát platí jeden rok. Modul jej obnovuje přes službu
**CA EET 2.0** Finanční správy bez návštěvy portálu: nastavený počet dní před
vypršením požádá o následný certifikát, stáhne jej jako **nový záznam
certifikátu**, odešle s ním zprávu v ověřovacím módu, a teprve když ji brána
přijme, přepne společnost na nový certifikát, starý archivuje a stažení úřadu
potvrdí. **Renew with CA EET** na certifikátu spustí tentýž cyklus ručně a stav
**Renewal** ukazuje, kde právě je. Selže-li ověření nebo úřad žádost odmítne,
starý certifikát zůstává v užívání a správce EET 2.0 dostane aktivitu. Zvláštní
denní kontrola upozorní 30, 14 a 7 dní před vypršením.

## Omezení {#limitations}

- Adresa certifikační autority pro **playgroundové** certifikáty je náš výklad
  zveřejněné specifikace, která uvádí tři prostředí, aniž by řekla, které
  z neprodukčních obsluhuje playground. Produkční obnovy se to netýká. Obě
  adresy jsou systémové parametry, které správce může změnit.
- Modul nerozezná kontaktní platbu od vzdálené; výchozí hodnota deníku
  a příznak na platbě jsou vaše rozhodnutí.
- **Kopie produkční databáze** nesmí evidovat tržby. Neutralizace databáze
  v Odoo (používaná při sestavení staging větví na Odoo.sh a při *duplikaci
  s neutralizací*) vypne EET 2.0 u každé společnosti kopie; certifikáty
  a nastavení zůstávají, takže kopii lze znovu zapnout proti playgroundu.
- Režim *EET OFF* pro nejmenší živnostníky je volba učiněná vůči finančnímu
  úřadu, nikoli zdejší nastavení; společnost v něm EET 2.0 prostě nechá vypnuté.
- Evidence za jiného poplatníka (*pověření*, *zastoupení*) je ve zprávě
  přenášena, ale zatím nemá vlastní konfigurační obrazovku.
