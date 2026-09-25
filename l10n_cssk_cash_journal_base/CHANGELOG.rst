=========
Changelog
=========

All notable changes to **l10n_cssk_cash_journal_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-23
-------------------------

Added
~~~~~

- **First version: the shared engine for the peňažný denník / peněžní deník.**
  A single-entry cash journal derived from ordinary double-entry books, for a
  sole trader keeping SK daňová evidencia (§ 6 ods. 11 ZDP), CZ daňová evidence
  (§ 7b ZDP), SK jednoduché účtovníctvo (ZoÚ § 15) or flat-rate expenses.

  - ``cssk.cash.category`` — the členenie, per country: income / expense /
    transit, whether it reaches the tax base, and whether it is a non-cash row.
  - ``cssk.cash.journal.line`` — the stored, numbered row, with the money
    columns (pokladnica / banka), the VAT column kept apart from the base, and
    the document it came from.
  - ``account.account.cssk_cash_category_id`` plus a per-line override on
    ``account.move.line``: the account carries the default category, a document
    line overrides it. The same two-carrier arrangement as the predkontácia
    design.
  - ``res.company.cssk_bookkeeping_regime`` (``pu`` by default, so installing
    changes nothing) and ``cssk_cash_journal_start`` for a mid-year migration.
  - ``cssk.cash.journal.generate`` — regeneration over a period, idempotent,
    leaving manual rows and anything behind the accounting lock date alone.

- **A payment is split across the paid document pro rata**, every line and
  every VAT rate — Odoo's own cash-basis convention. POHODA settles VAT out of
  the first partial payment instead; no statute we could find dictates either,
  so ``_cssk_split_document`` is one overridable method.

Notes
~~~~~

- **Liquidity cannot be recognised by account type.** Measured on a fresh 19.0
  company: the outstanding receipts, bank suspense and inter-bank transfer
  accounts are all ``asset_current``, and only bank and till accounts are
  ``asset_cash``. A first draft filtered on the type and generated **nothing at
  all** for a payment registered through the payment wizard. Transit accounts
  are now collected from configuration (the chart template's
  ``account_journal_payment_debit_account_id`` / ``..._credit_account_id``,
  payment method lines, journal suspense accounts, the company transfer
  account).
- **The money is counted once, at the latest point it reached.** A receipt
  exists as a payment on an outstanding account and again as a bank statement
  line; the bank line wins within one entry, and an outstanding line is dropped
  once a statement has taken it over. A transfer, whose two legs are both real,
  keeps both rows — as priebežné položky.
- Payment entry and receivable are counterparts of the same entry and are never
  reconciled to each other, so the chain walk follows same-move counterparts as
  well as reconciliations.

Review record
~~~~~~~~~~~~~

Second opinion taken from GitHub Copilot / **gpt-5.3-codex** on 2026-09-23, per
the CLAUDE.md rule for money logic. Twelve findings; the disposition:

**Accepted and fixed**

- **Allocation divided by the sum of magnitudes.** The review's most valuable
  catch, by way of its point about absolute values losing sign semantics: a
  receipt of 120 with a 20 bank charge deducted was split 85.71 / 14.29 across
  the two categories. A line's own sign now decides its column and the scale
  comes from the **signed** total, so each side keeps its whole amount. Two
  tests: the net receipt, and an invoice carrying a negative line.
- **A zero-balance counterpart absorbed the rounding remainder**, filing real
  money under a line worth nothing. Zero lines are dropped before allocating.
- **Deduplication only looked one reconciliation hop**, so a receipt could be
  counted twice whenever the statement reached the payment through more than one
  step. It now walks the chain.
- **Unordered matched amounts** made an over-matched receivable split
  differently from one regeneration to the next; the SQL is ordered.
- **Unmatched money on a receivable was reported as transit.** It is normally an
  advance received or paid, so it is now its own row, flagged for the
  accountant's decision, with a test.
- **A transit row with no transit category** was created silently; it is flagged.
- **Money posted outside a bank or cash journal was ignored** — an accountant's
  correction in the Miscellaneous journal moves real money. The journal is no
  longer part of the test, and the money column is read off the account.
- **Numbering depended on the database id**, so regenerating could renumber the
  same day's rows. It now sorts on the accounting line behind each row, with a
  test that two runs agree.
- **N+1 queries** in the deduplication pass: the reconciliation lookup is now a
  single query for the whole period.
- **``ondelete="cascade"``** would have removed rows of a filed book when
  someone deleted the entry behind them; all four references are ``set null``.

**Not acted on**

- *"delete-then-rebuild in ``_cssk_regenerate`` is brittle."* It is one
  transaction, and the alternative (diffing rows against what the books now say)
  is more machinery for the same result. Manual rows and locked periods are
  already excluded.
- *"residual on a write-off or FX line may not be transit."* True, and it is
  what the review-flagged rows are for; a proper treatment of write-offs and
  realised exchange differences is its own piece of work, noted in the README.
