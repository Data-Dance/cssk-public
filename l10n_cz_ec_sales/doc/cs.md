---
title: Souhrnné hlášení CZ
summary: České souhrnné hlášení — tiskopis EPO DPHSHV — vypočtené z daní pro plnění do EU v české účtové osnově Odoo a exportované jako XML pro EPO.
verified: 19.0.1.3.0
---

## K čemu slouží {#purpose}

Český plátce DPH, který dodává zboží nebo poskytuje služby osobám
registrovaným k dani v jiném členském státě EU, je vykazuje v **souhrnném
hlášení**, které se podává elektronicky přes EPO Finanční správy jako
tiskopis **DPHSHV**.

Tento modul je českou vrstvou modulu
[module:l10n_cssk_ec_summary_base](module:l10n_cssk_ec_summary_base), který
obsahuje obrazovky a postup — příprava hlášení, kontrola řádků, export a
podání jsou popsány [tam](module:l10n_cssk_ec_summary_base#usage). Tento modul
přidává české kódy plnění, XML šablonu DPHSHV a oficiální schéma a označí
standardní daně české účtové osnovy Odoo.

## Právní rámec {#legal}

Odkazy jsou na [§ 102 zákona č. 235/2004 Sb., o dani z přidané
hodnoty](law:cz/2004/235).

- **Kdo podává.** Plátce, kterému vznikla povinnost přiznat dodání zboží z
  tuzemska do jiného členského státu osobě registrované k dani v jiném
  členském státě, přemístění zboží plátcem do jiného členského státu, dodání
  zboží kupujícímu při třístranném obchodu, je-li prostřední osobou, nebo
  poskytnutí služby s místem plnění v jiném členském státě podle § 9 odst. 1,
  u které je povinen přiznat daň příjemce (§ 102 odst. 1). Dále plátce, který
  přemístil zboží v režimu skladu (odst. 2), a identifikovaná osoba u
  takových služeb a třístranných obchodů (odst. 3).
- **Období a lhůta.** Plátce podává souhrnné hlášení **za každý kalendářní
  měsíc do 25 dnů** po jeho skončení (odst. 5). Plátce, který uskutečňuje jen
  poskytnutí služeb, podává hlášení **ve lhůtě pro podání daňového přiznání**
  (odst. 6) — čtvrtletní plátce tedy čtvrtletně — dokud neuskuteční dodání
  zboží; od té doby podává měsíčně do konce kalendářního roku (odst. 7).
- **Měna.** Údaje se uvádějí v české měně (odst. 4).
- **Opravy.** Zjistí-li plátce v podaném hlášení chybné údaje, je povinen do
  **15 dnů** ode dne zjištění podat **následné souhrnné hlášení** (odst. 8).

Kódy plnění podle pokynů k tiskopisu EPO, jak je obsahuje oficiální schéma:

| Kód | Plnění |
|---|---|
| 0 | dodání zboží do jiného členského státu osobě registrované k dani v jiném členském státě (§ 13 odst. 1 a 2) |
| 1 | přemístění obchodního majetku plátcem do jiného členského státu (§ 13 odst. 6) |
| 2 | dodání zboží formou třístranného obchodu (§ 17), vyplňuje jen prostřední osoba |
| 3 | poskytnutí služby s místem plnění v jiném členském státě (§ 9 odst. 1) |

## Verze tiskopisu {#version}

Modul instaluje **jedinou** verzi, *Souhrnné hlášení 2025*, platnou od
1. 1. 2010 bez data konce. Vytváří strukturu EPO *Pisemnost / DPHSHV*
(`verzePis` 02.01.05, struktura ze dne 11. 8. 2026) a ověřuje ji proti
přiloženému schématu `dphshv_epo2.xsd`. Kontrolní součet schématu a verze
struktury jsou zapsané v `data/SCHEMA_VERSION` i s postupem aktualizace a
test selže, když se soubor nebo `verzePis` šablony od záznamu odchýlí.

Jediná otevřená verze je záměr: Finanční správa vydává pro tiskopis jediné
schéma a aktualizuje ho na místě a EPO přijímá každé období v aktuální
struktuře. Neexistuje starší český tiskopis, který by se volil podle roku;
„2025“ v názvu je jen označení.

XML obsahuje záhlaví (*VetaD*: rok, měsíc nebo čtvrtletí, forma hlášení), údaje
o subjektu (*VetaP*, převzaté z modulu
[module:l10n_cz_statutory](module:l10n_cz_statutory) bez e-mailu a telefonu,
které tiskopis nemá) a jednu *VetaR* na řádek: kód státu, DIČ pořizovatele bez
kódu státu, kód plnění, počet plnění a celkovou hodnotu v celých korunách.
Storno řádek nese `k_storno="A"` a jen kód státu, DIČ a kód plnění.

## Nastavení {#setup}

Při instalaci modul nastaví kód plnění na daních pro plnění do EU u každé
společnosti, která v tu chvíli používá českou účtovou osnovu, pokud tam kód
ještě není:

| Daň české osnovy Odoo | Kód |
|---|---|
| 0% EU G — dodání zboží do EU | 0 |
| 0% EU S — poskytnutí služby do EU | 3 |

Pro kódy **1** a **2** standardní daň neexistuje. Přemísťujete-li vlastní zboží
nebo jste prostřední osobou v třístranném obchodu, musíte daň, kterou k tomu
používáte, označit sami — viz [nastavení společného
modulu](module:l10n_cssk_ec_summary_base#setup), kde jsou i údaje
společnosti, které export potřebuje (DIČ, finanční úřad v nastavení *Výchozí
správce daně*).

## Příprava a podání {#usage}

Postupujte podle [společného postupu](module:l10n_cssk_ec_summary_base#usage)
v nabídce *Účetnictví → Výkazy → Zákonné výkazy → Souhrnné hlášení*. Tento
modul nabízí typy *Řádné*, exportovaný jako forma **R**, a *Opravné* a
*Následné (dodatečné)*, oba exportované jako **N** (následné souhrnné
hlášení): tiskopis zná jen tyto dvě a § 102 opravné hlášení nezná.

**Následné hlášení obsahuje jen změny.** Při **Vypočítat** modul porovná
přepočtené období s tím, co za ně bylo podáno — s hlášeními téhož období
označenými jako podaná nebo zaznamenanými jako historická podání, v pořadí,
v jakém byla podána — a ponechá:

- **nový** řádek tak, jak je;
- řádek, jehož hodnota (v celých korunách, jak se exportuje) se **změnila**,
  jako storno řádek rušící podaný řádek a za ním opravený řádek;
- dříve podaný řádek, který **zmizel**, jen jako storno řádek.

Nezměněné řádky se vynechají. Storno řádky jsou zobrazené šedě se
zaškrtnutým *Ruší podaný řádek*. Následné hlášení bez zaznamenaného podaného
hlášení za stejné období se odmítne: původní hlášení nejdřív označte jako
podané, nebo ho importujte jako historické podání.

Export zapisuje kód státu podle DIČ odběratele tak, jak ho uvádí tiskopis —
**EL** pro Řecko, **XI** pro Severní Irsko — a každou hodnotu zaokrouhluje na
celé koruny **nahoru**. Odběratel s DIČ XI se přijme jen u zboží; služba pro
něj export zastaví.

Po **Exportovat XML** nahrajte soubor do EPO, nebo použijte **Podat**: s
modulem [module:l10n_cz_epo](module:l10n_cz_epo) lze hlášení odeslat na EPO ke
kontrole, nebo ho rovnou podat, podepsané certifikátem společnosti.

## Omezení {#limitations}

Než se na export spolehnete při ostrém podání, prověřte:

- **Opravy se porovnávají s tím, co je zaznamenáno zde.** Podání učiněné
  mimo Odoo a nezaznamenané jako historické podání porovnání nevidí.
- **Kódy se nekontrolují.** Export propustí jakoukoli jednu číslici; existují
  jen kódy 0–3.
- Režim skladu (§ 102 odst. 2) není podporován.
- Volba měsíčního či čtvrtletního podávání a přechod na měsíční po prvním
  dodání zboží (odst. 7) jsou na vás; modul je nekontroluje.
