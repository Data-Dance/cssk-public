=========
Changelog
=========

All notable changes to **l10n_cssk_cash_journal_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.6.0] — 2026-10-04
-------------------------

Fixed
~~~~~

- **An expense outside an invoice is one row**, carrying both its base and its
  VAT, as a paid bill already was. An Expenses-app expense or a hand-made entry
  with a tax used to give two rows, one with the base and one with the VAT
  under the VAT account's category. Each VAT line is now folded into the base
  line it was computed on. The money is unchanged: it only moves from a row of
  its own into the base row's VAT. Reported by a customer's accountant.

Added
~~~~~

- ``_cssk_write_national``: a hook through which the country module puts its
  statutory layout first in the spreadsheet.

[19.0.1.5.0] — 2026-09-30
-------------------------

Changed
~~~~~~~

- **The denník mapping has a page of its own on the account form**, second in
  the notebook after Accounting, instead of two fields under the account type.
  It is a page's worth of subject: a category per direction, which one wins, and
  when the second is needed at all.
- **The inbound category reaches the form for the first time.** It was added for
  two-way accounts — a loan received and repaid, ``343`` paying VAT over and
  receiving the nadmerný odpočet back — and never put on a view, so the only way
  to set it by hand was the chart mapping or the shell.
- Both categories are also optional columns on the account list, for mapping a
  chart in bulk.

Notes
~~~~~

- The page is **always visible**, deliberately. Hiding it unless the company
  keeps a single-entry regime was the first idea and is a trap: the regime
  defaults to podvojné účtovníctvo, so a fresh install would hide the page
  everywhere and the module would look like it had done nothing. An accountant
  also maps the chart before switching regime, not after.
- Two tests: the page renders with both fields (an inherited page that stops
  matching its anchor fails silently on the next Odoo version), and both fields
  are writable.

[19.0.1.4.1] — 2026-09-28
-------------------------

Fixed
~~~~~

- **The Cash Journal menu is a section of Accounting → Accounting**, no longer a
  child of the Invoicing root. Enterprise's ``accountant`` moves ``account``'s
  own submenus into its Accounting app and leaves everything else under
  ``account.menu_finance`` behind, so on Enterprise the menu sat under a stray
  "Invoicing" app nobody opens. The menu still needs the Bookkeeper group
  (``account.group_account_user``; "Show Full Accounting Features" on
  Community).
- **The direction-mismatch review reason is two sentences**, one per direction,
  instead of the raw ``in`` / ``out`` code spliced into English, which no
  translation could inflect.

Added
~~~~~

- Slovak and Czech translations (``i18n/sk.po``, ``i18n/cs.po``), complete.

[19.0.1.4.0] — 2026-09-27
-------------------------

Added
~~~~~

- **The chart maps itself.** ``res.company._cssk_map_chart_categories()`` fills
  the denník category on every account a country mapping knows, by code prefix;
  the country modules supply the table through ``_cssk_chart_category_map()``. It
  runs when a chart is loaded (an override of ``account.chart.template._load``,
  because the usual order is module first and chart second), from each country
  module's ``post_init_hook`` for charts that already exist, and from a button in
  the settings. It **never overwrites a category somebody chose** unless asked,
  so it is safe to run again after a chart is extended.

  Measured on a fresh Slovak company: loading the chart maps 89 accounts
  outbound and 15 of them inbound as well. Before this, a new database flagged
  essentially every row for review until someone mapped 40-odd accounts by hand
  — twice over for the two-way ones.

Notes
~~~~~

- **``res.company.country_id`` cannot be searched in 19.0**: it is a non-stored
  compute over the company's partner, and a domain on it raises *Cannot convert
  res.company.country_id to SQL because it is not stored*. The hooks filter in
  Python instead. Cost one failed install.

[19.0.1.3.0] — 2026-09-27
-------------------------

Added
~~~~~

- **A category per direction on the account** (``cssk_cash_category_in_id``).
  An account can legitimately move both ways — a loan account receives the loan
  and pays the instalments, ``343`` pays the VAT over and receives the nadmerný
  odpočet back — and those are two columns of the book. Mapped one way, a loan of
  10 000 received and 2 500 repaid netted to 7 500 of "príjmy neovplyvňujúce ZD"
  and left "výdavky neovplyvňujúce ZD" empty. Found by a cooperating accountant
  asking whether a pôžička shows in the denník at all.
- **A storno is now only a storno.** ``counter_entry`` is reserved for a payment
  matched to a credit note or a reversal entry, which is what it was meant for. A
  direction whose category contradicts it and is not a reversal is **flagged for
  review** with the account named, instead of silently netting two columns.
- **The denník prints as a spreadsheet as well as a PDF.** A print wizard takes
  the period and the format; the PDF layout comes from the country module,
  because a denník's columns are a national matter, and the spreadsheet is
  country-neutral: sheet one is every row as the book has it, sheet two the
  totals per category. The rows sheet is deliberately flat so the accountant can
  pivot it her own way rather than being given one fixed pivot. Adds a dependency
  on ``report_xlsx``.
- **The partial-payment model is a company setting**
  (``cssk_cash_partial_allocation``): pro rata, VAT first, or base first. All
  three are permissible — the entity fixes one in its internal directive, keeps it
  for the year and applies it to income and expenses alike. Pro rata stays the
  default. Across a document's own lines the split is always pro rata, since the
  directive governs base versus VAT, not which expense line a part payment bought
  first.

Notes
~~~~~

- **A received advance is taxable income when the money arrives**, and a paid one
  a taxable expense, classified by what the advance is for. This is the opposite
  of the VAT treatment, where a zálohová faktúra is not a taxable event. It
  follows that an advance invoice should be posted to the account the final
  supply will land on; then the denník needs no special case, which two new tests
  pin. A payment with no document behind it stays a review row, because what the
  advance is for cannot be derived.

[19.0.1.2.0] — 2026-09-26
-------------------------

Fixed
~~~~~

- **A refunded sale was reported as an expense.** ``kind`` was doing double duty
  as the money direction and the classification, so a credit note paid back to a
  customer produced an expense row carrying an income category. The tax base came
  out right and both gross columns of the tax return came out wrong — SK tabuľka 1
  read príjmy 1000 against výdavky 200 where the statute wants príjmy 800, and the
  sales column of the book read 1200. Direction and classification are now
  separate fields (``money_direction``, ``kind``), a contradiction between them is
  flagged as ``counter_entry``, and ``amount_classified`` carries the amount
  negative so a storno reduces its own column — as POHODA and Money show it.
- **An account mapped to a transit category produced an expense row.** A "261
  Peniaze na ceste" account that the accountant maps to the transit category but
  that Odoo does not know as an outstanding or transfer account landed in
  "výdavky neovplyvňujúce základ dane" instead of the priebežné columns. The
  classification now follows the category, so this is fixed by construction.

Both were found when a cooperating accountant asked which side of a document
(MD/D) the denník should read. The answer is neither: the line's own sign gives
the direction, and the category gives the column. Five tests added across the
three modules, including the mirror case of a refund received from a supplier.

Changed
~~~~~~~

- ``cssk.cash.figures._cssk_flows`` now returns the classification totals net of
  storno rows, while ``money_income`` / ``money_expense`` and the VAT figures
  still follow the money.
- Migration ``19.0.1.2.0`` fills ``money_direction`` on rows generated earlier.
  Note that a migration script still takes ``(cr, version)`` in 19.0, unlike
  ``post_init_hook``, which took ``(env)`` from 19.0 on.

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
