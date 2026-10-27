---
title: CZ statutární číselníky a údaje podávajícího
summary: Finanční úřady, typy daňových subjektů a údaje o podávajícím, které potřebuje každé české elektronické podání (EPO), a příznak opravy u nedobytné pohledávky na fakturách.
verified: 19.0.1.3.0
---

## K čemu slouží {#purpose}

Každé české podání přes daňový portál EPO — přiznání k DPH (DPHDP3),
kontrolní hlášení, souhrnné hlášení, přiznání k dani z příjmů právnických
osob (DPPO) — nese stejnou hlavičku: kterému finančnímu úřadu je určeno,
kdo je daňový subjekt, kdo podání podepisuje a kdo ho sestavil. Modul tyto
údaje zadává jednou pro všechny tyto formuláře:

- **české finanční úřady** a jejich kódy;
- **typy daňových subjektů** *Fyzická osoba* a *Právnická osoba*;
- **údaje o podávajícím** na společnosti: oprávněná osoba, kdo podání
  sestavil a zástupce, například daňový poradce;
- **kontrolu před exportem**, zda lze finanční úřad společnosti podat;
- **příznak opravy u nedobytné pohledávky** na fakturách a dobropisech,
  který čte přiznání k DPH i kontrolní hlášení.

Spolu s ním se nainstaluje modul `partner_nace`, ze kterého přiznání k DPH
a DPPO berou převažující činnost společnosti (kód CZ-NACE).

Samotné číselníky (*Finanční úřady*, *Typy osob / subjektů*) zavádí
[module:l10n_cssk_core](module:l10n_cssk_core); tento modul je plní českými
daty, aby se nic z nich nenačetlo do slovenské databáze.

## Právní rámec {#legal}

- **Oprava u nedobytné pohledávky.** Věřitel je oprávněn opravit základ
  daně v případě nedobytné pohledávky za podmínek
  [§ 46 a násl. zákona o DPH](law:cz/2004/235) (mimo jiné při vymáhání v
  exekučním nebo insolvenčním řízení). Dlužník, který je plátcem, je pak
  povinen snížit uplatněný odpočet daně —
  [§ 74b zákona o DPH](law:cz/2004/235). Ani jedno není běžný opravný daňový
  doklad: přiznání k DPH je vykazuje na samostatných řádcích a kontrolní
  hlášení je uvádí bez ohledu na částku, a proto to musí být na dokladu
  vyznačeno.

## Nastavení {#setup}

**Společnost.** *Nastavení → Uživatelé a společnosti → Společnosti*, otevřete
společnost:

| Pole | Co zadat |
|---|---|
| Finanční úřad (*Tax Authority*) | **Krajský** finanční úřad, kterému společnost podává, např. *Finanční úřad pro Jihomoravský kraj*. Jeho kód se podává jako `c_ufo`. |
| Finanční Úřad (CZ) | Pole samotného Odoo: **územní pracoviště**. Jeho kód se podává jako `c_pracufo`. Nepovinné. |
| Typ subjektu | *Právnická osoba* nebo *Fyzická osoba*. Určuje, zda se podává za právnickou osobu (`typ_ds` P), nebo za fyzickou osobu (F). Nevyplněné pole se bere jako právnická osoba. |
| NACE (main activity) | Na kontaktu společnosti; podává se jako kód převažující činnosti. |

Obě pole pro finanční úřad se v češtině jmenují *Finanční úřad* a snadno se
zamění: první je krajský úřad, druhé územní pracoviště. Výchozí finanční úřad
lze nastavit i v *Účetnictví → Konfigurace → Nastavení*, blok *Česká /
slovenská lokalizace*, pole *Výchozí správce daně*.

**Karta *EPO podání*** ve formuláři společnosti, jen u českých společností:

| Skupina | Pole | Kdy |
|---|---|---|
| Fyzická osoba | Titul, Jméno, Příjmení | společnost je fyzická osoba |
| Oprávněná osoba | jméno, příjmení, vztah k právnické osobě (např. *jednatel*) | společnost je právnická osoba |
| Sestavil | jméno, příjmení, telefon | kdo podání sestavil |
| Zástupce | Zástupce, Typ zástupce, Evidenční číslo zástupce, Datum narození zástupce | za společnost podává někdo jiný |

Adresa, telefon a e-mail v podání se berou z kontaktních údajů společnosti.
Ulice se rozdělí na název ulice, číslo popisné a číslo orientační (z
`Diabasová 1141/11`); ulice, která nekončí číslem, se podá celá a bez čísla
domu.

U **zástupce** vyberte kontakt a *Typ zástupce* (jakmile je zástupce
vyplněn, je povinný) z číselníku EPO — například *4b – daňový poradce nebo
advokát (fyzická osoba)* nebo *4c – právnická osoba vykonávající daňové
poradenství*. Kontakt typu společnost se podá jako právnická osoba s názvem
a IČO; osoba se podá jako fyzická osoba — jméno se rozdělí podle poslední
mezery na jméno a příjmení — a potřebuje buď *Evidenční číslo zástupce* (u
daňového poradce číslo osvědčení Komory daňových poradců), nebo datum
narození.

**Finanční úřady.** *Účetnictví → Konfigurace → CZ/SK lokalizace → Finanční
úřady* obsahuje 14 krajských finančních úřadů a Specializovaný finanční úřad
s adresami a u každého krajského úřadu jeho územní pracoviště. Kódy se
přebírají z oficiálního seznamu finančních úřadů v Odoo, takže nový úřad se
objeví, jakmile Odoo tento seznam aktualizuje. Instalace i aktualizace
modulu doplní chybějící úřady a nikdy nepřepíše ty, které jste upravili.

## Před exportem: kontrola finančního úřadu {#export-check}

Při exportu českého podání se nejprve zkontroluje finanční úřad společnosti
a export se zastaví s vysvětlením, pokud:

- společnost nemá finanční úřad vyplněný;
- finanční úřad není český;
- úřad nemá *Kód podání*;
- kód má víc než tři číslice — typicky proto, že bylo místo krajského úřadu
  vybráno územní pracoviště; hláška pak jmenuje krajský úřad, který je
  třeba vybrat.

Kontrola platí pro společnosti s daňovou zemí Česká republika a netýká se
přiznání OSS, které finanční úřad nenese.

## Oprava u nedobytné pohledávky na dokladech {#bad-debt}

Na faktuře, přijaté faktuře nebo dobropisu české společnosti, karta *Další
informace*, pole **Oprava u nedobytné pohledávky** označuje opravu daně u
nedobytné pohledávky:

| Hodnota | Použití |
|---|---|
| Oprava u nedobytné pohledávky (§ 46 / § 74b) | oprava věřitele (§ 46 a násl.) nebo dlužníka (§ 74b) |
| Oprava podle § 44 ve znění do 31. 3. 2019 | postup podle dřívějšího § 44, jen pro plnění uskutečněná do 31. 3. 2019 |

Na dokladu ponechte běžné daně; na správné řádky ho přesune právě tento
příznak. S modulem [module:l10n_cz_vat_return](module:l10n_cz_vat_return) jde
daň do ř. 33 (věřitel) nebo ř. 34 (dlužník) přiznání k DPH místo běžných
řádků a s modulem [module:l10n_cz_kh](module:l10n_cz_kh) se doklad uvede v
oddílu A.4 nebo B.2 kontrolního hlášení bez ohledu na částku.

Pole lze měnit jen u dokladu ve stavu návrh a změny se zapisují do
chatteru. Hodnotu podle dřívějšího § 44 Odoo odmítne, pokud je opravovaný
doklad (ten, který dobropis opravuje) z doby po 31. 3. 2019, a příznak
odmítne úplně u společnosti, která české DPH nepodává.

## Omezení {#limitations}

- Adresy finančních úřadů jsou jen pro pohodlí a automaticky se
  neaktualizují; pokud je tisknete, ověřte je.
- Jméno zástupce, který je fyzickou osobou, se dělí podle poslední mezery,
  takže dvojité příjmení v podání zkontrolujte.
- Číslo domu se oddělí jen z ulice, která končí číslem.
- Typ plátce v přiznání k DPH je vždy *plátce* (P), pokud jiný stav
  nezaznamená modul [module:l10n_cz_vat_status](module:l10n_cz_vat_status).
- Příznak opravy u nedobytné pohledávky nekontroluje samotné podmínky § 46
  (lhůty, řízení); jen zaznamenává, podle jakého postupu se doklad řídí.
