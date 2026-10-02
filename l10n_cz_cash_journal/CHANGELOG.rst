=========
Changelog
=========

All notable changes to **l10n_cz_cash_journal** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.4] — 2026-09-28
-------------------------

Added
~~~~~

- Czech translation of the English UI terms (``i18n/cs.po``). The statutory
  labels are Czech in the source and stay untranslated.

[19.0.1.0.3] — 2026-09-27
-------------------------

Added
~~~~~

- **The official CZ chart is mapped out of the box** (``CZ_CHART_MAP``), in the
  same shape as the Slovak one and deliberately not a copy of it: **526 →
  pojistné podnikatele as NON-deductible** (§ 25 odst. 1 písm. g), where Slovakia
  maps the same account to a tax expense. Two-way pairs: 343, 231-461-479, 491,
  341, 331, 336; 311/321 and 314/324 stay unmapped.

[19.0.1.0.2] — 2026-09-27
-------------------------

Notes
~~~~~

- Inherits the per-direction category and the partial-payment setting from
  ``l10n_cssk_cash_journal_base`` 19.0.1.3.0. Accounts worth mapping both ways in
  a Czech chart: ``461`` úvěry, ``343`` DPH, and partner advance accounts.

[19.0.1.0.1] — 2026-09-26
-------------------------

Fixed
~~~~~

- **A dobropis now reduces ř. 101 and its own column of the deník** instead of
  appearing as an expense. Odoo posts a credit note on the opposite side rather
  than as a negative on the original one, and the book has to undo that. Fix is
  in ``l10n_cssk_cash_journal_base`` 19.0.1.2.0.

[19.0.1.0.0] — 2026-09-23
-------------------------

Added
~~~~~

- **The Czech členění** for daňová evidence (§ 7b ZDP), following POHODA and
  Money S3 since no regulation prescribes one.
- **The peněžní deník report**, with running pokladna and banka balances.
- **``l10n.cz.cash.priloha``** — Příloha č. 1 ř. 101/102/104 and oddíl D.
- **The § 7b odst. 4 zápis** about the year-end stock-take, which Czech law
  requires in writing and Slovak law does not require at all.

Notes
~~~~~

- **Pojistné podnikatele is non-deductible here and deductible in the Slovak
  module** (CZ § 25 odst. 1 písm. g vs SK § 19 ods. 3 písm. i). Asserted in both
  test suites, including a cross-check that reads the Slovak catalogue.
- Oddíl D row 9 "Mzdy" is read as the liability on 331; the form does not say
  whether it means that or the year's wage cost. Flagged in the README.
