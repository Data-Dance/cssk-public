---
title: CZ Evidenční list důchodového pojištění (ELDP)
summary: Evidenční list důchodového pojištění za kalendářní rok — vyměřovací základ a dny pojištění každého zaměstnance sestavené z výplatních pásek roku a vyexportované do hromadného XML ve struktuře ČSSZ ELDP09.
verified: 19.0.1.0.5
---

## K čemu slouží {#purpose}

*Evidenční list důchodového pojištění* (**ELDP**) zaznamenává za každého
zaměstnance a kalendářní rok dobu důchodového pojištění a vyměřovací
základ, ze kterého bylo placeno pojistné. ČSSZ z něj určuje nárok na
důchod.

Modul sestaví hromadné ELDP (záznam `eldp09` za každého zaměstnance v obálce
`RELDP`) za celý rok z výplatních pásek tohoto roku a vyexportuje ho do XML
ověřeného proti oficiálnímu schématu `ELDP09.xsd`. Výplatní pásky čte přes
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
takže funguje s oběma jádry českých mezd — viz
[příručku českých mezd](module:l10n_cz_hr_payroll_base#declarations).

**Od roku 2026 zaměstnavatel v běžných případech ELDP nepodává.** Než modul
použijete, přečtěte si následující oddíl.

## Právní rámec {#legal}

Odkazy směřují na
[zákon o organizaci a provádění sociálního zabezpečení](law:cz/1991/582).

- **Od roku 2026 sestavuje ELDP ČSSZ.** Podle § 38 odst. 1 a 2 ve znění
  účinném od 1. ledna 2026 sděluje zaměstnavatel údaje potřebné pro
  důchodové pojištění každý měsíc prostřednictvím *jednotného měsíčního
  hlášení zaměstnavatele* (JMHZ, [zákon č. 323/2025 Sb.](law:cz/2025/323))
  a evidenční list z nich sestaví ČSSZ. Vede se od 1. ledna nebo ode dne
  vzniku účasti na pojištění do 31. prosince nebo do dne jejího skončení
  (§ 38 odst. 3).
- **Kdy zaměstnavatel ELDP podává i nadále.** Podle přechodných ustanovení
  [zákona č. 360/2025 Sb.](law:cz/2025/360) (čl. V) vede a předkládá
  zaměstnavatel ELDP postupem a ve lhůtách podle §§ 38 a 39 ve znění účinném
  do konce roku 2025
  - za **kalendářní roky před rokem 2026** (tedy ELDP za rok 2025);
  - za zaměstnance, jehož účast na důchodovém pojištění **skončila před
    1. dubnem 2026**, s údaji za rok 2026;
  - na výzvu ČSSZ, do 8 dnů od jejího obdržení.

  Pro první dva případy modul ELDP v elektronické struktuře ELDP09 vytváří;
  rok 2026 pro ostatní zaměstnance a každý rok od 2027 odmítne. ELDP
  vyžádaný ČSSZ je třeba připravit mimo modul.
- **Co se do listu zapisuje** (§ 38 odst. 4): identifikační údaje
  zaměstnavatele, jméno, poslední příjmení a rodné příjmení, datum a místo
  narození, místo trvalého pobytu a rodné číslo, druh výdělečné činnosti,
  doba účasti na pojištění, vyměřovací základ a vyloučené doby.

## Nastavení {#setup}

Na společnosti:

| Údaj | Použije se jako |
|---|---|
| *Variabilní symbol ČSSZ (VS)*, 8 až 10 číslic | `<comp vs>` |
| *Kód OSSZ*, číslo od 100 do 999 | `tco` a `dep`, příslušná správa sociálního zabezpečení; výchozí hodnota je 100 |
| *IČO* | `<comp id>` |

Pole *Variabilní symbol ČSSZ (VS)* a *Kód OSSZ* jsou na záložce **Mzdové
výkazy** formuláře společnosti (viz
[základ mzdových hlášení](module:l10n_cssk_payroll_declaration_base#company)).
Sdílejí je i moduly PVPOJ a ONZ.

U zaměstnance: **rodné číslo** v poli *Identifikační č.* (9 nebo 10 číslic),
datum narození (pole *Birthday*, v češtině nepřeložené), *Místo narození*,
soukromá adresa (ulice s číslem domu, obec, PSČ) a *Počáteční datum smlouvy*
a *Datum ukončení smlouvy* všech verzí smlouvy — počítají se i dřívější
smlouvy v roce, nejen ta současná.

## Sestavení ELDP {#usage}

*Mzdová hlášení → CZ ELDP (důchodové)*, pak *Nový*.

1. Zvolte **Rok**. Obdobím je vždy 1. leden až 31. prosinec.
2. Klikněte na **Vygenerovat**. Modul vybere všechny potvrzené výplatní
   pásky společnosti, jejichž období v daném roce končí (koncepty a zrušené
   se nezapočítají; viz [základ mzdových hlášení](module:l10n_cssk_payroll_declaration_base#payslips)),
   založí záznam za každého zaměstnance, ověří XML proti `ELDP09.xsd` a přiloží ho.
3. Podejte XML přes ePortál ČSSZ a klikněte na **Označit jako odeslané**.
   **Vrátit do konceptu** jej znovu otevře.

Za rok **před 2026** obsahuje ELDP všechny zaměstnance s výplatní páskou
v daném roce. Za rok **2026** jen zaměstnance s výplatní páskou v roce 2026,
jejichž poslední zaměstnání skončilo před 1. dubnem 2026; ostatní se vykazují v JMHZ.
Roky **2027 a pozdější** modul odmítne.

Generování se zastaví, chybí-li nebo je-li neplatný VS či kód OSSZ, nemá-li
zaměstnanec platné rodné číslo nebo datum narození, není-li v roce žádná
výplatní páska, nebo — za rok 2026 — neodešel-li před 1. dubnem 2026 žádný
zaměstnanec s výplatní páskou. Zastaví se také, má-li zaměstnanec v roce víc
než tři oddělená období zaměstnání: jedno ELDP pojme nejvýš tři (omezení
schématu ELDP09), takže ELDP tohoto zaměstnance připravte ručně.

## Co každý záznam obsahuje {#output}

| Položka | Zdroj |
|---|---|
| rodné číslo, datum a místo narození | zaměstnanec |
| příjmení (`sur`) a jméno (`fir`) | jméno zaměstnance: poslední slovo je příjmení, vše před ním jméno (jména). Má-li zaměstnanec samostatná pole jména a příjmení (OCA `hr_employee_firstname`), použijí se ta. |
| rodné příjmení | současné příjmení — viz omezení |
| adresa | soukromá adresa; číslo na konci ulice se bere jako číslo domu, pošta (`pos`) je prvních pět písmen obce |
| typ ELDP (`typ`) | *1*, pokud zaměstnání trvá i po 31. prosinci, *2*, pokud poslední období zaměstnání během roku skončilo |
| období (řádky `t1`, `fro`–`to`) | jeden řádek za každé období zaměstnání v roce (nejvýš tři), sestavené z počátečních a koncových dat všech verzí smlouvy zaměstnance, oříznutých na daný rok |
| dny pojištění (`din`) | kalendářní dny každého období v daném roce |
| vyměřovací základ (`inc`) | za každé období součet měsíčních vyměřovacích základů zaměstnance z jeho řádku *Sociální pojištění (zaměstnavatel)* (`SOCIALER`) — hrubá mzda omezená maximálním vyměřovacím základem (*§ 15a zák. 589/1992 Sb.*), za měsíc bez pojištění nic — zaokrouhlený na celé koruny **nahoru**. Páska patří do období, do kterého připadá její koncové datum |
| druh činnosti (`cod`) | vždy *1* |
| vyloučené a odečítané dny (`dex`, `dar`), měsíční značky | vždy 0 / prázdné |

## Omezení {#limitations}

- **Rodné příjmení je současné příjmení** a víceslovné příjmení se rozpozná
  jen se samostatnými poli jména a příjmení.
- **Vyloučené doby se neodečítají.** Vyměřovací základ se bere z výplatních
  pásek, jak jsou; zkontrolujte jej u zaměstnanců s neplaceným volnem,
  pracovní neschopností, mateřskou nebo rodičovskou dovolenou.
- **Nejvýš tři období zaměstnání na zaměstnance.** Zaměstnance s více
  obdobími modul odmítne; jeho ELDP připravte ručně.
- Vyloučené dny jsou vždy 0 a každý záznam má druh činnosti *1*, i pro
  dohody.
- Jen řádné podání; opravy se podávají přes portál. Dodává se jen struktura
  ELDP09.
- Ověření proti schématu kontroluje tvar souboru, ne částky. Žádné ELDP
  z tohoto modulu dosud nebylo potvrzeno ostrým podáním na ČSSZ.
