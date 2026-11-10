---
title: Kiosk docházky: důvod odchodu (CZ/SK)
summary: Kiosk docházky se zeptá, proč zaměstnanec odchází, a z odpovědi vytvoří návrh nepřítomnosti ke schválení personalistou.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Kiosk docházky v Odoo zaměstnance jen přihlašuje a odhlašuje. Na
českých a slovenských pracovištích zaměstnanec, který během dne odchází,
obvykle řekne proč: návštěva lékaře, doprovod člena rodiny, vyřizování,
návštěva úřadu. Tento modul se na to zeptá přímo na kiosku. Při **odchodu**
kiosk ukáže tlačítko **Konec práce** a po jednom tlačítku pro každý důvod.
Konec práce je běžný odchod. Důvod zaznamená odchod, uloží důvod do docházky
a vytvoří **návrh nepřítomnosti** (*Ke schválení*) od času odchodu do konce
pracovního dne, který schválí personalista.

Závisí jen na aplikacích Odoo *Docházka* a *Volno* a funguje
s kterýmkoli mzdovým jádrem i bez mezd.

## Právní rámec {#legal}

Obvyklé důvody jsou osobní překážky v práci podle zákoníků práce:

- **Česko.** Vyšetření nebo ošetření u lékaře a doprovod člena rodiny jsou
  překážky na straně zaměstnance podle
  [§ 199 zákoníku práce](law:cz/2006/262); jejich rozsah a náhradu mzdy
  stanoví nařízení vlády č. 590/2006 Sb. (příloha, body 1 a 8).
- **Slovensko.** Vyšetření nebo ošetření ve zdravotnickém zařízení a doprovod
  člena rodiny jsou důležité osobní překážky v práci podle
  [§ 141 ods. 2 písm. a) a b) Zákonníka práce](law:sk/2001/311#paragraf-141.odsek-2);
  pracovní volno s náhradou mzdy na vlastní vyšetření náleží nejvýše sedm dní
  v kalendářním roce.

Modul zaznamená dobu nepřítomnosti a posouzení nechá na personalistovi: zda je
nepřítomnost omluvená a zda je placená, se rozhodne při schválení návrhu
a podle typu nepřítomnosti, který nese.

## Nastavení {#setup}

Modul nevytváří vlastní typy volna: typy a to, co který platí, patří
národním mzdovým modulům nebo vám. České mzdové moduly dodávají typ
*Placená překážka - lékař / doprovod*; slovenské typy *Placená překážka –
lékařské vyšetření* a *Placená překážka – doprovod rodinného příslušníka*,
každý s ročním limitem sedmi dnů. Typ
nabídnete na kiosku zaškrtnutím **Zobrazit v kiosku docházky** (*Volno ›
Konfigurace › Typy volných dnů*). Označené typy jsou v **Volno › Konfigurace ›
Důvody pro kiosk**, kde je přetáhnete do pořadí, každému dáte barvu tlačítka
a přidáte nové. Pro důvod na kiosku doporučujeme:

- **trvání** v hodinách, protože odchod je část dne;
- **vyžaduje nárok** vypnuté: se zapnutým nevznikne zaměstnanci bez nároku
  návrh nepřítomnosti (důvod se do docházky uloží i tak) a formulář na to
  upozorní;
- **schvalování** zapnuté, aby návrh zůstal *Ke schválení*. Bez schvalování se
  nepřítomnost hned potvrdí.

Samotný kiosk se nastavuje jako obvykle v *Docházka › Konfigurace ›
Nastavení*. Dokud není označen žádný důvod, kiosk se chová přesně jako bez
modulu.

## Na kiosku {#usage}

1. Zaměstnanec přiloží kartu nebo vybere své jméno a zadá PIN.
2. Pokud se právě odhlašuje, zobrazí se obrazovka s důvody.
3. **Konec práce** ho odhlásí běžně; důvod ho odhlásí a vytvoří návrh
   nepřítomnosti.

**Návrat týž den.** Když se zaměstnanec týž den znovu přihlásí, návrh se
zkrátí tak, aby končil návratem a pokrýval jen dobu mimo práci. Každý odchod
má vlastní návrh. Nepřítomnost, kterou personalista už schválil, se nikdy
nemění.

**Po automatickém odhlášení.** Pokud zapomenutou docházku uzavřelo
*Automatický odchod* Odoo, při dalším přiložení karty se kiosk zeptá na
důvod dřívějšího odchodu a ukáže, kdy k automatickému odhlášení došlo. Důvod
označí tu docházku a vytvoří její návrh; výchozí tlačítko zaměstnance jen
přihlásí. Skutečný čas odchodu tu není znám, takže hodiny opraví personalista
při schválení.

Návrhy najde personalista mezi běžnými žádostmi o nepřítomnost
(*Volno › Správa*). Důvod je uveden u každé docházky a lze podle něj
seskupovat (*Důvod odchodu*).

## Omezení {#limits}

- Zkrácení návrhu při návratu funguje jen při přihlášení na kiosku, ne
  z backendu.
- Odchod celý mimo pracovní dobu dostane hodinový návrh, který nezapočítá
  žádné pracovní hodiny; personalista ho upraví.
- Se zapnutou *Správou absencí* snižuje očekávané hodiny jen schválená
  nepřítomnost, proto schvalujte návrhy včas, jinak se odchody do té doby jeví
  jako manko.
- V databázi s více společnostmi patří návrh společnosti kiosku;
  schvalovatel ho uvidí, jen když má tuto společnost aktivní.
