# Daň z motorových vozidiel — DMVv25

Účtovníctvo → Výkazy → Zákonné výkazy → Daň z motorových vozidiel.

## Rozsah

Slovenské právnické osoby, bežný kalendárny rok, EUR a vozidlá L1e–L7e, M1 alebo
N1. Výpočet používa overené celé mesiace daňovej povinnosti. Odpočet DPH,
percento výdavkov na palivo a kniha jázd sú samostatné pravidlá.
Iné kategórie, oslobodenia, kombinovaná doprava, osobitné skrátené obdobia
a opakovaný vznik/zánik pri rovnakom EČV nie sú rozsahom tejto verzie.
Nepodporované voľby ani duplicitné vozidlá sa nemajú zameniť za bežný prípad.

## Príprava

1. Doplňte DIČ a sídlo firmy. Firma nemusí byť platiteľom DPH. Ulica a číslo
   používajú spoločnú funkciu lokalizácie.
2. Overte bežné obdobie, úplnosť vozidiel, technické doklady, evidenciu v SR,
   postavenie daňovníka, prvú evidenciu a skutočný vznik/zánik povinnosti.
   Dátum faktúry sám neurčuje vznik povinnosti. Uveďte aj elektromobil s nulou.
3. Zadajte skutočne zaplatené preddavky a podklady aj pre overenú nulu.
   Platba dane nie je automaticky preddavkom. Overte ročné upravené sadzby
   všetkých vozidiel podliehajúcich dani k nasledujúcemu 1. januáru. Tlačidlo
   návrhu vychádza zo známych vozidiel a vymaže potvrdenie overenia; doplnenie
   nových vozidiel, predaj a správnu verziu sadzieb treba stále overiť.
4. Vypočítajte a skontrolujte sadzbové úseky. Export používa spoločný postup
   podaní, QWeb a pôvodnú oficiálnu XSD. Každý úsek sa zaokrúhľuje nadol
   samostatne; mesačný zlomok sa nezaokrúhľuje. Hranica malej sumy na úhradu
   nevymazáva vypočítanú daň vo formulári.
5. Stiahnite XML. Pri zmene podkladov, firmy, šablóny alebo verzie sa nepodaný
   výpočet/export stane neaktuálnym. Vráťte ho do návrhu a znova vypočítajte.

## Opravy a archív

Zaevidovanie podania vyžaduje jeho identifikátor a skutočný doklad o podaní.
Tlačidlo samo nič neodosiela. Uchová sa presné XML, výpočet aj podklady.
Podané priznanie nemožno meniť, resetovať ani vymazať; jeho stiahnutie
neprehodnocuje dnešné firemné údaje.

Pred riadnou lehotou pripravte samostatné **opravné** priznanie ako úplnú
náhradu. Po lehote použite **dodatočné** s dátumom zistenia, dôvodmi a overením
možnosti podať ho vrátane prípadných obmedzení pri daňovej kontrole.
Základom musí byť posledné uchované podanie firmy a roka. Zosúlaďte každé
pôvodné vozidlo práve raz, aj nezmenené; doplňte novo zistené vozidlá.
Odkaz na predchádzajúci riadok umožňuje jednoznačnú opravu aj pri chybnom EČV.

Pri úplnom odstránení pôvodnej chybnej povinnosti zachovajte odkaz na vozidlo,
opravte skutočné dátumy povinnosti mimo roka priznania a výslovne potvrďte
odstránenie s podkladmi. Uchová sa pôvodná daň, opravená nula a záporný rozdiel.
Vymazanie pôvodného vozidla bez zosúladenia je odmietnuté.

Dodatočné priznanie obsahuje rozdiely za vozidlá aj spolu. Zachováva pôvodné
preddavky; neskoršie platby dane sa na ne nepreznačujú. Oprava predpokladanej
dane automaticky nemení už platný rozpis preddavkov. Žiadosť o vrátenie
vyžaduje kladný preplatok, overenie a vlastný firemný IBAN. Nie je to prijatá
vratka. Pri príprave opravy sa žiadosť nekopíruje, aby nevznikla duplicitná.

## Účtovanie a overenie

Ide o podklady daňového priznania, nie ďalšiu účtovnú knihu. Zápisy a platby
sa vykonávajú v natívnom účtovníctve a bankovom párovaní. Samotný výpočet
nevytvára zápis ani platbu. Prístup rešpektuje aktívne firmy a práva účtovníka
aj správcu. Generované sumy a archívy sú chránené aj pri priamom API/default_*.

Odoo testy spustite s `--test-enable --test-tags=/l10n_sk_vehicle_tax` pri
inštalácii/aktualizácii modulu. Overujú príklad FS2026 s hybridom86,95,
viacstranové a nulové XML, opravy, zastarané podklady, firemné práva aj tok
bežného účtovného správcu bez sudo. XSD nie je potvrdením prijatia úradom.

## Primárne zdroje

- [Zákon361/2014, zverejnené znenie od2025](https://static.slov-lex.sk/static/SK/ZZ/2014/361/20250101.print.html).
- [Poučenie MF/017488/2024-726](https://www.mfsr.sk/files/archiv/71/Poucenie-na-vyplnenie-DP-k-DzMV_v2025_final.pdf).
- [Príklady Finančnej správy2026](https://podpora.financnasprava.sk/335558-Vyp%C3%ADsanie-vyplnenie-da%C5%88ov%C3%A9ho-priznania-r-2026).
- [Oficiálna XSD](https://ekr.financnasprava.sk/Formulare/XSD/dmv2025.xsd), SHA256
  `d1b154eb027c5d70ed4afaeef85add1612a74674960cfd4665be1cd476502b57`.

Pre každý ostrý rok znovu overte legislatívu, formulár a sadzby. Otvorená
platnosť zverejnenej verzie negarantuje nezmeniteľnosť zákona. Pri zmene
pripravte novú dátumovanú verziu; už použitá verzia sa neprepisuje.
