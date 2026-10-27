---
title: Bločky z eKasy cez QR kód
summary: Prečíta QR kód na pokladničnom doklade (bločku) a zo služby na overovanie dokladov finančnej správy načíta doklad tak, ako ho predávajúci zaevidoval v eKase — položky, sadzby DPH aj rekapituláciu DPH podľa sadzieb.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

Každý pokladničný doklad vyhotovený pokladnicou eKasa nesie QR kód. Za ním má
finančná správa uložený doklad presne tak, ako ho predávajúci zaevidoval:
každú položku s množstvom a sadzbou DPH, rekapituláciu DPH podľa sadzieb a
identifikáciu predávajúceho.

Modul je *poskytovateľom údajov* pre rámec na zachytávanie bločkov
[module:l10n_cssk_receipt_capture](module:l10n_cssk_receipt_capture). Keď má
zachytený bloček QR kód zo slovenskej eKasy, modul si doklad vyžiada od
štátnej služby na overovanie dokladov a vyplní ho **údajmi, ktoré zaevidoval
sám predávajúci**, namiesto čítania fotografie. Zaúčtovanie bločku ako
dodávateľskej faktúry alebo výdavku je potom úlohou rámca.

Modul pozná dva druhy QR kódu:

| Doklad | Čo obsahuje QR kód |
|---|---|
| on-line (bežný prípad) | len identifikátor dokladu: `O-` a 32 hexadecimálnych znakov, pri doklade z virtuálnej registračnej pokladnice `V-` |
| off-line (pokladnica sa nestihla spojiť s eKasou) | `OKP:kód pokladnice:dátum a čas:poradové číslo:suma`, čo služba prijme ako kľúč na vyhľadanie |

Off-line doklad dostane skutočný identifikátor, keď ho pokladnica dodatočne
odošle do eKasy. Modul si uloží práve ten, takže ten istý nákup nemožno
zachytiť dvakrát.

## Právny rámec {#legal}

Od 1. januára 2026 evidenciu tržieb upravuje
[zákon o evidencii tržieb](law:sk/2025/384), ktorý nahradil doterajší zákon
č. 289/2008 Z. z. o používaní elektronickej registračnej pokladnice
([§ 21](law:sk/2025/384#paragraf-21)).

- **Služba.** Podľa [§ 2 písm. ai)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-ai)
  je *službou na overovanie dokladov* služba finančného riaditeľstva, ktorá
  prostredníctvom QR kódu na pokladničnom doklade umožňuje overovať správnosť
  údajov uložených v systéme pre pokladnice eKasa, *„sprístupňovať a získavať
  tieto údaje“*.
- **Kto ju smie používať.** *Overovateľom* je osoba, ktorá je po splnení
  podmienok podľa § 18 ods. 11 oprávnená službu používať —
  [§ 2 písm. aj)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-aj).
- **Predávajúci to musí strpieť.**
  [§ 18 ods. 3](law:sk/2025/384#paragraf-18.odsek-3): predávajúci *„je povinný
  strpieť“* sprístupnenie údajov uložených v systéme pre pokladnice eKasa
  prostredníctvom služby na overovanie dokladov.
- **Povinnosti overovateľa.** Podľa
  [§ 18 ods. 11](law:sk/2025/384#paragraf-18.odsek-11) je overovateľ povinný
  **pred začatím používania služby oznámiť finančnému riaditeľstvu IP adresu**,
  z ktorej bude k službe pristupovať, zasielať finančnému riaditeľstvu pravdivé
  výsledky overenia a dodržiavať podmienky používania, ktoré finančné
  riaditeľstvo určí a uverejní na svojom webovom sídle.

Modul nevie overiť, že oznámenie bolo urobené, preto ho od vás vyžaduje ako
vyhlásenie a kým ho nezaškrtnete, každé vyhľadanie odmietne (pozri
[Nastavenie](#setup)). V čase vzniku tejto verzie podmienky používania
uverejnené neboli; kým nebudú, oznámenie znamená obrátiť sa na finančné
riaditeľstvo priamo.

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia* (v edícii Community bez plného
účtovníctva *Fakturácia → Konfigurácia → Nastavenia*), blok **Slovak eKasa
Receipt Lookup** pod blokom *Fiscal Receipt Capture*. Modul zatiaľ nemá
slovenský preklad, popisy sú po anglicky:

| Nastavenie | Čo robí |
|---|---|
| Zapnúť vyhľadávanie (*Enable eKasa Lookup*) | Zapne vyhľadávanie pre aktuálnu spoločnosť. Predvolene vypnuté. |
| IP adresa oznámená (*IP Address Notified (§ 18/11)*) | Zaškrtnite až vtedy, keď finančnému riaditeľstvu bola oznámená verejná IP adresa, z ktorej sa váš server Odoo pripája. Kým nie je zaškrtnuté, každé vyhľadanie sa s vysvetlením odmietne. |
| Oznámená IP adresa, dátum oznámenia (*Notified IP Address*, *Notified On*) | Adresa, ktorú ste oznámili, a dátum. Slúži ako záznam; modul ju neporovnáva so skutočne používanou adresou. |
| Hodinový limit (*Hourly Lookup Budget*) | Najviac vyhľadaní za hodinu, predvolene 60. Nula znamená žiadne vyhľadávanie. |
| Časový limit (*Lookup Timeout (s)*) | Ako dlho čakať na odpoveď služby, predvolene 30 sekúnd. |

Prečo limit: služba povoľuje približne 60 vyhľadaní za celú hodinu (hh:00 až
hh:59) z jednej IP adresy a adresu, ktorá limit prekročí, zablokuje. Modul
počíta svoje volania za každú spoločnosť a zastaví sa skôr. Skutočný limit
však platí pre **adresu**: ak sa z jednej adresy pripája viac spoločností alebo
databáz, znížte im limity tak, aby ho spolu neprekročili.

Spoločnosti, ktoré existovali pred inštaláciou, dostanú predvolený limit 60.

Samotného poskytovateľa — *Slovak eKasa (QR lookup)*, obmedzeného na
Slovensko — vytvorí modul a nájdete ho medzi ostatnými poskytovateľmi údajov
rámca.

## Zachytenie bločku {#usage}

Bloček zachyťte ako zvyčajne v rámci zachytávania bločkov (*Účtovníctvo →
Dodávatelia → Fiscal Receipts*): naskenujte QR kód kamerou, prepíšte ho alebo
nahrajte fotografiu.

- **Z fotografie** sa QR kód dekóduje na serveri. Ak je na bločku viac kódov
  (napríklad kód vernostnej aplikácie nad fiškálnym), použije sa len kód,
  ktorému modul rozumie. Obrazovka skenovania pripomenie, ktorý kód treba
  naskenovať: ten priamo nad textom *OVERTE DOKLAD POMOCOU QR KÓDU*.
- **Ak sa kód nedá dekódovať**, ale iný poskytovateľ (napríklad čítanie
  pomocou AI) prečítal identifikátory vytlačené vedľa neho — `UID` on-line
  dokladu alebo OKP, kód pokladnice, dátum a čas, číslo a sumu off-line
  dokladu — modul z nich zostaví kľúč a skúsi ho. Vytlačené `0-` sa číta ako
  `O-` (v písme bločkov vyzerajú rovnako) a číslo dokladu vytlačené ako
  `202609/5` sa najprv skúsi ako `5`. Zle prečítaný kľúč nenájde nič, nie
  cudzí doklad, a suma zaevidovaného dokladu sa navyše musí zhodovať so sumou
  na fotografii, inak sa výsledok zamietne.
- **Čo sa vyplní:** dátum vyhotovenia (bratislavský čas bez ohľadu na to, kde
  je ten, kto bloček zachytáva), celková suma, obchodné meno, DIČ, IČ DPH, IČO
  a či je predávajúci platiteľom DPH, predajné miesto ako poznámka, všetky
  položky a rekapitulácia DPH podľa sadzieb. Na formulári bločku pribudnú dve
  polia: **OKP** (overovací kód podnikateľa) a **Paragón** (doklad vystavený
  ručne počas nefunkčnosti pokladnice).

Ako sa údaje čítajú, je pre zaúčtovanie dôležité:

- Rekapitulácia DPH sa berie z rekapitulácie podľa sadzieb na samotnom
  doklade. Ak ju služba nevráti, vypočíta sa zo sadzieb položiek a na bloček sa
  zapíše upozornenie.
- Cena položky je **celková suma riadku vrátane DPH**, nie jednotková cena.
  Rámec účtuje sumu riadku, takže bloček na 31,17 l nafty za 57,85 € sa
  zaúčtuje na 57,85 €.
- IČ DPH predávajúceho sa uloží tak, ako ho vráti služba, nikdy sa neodvodzuje
  z DIČ — člen skupiny DPH podáva pod číslom skupiny.

Keď vyhľadanie zlyhá, bloček uvedie prečo:

| Výsledok | Čo sa stane |
|---|---|
| vypnuté, IP adresa nepotvrdená, limit vyčerpaný | Poskytovateľ eKasa ustúpi a bloček môže prečítať ďalší poskytovateľ (napríklad čítanie pomocou AI). |
| výpadok siete | Bloček zostane nezmenený a neskôr sa automaticky skúsi znova. |
| doklad nie je zaevidovaný | Finančná správa k tomuto kódu nemá žiadny doklad. Kód bol buď zle prečítaný, alebo predávajúci tržbu nezaevidoval — čo môže stáť za nahlásenie. |
| služba požiadavku odmietla | Zvyčajne ide o firewall služby, nie o bloček; automaticky sa neopakuje. |

## Záznam overení {#log}

Každé volanie služby sa zaznamená: *Účtovníctvo → Dodávatelia → Fiscal
Receipts → eKasa Verification Log* a z bločku cez tlačidlo **Lookups**. Každý
riadok ukazuje čas volania, identifikátor alebo kľúč, na ktorý sa modul pýtal,
bloček a výsledok (*Receipt found* — doklad nájdený, *Not registered* — nie je
zaevidovaný, *Refused by the service* — služba odmietla, *Network or transport
error* — chyba siete). Do hodinového limitu sa počítajú aj odmietnuté a
neúspešné volania.

Záznam je vaším vlastným prehľadom o tom, čo ste overovali. Čítať ho môžu
používatelia s právom fakturácie, upravovať a mazať len správcovia
účtovníctva.

## Obmedzenia {#limitations}

- **Zasielanie výsledkov overenia nie je naprogramované.** § 18 ods. 11
  ukladá overovateľovi zasielať finančnému riaditeľstvu pravdivé výsledky
  overenia; modul si ich len ukladá vo vlastnom zázname. Spôsob zasielania
  závisí od podmienok, ktoré finančné riaditeľstvo ešte neuverejnilo.
- Oznámenie IP adresy je vaše vyhlásenie. Modul neoveruje ani to, že bolo
  urobené, ani že oznámená adresa je tá, ktorú server skutočne používa.
- Hodinový limit sa počíta za spoločnosť. Spoločnosti alebo databázy so
  spoločnou odchádzajúcou adresou zdieľajú jeden skutočný limit, ktorý modul
  nevidí.
- Služba zatiaľ nemá zverejnené rozhranie pre tretie strany; modul ju volá
  rovnako ako verejná stránka na overenie dokladu. Ak ju finančná správa zmení,
  vyhľadávanie nebude fungovať, kým sa modul neupraví.
- Len slovenské doklady z eKasy. České a zahraničné bločky a slovenské bločky,
  ktorých kód sa nedá prečítať vôbec, potrebujú iného poskytovateľa.
- Obrazovky modulu sú po anglicky; slovenský preklad zatiaľ chýba.
