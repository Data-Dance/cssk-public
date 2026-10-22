=========
Changelog
=========

All notable changes to **l10n_cz_cash_journal** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
