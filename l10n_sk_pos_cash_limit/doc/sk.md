---
title: Slovensko — limit platby v hotovosti na pokladnici
summary: Pred prijatím viac ako 5 000 € v hotovosti na pokladnici Point of Sale sa spýta pokladníka a takú objednávku označí v back office.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Slovenský zákon zakazuje platbu v hotovosti nad 5 000 € a predaj na pokladnici
nie je výnimkou: limit 15 000 € platí len medzi fyzickými osobami
nepodnikateľmi. Keď hotovosť na objednávke po odpočítaní vydaného výdavku
presiahne 5 000 €, obrazovka platby sa pred potvrdením zastaví a požiada
pokladníka o potvrdenie. „Späť“ vráti na obrazovku platby, aby sa zvyšok
zaplatil kartou alebo prevodom; „Pokračovať“ objednávku potvrdí. Formulár
objednávky v back office potom ukáže rovnaké upozornenie, takže sa také
objednávky dajú nájsť a skontrolovať.

**Hotovosť v cudzej mene** sa ocení v eurách referenčným kurzom ECB alebo NBS
platným v deň predchádzajúci dňu platby (§ 6 ods. 1), ktorý pokladnica dostane
pri otvorení. Pokladnica v mene bez známeho kurzu kurz neháda a nepýta sa.

**Ten istý zákazník platí v ten deň v hotovosti znova.** Usmernenie finančnej
správy považuje jeden nákup zaplatený po častiach za jednu platbu, ale samostatne
uzavreté nákupy za samostatné (pokyn k zákonu 394/2012, čl. 2.3, príklady 15
a 17). Pokladnica ich nerozlíši, preto keď má objednávka zákazníka, pripočíta
hotovosť, ktorú zákazník v ten deň už zaplatil na ktorejkoľvek pokladnici
spoločnosti, a ukáže ju v otázke; rozhodne pokladník. Back office pripočíta len
skoršie objednávky, takže prvá objednávka série zostane bez upozornenia.

Nainštaluje sa sám, keď sú prítomné
[module:l10n_sk_invoice](module:l10n_sk_invoice) aj Point of Sale, a rovnako
ako upozornenie pri platbách v tom module upozorňuje, neblokuje.

## Právny základ {#legal}

- [Zákon č. 394/2012 Z. z.](law:sk/2012/394), § 4 ods. 1: platba v hotovosti
  nad 5 000 € je zakázaná; ods. 2 zvyšuje limit na 15 000 € len medzi fyzickými
  osobami nepodnikateľmi.
- § 6 ods. 1: hotovosť v cudzej mene referenčným kurzom predchádzajúceho dňa;
  ods. 2: časti jednej platby z jedného právneho vzťahu sa sčítavajú.
- § 8 uvádza výnimky, napríklad platby pri správe daní alebo pri exekúcii,
  ktoré pokladnica nerozpozná; preto potvrdenie, nie blokovanie.

## Obmedzenia {#limits}

Objednávky bez zákazníka sa posudzujú každá zvlášť a časti jedného nákupu zaplatené v rôzne dni sa nesčítavajú. Pri vrátení nad 5 000 € v hotovosti sa pokladnica tiež spýta: aj vyplatenie je platba v hotovosti, k platbám zákazníka sa však nepripočíta. Bez pripojenia pokladnica
posúdi len samotnú objednávku a back office sčíta neskôr. Kurz je kurz dňa pred
otvorením pokladnice; relácia otvorená cez polnoc si ho ponechá.
