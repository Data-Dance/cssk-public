---
title: CZ status k DPH (plátce / identifikovaná osoba / neplátce)
summary: Eviduje, kdy byla česká společnost plátcem, identifikovanou osobou nebo neplátcem, a každou fakturu, přiznání k DPH i kontrolní hlášení zdaní podle statusu ke dni daného dokladu.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Česká společnost nemusí být **plátcem DPH** po celou dobu své existence.
Začíná jako **neplátce**, plátcem se stane po překročení obratu nebo
dobrovolnou registrací, mezitím může být **identifikovanou osobou** a
registrace jí může být zase zrušena. Každá změna nastává k určitému dni,
často v průběhu roku.

Bez tohoto modulu považuje česká lokalizace každou českou společnost za
plátce. S ním zaznamenáte historii statusu a každý doklad se zdaní podle
statusu ke svému dni:

- faktury neplátce nenesou DPH a netváří se jako daňový doklad; DPH na
  přijatých fakturách jde do nákladů;
- identifikovaná osoba přiznává daň z pořízení zboží z jiného členského státu
  a ze služeb od zahraničních osob bez nároku na odpočet a dál vykazuje
  služby poskytnuté do jiného členského státu;
- přiznání k DPH se podává se správným typem plátce a kontrolní hlášení
  zahrnuje jen dny, kdy byla společnost plátcem.

**Bez historie se nic nemění.** Dokud společnost nemá ani jeden řádek
statusu, nic se nechová jinak: přiznání uvádí *P*, daně, kontrolní hlášení i
faktura zůstávají, jak byly, a žádné nové daně nevzniknou.

## Právní rámec {#legal}

Odkazy jsou na [zákon o DPH (č. 235/2004 Sb.)](law:cz/2004/235).

- **Kdy se osoba stává plátcem.** § 6 odst. 1: od prvního dne kalendářního
  roku následujícího po roce, v němž obrat v tuzemsku překročil 2 000 000 Kč;
  § 6 odst. 2: dnem následujícím po dni, kdy obrat v běžném roce překročil
  2 536 500 Kč, nebo po dni překročení limitu, pokud to osoba ve včas podané
  přihlášce sdělila. § 6f: dobrovolný plátce ode dne následujícího po dni
  oznámení rozhodnutí o registraci. § 6g až § 6i: identifikovaná osoba ode
  dne prvního pořízení zboží, přijetí plnění nebo poskytnutí služby, které ji
  zakládá.
- **Zánik.** § 107b odst. 3 a 4: plátce i identifikovaná osoba, jimž byla
  registrace zrušena na žádost, jimi přestávají být dnem následujícím po dni
  oznámení rozhodnutí; § 107b odst. 5: plátce, jemuž byla registrace zrušena
  na žádost, se stává identifikovanou osobou dnem, kdy přestal být plátcem,
  pokud nesplňuje podmínky pro zrušení registrace identifikované osoby nebo
  o to v žádosti požádal.
- **Daň na výstupu.** § 108 odst. 1: daň ze zdanitelného plnění přiznává
  plátce. § 108 odst. 4 písm. g): daň je povinna přiznat i osoba, která
  vystaví doklad, na kterém daň uvede — proto modul fakturu neplátce s DPH
  odmítne zaúčtovat, a ne jen upozorní.
- **Co přiznává identifikovaná osoba.** § 108 odst. 2: daň z pořízení zboží
  z jiného členského státu; § 108 odst. 3 písm. a): daň ze služby, dodání
  zboží s instalací nebo montáží a dodání zboží soustavami nebo sítěmi od
  osoby neusazené v tuzemsku. Ostatní zboží od takové osoby (§ 108 odst. 3
  písm. b)), přenesení daňové povinnosti v tuzemsku (§ 108 odst. 4 písm. a))
  a samovyměření při dovozu (písm. c)) se týkají jen plátce; neplátce daň při
  dovozu platí celnímu úřadu (§ 108 odst. 5 písm. a)).
- **Odpočet.** § 72 odst. 1 přiznává nárok na odpočet jen plátci; podle § 72
  odst. 5 vzniká okamžikem, kdy nastaly skutečnosti zakládající povinnost daň
  přiznat.
- **Okamžik vzniku povinnosti přiznat daň.** § 20a odst. 1: ke dni
  uskutečnění zdanitelného plnění (DUZP).
- **Podání.** § 101 odst. 1: daňové přiznání podává plátce i identifikovaná
  osoba; § 101c: „*Plátce* je povinen podat kontrolní hlášení“ — neplátce ani
  identifikovaná osoba je nepodávají.
- **Doklady.** § 28 odst. 1: povinnost vystavit daňový doklad má plátce;
  § 28 odst. 3 ji rozšiřuje na každou osobu povinnou k dani u přeshraniční
  služby.

## Nastavení {#setup}

*Nastavení → Uživatelé a společnosti → Společnosti*, otevřete českou
společnost, karta **Status k DPH** (zobrazí se jen u společností se zemí
Česko).

1. Přidejte jeden řádek za každou změnu, od nejstarší. Každý řádek říká „od
   tohoto dne byla společnost …“ a platí do dne před začátkem dalšího řádku.
   Dny před prvním řádkem se považují za plátcovské, takže pokud společnost
   začínala jako neplátce, musí to říkat její první řádek (právní důvod
   *Nikdy nebyl registrován*, od prvního dne).
2. U každého řádku vyberte **Právní důvod** a zadejte **Rozhodný den** — den,
   od kterého zákon počítá (překročení obratu, oznámení rozhodnutí, nabytí
   právní moci, první pořízení…). Status a den **Platnost od** se pak navrhnou:

   | Právní důvod | Status | Platnost od |
   |---|---|---|
   | § 6 odst. 1 – obrat překročen, plátce od 1. 1. | plátce | 1. 1. následujícího roku |
   | § 6 odst. 2 – obrat překročen, plátce dnem následujícím | plátce | rozhodný den + 1 |
   | § 6f / § 94a – dobrovolná registrace (den po oznámení) | plátce | rozhodný den + 1 |
   | § 6a–6ea – jiný důvod | plátce | zadejte ručně |
   | § 6g – první pořízení zboží…, § 6h – přijetí plnění…, § 6i – poskytnutí služby… | identifikovaná osoba | rozhodný den |
   | § 6j–6l / § 97a – registrace na přihlášku (den po oznámení) | identifikovaná osoba | rozhodný den + 1 |
   | § 107b odst. 5 – po zrušení registrace plátce | identifikovaná osoba | rozhodný den |
   | Nikdy nebyl registrován | neplátce | zadejte ručně |
   | § 106 odst. 8 písm. a) – zrušení registrace z moci úřední (právní moc) | neplátce | rozhodný den |
   | § 107b odst. 3 – zrušení registrace na žádost (den po oznámení) | neplátce | rozhodný den + 1 |
   | § 106b – zánik registrace plátce | neplátce | rozhodný den |
   | § 107 odst. 3 – zrušení registrace identifikované osoby z moci úřední (právní moc) | neplátce | rozhodný den |
   | § 107b odst. 4 – zrušení registrace identifikované osoby na žádost (den po oznámení) | neplátce | rozhodný den + 1 |

   Plátcem podle § 6 se osoba stává ze zákona k uvedenému dni bez ohledu na
   datum rozhodnutí o registraci: zadejte tento den, ne den rozhodnutí. Návrh
   je jen návrh, **Platnost od** lze přepsat. Právní důvod, který k
   vybranému statusu nepatří, systém odmítne.
3. Volitelně zapište **Č. j. rozhodnutí** a poznámku.

**Status k DPH dnes** ukazuje aktuální status. Dvě pole **Text na faktuře**
obsahují větu, která se tiskne na fakturách neplátce a identifikované osoby
(výchozí „Nejsem plátce DPH.“ a „Nejsem plátce DPH (identifikovaná osoba).“;
právnická osoba může dát přednost „Nejsme plátci DPH.“; prázdné pole netiskne
nic).

Jakmile existuje řádek se statusem jiným než plátce, modul vytvoří **daně
pro neplátce** k nákupním daním společnosti (viz [Daně](#taxes)). Tlačítko
**Znovu vytvořit daně pro neplátce** doplní chybějící; spouští se také samo
při každé změně historie a před zaúčtováním.

Pozdější změna historie znovu rozhodne o již zaúčtovaných dokladech: oddíl
kontrolního hlášení se přepočítá od nejdřívějšího změněného dne a zápisy
odložení DPH se zruší nebo vytvoří (viz [Podání](#filings)). Již podaná
přiznání se nemění — jejich oprava vyžaduje dodatečné přiznání.

## Rozhodný den dokladu {#dates}

Doklad se řídí statusem ke svému **DUZP**; chybí-li, ke dni vystavení a pak
ke dni účetního případu. Obě otázky, na které status odpovídá — vzniká daň na
výstupu, lze uplatnit odpočet — váže zákon na den uskutečnění zdanitelného
plnění (§ 20a odst. 1, § 72 odst. 5); datum vystavení ani datum zaúčtování
nerozhoduje.

- **Hraniční dny.** Řádek platí od svého prvního dne včetně. Doklad s DUZP v
  první den nového statusu spadá pod nový status, doklad s DUZP o den dříve
  pod původní.
- **Opravné daňové doklady** (dobropisy) se řídí statusem faktury, kterou
  opravují, i když jsou vystaveny až po změně.
- Ke dni, kdy společnost nebyla plátcem, ukazuje doklad vedle DUZP pole
  **Status společnosti k DPH**.

## Co se stane s daněmi {#taxes}

Daně se rozpoznávají podle řádku přiznání, na který se vykazuje jejich
základ (štítky *VAT <n> Base* české účtové osnovy), takže i vlastní daně se
zpracují stejně, pokud nesou štítky osnovy.

| Daň (řádek přiznání jejího základu) | plátce | identifikovaná osoba | neplátce |
|---|---|---|---|
| Prodej: tuzemský, vývoz, ostatní zdaněný prodej | beze změny | **odstraní se** | **odstraní se** |
| Prodej: služba podle § 9 odst. 1 do jiného členského státu (ř. 21), třístranný obchod (ř. 31) | beze změny | beze změny | **odstraní se** |
| Nákup: tuzemský s odpočtem (ř. 40/41 a další odpočitatelné daně) | beze změny | **bez odpočtu**, DPH do nákladů | **bez odpočtu**, DPH do nákladů |
| Nákup: přenesení daňové povinnosti podle § 92a (ř. 10/11) | beze změny | **bez odpočtu**, DPH do nákladů | **bez odpočtu**, DPH do nákladů |
| Nákup: zboží z EU, služby z EU a ze zahraničí, ostatní samovyměření (ř. 3–6, 12, 13) | beze změny | **samovyměření bez odpočtu** | **odstraní se** |
| Nákup: dovoz (ř. 7/8, 32, 42) | beze změny | **odstraní se** | **odstraní se** |
| Nákup: nový dopravní prostředek (ř. 9) | beze změny | beze změny | beze změny |

Varianty jsou kopie původní daně, pojmenované podle ní s příponou *(no
deduction)* nebo *(identified person)* a s ní provázané (pole **Daň plátce**
na formuláři daně):

- **Bez odpočtu** — jediný řádek daně bez účtu a bez štítků. Odoo jej zaúčtuje
  na nákladový účet řádku faktury, takže DPH se stane součástí nákladu;
  na účet 343 ani do přiznání se nic nedostane.
- **Samovyměření bez odpočtu** — strana závazku a její štítky (ř. 3–6, 12,
  13) zůstávají jako u daně plátce; strana odpočtu ztratí účet a jde do
  nákladů a všechny štítky odpočtu (ř. 40–53) se odstraní. Přiznání ukáže daň
  na výstupu a žádný odpočet.

Daně se nastaví automaticky při vzniku řádku z produktu nebo účtu a znovu,
když u konceptu změníte DUZP nebo datum vystavení přes hranici statusu — v
obou směrech, takže návrat data vrátí daně plátce.

**Zaúčtování se odmítne**, pokud daně faktury neodpovídají statusu k jejímu
DUZP. Koncept s takovými řádky ukáže upozornění s tlačítkem **Použít daně
podle statusu DPH**, které je nahradí. Nákupní daň, jejíž rozdělení nemá tvar
české osnovy (jeden řádek daně +100 % a jeden −100 %), variantu pro
identifikovanou osobu nedostane; přijatou fakturu s ní nelze ke dni
identifikované osoby zaúčtovat, dokud daň nenastavíte ručně.

## Na faktuře {#invoice}

Faktura vystavená ke dni, kdy společnost nebyla plátcem:

- nenese DPH (daně byly odstraněny);
- netiskne **DUZP** — jediný údaj, který existuje jen kvůli DPH. Název
  „Faktura“ nic netvrdí a zůstává;
- pod poznámkami tiskne **Text na faktuře**.

Výjimkou je služba identifikované osoby podle § 9 odst. 1 do jiného členského
státu, kterou § 28 odst. 3 vyžaduje doložit daňovým dokladem: taková faktura
DUZP ponechá. Text pro identifikovanou osobu se tiskne i na ní.

## Podání {#filings}

- **Přiznání k DPH (DPHDP3).** Typ plátce se bere ze statusu k **poslednímu
  dni** období přiznání: *P* plátce, *I* identifikovaná osoba, *N* neplátce.
  Každý doklad v období byl zdaněn podle statusu ke svému DUZP. Mění-li se
  status v průběhu období, přiznání to při výpočtu uvede v chatteru; zda
  změna vyžaduje samostatné podání za část období, posuďte se správcem daně.
- **Kontrolní hlášení.** Zahrnou se jen doklady s datem ve dnech, kdy byla
  společnost plátcem. Období bez jediného takového dne nelze spočítat vůbec;
  hláška doporučí odpovědět na případnou výzvu správce daně „B – Nemám
  povinnost podat KH“. Období se změnou se spočítá z plátcovských dnů a
  chatter hlášení vypíše jednotlivé úseky.
- **Souhrnné hlášení.** Služby identifikované osoby podle § 9 odst. 1 si daň
  ponechávají, takže je souhrnné hlášení vykáže jako u plátce.
- **Deklarované období DPH** (pozdější období odpočtu z modulu
  [module:l10n_cssk_core](module:l10n_cssk_core)). Slouží plátci, který
  uplatňuje odpočet později, než nárok vznikl. U dokladu s datem, kdy
  společnost nebyla plátcem, se **ignoruje**: doklad se vykáže v období svého
  DUZP a jeho DPH se zápisy odložení z účtu 343 nepřesouvá. Formulář to uvede
  v modré poznámce. Pokud by změna historie měla zrušit nebo vytvořit zápisy
  odložení v uzamčeném období, doklad dostane zprávu do chatteru a zápisy
  zůstanou na vás.

## Prodejní a nákupní objednávky {#orders}

Dva propojovací moduly se nainstalují samy, je-li nainstalován Prodej nebo
Nákup:

- [module:l10n_cz_vat_status_sale](module:l10n_cz_vat_status_sale) — řádky
  prodejních objednávek;
- [module:l10n_cz_vat_status_purchase](module:l10n_cz_vat_status_purchase)
  — řádky nákupních objednávek, včetně řádků vzniklých z pravidel doplňování
  zásob a výroby na zakázku.

Navrhnou daně, které status připouští k **datu objednávky**. Objednávka nemá
DUZP, takže jde jen o návrh: faktura z ní vytvořená se rozhodne znovu podle
svého DUZP a s daněmi, které už neodpovídají, ji nelze zaúčtovat. Objednávka
potvrzená v červnu a fakturovaná v červenci přes registraci dostane daně
opravené až na faktuře.

## Omezení {#limitations}

- **Úpravy při změně statusu** se neprovádějí: odpočet daně ze zásob a
  majetku při vzniku plátcovství ani opravy a odvody při zrušení registrace.
  Zaúčtujte je ručně.
- **Obrat se nehlídá.** Status je to, co zaznamenáte.
- **Skupina** (*typ plátce S*) a **nový dopravní prostředek** (*R*, *D*) se
  nemodelují; daně ř. 9 zůstávají beze změny.
- **Daň při dovozu placená celnímu úřadu** neplátcem se neúčtuje: dovozní daně
  se z přijaté faktury odstraní a daň vyměřenou celním úřadem zaúčtujte z
  celního dokladu jako náklad.
- **Zálohové daňové doklady** z jiných modulů se neblokují; neplátce by je
  vystavovat neměl.
- **OSS a režim pro malé podniky** nejsou statusy tohoto modulu.
- **Importy** historických dokladů mohou kontrolu při zaúčtování obejít
  technickým klíčem kontextu `l10n_cz_vat_status_skip_check`; v uživatelském
  rozhraní jej nic nenastavuje.
- **Otevřené otázky** pro daňového poradce, kde modul volí výchozí řešení:
  daně ř. 12/13 považuje za daně, které přiznává identifikovaná osoba, ačkoli
  pokrývají i zboží podle § 108 odst. 3 písm. b), které přiznává jen plátce;
  pořízení zboží z jiného členského státu se řídí DUZP na faktuře, ne dnem
  podle § 25; dobropis po zrušení registrace přebírá status původní faktury;
  samovyměření plátce s pozdějším deklarovaným obdobím přesouvá závazek
  spolu s odpočtem.
