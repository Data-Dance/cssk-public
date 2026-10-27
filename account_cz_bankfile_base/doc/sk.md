---
title: Formáty bankových súborov CZ/SK — spoločné zostavovače
summary: Zostavovače súborov ABO a MultiCash a čítanie českých čísel účtov, ktoré zdieľajú moduly bankových súborov.
verified: 19.0.1.3.2
family: account_abo#format
---

Obsahuje zostavovače platobných súborov ABO a MultiCash, aby varianty pre Community (platobný príkaz) aj Enterprise (hromadná platba) vytvárali rovnaké súbory, a k tomu čítanie českých čísel účtov v oboch zápisoch (IBAN aj `predčíslie-číslo/kód banky`) a značiek `VS:`/`KS:`/`SS:` v texte platby. To isté čítanie účtov používajú moduly KB BEST a Fio a importy výpisov MT940 a KB.

Nemá obrazovku ani nastavenia. Inštaluje sa ako závislosť modulov, ktoré ho potrebujú.
