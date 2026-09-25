=========
Changelog
=========

All notable changes to **l10n_sk_cash_journal** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
