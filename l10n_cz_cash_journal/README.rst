==========================================
Czechia — Peněžní deník
==========================================

The Czech half of the cash-journal family; the engine is in
``l10n_cssk_cash_journal_base``.

There is no statutory layout here
=================================

§ 7b ZDP asks for příjmy and výdaje "v členění potřebném pro zjištění základu
daně" plus a record of majetek and dluhy, and nothing more. The term *peněžní
deník* appears in the income-tax act nowhere at all — it is defined only by
§ 13b zákona o účetnictví, for jednoduché účetnictví, which an OSVČ may not keep
(§ 1f). So the členění here follows POHODA and Money S3, which is what the
accountant reading the book already knows.

What it ships
=============

* **The catalogue**: P1–P3 / PN1–PN9, V1–V9 / VN1–VN9, C1 průběžné položky, and
  Z1/Z2 for odpisy and the § 23 odst. 8 adjustment.
* **The peněžní deník report** — materiál apart from zboží, odvody za
  zaměstnance apart from mzdy, with running pokladna and banka balances.
* **``l10n.cz.cash.priloha``** — ř. 101, ř. 102 and ř. 104 of Příloha č. 1, and
  **oddíl D** with the start-and-end balances of hmotný majetek, hotovost,
  bankovní účty, zásoby, pohledávky, ostatní majetek, dluhy, rezervy and mzdy.
* **The § 7b odst. 4 zápis** — Czech law requires a written record of the
  year-end stock-take (Slovakia requires none for daňová evidencia), so the
  closing figures print as the body of that record.

Two things that are Czech, not shared
=====================================

* **Pojistné podnikatele is not deductible** (§ 25 odst. 1 písm. g ZDP), where
  Slovakia allows it. A test in each module asserts the disagreement.
* **Jednoduché účetnictví is closed to an OSVČ** (§ 1f zákona o účetnictví), so
  the regime field refuses ``ju`` for a Czech company.

Balances come from account code prefixes
========================================

``PRILOHA_D_SLOTS`` maps oddíl D to the účtová osnova of vyhláška č. 500/2002
Sb.: 02+03+08 hmotný majetek at zůstatková cena, 211 pokladna, 221 bankovní
účty, 1 zásoby, 31 pohledávky, 01+07 ostatní majetek, 32 dluhy, 45 rezervy,
331 mzdy. Liability slots are reported positive, as the form asks.

Status
======

**Functional, tested live on Community 19.0** (8 tests: the catalogue, the
non-deductible insurance end to end, the deník columns and balance, ř. 101/102,
oddíl D at both ends, dluhy reported positive, and the zápis rendering).

**Open:** oddíl D row 9 "Mzdy" is read as unpaid wages (331). The form's
instructions do not spell out whether it means the liability or the year's wage
cost, and the two differ — worth confirming with the accountant before filing.

Credits
=======

Data Dance s.r.o. — https://www.datadance.eu
