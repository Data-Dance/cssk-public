=========
Changelog
=========

All notable changes to **l10n_cz_dppo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **``dppdp9_epo2.xsd`` refreshed** to the file the Finanční správa
  publishes now. It was changed in place without a new version (still
  05.01.01 of 21. 10. 2025): three annotations and the order of one
  pattern's alternatives, nothing a return is validated against. The pin in
  ``data/SCHEMA_VERSION`` follows; the row list of the statements was
  compared again for platnost 2026 and is unchanged.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **ř. 50 / ř. 150 of 19.0.1.7.0 are not on 18.0.** Port the row
  definitions, the two XML attributes, the calendar-year guard, the
  migration and the tests together.
- **The sbírka listin request of 19.0.1.8.0 is not on 18.0.** Port the
  fields, the checks, the template records and the tests together.

[19.0.1.8.0] — 2026-11-24
-------------------------

Added
~~~~~

- **Handing the účetní závěrka to the sbírka listin through the return**
  (§ 21b zákona o účetnictví). A group on the return adds the request
  (``VetaUZ``, tiskopis 25 5404/I) with its scope: the Rozvaha and the Výkaz
  zisku a ztráty linked to the return, and the příloha, the přehled o
  peněžních tocích and the přehled o změnách vlastního kapitálu as uploaded
  files (``PredepsanaPriloha`` PP_OPISPUV / PP_PTOK / PP_ZVKAP, counted on
  ``VetaD``). An e-mail for the confirmation is optional.
- ``VetaD/neschval_uz`` and ``neaudit_uz``: two ticks for statements not yet
  approved or not yet audited.
- The export refuses what the XSD cannot see and the tax office would not
  pass on (§ 21b odst. 5): a request naming statements that are not linked,
  a request for nothing, a malformed e-mail, a file type EPO does not take,
  more than 10 240 kB of files.

[19.0.1.7.0] — 2026-11-24
-------------------------

Added
~~~~~

- **ř. 50 and ř. 150 from the tax depreciation register.** The difference
  between accounting and tax depreciation of the year is computed where
  ``account_asset_tax`` is installed, on ř. 50 where the accounting
  depreciation is higher and on ř. 150 where the tax depreciation is
  (*Pokyny* 25 5404/1, K ř. 50 and K ř. 150). Both rows are filed as
  ``kc_ii60_50`` / ``kc_ii170_150``. They were not on the return at all;
  the difference had to be worked out elsewhere and typed into the
  subtotal.

Changed
~~~~~~~

- **ř. 70 and ř. 170 are sums.** Each is the new typed row of the other
  items (ř. 20–63 without ř. 50, ř. 100–162 without ř. 150) plus ř. 50 or
  ř. 150. A migration adds the rows to an installed version and switches the
  two subtotals where they are still as shipped. A return computed before
  the upgrade keeps the subtotal typed on it, so its tax base does not move;
  open returns get a note asking whether that subtotal already contains the
  depreciation difference.
- **The export refuses a typed ř. 70 / ř. 170 that is not the sum of its
  rows**, since the file now carries ř. 50 / ř. 150 beside the subtotal.
- A period that crosses a calendar year end gets no computed ř. 50 / ř. 150
  (the tax plan is kept by calendar year) and says so in its history.

[19.0.1.6.0] — 2026-11-15
-------------------------

Added
~~~~~

- **Porovnat s účetní závěrkou.** A button on a Czech return compares ř. 10
  (výsledek hospodaření před zdaněním) with the row "** Výsledek hospodaření
  před zdaněním" of the Výkaz zisku a ztráty — the statement linked to the
  return, or else a computed one for exactly the same period — and records
  the result on the comparison screen. The two are the same figure, so a
  difference is reported as one. The Slovak return has the same check in
  ``l10n_sk_dppo_fs``.

Fixed
~~~~~

- **ř. 10 counts the převodové účty 597 and 598.** It left out the whole of
  účtová skupina 59; the income tax (591, 592, 593, 595, 599) and the převod
  podílu společníkům (596) belong below the result before tax, but 597 and
  598 are costs above it. With their counterparts 697 and 698 counted, a
  company using them had ř. 10 overstated by what stood on 597 and 598. An
  installed version is corrected on upgrade where the row still holds the
  shipped formula; recompute a return to refresh its figures.
- The výkazy tests pass with the OCA asset register's profiles installed and
  with Czech loaded.

[19.0.1.5.1] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak and Czech catalogues: translated the strings that were still English.

[19.0.1.5.0] — 2026-10-27
-------------------------

Added
~~~~~

- **The výkazy are filed in plný rozsah** when the linked Rozvaha and Výkaz
  zisku a ztráty are the full-scope versions of l10n_cz_fs (uv_rozsah P),
  with every numbered row of the číselník; linked abridged statements are
  filed in the zkrácený rozsah as before.

Changed
~~~~~~~

- A Rozvaha and a Výkaz zisku a ztráty of different rozsahy are refused:
  the return states one rozsah for both.

[19.0.1.4.0] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Periods from 2021 can be entered.** The DPPDP9 version was valid from
  1 January 2025, so a 2024 or earlier return could not be created, although
  the Finanční správa files every period in the one current structure (the
  XSD accepts periods from 2021). The version is now open from 2021 and is
  named *DPPDP9*. Existing databases are updated on upgrade unless the dates
  were changed by hand.

- **19 % for periods begun before 2024.** ř. 280 was a flat 21 %. The rate is
  the one in force on the first day of the period — zákon č. 349/2023 Sb.,
  čl. XVI bod 1 keeps the earlier wording for every zdaňovací období begun
  before 1 January 2024 — so a hospodářský rok from July 2023 is taxed at
  19 % although it ends in 2024.

[19.0.1.3.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Donations are filed on ř.260 and reduce ř.270.** One row, filed as
  ř.240, stood for the § 34 deductions and the § 20 odst. 8 donations
  together, and ř.270 rounded ř.250 without deducting any donation. The rows
  now follow tiskopis 25 5404 vzor č. 36: ř.240 is the § 34 deduction in its
  wording to 31. 12. 2004, research and development is ř.242, vocational
  training ř.243, ř.250 = ř.200 − 230 − 240 − 242 − 243, donations are
  ř.260, and ř.270 = (ř.250 − ř.260) rounded down to whole thousands. The
  export writes ``kc_ii_242``, ``kc_ii_243`` and ``kc_ii240_260``. On an
  existing database the shipped rows are updated on upgrade; an amount
  already entered on ř.240 is not moved, because only the accountant knows
  which of the three it was.

[19.0.1.3.0] — 2026-09-29
-------------------------

Fixed
~~~~~

- **DPPDP9** ``VetaD`` now carries ``c_nace``, the company's CZ-NACE code, which
  EPO checks critically against the code list.

[19.0.1.2.0] — 2026-09-28
-------------------------

Fixed
~~~~~

- **Every DPPDP9 declared itself a return on entering liquidation.** VetaD
  carried ``typ_dapdpp="B"`` hard-coded, which the XSD defines as *daňové
  přiznání při vstupu do likvidace*; the ordinary return for the tax period
  is **A**. It is now a choice on the return (*Typ daňového přiznání*, the
  XSD's full code list), defaulting to A.
- **``typ_zo`` was "1", which is no letter of § 21a ZDP.** It is now derived
  from the period — a calendar year A, another twelve-month year B, anything
  longer D — and can be set by hand (C for the period from a merger's decisive
  day). ``typ_popldpp`` is a choice too, defaulting to 1 (ostatní).
- **"Dodatečné" exported E, which the form reads as "dodatečné-opravné".** D
  now exists and E is labelled for what it is (migration 19.0.1.2.0); a
  dodatečné return needs *Důvody zjištěny dne* (``d_zjist``) before export.
  Returns already exported are not touched.

TODO
~~~~

- CZ asset ř.50/150 wiring is still pending. The asset book-vs-tax difference is not yet fed
  into the DPPDP9 spine (připočitatelné ř.50 / odčitatelné ř.150); the SK counterpart
  (``l10n_sk_dppo``) is wired via the ``asset_diff`` line kind, CZ is not.

[19.0.1.1.0] — 2026-09-28
-------------------------

Added
~~~~~

- **Rozvaha and Výkaz zisku a ztráty inside the return.** The účetní závěrka
  is filed as the XSD's own výkaz records — VetaUA (aktiva: brutto / korekce /
  netto / netto minulé), VetaUD (pasiva) and VetaUB (VZZ druhové členění),
  zkrácený rozsah per vyhláška 500/2002 Sb., in thousands — with the VetaD
  header (``uv_vyhl``, ``uv_rozsah``, ``uv_mena``, ``uz_rad``, ``d_uv``). The
  figures are those of the ``l10n_cz_fs`` Rozvaha / VZZ linked to the return
  (new dependency), matched row by statutory designation; there is no second
  account mapping. Linking is explicit, and a half-linked pair, a statement of
  another period or company, an uncomputed one, or one missing a row the
  výkaz reads is refused by name.
- The EPO row číselník for the three tables (the XSD does not carry it) is
  vendored as ``data/uv_radky_500.csv``. Every row of the zkrácený rozsah is
  mapped or declared not applicable with a reason (C.II.1., C.II.3., pasiva
  C.III., VZZ V.), and every other výkaz record of the XSD is declared not
  applicable by table; a test enforces both, and checks each EPO total
  against its statutory parts by signed weight per account of the l10n_cz
  chart.
- ``data/SCHEMA_VERSION`` pins the XSD and the číselník (size + md5) with the
  refresh procedure.

Changed
~~~~~~~

- ``data/dppdp9_epo2.xsd`` replaced by the published file (it differed only in
  the order of a pattern's alternatives), and ``verzePis`` raised from 05.01
  to the published structure version 05.01.01.
- A return exported with no statements linked says so in the chatter: the
  závěrka must then go as an E-příloha.
- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Statutory rounding unified to HALF-UP (``statutory_round()``/``statutory_whole()``). (Wave 1)
- Multi-company ``ir.rule`` (``company_id in company_ids``) added. (Wave 1)

Fixed
~~~~~

- Removed ``typ_ds="P"`` from the DPPDP9 VetaP element — that attribute belongs to the DPH forms,
  not the income-tax return. (Wave 1)
- EPO Pisemnost/DPPDP9 XML: empty attributes now emitted as ``None`` (omitted) instead of ``""``
  (XSD-invalid). (Wave 1)

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech corporate income-tax return (DPPDP9) on ``l10n_cssk_income_tax_base``: II. oddíl tax
  spine (ř.10 → ř.340) mapped to the EPO ``VetaO/@kc_ii*`` attributes.
- ř.10 (výsledek hospodaření před zdaněním) computed from the P&L (class 6 − class 5, excluding
  income-tax accounts 591–599); připočitatelné/odčitatelné adjustments, §34 deductions and slevy
  are accountant-entered and aggregate into the spine.
- EPO Pisemnost/DPPDP9 XML export validated against the bundled official XSD
  (``data/dppdp9_epo2.xsd``).
- cs_CZ jsonb translations (i18n sweep).
