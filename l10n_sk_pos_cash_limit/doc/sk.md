---
title: Slovensko — limit platby v hotovosti na pokladnici
summary: Pred prijatím viac ako 5 000 € v hotovosti na pokladnici Point of Sale sa spýta pokladníka a takú objednávku označí v back office.
verified: 19.0.1.0.0
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

Nainštaluje sa sám, keď sú prítomné
[module:l10n_sk_invoice](module:l10n_sk_invoice) aj Point of Sale, a rovnako
ako upozornenie pri platbách v tom module upozorňuje, neblokuje.

## Právny základ {#legal}

- [Zákon č. 394/2012 Z. z.](law:sk/2012/394), § 4 ods. 1: platba v hotovosti
  nad 5 000 € je zakázaná; ods. 2 zvyšuje limit na 15 000 € len medzi fyzickými
  osobami nepodnikateľmi.
- § 8 uvádza výnimky, napríklad platby pri správe daní alebo pri exekúcii,
  ktoré pokladnica nerozpozná; preto potvrdenie, nie blokovanie.

## Obmedzenia {#limits}

Pokladnica sa pýta, len ak pracuje v eurách; v inej mene back office prepočíta
a objednávku označí. Jedna objednávka je jedna platba: viac dokladov jedného
obchodu (§ 6 ods. 2) pokladnica nesčítava.
