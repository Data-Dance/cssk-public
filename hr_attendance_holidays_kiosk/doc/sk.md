---
title: Kiosk dochádzky: dôvod odchodu (CZ/SK)
summary: Kiosk dochádzky sa opýta, prečo zamestnanec odchádza, a z odpovede vytvorí návrh neprítomnosti na schválenie personalistom.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Kiosk dochádzky v Odoo zamestnancov len prihlasuje a odhlasuje.
Na slovenských a českých pracoviskách zamestnanec, ktorý počas dňa odchádza,
zvyčajne povie prečo: návšteva lekára, sprevádzanie člena rodiny, vybavovanie,
návšteva úradu. Tento modul sa na to opýta priamo na kiosku. Pri
**odchode** kiosk ukáže tlačidlo **Koniec práce** a po jednom tlačidle pre
každý dôvod. Koniec práce je bežný odchod. Dôvod zaznamená odchod, uloží dôvod
do dochádzky a vytvorí **návrh neprítomnosti** (*Na schválenie*) od času
odchodu do konca pracovného dňa, ktorý schváli personalista.

Závisí len od aplikácií Odoo *Dochádzky* a *Voľné dni* a funguje
s ktorýmkoľvek mzdovým jadrom aj bez miezd.

## Právny rámec {#legal}

Obvyklé dôvody sú osobné prekážky v práci podľa zákonníkov práce:

- **Slovensko.** Vyšetrenie alebo ošetrenie v zdravotníckom zariadení
  a sprevádzanie člena rodiny sú dôležité osobné prekážky v práci podľa
  [§ 141 ods. 2 písm. a) a b) Zákonníka práce](law:sk/2001/311#paragraf-141.odsek-2);
  pracovné voľno s náhradou mzdy na vlastné vyšetrenie patrí najviac sedem dní
  v kalendárnom roku.
- **Česko.** Vyšetrenie alebo ošetrenie u lekára a sprevádzanie člena rodiny
  sú prekážky na strane zamestnanca podľa
  [§ 199 zákoníka práce](law:cz/2006/262); rozsah a náhradu mzdy upravuje
  nariadenie vlády č. 590/2006 Sb. (príloha, body 1 a 8).

Modul zaznamená čas neprítomnosti a posúdenie nechá na personalistovi: či je
neprítomnosť ospravedlnená a či je platená, sa rozhodne pri schválení návrhu
a podľa typu neprítomnosti, ktorý nesie.

## Nastavenie {#setup}

Modul nevytvára vlastné typy voľných dní: typy a to, čo ktorý platí, patria
národným mzdovým modulom alebo vám. Slovenské mzdové moduly dodávajú typy
*Platená prekážka — vyšetrenie u lekára* a *Platená prekážka — sprevádzanie
rodinného príslušníka*, každý so ročným limitom siedmich dní; české mzdové
moduly typ *Placená překážka - lékař / doprovod*. Typ ponúknete na kiosku zaškrtnutím **Zobraziť
v kiosku dochádzky** (*Voľné dni › Konfigurácia › Typy voľných dní*).
Označené typy sú v **Voľné dni › Konfigurácia › Dôvody pre kiosk**, kde ich
presuniete do poradia, každému dáte farbu tlačidla a pridáte nové.
Pre dôvod na kiosku odporúčame:

- **trvanie** v hodinách, lebo odchod je časť dňa;
- **vyžaduje nárok** vypnuté: so zapnutým nevznikne zamestnancovi bez nároku
  návrh neprítomnosti (dôvod sa do dochádzky uloží aj tak) a formulár na to
  upozorní;
- **schvaľovanie** zapnuté, aby návrh zostal *Na schválenie*. Bez schvaľovania
  sa neprítomnosť hneď potvrdí.

Samotný kiosk sa nastavuje ako obvykle v *Dochádzky › Konfigurácia ›
Nastavenia*. Kým nie je označený žiadny dôvod, kiosk sa správa presne ako
bez modulu.

## Na kiosku {#usage}

1. Zamestnanec priloží kartu alebo vyberie svoje meno a zadá PIN.
2. Ak sa práve odhlasuje, zobrazí sa obrazovka s dôvodmi.
3. **Koniec práce** ho odhlási bežne; dôvod ho odhlási a vytvorí návrh
   neprítomnosti.

**Návrat v ten istý deň.** Keď sa zamestnanec v ten istý deň znova prihlási,
návrh sa skráti tak, aby končil návratom a pokrýval len čas mimo práce. Každý
odchod má vlastný návrh. Neprítomnosť, ktorú personalista už schválil, sa
nikdy nemení.

**Po automatickom odhlásení.** Ak zabudnutú dochádzku uzavrelo
*Automatický odchod* Odoo, pri ďalšom priložení karty sa kiosk opýta na
dôvod skoršieho odchodu a ukáže, kedy k automatickému odhláseniu došlo. Dôvod
označí tú dochádzku a vytvorí jej návrh; predvolené tlačidlo zamestnanca len
prihlási. Skutočný čas odchodu tu nie je známy, takže hodiny opraví
personalista pri schválení.

Návrhy nájde personalista medzi bežnými žiadosťami o neprítomnosť
(*Voľné dni › Manažment*). Dôvod je uvedený pri každej dochádzke a dá sa podľa
neho zoskupovať (*Dôvod odchodu*).

## Obmedzenia {#limits}

- Skrátenie návrhu pri návrate funguje len pri prihlásení na kiosku, nie
  z backendu.
- Odchod celý mimo pracovného času dostane hodinový návrh, ktorý nezapočíta
  žiadne pracovné hodiny; personalista ho upraví.
- So zapnutou *Správou absencií* znižuje očakávané hodiny len schválená
  neprítomnosť, preto schvaľujte návrhy včas, inak sa odchody dovtedy javia
  ako manko.
- V databáze s viacerými spoločnosťami patrí návrh spoločnosti kiosku;
  schvaľovateľ ho uvidí, len keď má túto spoločnosť aktívnu.
