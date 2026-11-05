# Dated parameters from 1 January 2027

Checked 2026-11-05. Eleven new values are appended; no 2026 value is overwritten.

Sources and derivation:

- [ZDP 595/2003, effective2027](https://static.slov-lex.sk/static/SK/ZZ/2003/595/20270101.html), §§11,15,33,35: NČZD, taper, tax bands, child-bonus taper. Subsistence minimum295.22 gives annual NČZD6199.62 and monthly516.64; annual bands45700.06/62704.73/77938.08, monthly3808.34/5225.39/6494.84. Annual bands must not be reconstructed from rounded monthly ceilings.
- [VšZP2027](https://www.vszp.sk/platitelia/platenie-poistneho/oznamenia-zmeny/zmeny-od-01-01-2027/): health minimum base295.22. Employee/employer5%/11% rates already present remain applicable; minimum advances total47.23.
- [SP general assessment table](https://www.socpoist.sk/nastroje-sluzby/tabulky/tabulka-vseobecneho-vymeriavacieho-zakladu): average2025=1620, VVZ19440. [461/2003 §138](https://static.slov-lex.sk/static/SK/ZZ/2003/461/20270101.print.html) gives11×1620=17820 social ceiling. ZDP§33 gives18×1620=29160 annual child-bonus taper threshold.
- [SP2027 daily ceiling](https://socpoist.sk/news/zmena-2027-socialna-poistovna-bude-vyplacat-vyssie-maximalne-sumy-davok-nemocenske-materske):106.5206.
- [NIP2027 minimum wage](https://www.ip.gov.sk/inspektorat-prace-kosice/domov/aktuality/minimalna-mzda-minimalne-mzdove-naroky-roku-2027.html): hourly5.586 (40-hour week).

Tax figures are calculated from the enacted multipliers and published reference amounts; they are not presented as an already-published FS2027 parameter table. This data update does not implement new personal eligibility profiles, all absence/transition cases, new annual forms, or the full 2027 payroll workflow. OOP300 is the separate PR13; this patch does not duplicate it.
