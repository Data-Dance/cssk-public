---
title: SK vozidlá a PHL — paušály pre DPH a daň z príjmov
summary: 50 % odpočet DPH pri osobných vozidlách používaných aj na súkromné účely (§ 85n) cez sadzby dane a 80 % paušál na PHL pre daň z príjmov cez rozúčtovanie prijatej faktúry — dva nezávislé režimy.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Osobné vozidlo používané na podnikanie aj na súkromné účely je obmedzené
dvakrát a od 1. 1. 2026 sú obe obmedzenia na sebe nezávislé:

| Režim | Predpis | Podiel | Ako to rieši modul |
|---|---|---|---|
| Odpočet DPH | § 85n zákona o DPH | **50 %** DPH z vozidla a všetkého, čo sa preň obstaráva | dve sadzby dane na vstupe, ktoré odpočítajú len polovicu DPH — pozri [DPH](#vat) |
| Daňový výdavok na PHL | § 19 ods. 2 písm. l) bod 3 zákona o dani z príjmov | paušál do **80 %** nákupu PHL | sprievodca na prijatej faktúre, ktorý zvyšok presunie na účet daňovo neuznaných nákladov — pozri [Rozúčtovanie PHL](#fuel) |

Každú polovicu možno použiť bez druhej: sadzby DPH na faktúre za opravu,
rozúčtovanie PHL pri spoločnosti, ktorá nie je platiteľom DPH, obe na
faktúre za PHL platiteľa.

## Právny rámec {#legal}

**DPH.** [§ 85n zákona o DPH](law:sk/2004/222#paragraf-85n) sa uplatní od
1. 1. 2026 do 30. 6. 2028 na motorové vozidlá kategórie **M1, L1e a L3e**
(osobné motorové vozidlo):

- platiteľ, ktorý také vozidlo nadobudne ako dlhodobý majetok, odpočíta daň
  z neho v rozsahu **50 %**
  ([ods. 1](law:sk/2004/222#paragraf-85n.odsek-1)); rovnako daň z nájmu
  iného ako krátkodobého
  ([ods. 2](law:sk/2004/222#paragraf-85n.odsek-2)) a daň z tovarov a
  služieb prijatých v súvislosti s vozidlom používaným na podnikanie aj na
  iný účel — PHL, opravy, diaľničné známky a pod.
  ([ods. 3](law:sk/2004/222#paragraf-85n.odsek-3));
- obmedzenie sa neuplatní na vozidlo používané výlučne na krátkodobý alebo
  iný ako krátkodobý nájom, prepravu osôb vrátane taxislužby, prevádzkovanie
  autoškoly, ani na predvádzacie, testovacie alebo náhradné vozidlo
  ([ods. 4](law:sk/2004/222#paragraf-85n.odsek-4)), ani na vozidlo
  používané výlučne na podnikanie, ak platiteľ vedie podrobné **záznamy v
  elektronickej podobe** o každej jazde
  ([ods. 5](law:sk/2004/222#paragraf-85n.odsek-5) a
  [ods. 6](law:sk/2004/222#paragraf-85n.odsek-6));
- použitie podľa ods. 4 alebo 5 treba **oznámiť** daňovému úradu na
  tlačive finančného riaditeľstva v lehote na podanie priznania za obdobie,
  v ktorom sa odpočet prvýkrát uplatnil
  ([ods. 9](law:sk/2004/222#paragraf-85n.odsek-9)).

Do 31. 12. 2025 záverečná časť
[§ 49 ods. 5](law:sk/2004/222#paragraf-49.odsek-5) umožňovala platiteľovi,
ktorý uplatňoval paušálne výdavky na PHL a nemohol preukázať rozsah
použitia na podnikanie, odpočítať daň z PHL do výšky paušálu. Od 1. 1. 2026
táto časť vypadla; odpočet DPH sa už paušálom dane z príjmov neriadi.

**Daň z príjmov.** Spotrebované PHL sú daňovým výdavkom okrem iného **vo
forme paušálnych výdavkov do výšky 80 %** z celkového preukázateľného
nákupu PHL za zdaňovacie obdobie, pri primeranom počte najazdených
kilometrov podľa stavu tachometra na začiatku a na konci obdobia, pre každé
motorové vozidlo samostatne
([§ 19 ods. 2 písm. l) bod 3](law:sk/2003/595#paragraf-19.odsek-2.pismeno-l.bod-3)).
Je to jeden zo štyroch spôsobov, ktoré ustanovenie pripúšťa; voľba je na
daňovníkovi.

**Neodpočítaná DPH.** Zákon o dani z príjmov vo všeobecnosti uvádza DPH, na
ktorej odpočítanie platiteľ nemá nárok, medzi daňovými výdavkami
([§ 19 ods. 3 písm. k) bod 2](law:sk/2003/595#paragraf-19.odsek-3.pismeno-k.bod-2))
a pri hmotnom majetku ako súčasť vstupnej ceny
([§ 25 ods. 5 písm. b)](law:sk/2003/595#paragraf-25.odsek-5.pismeno-b)).
Pre DPH, ktorú neodpočíta § 85n, však od 1. 1. 2026 platí prechodné
ustanovenie [§ 52zzzk](law:sk/2003/595#paragraf-52zzzk): *„Za daňový
výdavok podľa § 2 písm. i) a § 19 sa nepovažuje daň z pridanej hodnoty podľa
osobitného predpisu, ak na jej odpočítanie nemá platiteľ dane z pridanej
hodnoty nárok, pričom ak ide o daň z pridanej hodnoty vzťahujúcu sa na hmotný
majetok …, táto nie je súčasťou vstupnej ceny“*, kde osobitným predpisom je
§ 85n zákona o DPH. Neodpočítaná polovica preto **nie je daňovým výdavkom** a
pri kúpenom vozidle **nie je súčasťou vstupnej ceny** na daňové odpisovanie.
Modul ju zaúčtuje na ten istý účet ako daňovo neuznanú časť PHL (pozri
[DPH](#vat)), odkiaľ sa v daňovom priznaní pripočíta.

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Vozidlá a PHL**,
nastavenie **Paušály**, zobrazené len pri spoločnostiach so slovenskou
osnovou. Podiel podľa § 85n medzi nimi nie je: zákon ho stanovuje na 50 % a
je zabudovaný v oboch sadzbách dane pre vozidlá.

| Nastavenie | Predvolené | Účinok |
|---|---|---|
| Daňový podiel PHL (%) | 80 | Podiel, ktorý rozúčtovanie PHL ponechá ako daňový výdavok; ponúkne sa v sprievodcovi. |
| Daňovo neuznané náklady na vozidlo | 548000 *Ostatné náklady na hospodársku činnosť* | Účet, na ktorý rozúčtovanie PHL presunie zvyšok; ponúkne sa v sprievodcovi. |

Obe sadzby, **23 % vozidlo (50 % odpočet)** a **19 % vozidlo (50 %
odpočet)**, nájdete v *Účtovníctvo → Konfigurácia → Dane*. Vytvoria sa pri
inštalácii modulu v každej spoločnosti, ktorá už slovenskú osnovu má, a pri
neskoršom načítaní slovenskej osnovy do spoločnosti. Sadzbu, ktorú
spoločnosť už má, inštalácia nemení. Ak v osnove spoločnosti chýba účet alebo
skupina daní, ktoré sadzby potrebujú (343120, 343110, 548000, skupina DPH 23 % alebo
19 %), inštalácia spoločnosť preskočí a zapíše upozornenie do logu; sadzby
jej vytvorte ručne podľa bežných sadzieb na vstupe s rozdelením dane
opísaným nižšie.

## DPH: sadzby pre vozidlá {#vat}

Na faktúre za niečo, na čo sa vzťahuje § 85n — kúpu alebo dlhodobý nájom
vozidla, PHL, opravu, diaľničnú známku — zvoľte na riadku namiesto bežnej
sadzby **23 % vozidlo (50 % odpočet)** (prípadne 19 %). Dodávateľ účtuje a
dostane celú DPH; sadzba ju rozdelí:

| Časť DPH | Účet | Daňová mriežka |
|---|---|---|
| 50 % — odpočítaná | 343120 (23 %), 343110 (19 %) | ten istý riadok odpočtu v daňovom priznaní ako bežná sadzba na vstupe |
| 50 % — neodpočítaná | 548000 | žiadna: do priznania sa nedostane |

Príklad: PHL za 100,00 € plus 23 % DPH. Faktúra je na 123,00 €; 11,50 € DPH
sa odpočíta na 343120, 11,50 € ide na 548000.

Rozdelenie DPH priamo v sadzbe dane zaručuje správne priznanie: daňovú
mriežku nesie len odpočítateľná polovica. Keby sa polovica plne odpočítanej
DPH presunula do nákladov dodatočným zápisom, priznanie by stále vykázalo
odpočet celej sumy.

Pre vozidlá, na ktoré sa § 85n nevzťahuje — iné kategórie, výnimky podľa
ods. 4 alebo vozidlo používané výlučne na podnikanie so záznamami podľa
ods. 6 — používajte bežné sadzby.

## Rozúčtovanie PHL pre daň z príjmov {#fuel}

Na prijatej faktúre alebo dobropise **v stave návrh** kliknite na
**Rozúčtovanie PHL**:

1. *Daňový podiel (%)*: ponúkne sa z nastavení (80).
2. *Účet neuznanej časti*: ponúkne sa z nastavení (548000).
3. *Riadky PHL*: vyberte riadky faktúry, ktoré sú PHL.
4. Kliknite na **Rozúčtovať**.

Každý vybraný riadok si ponechá daňový podiel zo svojej sumy;
zvyšok pribudne ako nový riadok na účte neuznanej časti s rovnakými daňami.
Celková suma faktúry, DPH ani záväzok sa nezmenia — preúčtuje sa len
náklad. Rozúčtovanie sa zapíše do chatu dokladu.

Pokračovanie príkladu: riadok PHL 100,00 € sa zmení na 80,00 € na účte
spotreby PHL a 20,00 € na 548000, oba so sadzbou pre vozidlo.

Riadok, ktorý už bol rozúčtovaný, nemožno rozúčtovať znova. Rozúčtovanie
riadok prepíše na množstvo 1 so zostávajúcou sumou (prípadná zľava je už
započítaná a vymaže sa). Rozdelí sa suma tak, ako bola zadaná: pri dani
zahrnutej v cene sa delí cena s DPH, takže celková suma faktúry sa v žiadnom
prípade nezmení.

## V daňových priznaniach {#reporting}

- Priznanie k DPH zahrnie cez daňovú mriežku len odpočítanú polovicu; nič
  ďalšie netreba robiť.
- Sumy na účte neuznanej časti sa do daňového priznania k dani z príjmov
  právnickej osoby **neprenášajú automaticky**. Zadajte ich medzi
  pripočítateľné položky sami — pozri
  [module:l10n_sk_dppo](module:l10n_sk_dppo#usage). Neodpočítaná DPH podľa
  § 85n aj daňovo neuznaná časť PHL sú pripočítateľnými položkami (pozri
  [Právny rámec](#legal)), ak sa na tento účet neúčtuje nič iné.

## Obmedzenia {#limitations}

- Nič nie je ohraničené dátumom. Režim 50 % platí od 1. 1. 2026 do
  30. 6. 2028; na faktúrach mimo tohto obdobia zvoľte sadzbu sami.
- Modul vaše vozidlá nepozná: kategórie M1/L1e/L3e, výnimky ani výlučné
  použitie na podnikanie nie sú modelované, nevedie knihu jázd ani
  elektronické záznamy podľa § 85n ods. 6 a nevytvorí oznámenie podľa
  ods. 9.
- Neodpočítaná DPH ide vždy na 548000 (účet je v sadzbe dane), aj keď
  zmeníte *Daňovo neuznané náklady na vozidlo*. Pri kúpe vozidla skončí v
  nákladoch, nie v obstarávacej cene majetku — pre daň z príjmov správne
  (§ 52zzzk), či ju má zahrnúť do obstarávacej ceny účtovníctvo, posúdi váš
  účtovník.
- Nový riadok rozúčtovania nemá produkt a pôvodný riadok stratí množstvo
  (litre).
- Či možno paušál 80 % uplatniť — primeraný počet kilometrov podľa
  tachometra, pre každé vozidlo samostatne — posúdi účtovník, nie modul.
