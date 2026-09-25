==========================================
CZ/SK Cash Journal — Shared Framework
==========================================

The country-neutral engine behind the Slovak **peňažný denník** and the Czech
**peněžní deník**, for a sole trader who keeps SK **daňová evidencia**
(§ 6 ods. 11 ZDP), CZ **daňová evidence** (§ 7b ZDP), SK **jednoduché
účtovníctvo** (ZoÚ § 15) or flat-rate expenses.

**The books stay double-entry.** The denník is a stored projection of ordinary
``account.move`` data onto the cash basis, so invoicing, bank import, DPH /
KV DPH / KH, e-invoicing, assets and POS keep working untouched. POHODA,
Money S3 and ABRA Flexi are built the same way: one engine, with a posting rule
carrying the category.

Architecture
============

* ``cssk.cash.category`` — the *členenie*, per country: ``kind``
  (income / expense / transit), ``taxable`` (does it reach the tax base) and
  ``non_cash`` (depreciation, tax-base adjustments — POHODA's *nepeněžní
  deník*).
* ``cssk.cash.journal.line`` — the stored, numbered row: money columns
  (pokladnica / banka), the VAT column kept apart from the base, and the
  document behind it.
* ``account.account.cssk_cash_category_id`` — the default category per account,
  overridden per document line. The account is the natural carrier because a
  *predkontácia* names an account; see
  ``docs/predkontacia-document-level-design.md``.
* ``res.company.cssk_bookkeeping_regime`` — ``pu`` by default, so installing
  this module changes nothing until someone chooses a single-entry regime.
* ``cssk.cash.journal.generate`` — regeneration over a period.

How a row comes to exist
========================

1. Every movement of money is found **once**, at the latest point it reached: a
   bank or till line wins over the outstanding leg of the same entry, and an
   outstanding line is dropped once a statement takes it over.
2. Its counterparts say what the money was *for*. A receivable or payable is
   followed through reconciliation to the documents behind it; a transit
   account (outstanding, suspense, transfer) is followed one hop further,
   through same-move counterparts as well as reconciliations.
3. The paid document is split **pro rata** over its lines and VAT rates, and
   each part becomes a row carrying that line's category.
4. Anything that cannot be resolved becomes a row flagged ``needs_review`` with
   the reason. Nothing is guessed and nothing is dropped, so the book still
   reconciles to the bank.

Two decisions worth knowing
===========================

* **Partial payments are pro-rated**, as Odoo's own
  ``account_reports_cash_basis`` does. POHODA settles the VAT in full out of the
  first partial payment. No statute we could find dictates either — the SK JÚ
  opatrenie (§ 19 ods. 5) leaves it to an internal rule — so
  ``_cssk_split_document`` is a single overridable method.
* **Liquidity cannot be recognised by account type.** On a fresh 19.0 company
  the outstanding receipts, suspense and transfer accounts are all
  ``asset_current``; only bank and till accounts are ``asset_cash``. Transit
  accounts are therefore read from configuration.

Status
======

**Functional, tested live on Community 19.0** (25 tests: full and partial
payments, VAT apart from the base, pro-rata rounding, a receipt net of a
deducted charge, a negative document line, zero-balance counterparts, the
outstanding-account chain, direct bank charges, money moved in a misc journal,
bank-to-till transfers, unmatched receipts as possible advances, unmapped
accounts, non-cash rows, idempotent regeneration, stable numbering, lock and
start dates, category constraints).

**Known gaps:** write-offs and realised exchange differences reach the book as
review-flagged rows rather than a considered treatment; multi-currency payments
are recorded in company currency only.

**Not built yet:** the country modules. They ship the statutory category
catalogues, the denník grid in its official column layout, and the rows of the
personal income-tax return (SK DPFO typ B tabuľka 1 / 1a / 1b, CZ Příloha č. 1
including oddíl D). Conversion between single-entry and double-entry is
deliberately deferred — the year-end balances it needs are produced for the tax
return anyway.

Credits
=======

Data Dance s.r.o. — https://www.datadance.eu
