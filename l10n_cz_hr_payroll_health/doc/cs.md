---
title: CZ Hlášení zdravotním pojišťovnám (PPPZ, HOZ)
summary: Dvě hlášení zaměstnavatele zdravotním pojišťovnám — měsíční přehled o platbě pojistného (PPPZ) sečtený z výplatních pásek a hromadné oznámení zaměstnavatele (HOZ) o nástupech a odchodech zaměstnanců — jako XML za každou pojišťovnu.
verified: 19.0.1.1.1
---

## K čemu slouží {#purpose}

Český zaměstnavatel hlásí **každé zdravotní pojišťovně**, u níž jsou
pojištěni jeho zaměstnanci:

- **PPPZ** — *přehled o platbě pojistného zaměstnavatele*, každý měsíc:
  kolik jeho zaměstnanců pojišťovna pojišťuje, úhrn jejich vyměřovacích
  základů a celkové pojistné;
- **HOZ** — *hromadné oznámení zaměstnavatele*: kteří zaměstnanci
  nastoupili nebo odešli.

Modul sestaví obě hlášení jako XML ve společné struktuře, kterou pojišťovny
zveřejňují (`PrehledPlatbyZamestnavatele` a `hromadneOznameniZamestnavatele`,
verze 8 z roku 2025, s pevnou hlavičkou *2026+*), ověřené proti dodaným
schématům `PPPZ_2025_v8.xsd` a `HOZ_2025_v8.xsd`. Jedno hlášení patří jedné
pojišťovně; za každou pojišťovnu se podává zvlášť. PPPZ čte výplatní pásky
přes
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
takže funguje s oběma jádry českých mezd — viz
[příručku českých mezd](module:l10n_cz_hr_payroll_base#declarations).

Na rozdíl od hlášení ČSSZ tato dvě hlášení v roce 2026 jednotné měsíční
hlášení zaměstnavatele (JMHZ) **nenahradilo**; podávají se pojišťovnám
i nadále.

## Právní rámec {#legal}

- **Pojistné.** Pojistné na zdravotní pojištění činí 13,5 % z vyměřovacího
  základu a zaokrouhluje se na celé koruny nahoru
  ([§ 2 zákona o pojistném na veřejné zdravotní pojištění](law:cz/1992/592));
  zaměstnanec hradí jednu třetinu a zaměstnavatel dvě třetiny
  ([§ 9 odst. 2 zákona o veřejném zdravotním pojištění](law:cz/1997/48);
  v mzdovém modulu 4,5 % a 9 %). Pojistné za měsíc je splatné od 1. do 20. dne
  následujícího měsíce (§ 5 odst. 2 zákona o pojistném).
- **PPPZ.** Nejpozději v den splatnosti pojistného předá zaměstnavatel každé
  pojišťovně, u níž jsou pojištěni jeho zaměstnanci, přehled o platbách
  pojistného s úhrnem jejich vyměřovacích základů, celkovou výší pojistného
  a počtem zaměstnanců ([§ 25 odst. 3](law:cz/1992/592)). Nové skutečnosti,
  které mění údaje podaného přehledu, ohlásí do 8 dnů opravným přehledem
  (§ 25 odst. 4). Obojí lze podat jen elektronicky ve formátu, který stanoví
  pojišťovna (§ 25 odst. 7).
- **HOZ.** Zaměstnavatel oznámí pojišťovně nástup zaměstnance do zaměstnání
  a jeho ukončení do 8 dnů; u zaměstnance činného jen na základě dohody
  o provedení práce nebo dohody o pracovní činnosti do 20. dne měsíce
  následujícího po měsíci, v němž se stal nebo přestal být plátcem pojistného
  ([§ 10 odst. 1 písm. a) zákona o veřejném zdravotním pojištění](law:cz/1997/48)).
  Oznámení obsahuje jméno, příjmení, trvalý pobyt a rodné číslo (§ 10
  odst. 1 poslední věta) a podává se jen elektronicky (§ 10c).

## Nastavení {#setup}

Na formuláři společnosti, karta *Mzdové výkazy*, skupina *Zdravotní
pojištění (PPPZ / HOZ)*, a v adrese společnosti:

| Údaj | Použije se jako |
|---|---|
| *Výchozí zdravotní pojišťovna* | pojišťovna každého zaměstnance, který žádnou nastavenou nemá; předvyplní se v nových hlášeních. Výchozí hodnota *111 — VZP*. |
| *Číslo plátce zdravotního pojištění*, 10 číslic | `identifikacniCisloPlatce`, číslo zaměstnavatele u pojišťovny. Není-li vyplněno, použije se IČO doplněné o `00` (první mzdová účtárna). |
| *IČO* | náhradní zdroj čísla plátce |
| ulice, obec, PSČ, telefon | adresa zaměstnavatele (obec a PSČ povinné). Číslo domu je číslo na konci ulice; druhý řádek ulice se použije, jen obsahuje-li pouze číslo. |

U zaměstnance: *Zdravotní pojišťovna* (jedna z 111, 201, 205, 207, 209, 211,
213), na formuláři zaměstnance vedle pole *Identifikační č.*, rodné číslo
v poli *Identifikační č.* (pro HOZ), soukromá adresa a data smlouvy. Dokud
není pojišťovna zaměstnance vyplněna, vykazuje se zaměstnanec výchozí
pojišťovně společnosti.

## Měsíční přehled (PPPZ) {#pppz}

*Mzdová hlášení → CZ PPPZ (zdravotní)*, pak *Nový*.

1. Zvolte **Zdravotní pojišťovnu**, **Rok** a **Měsíc**.
2. *Typ opravy* (Correction Type) ponechte na *Řádný*, nebo pro opravný
   přehled zvolte *Opravný*. Opravný přehled lze vygenerovat jen tehdy,
   existuje-li přehled téže společnosti za stejný rok a měsíc odeslaný téže
   pojišťovně.
3. Klikněte na **Vygenerovat**. Modul vezme potvrzené výplatní pásky měsíce
   (ty, jejichž období v měsíci končí) zaměstnanců, kteří k dané pojišťovně
   patří, ověří XML a přiloží ho.
4. Nahrajte XML na portál pojišťovny a klikněte na **Označit jako
   odeslané**.

| Položka | Zdroj |
|---|---|
| počet zaměstnanců (`pocetZamestnancu`) | zaměstnanci dané pojišťovny s nenulovým pojistným v měsíci |
| pojistné celkem (`soucetPojistneho`) | součet řádků zdravotního pojištění zaměstnance a zaměstnavatele (`HEALTHEE`, `HEALTHER`), zaokrouhlený jednou |
| úhrn vyměřovacích základů (`soucetZakladuPojistneho`) | **dopočtený**: pojistné děleno 0,135. Tím se promítne i minimální vyměřovací základ, protože mzdy rozdíl doplácejí na vrub zaměstnance. |
| typ přehledu (`typPrehledu`) | *radny* nebo *opravny* podle typu opravy |

Generování se zastaví, chybí-li pojišťovna, nemá-li společnost číslo plátce
(ani IČO), obec nebo PSČ, nejsou-li výplatní pásky, nebo nemá-li žádná z nich
pojistné pro danou pojišťovnu.

## Nástupy a odchody (HOZ) {#hoz}

*Mzdová hlášení → CZ HOZ (zdravotní oznámení)*, pak *Nový*.

1. Zvolte **Zdravotní pojišťovnu** a **Typ události** — *Přihlášení (P)*
   nebo *Odhlášení (O)*. Platí pro všechny zaměstnance v oznámení.
2. Případně vyplňte **Datum události**; jinak se použije počáteční
   (přihlášení) nebo koncové (odhlášení) datum smlouvy každého zaměstnance.
3. Přidejte **Zaměstnance** a klikněte na **Vygenerovat**.

Každý zaměstnanec tvoří jednu `zmenaZamestance` s kódem *P* nebo *O*,
datem, rodným číslem jako číslem pojištěnce, jménem (poslední slovo je
příjmení, zbytek jméno) a — je-li vyplněna — soukromou ulicí, obcí
a pětimístným PSČ. Generování se zastaví u zaměstnance bez rodného čísla
o 9 nebo 10 číslicích nebo bez data, které událost potřebuje.

## Omezení {#limitations}

- **Zaokrouhlení.** PPPZ zaokrouhluje jednou celkovou částku společnosti,
  zákon zaokrouhluje nahoru pojistné každého zaměstnance. Vyměřovací základ
  se dopočítává zpět z pojistného a může se od úhrnu základů zaměstnanců
  lišit o několik korun. Porovnejte s rekapitulací mezd.
- **Dopočtený základ ve zvláštních případech.** U zaměstnance, za kterého
  platí pojistné i stát, nebo který je z minimálního vyměřovacího základu
  vyňat, nemusí pojistné ÷ 13,5 % odpovídat vyměřovacímu základu. Tyto
  zaměstnance zkontrolujte.
- Pole *Reference opravy* (Correction Reference) se do XML nezapisuje.
- **Kódy HOZ.** Jen *P* a *O*. Změnu pojišťovny, státního pojištěnce, první
  přihlášení cizinců a opravy modul nezná a zaměstnance bez českého rodného
  čísla oznámit nelze.
- **Data v HOZ** se berou ze smlouvy platné ke dnešku.
- **Pojišťovny.** Dodává se sedm kódů pojišťoven; další kód vyžaduje změnu
  kódu modulu.
- Verze tiskopisu se předvyplní podle dnešního data a dodává se jen verze 8.
- Ověření proti schématu kontroluje tvar souboru, ne částky. Žádné hlášení
  z tohoto modulu dosud nebylo potvrzeno ostrým podáním.
