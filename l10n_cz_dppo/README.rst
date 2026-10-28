=======================================
CZ Corporate Income Tax Return (DPPDP9)
=======================================

The Czech country layer for the income-tax framework
(``l10n_cssk_income_tax_base``). It builds the corporate income-tax return
(Přiznání k dani z příjmů právnických osob, DPPDP9): ``ř.10`` (výsledek
hospodaření před zdaněním) is computed from the P&L, the adjustments are entered
by the accountant, and the II. oddíl tax-calculation spine
(základ daně → daň 21 %, 19 % for periods begun before 2024 → daň po slevách)
is arithmetic.

The export produces the official EPO ``Pisemnost``/``DPPDP9`` XML and validates
it against the bundled official DPPDP9 XSD (``data/dppdp9_epo2.xsd``).

Features
========

* ``ř.10`` (výsledek hospodaření před zdaněním) is computed from the P&L:
  class 6 − class 5, excluding the income-tax accounts 591–599.
* The připočitatelné / odčitatelné adjustments (ř.20–170), the § 34
  deductions (ř.230 ztráta, ř.240 pre-2005 odečty, ř.242 VaV, ř.243 odborné
  vzdělávání), the § 20 odst. 8 dary (ř.260) and the slevy na dani (ř.300)
  are manual, accountant-entered, and aggregate into the spine.
* The II. oddíl tax-calculation spine (ř.10 → ř.340) is arithmetic:
  základ daně → zaokrouhlení → daň 21 % / 19 % (§ 21 odst. 1, by the
  period's first day) → daň po slevách →
  celková daňová povinnost.
* Each spine line maps to its official EPO ``VetaO/@kc_ii*`` attribute; only
  non-zero spine lines are emitted.
* The export builds the EPO ``Pisemnost``/``DPPDP9`` XML and validates it
  against the bundled official DPPDP9 XSD (``data/dppdp9_epo2.xsd``).
* Statement types Řádné (B), Opravné (O) and Dodatečné (E) are shipped as
  version data.
* The účetní závěrka travels inside the return: link the computed
  ``l10n_cz_fs`` Rozvaha and Výkaz zisku a ztráty of the same period, and the
  export files them as ``VetaUA`` (aktiva — brutto / korekce / netto / netto
  minulé), ``VetaUD`` (pasiva) and ``VetaUB`` (VZZ druhové členění), in
  thousands, in the plný or zkrácený rozsah of the linked statements
  (vyhláška 500/2002 Sb., § 3a; both must be of the same one). Each EPO row
  takes the
  ``l10n_cz_fs`` row of the same statutory designation — one account mapping,
  not two. The row numbers come from the EPO číselník vendored as
  ``data/uv_radky_500.csv``; ``models/dppdp9_vykazy.py`` maps every row of
  either rozsah or states why it is not applicable. XSD and číselník are
  pinned in ``data/SCHEMA_VERSION``.

**Not applicable, by design:** C.II.3. / pasiva C.III. in both rozsahy (the
alternative placement of časové rozlišení, which is filed under D.); in the
zkrácený rozsah also C.II.1. dlouhodobé pohledávky (the chart convention files
every receivable as krátkodobé) and VZZ V. (účet 665 is not split there, so it
is all filed on IV.; the plný-rozsah VZZ splits it by account tag) — confirm
these with the accountant. The mikro rozsah (M) is not produced.

**Out of scope:** the appendix tables (odpisy příl. 1B, § 23e výpůjční náklady
příl. 3, zápočet daně ze zahraničí, investiční fondy), the přehledy and the
příloha účetní závěrky (E-přílohy). The XSD makes every line but the VetaD header optional, so a
spine-only return validates. Confirm the VetaD header codes
(``typ_dapdpp`` / ``typ_zo`` / ``typ_popldpp``) and the full adjustment set with
a Czech accountant before live filing.

Usage
=====

Create a corporate income-tax return for the company and period, pick the
statement type (Řádné / Opravné / Dodatečné), and compute the lines: ``ř.10``
is derived from the P&L and the tax spine is evaluated automatically. Enter the
připočitatelné / odčitatelné adjustments, the loss and § 34 deductions and the
slevy na dani by hand, link the Rozvaha and the Výkaz zisku a ztráty
(computed in *Financial statements*), recompute, then export the EPO ``Pisemnost``/``DPPDP9``
XML — it is validated against the bundled DPPDP9 XSD before it is attached.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
