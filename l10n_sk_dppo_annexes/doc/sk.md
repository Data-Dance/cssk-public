# Prílohy DPPO: tabuľky A a B

Na priznaní zapnite **Použiť overené tabuľky A a B**. Položky tabuľky A
zaraďte do predpísaných riadkov A1 až A16 a uchovajte podklady. Súčet A17
sa prenesie do hlavného riadka 130. Zadané sumy musia pokrývať celú firmu.

Do B1 zadajte účtovné odpisy, do B2 daňové odpisy pred odpočítaním B3/B4,
do B3 neuplatnenú časť prenajatého majetku a do B4 prerušené odpisy.
Pomerný odpis pri predaji patrí do B5, nie súčasne do B2. Program spočíta
B6 = B2 − B3 − B4 + B5 a rozdiel proti B1 premietne do riadka 150 alebo 250.
Ostatné daňové úpravy vrátane riadka 290 zostávajú natívnymi vstupmi DPPO.

Po overení úplnosti vypočítajte priznanie a vyexportujte XML. Zmena kníh,
podkladov alebo hlavných riadkov vyžaduje nový výpočet. Ručne zadaný
hlavný riadok, ktorý odporuje prílohe, program odmietne. Pôvodný podaný
súbor zostáva uchovaný. Označenie podania v programe nič neposiela úradu.

Implementovaná je štruktúra DPPOv25; overenie neskoršieho ročníka je
samostatná úloha. Ostatné prílohy a osobitné režimy sa nedopĺňajú odhadom.
