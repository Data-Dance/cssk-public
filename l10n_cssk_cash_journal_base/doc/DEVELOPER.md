# l10n_cssk_cash_journal_base: developer notes

Not user documentation: this file is not rendered into a page.

## Design

- `cssk.cash.category` — the *členenie*, per country: `kind`
  (income / expense / transit), `taxable` (does it reach the tax base) and
  `non_cash` (depreciation, tax-base adjustments — POHODA's *nepeněžní
  deník*).
* `cssk.cash.journal.line` — the stored, numbered row: money columns
  (pokladnica / banka), the VAT column kept apart from the base, and the
  document behind it.
* `account.account.cssk_cash_category_id` — the default category per account,
  overridden per document line. The account is the natural carrier because a
  *predkontácia* names an account; see
  `docs/predkontacia-document-level-design.md`.
* `res.company.cssk_bookkeeping_regime` — `pu` by default, so installing
  this module changes nothing until someone chooses a single-entry regime.
* `cssk.cash.journal.generate` — regeneration over a period.
* `cssk.cash.journal.print` — the book as a PDF (national layout, from the
  country module) or as a spreadsheet (rows plus totals per category).

1. Every movement of money is found **once**, at the latest point it reached: a
   bank or till line wins over the outstanding leg of the same entry, and an
   outstanding line is dropped once a statement takes it over.
2. Its counterparts say what the money was *for*. A receivable or payable is
   followed through reconciliation to the documents behind it; a transit
   account (outstanding, suspense, transfer) is followed one hop further,
   through same-move counterparts as well as reconciliations.
3. The paid document is split **pro rata** over its lines and VAT rates, and
   each part becomes a row carrying that line's category.
4. Anything that cannot be resolved becomes a row flagged `needs_review` with
   the reason. Nothing is guessed and nothing is dropped, so the book still
   reconciles to the bank.
