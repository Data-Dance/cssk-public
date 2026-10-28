---
title: CZ Přehled o výši pojistného (PVPOJ)
summary: Měsíční přehled o výši pojistného pro ČSSZ — celkové pojistné na sociální zabezpečení zaměstnavatele za měsíc, sečtené z výplatních pásek a vyexportované do XML ve struktuře PVPOJ 2025.
verified: 19.0.1.1.4
---

## K čemu slouží {#purpose}

*Přehled o výši pojistného* (**PVPOJ**) je měsíční hlášení zaměstnavatele
České správě sociálního zabezpečení o pojistném na sociální zabezpečení
a příspěvku na státní politiku zaměstnanosti za kalendářní měsíc: úhrn
vyměřovacích základů, pojistné zaměstnavatele a zaměstnanců a uplatněná
sleva na pojistném za zaměstnance na kratší úvazek.

Modul sestaví přehled za jeden měsíc z výplatních pásek tohoto měsíce
a vyexportuje ho do XML ve struktuře ČSSZ `PVPOJ2025`, ověřeného proti
oficiálnímu schématu `PVPOJ25.xsd`. Výplatní pásky čte přes
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
takže funguje s oběma jádry českých mezd — viz
[příručku českých mezd](module:l10n_cz_hr_payroll_base#declarations).

**Od roku 2026 se přehled podává už jen za starší období.** Než modul
použijete, přečtěte si následující oddíl.

## Právní rámec {#legal}

- **Od roku 2026 přehled nahradilo JMHZ.** Od 1. ledna 2026 sděluje
  zaměstnavatel vyměřovací základ a výši pojistného prostřednictvím
  *jednotného měsíčního hlášení zaměstnavatele* (JMHZ) podle
  [§ 9 odst. 2 zákona o pojistném na sociální zabezpečení](law:cz/1992/589),
  který odkazuje na [zákon o jednotném měsíčním hlášení zaměstnavatele](law:cz/2025/323).
  JMHZ se podává od 1. do 20. dne následujícího měsíce (§ 7 odst. 1 tohoto
  zákona). Tento modul JMHZ nevytváří.
- **Kdy se PVPOJ podává i nadále.** Podle přechodných ustanovení
  [zákona č. 360/2025 Sb.](law:cz/2025/360) (čl. IX) se přehled podává
  - za **měsíce před lednem 2026**, způsobem podle znění účinného do konce
    roku 2025 — i když se podává nebo opravuje teprve nyní;
  - za **leden až březen 2026** zaměstnavatelem, který byl v těchto měsících
    zaměstnavatelem a 1. dubna 2026 už jím není, a to do 20. dne měsíce
    následujícího po měsíci, v němž zaměstnavatelem být přestal.
- **Částky.** Pojistné je splatné od 1. do 20. dne následujícího měsíce
  ([§ 9 odst. 1](law:cz/1992/589)). Sazba zaměstnavatele činí 24,8 %
  z vyměřovacího základu běžných zaměstnanců (*§ 7 odst. 1 písm. a)*, pásmo
  A), sazba zaměstnance 7,1 % (*písm. d)*); pojistné se zaokrouhluje na celé
  koruny nahoru (*§ 7 odst. 3*). Vyšší sazby zaměstnavatele pro zdravotnické
  záchranáře a hasiče podniků (pásmo B) a pro rizikové zaměstnání (pásmo C)
  podle *§ 5a odst. 1 písm. b) a c)* modul nepodporuje.
- **Sleva na pojistném.** Zaměstnavatel může uplatnit slevu za zaměstnance
  s kratší pracovní dobou (8 až 30 hodin týdně) z okruhu
  [§ 7a odst. 1](law:cz/1992/589) — starší 55 let, rodič dítěte mladšího 10
  let, pečující osoba, student mladší 26 let, účastník rekvalifikace, osoba se
  zdravotním postižením, nebo kdokoli mladší 21 let (u něj se podmínka
  kratší pracovní doby neuplatní) — pokud měsíční vyměřovací základ
  nepřesáhne 1,5násobek průměrné mzdy (*§ 7a odst. 3*). Přehled pak tyto
  zaměstnance vyjmenuje.

## Nastavení {#setup}

Na společnosti:

| Údaj | Použije se jako |
|---|---|
| *Variabilní symbol ČSSZ (VS)*, **přesně 10 číslic** | `<vs>`, variabilní symbol zaměstnavatele u ČSSZ |
| *Kód OSSZ*, číslo od 100 do 999 | `<kodOSSZ>`, příslušná správa sociálního zabezpečení; výchozí hodnota je 100 |
| *IČO*, není-li vyplněno, pak *DIČ* | `<IC>` |
| obec a PSČ (ulice nepovinná) | adresa zaměstnavatele; číslo popisné je číslo na konci ulice, druhý řádek ulice se použije, jen obsahuje-li pouze číslo |

Pole *Variabilní symbol ČSSZ (VS)* a *Kód OSSZ* jsou na záložce **Mzdové
výkazy** formuláře společnosti (viz
[základ mzdových hlášení](module:l10n_cssk_payroll_declaration_base#company)).
Sdílejí je i moduly ELDP a ONZ. Protože kód OSSZ má
výchozí hodnotu, zapomenutý kód se neohlásí jako chyba — zkontrolujte jej.

Pro přílohu se slevou nastavte u zaměstnance v mzdovém modulu *Kategorie
slevy na pojistném*, pracovní dobu s kratším týdenním úvazkem a datum
narození.

## Sestavení přehledu {#usage}

*Mzdová hlášení → CZ PVPOJ (sociální)*, pak *Nový*. Nabídka *Mzdová
hlášení* je samostatná aplikace v hlavní nabídce.

1. Zvolte **Rok** a **Měsíc**. Obdobím je vždy celý kalendářní měsíc.
2. Klikněte na **Vygenerovat**. Modul vybere všechny potvrzené výplatní
   pásky společnosti, jejichž období v měsíci končí (koncepty a zrušené se
   nezapočítají; viz [základ mzdových hlášení](module:l10n_cssk_payroll_declaration_base#payslips)), založí
   řádek za každého zaměstnance, sestaví XML, ověří ho proti `PVPOJ25.xsd`
   a přiloží.
3. Podejte XML přes ePortál ČSSZ a klikněte na **Označit jako odeslané**.
   Podaná kopie se uchová. **Vrátit do konceptu** přehled znovu otevře;
   odeslaný přehled nelze smazat.

Generování se zastaví, pokud VS nemá 10 číslic, kód OSSZ neleží mezi 100
a 999, společnost nemá obec nebo PSČ, nebo za měsíc neexistuje žádná
výplatní páska. Zastaví se také, s odkazem na JMHZ, za **duben 2026
a pozdější** měsíce a za **leden až březen 2026**, má-li společnost
zaměstnance, jehož smlouva trvá 1. dubna 2026 — tyto měsíce podává jen
zaměstnavatel, který jím k tomu dni už nebyl. Měsíc před rokem 2025 modul
odmítne také: dodává se jen struktura 2025.

## Co přehled obsahuje {#output}

| Položka | Zdroj |
|---|---|
| vyměřovací základ zaměstnavatele v pásmu A (`zakladZamestnavateleA`) | úhrn měsíčních vyměřovacích základů zaměstnanců, každý zaokrouhlený na celé koruny **nahoru** (*§ 5d*). Základ zaměstnance se bere z jeho řádku *Sociální pojištění (zaměstnavatel)* (`SOCIALER`) — hrubá mzda omezená maximálním vyměřovacím základem; zaměstnanec bez tohoto řádku (měsíc, kdy není pojištěn) nepřispívá ničím |
| pojistné zaměstnavatele v pásmu A (`pojistneZamestnavateleA`) a celkem | 24,8 % z tohoto úhrnu, zaokrouhleno **nahoru** jednou, za celou společnost (*§ 7 odst. 1 písm. a) a odst. 3*) |
| pojistné zaměstnanců (`pojistneZamestnance`) | součet řádků *Sociální pojištění celkem (zaměstnanec)* (`SOCIALEETOT`), zaokrouhlených **nahoru** za každého zaměstnance |
| pojistné celkem (`pojistneCelkem`) | pojistné zaměstnavatele + zaměstnanců |
| sleva zaměstnavatele (`slevaZamestnavatele`) | počet zaměstnanců se slevou a úhrn jejich vyměřovacích základů; sleva sama je 5 % z tohoto úhrnu, zaokrouhleno **nahoru** (*§ 7b odst. 1*) |
| pojistné k úhradě (`pojistneUhrada`) | pojistné celkem snížené o slevu |
| příloha se zaměstnanci (`slevaZamestnanci`) | za každého zaměstnance se slevou: jméno, datum narození, vyměřovací základ (ne hrubá mzda), písmeno důvodu (a–g) podle kategorie slevy a týdenní rozsah pracovní doby z jeho pracovního kalendáře |
| typ přehledu | vždy *N* (řádný) |
| datum vyplnění | den, kdy kliknete na *Vygenerovat* |

Pokud žádná výplatní páska měsíce slevu nemá, blok slevy ani příloha se
neuvádějí.

## Omezení {#limitations}

- **Ne za období od ledna 2026**, s výjimkou případu popsaného v oddílu
  [Právní rámec](#legal); tyto údaje patří do JMHZ. Zda společnost
  k 1. dubnu 2026 „již není zaměstnavatelem“, se posuzuje podle dat smluv
  jejích zaměstnanců.
- **Počítá se ze základů, ne z pojistného na páskách.** Pojistné
  zaměstnavatele i sleva se počítají z vyměřovacích základů zaměstnanců,
  a mohou se proto o korunu lišit od součtu řádků pojistného na výplatních
  páskách. Před podáním porovnejte součty s rekapitulací mezd.
- **Jen pásmo A.** Zaměstnanci v rizikovém zaměstnání a záchranáři či hasiči
  (pásma B a C) se vykazují v pásmu A se sazbou 24,8 %.
- **Jen řádný přehled.** Typ je vždy *N*; opravný přehled je třeba podat
  přes portál.
- **Důvod slevy.** Zaměstnanec, jehož kategorii slevy nelze přečíst, se
  vykáže s důvodem *g* (mladší 21 let). Přílohu zkontrolujte.
- **Rozdělení jména.** V příloze je poslední slovo jména zaměstnance
  příjmením a vše před ním jménem (jmény), nemá-li zaměstnanec samostatná
  pole jména a příjmení (OCA `hr_employee_firstname`).
- Ověření proti schématu kontroluje tvar souboru, ne částky. Žádný přehled
  z tohoto modulu dosud nebyl potvrzen ostrým podáním na ČSSZ; první
  zkontrolujte ručně.
