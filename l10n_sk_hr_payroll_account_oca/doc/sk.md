---
title: Slovenské mzdy — účtovníctvo (OCA)
summary: Zaúčtuje slovenské výplatné pásky z aplikácie OCA payroll do slovenskej účtovej osnovy.
verified: 19.0.1.0.5
family: l10n_sk_hr_payroll_base#accounting
---

Nastaví slovenským mzdovým pravidlám účty MD a D pre každú spoločnosť so slovenskou osnovou — mzdy, náhrada mzdy pri prekážkach na strane zamestnávateľa a (ak sú nainštalované) mzdové zvýhodnenia na 521000, čistá mzda na 331000, poistné na 336000 a 524000, daň, daňový bonus a ročné zúčtovanie dane na 342000, exekučné zrážky na 379000, stravné a náhrada príjmu pri PN na 527000 a 333000 —, takže potvrdená výplatná páska zaúčtuje vyrovnaný zápis. Urobí to pri inštalácii pre spoločnosti, ktoré už slovenskú osnovu majú, a neskôr vždy, keď ju spoločnosť načíta.

Inštaluje sa zámerne a vyžaduje modul OCA `payroll_account` a slovenskú účtovú osnovu. Na každej zmluve zvoľte *Účtovnú knihu výplat*.

Ide o počiatočné predvolené nastavenie. Ak už má pravidlo účet použiteľný spoločnosťou, ďalšie načítanie osnovy zachová jeho dvojicu MD/D vrátane úmyselne prázdnej opačnej strany. Odložené nastavenie spoločnosti preto neprepíše samostatné analytiky poisťovní ani iné účtovné voľby. Nové pravidlá bez použiteľného mapovania dostanú predvolené účty. Vyhľadávanie rešpektuje natívnu firemnú doménu Odoo vrátane povolených účtov materskej spoločnosti pre pobočky.

Ak chcete obnoviť počiatočné predvolené účty, výslovne vyčistite oba účty príslušného pravidla a znovu spustite nastavenie osnovy. Existujúce ochrany mzdových zdrojov naďalej platia: vyčistenie konfigurácie neumožňuje prepísať zaúčtované mzdy ani uchované dôkazy.
