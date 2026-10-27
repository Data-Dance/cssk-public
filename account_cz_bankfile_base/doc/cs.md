---
title: Formáty bankovních souborů CZ/SK — společné sestavovače
summary: Sestavovače souborů ABO a MultiCash a čtení českých čísel účtů, které sdílejí moduly bankovních souborů.
verified: 19.0.1.3.2
family: account_abo#format
---

Obsahuje sestavovače platebních souborů ABO a MultiCash, aby varianty pro Community (platební příkaz) i Enterprise (hromadná platba) vytvářely stejné soubory, a k tomu čtení českých čísel účtů v obou zápisech (IBAN i `předčíslí-číslo/kód banky`) a značek `VS:`/`KS:`/`SS:` v textu platby. Totéž čtení účtů používají moduly KB BEST a Fio a importy výpisů MT940 a KB.

Nemá obrazovku ani nastavení. Instaluje se jako závislost modulů, které ho potřebují.
