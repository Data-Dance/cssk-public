---
title: CZ přepočet cizích měn k rozvahovému dni (kurzové rozdíly)
summary: Přepočte zůstatky v cizí měně kurzem ČNB k rozvahovému dni a kurzové rozdíly zaúčtuje na 563 a 663 — průvodcem OCA v edici Community a úpravou Odoo v edici Enterprise.
verified: 19.0.1.1.1
---

## K čemu slouží {#purpose}

K rozvahovému dni se otevřené pohledávky a závazky v cizí měně, devizové
účty a valutová pokladna přepočítávají kurzem tohoto dne; rozdíl proti
účetní hodnotě je nerealizovaný kurzový rozdíl. Česká osnova ho účtuje na
**563** *Kursové ztráty* a **663** *Kurzové zisky*.

Odoo samo účtuje kurzové rozdíly jen při spárování platby. Přepočet k
rozvahovému dni potřebuje další nástroj a který to je, závisí na edici:

| Edice | Nástroj | Modul |
|---|---|---|
| Community | průvodce *Přecenění měny* OCA (`account_multicurrency_revaluation`) | **tento modul**, [module:l10n_cz_currency_revaluation](module:l10n_cz_currency_revaluation) — viz [Community](#community) |
| Enterprise | výkaz *Nezrealizované kurzovní rozdíly* Odoo a jeho úprava | [module:l10n_cz_currency_revaluation_ee](module:l10n_cz_currency_revaluation_ee) — viz [Enterprise](#enterprise) |

Oba se nainstalují samy, je-li přítomen jejich nástroj a česká osnova
(`l10n_cz`). Nastaví účty a deník; samotný přepočet provede nástroj.

## Právní rámec {#legal}

Není-li uvedeno jinak, odkazy jsou na [zákon o účetnictví](law:cz/1991/563).

- Majetek a závazky se oceňují k okamžiku uskutečnění účetního případu a ke
  konci rozvahového dne (§ 24 odst. 2). K rozvahovému dni se přepočítává jen
  majetek a závazky uvedené v § 4 odst. 12 — pohledávky a závazky, podíly,
  cenné papíry, deriváty, ceniny a cizí měny, jsou-li vyjádřeny v cizí měně
  (§ 24c odst. 1 písm. b)).
- Přepočítává se **obecným kurzem**: kurzem vyhlášeným centrální bankou
  příslušnou pro měnu účetnictví pro den přepočtu, u účetnictví v Kč tedy
  kurzem ČNB; lze použít i kurz vyhlášený pro předcházející den (§ 24d
  odst. 1 a 3).
- **Pevný kurz** lze použít jen k okamžiku uskutečnění účetního případu,
  nikoli k rozvahovému dni (§ 24c odst. 2, § 24d odst. 4).
- Kurzové rozdíly se účtují na vrub finančních nákladů nebo ve prospěch
  finančních výnosů; u postupně splácených pohledávek a dluhů a u pohybů na
  účtech skupin 21, 22 a 26 je lze vyúčtovat až ke konci rozvahového dne —
  [§ 60 odst. 1 a 2 vyhlášky č. 500/2002 Sb.](law:cz/2002/500)

## Community: průvodce OCA {#community}

### Co modul nastaví {#setup}

U každé společnosti s českou osnovou — při načtení osnovy nebo při
instalaci, má-li ji společnost už načtenou:

| Nastavení | Hodnota |
|---|---|
| Účet kurzových ztrát | 563000, je-li prázdný |
| Účet kurzových zisků | 663000, je-li prázdný |
| Výchozí deník kurzových zisků a ztrát | deník **KURZ** *Kurzové rozdíly* typu *Ostatní*, který se založí, nemá-li společnost deník s tímto kódem |

Najdete je v *Účetnictví → Konfigurace → Nastavení*, oddíl *Přecenění ve
více měnách*, spolu s volbou *Automaticky zaúčtovat vytvořené zápisy*
(vypnuto: zápisy vzniknou jako koncept).

### Před prvním přepočtem {#before}

1. **Přidělte si přístup.** Nabídky OCA vidí jen členové skupiny
   *Zaúčtování dodatečných rezervních zápisů*, kterou ve výchozím stavu
   nemá nikdo. Přidejte ji uživateli v *Nastavení → Uživatelé*, oddíl
   *Extra práva*, který se zobrazí v režimu vývojáře.
2. **Vyberte účty k přepočtu.** Zaškrtněte *Povolit přecenění měny* u
   každého účtu, jehož zůstatek v cizí měně se má přepočítat: devizové
   bankovní účty a valutové pokladny (22x, 21x), pohledávky (311) a závazky
   (321) a další, které určí vaše účetní. U účtů, které se nepřepočítávají —
   například poskytnuté a přijaté zálohy, nebo co vylučuje váš vnitřní
   předpis — volbu nechte vypnutou.
3. **Načtěte kurzy.** Kurz ČNB k datu přepočtu musí být v Odoo, například
   přes [module:currency_rate_update_cz](module:currency_rate_update_cz).

### Provedení přepočtu {#usage}

*Účetnictví → Účetnictví → Uzávěrka → Přecenění měny*:

1. Zadejte *Datum přecenění* (rozvahový den). **Pole *Začátek období
   přecenění* vymažte** nebo ho nastavte dostatečně dříve: přepočtou se jen
   účetní položky s datem od tohoto dne, a výchozí hodnotou je první den
   aktuálního měsíce — ke konci roku by tak vypadly všechny otevřené položky
   z dřívějších měsíců. Zkontrolujte deník a vzor *Popis zápisu*.
2. Zkontrolujte seznam účtů: na začátku obsahuje všechny účty s volbou
   *Povolit přecenění měny* a pro tento přepočet můžete účty ubrat nebo
   přidat.
3. Klikněte na **Potvrdit**. U účtů pohledávek a závazků vznikne jeden
   zápis za účet, měnu a partnera, u ostatních účtů jeden za účet a měnu.
   Ztráty jdou na 563000, zisky na 663000.

*Výkaz přecenění měny* v *Účetnictví → Výkazy → Uzávěrkové zápisy* ukazuje
nerealizované kurzové rozdíly. *Storno přecenění měny* ve stejné nabídce
*Uzávěrka* stornuje zápisy přepočtu ze zvoleného období k datu, které
zadáte — zda na začátku dalšího období stornovat, rozhoduje vaše účetní.

### Společnosti s pevným měsíčním kurzem {#fixed-rate}

Společnost, která doklady účtuje pevným měsíčním kurzem, má tento kurz v
běžné kurzovní tabulce Odoo, a k rozvahovému dni přesto musí použít obecný
kurz daného dne (viz [výše](#legal)). Vede-li
[module:currency_rate_update_cz](module:currency_rate_update_cz) vedle
pevného kurzu i skutečné denní kurzy ČNB, tento modul zajistí, že průvodce
přepočtu použije **skutečný kurz** k datu přecenění (nebo poslední kurz před
ním). Společnost s denními kurzy samostatné skutečné kurzy nevede a nic se
pro ni nemění.

## Enterprise: úprava kurzových rozdílů {#enterprise}

[module:l10n_cz_currency_revaluation_ee](module:l10n_cz_currency_revaluation_ee)
se nainstaluje sám s účetnictvím Odoo Enterprise a u každé české
společnosti nastaví:

| Nastavení úpravy | Hodnota |
|---|---|
| Expense Provision Account (česky *Účet zajišťování výdajů*) | 563000 |
| Income Provision Account (česky *Účet poskytování příjmů*) | 663000 |
| Deník | KURZ *Kurzové rozdíly*, založený, pokud chybí, nemá-li společnost ještě deník pro přecenění |

Při instalaci se oba účty **přepíšou**, ať bylo nastaveno cokoli. Český
překlad Odoo obou polí je nesrozumitelný; jde o protiúčty pro ztrátu a pro
zisk.

Přepočet: *Účetnictví → Revize → Regularization Entries → Unrealized
Currencies* (tyto nabídky Odoo do češtiny nepřekládá) otevře výkaz
*Nezrealizované kurzovní rozdíly*. Nastavte jeho datum na rozvahový den a
klikněte na **Zadání úpravy**. Průvodce navrhne zápis: každý účet v cizí
měně se upraví a protizápis jde na 563000 při ztrátě nebo na 663000 při
zisku. *Datum opravného záznamu* je povinné: Enterprise k tomuto datu vždy
zaúčtuje storno úpravy, obvykle k prvnímu dni dalšího období.

## Omezení {#limitations}

- Moduly nastavují jen účty a deník. V edici Community se nic nepřepočítá,
  dokud účty nemají volbu *Povolit přecenění měny*, a nabídky zůstanou
  skryté, dokud uživatel nedostane uvedenou skupinu.
- *Začátek období přecenění* má výchozí hodnotu první den aktuálního měsíce
  a bez upozornění omezí přepočet na položky od tohoto dne.
- Výkaz Enterprise navrhne všechny účty v cizí měně. Ty, které se
  nepřepočítávají, vylučte přímo ve výkazu (přesunou se pod *Vyloučené
  účty*; Odoo si volbu pamatuje pro každý účet a měnu).
- Enterprise úpravu k datu storna vždy stornuje; ponechat ji nelze.
- Žádný z modulů nekontroluje, které účty se přepočítávají: o tom, i o
  vyloučení záloh a jiných položek, rozhoduje vaše účetní.
- Instalace založí deník KURZ u každé české společnosti, která nemá
  nastavený deník pro přecenění, ať cizí měny používá, nebo ne.
