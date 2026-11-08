# l10n_cssk_oss_base: developer notes

Not user documentation: this file is not rendered into a page.

## Core lookup overlay

- the lookup core performs is answered through a scoped overlay (a
  `ContextVar` set only while this module's mapping runs), so databases in
  the same server process that do not have this module keep core's map;
* **SK 5 % → another state** maps to whatever core maps SK 10 % to (the old
  band of books, medicines and basic food);
* **another state → SK 5 %**: each source state's lowest reduced rate, plus
  CZ 12 % (the merged Czech reduced rate since 2024);
* 19.0 core links only the FIRST domestic tax per foreign rate; the others are
  linked afterwards, as 18.0 did, which is what lets SK 5 % and SK 19 % share
  a destination rate.
