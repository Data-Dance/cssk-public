---
title: CZ manažerská výsledovka (MIS Builder)
summary: Manažerská výsledovka na české účtové osnově jako upravitelná šablona MIS Builder pro Odoo Community.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Odoo Enterprise má vlastní manažerské výkazy, Community žádné. Tento modul
dává databázi Community **manažerskou výsledovku** pro společnosti, které
účtují podle české účtové osnovy Odoo. Je to šablona pro modul OCA
[module:mis_builder](module:mis_builder), takže období, srovnání, rozpočty
a export do PDF a XLSX zajišťuje tento modul a šablonu si může controller sám
upravit.

Jde o manažerský pohled, **ne** o *Výkaz zisku a ztráty* do účetní závěrky.
Výkazy účetní závěrky sestavuje modul [module:l10n_cz_fs](module:l10n_cz_fs).
Seskupení jsou tu zvolena kvůli přehlednosti a neodpovídají řádkům výkazu,
proto oba výkazy neporovnávejte řádek po řádku. Výsledky se ale shodují:
*Výsledek hospodaření před zdaněním* i *po zdanění* jsou v obou stejná čísla.

## Co výkaz obsahuje {#lines}

Šablona se jmenuje **Manažerská výsledovka (CZ)**. Čte účty tříd 5 a 6 podle
začátku čísla účtu, takže nepotřebuje žádné štítky účtů:

| Řádek | Účty | Znaménko |
|---|---|---|
| Tržby za zboží | 604 | výnos |
| Tržby z prodeje výrobků a služeb | 601, 602 | výnos |
| Ostatní provozní výnosy | 64, 697, 699 | výnos |
| **Provozní výnosy celkem** | součet tří řádků výše | |
| Prodané zboží | 504 | náklad |
| Spotřeba materiálu a energie | 501, 502, 503 | náklad |
| Služby | 51 | náklad |
| Změna stavu zásob vlastní činnosti a aktivace | 58 | náklad |
| Osobní náklady | 52 | náklad |
| Daně a poplatky | 53 | náklad |
| Odpisy dlouhodobého majetku | 551 | náklad |
| (pomocný řádek) skupiny 54 a 55 včetně odpisů a účet 597 | 54, 55, 597 | náklad |
| Ostatní provozní náklady | 54, 55 a 597 bez 551 | náklad |
| **Provozní náklady celkem** | součet nákladových řádků (pomocný řádek se nezapočítává) | |
| **Provozní výsledek hospodaření** | provozní výnosy celkem − provozní náklady celkem | |
| Finanční výnosy | 66, 698 | výnos |
| Finanční náklady | 56, 57, 598 | náklad |
| **Výsledek hospodaření před zdaněním** | provozní výsledek + finanční výnosy − finanční náklady | |
| Daň z příjmů | 591, 592, 593, 595, 599 | náklad |
| Převod podílu na výsledku hospodaření společníkům | 596 | náklad |
| **Výsledek hospodaření po zdanění** | výsledek před zdaněním − daň z příjmů − převod podílu | |

Každá částka je **obrat za období**, ne kumulovaný zůstatek. Výnosy se
otáčejí, aby se zobrazovaly kladně, stejně jako náklady, a mezisoučty vycházejí
tak, jak čtenář čeká.

*Změna stavu zásob vlastní činnosti a aktivace* je nákladový řádek, protože
česká osnova účtuje obojí v účtové skupině 58 jako úpravu nákladů. Aktivace se
tam účtuje na stranu Dal, takže řádek bývá záporný a provozní náklady snižuje;
úbytek zásob vlastní činnosti ho naopak zvyšuje.

Pomocný řádek *(pomocný řádek) skupiny 54 a 55 včetně odpisů a účet 597* je
tam jen proto, aby se odpisy nezapočítaly dvakrát: účet 551 patří do skupiny
55. Jeho styl (*CZ — pomocný (skrytý)*) ho ve výkazu skrývá.

## Spuštění výkazu {#usage}

1. Nainstalujte modul. Potřebuje českou účtovou osnovu a modul
   [module:mis_builder](module:mis_builder).
2. Otevřete *Účetnictví → Výkazy → Výkaznictví MIS → Výkazy MIS* a klikněte
   na *Nové*.
3. Vyberte šablonu **Manažerská výsledovka (CZ)** a společnost.
4. Zvolte jedno období, nebo zapněte srovnávací režim a přidejte sloupce,
   například měsíce roku nebo letošní rok proti loňskému.
5. Výkaz si zobrazte, vytiskněte (PDF) nebo exportujte (XLSX). Z každé částky
   lze přejít na účetní položky, ze kterých vznikla.

Ve výchozím nastavení se započítávají jen zaúčtované zápisy.

## Úprava šablony {#adjusting}

Šablona je v nabídce *Účetnictví → Konfigurace → Výkaznictví MIS*. Které účty
patří do kterého řádku, je manažerské rozhodnutí a je třeba ho odsouhlasit
s účetní, zejména co patří do *Ostatních provozních nákladů* a co do
provozních skupin. Výrazy upravíte přímo tam.

Šablona a její styly se nahrají jen jednou: vaše úpravy aktualizaci modulu
přežijí.

Při přidávání řádků pozor na jednu past: technický název řádku nesmí začínat
předponou účetního výrazu, například `bal`, `balp`, `crd` nebo `deb`. MIS
Builder tyto řetězce přepisuje jako text a každý výraz, který se na takový
řádek odkazuje, pak ukáže `#ERR`. Proto se pomocný řádek jmenuje
`trida_54_55`.

## Omezení {#limitations}

- Účty se vybírají podle začátku čísla. Účty s jinými čísly, které do osnovy
  doplníte, výkaz nezachytí, dokud je nepřidáte do šablony.
- Není to přehled o peněžních tocích ani jejich plán. Plán peněžních toků dává
  modul OCA [module:mis_builder_cash_flow](module:mis_builder_cash_flow), *Přehled o peněžních tocích* do účetní
  závěrky modul [module:l10n_cz_fs](module:l10n_cz_fs).
