=========
Changelog
=========

All notable changes to **l10n_sk_transaction_tax** are documented here.

[Unreleased]
------------

Added
~~~~~

- Native ledger source workpapers and OZNDFTv26 using the common statutory
  export, filed-copy retention and delivery tracking.
- Reviewed whole bank debits, dated currency quotes, original recharged
  transactions and evidenced tax reductions/corrections.
- Native 538/345 and 345/538 posting, idempotent retries, unfiled reversal and
  difference-only provision on a filed correction.
- Company-scoped accountant permissions and protected filing/accounting
  evidence, including same-content storage migration.
- Identified original-transaction caps shared across partial repayments and
  effective filed months, with explicit review after earlier amendments.
- Excluded recharges, exact partial-month dates, foreign non-IBAN refund
  accounts and Slovak source/dependency controls.

- Native source checks for reversals, own provisions and petty-cash transfers.
- Retained exported evidence for filing and filed payloads for liability posting;
  later source drift warns without rewriting history.
- Retained export recording after renderer/schema upgrades using native
  attachment integrity and ownership checks, without a new rendering.
  Preserve access errors during source-drift checks.
- Existing external reversals recognised without creating another reversal.
- Computed monthly statutory deadlines and individually taxed, reviewed
  bank-batch payments; serializer and native-source errors in the ORM language.
- Receipt-verification warning for an on-time date recorded after the deadline,
  preserving legitimate retrospective filing and the exact exported bytes.
- Optional calendar reference instead of manual deadline attestation; a domestic
  bank warning under foreign-provider grounds without blocking special accounts.
- Native Slovak catalogs, common-case instructions and original XSD bytes.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- Not yet ported. Carry the complete source, filing, accounting and batch
  lifecycle together with their regression tests and original schema bytes.
