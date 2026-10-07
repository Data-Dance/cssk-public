=========
Changelog
=========

All notable changes to **l10n_sk_cash_journal** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-10-04
-------------------------

Added
~~~~~

- **The spreadsheet opens with the peňažný denník in its statutory layout**:
  pokladnica, banka, priebežné položky and DPH, each with príjem and výdaj, then
  the breakdown columns and the running balances. It uses the same figures as
  the PDF, read from the same computation. The flat sheet for pivoting
  follows. Asked for by a customer's accountant.

[19.0.1.0.4] — 2026-09-28
-------------------------

Added
~~~~~

- Slovak translation of the English UI terms (``i18n/sk.po``). The statutory
  labels are Slovak in the source and stay untranslated.

[19.0.1.0.3] — 2026-09-27
-------------------------

Added
~~~~~

- **The official SK chart is mapped out of the box** (``SK_CHART_MAP``): 501/504
  → zásoby, 502/511/512/518 → služby, 521 → mzdy, 526 → poistné podnikateľa
  (taxable, § 19 ods. 3 písm. i), 524/525 → poistné zamestnávateľa, 527 → tvorba
  SF, 551 → odpisy as a non-cash row, 513/543/545 → neovplyvňujúce ZD (§ 21),
  01–04 → nákup dlhodobého majetku, 261 → priebežné položky. Two-way pairs: 343
  (odvod / nadmerný odpočet), 231-461-479 (splátka istiny / prijatý úver), 491
  (osobná spotreba / vklad podnikateľa), 341, 331, 336. 311/321 and 314/324 are
  left unmapped on purpose — the first two are followed to the document, and an
  advance's column depends on what it is for.

[19.0.1.0.2] — 2026-09-27
-------------------------

Added
~~~~~

- A test for the two-way account case in the statutory grid: a loan received
  lands in "príjmy neovplyvňujúce ZD", its instalment in "výdavky neovplyvňujúce
  ZD", and neither touches tabuľka 1. Requires a category per direction on the
  account — see ``l10n_cssk_cash_journal_base`` 19.0.1.3.0.

Notes
~~~~~

- **Accounts worth mapping in both directions**: ``461`` / ``479`` úvery (prijatý
  úver PN2 in, splátka istiny VN5 out), ``343`` DPH (nadmerný odpočet PN3 in,
  odvod VN3 out), and any partner advance account.

[19.0.1.0.1] — 2026-09-26
-------------------------

Fixed
~~~~~

- **A refunded sale no longer inflates its sales column or tabuľka 1.** The grid
  prints a storno negative in its own column and the money columns still show the
  payment leaving the bank; tabuľka 1 reports the gross príjmy net of refunds and
  no expense. Fix is in ``l10n_cssk_cash_journal_base`` 19.0.1.2.0; this module
  gained the reporting side of it and a test that measures both.

[19.0.1.0.0] — 2026-09-23
-------------------------

Added
~~~~~

- **The Slovak členenie**, per opatrenie MF/27076/2007-74, § 4: P1–P3 and PN1–PN9
  on the income side, V1–V9 and VN1–VN9 on the expense side, C1 priebežné
  položky, and Z1/Z2 for odpisy and the § 17 ods. 8 / § 51a adjustments.
- **The peňažný denník report** in the statutory grid, with running cash and
  bank balances (§ 4 ods. 10).
- **``l10n.sk.cash.dpfo``** — tabuľka 1, 1a and 1b of DPFO typ B, VI. oddiel.

Notes
~~~~~

- **Poistné podnikateľa is taxable here and not in the Czech module** (SK § 19
  ods. 3 písm. i vs CZ § 25 odst. 1 písm. g). Asserted in both test suites.
- The "bank" balance is the bank account **plus the transit accounts**. Until a
  statement is imported the money sits on outstanding receipts, and once it is,
  the outstanding and suspense legs net out — so the sum is right either way.
  A test ties the book's closing balance to that ledger figure.
