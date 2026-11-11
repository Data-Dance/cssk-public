---
title: Bankovní napojení — hlavička deníku
summary: Jedna hlavička ve formuláři bankovního deníku, kam každé bankovní napojení dává své akce.
verified: 19.0.1.0.0
---

Formulář bankovního deníku v Odoo nemá hlavičku, proto každé bankovní napojení dávalo svá tlačítka někam do těla formuláře, ta pro Tatra banku dokonce do vlastní záložky. Tento modul přidá do formuláře každého bankovního deníku jednu hlavičku a moduly bankovních napojení (Tatra banka Premium API, Fio banka) v ní zobrazí své akce: *Stáhnout transakce*, *Stáhnout rozsah…*, *Znovu načíst z banky* a podobně. Každé tlačítko se ukáže jen tehdy, když je jeho napojení nastavené v poli *Bankovní napojení* deníku.

Nemá vlastní obrazovku ani nastavení. Instaluje se jako závislost modulů bankovních napojení.
