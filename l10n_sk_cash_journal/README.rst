==========================================
Slovakia — Peňažný denník
==========================================

The Slovak half of the cash-journal family; the engine is in
``l10n_cssk_cash_journal_base``.

What it ships
=============

* **The statutory členenie** — opatrenie MF SR č. MF/27076/2007-74, § 4: the
  columns of the peňažný denník kept in jednoduché účtovníctvo, which also serve
  daňová evidencia (§ 6 ods. 11 ZDP) where the form is free.
* **The peňažný denník report** in that grid, with pokladnica, banka and
  priebežné položky each split into príjem and výdaj, a DPH pair, the income and
  expense breakdown, and running balances — the entries have to reconcile to the
  cash and bank balances (§ 4 ods. 10).
* **DPFO typ B figures** (``l10n.sk.cash.dpfo``): tabuľka 1 with the § 6 rows
  and the r. 10 totals that feed rows 39 and 40 of the return, tabuľka 1a with
  the start-and-end balances for daňová evidencia, and tabuľka 1b for a
  flat-rate payer.

Two things that are Slovak, not shared
======================================

* **Poistné podnikateľa is a daňový výdavok** (§ 19 ods. 3 písm. i ZDP). The
  Czech module files the same payment as non-deductible, and a test in each
  module asserts the disagreement so nobody "harmonises" them.
* **Jednoduché účtovníctvo is still open to a Slovak SZČO** (ZoÚ § 9 ods. 2
  písm. a), in the 2026 and the 2027 wording. It was closed to Czech OSVČ. The
  company regime field offers ``ju`` only outside Czechia.

Configuring the chart
=====================

**The official chart maps itself.** Loading ``l10n_sk``'s chart sets the denník
category on 89 accounts, 15 of them in both directions, and installing this
module maps a chart that already exists. The button in Accounting →
Configuration re-applies it after the chart is extended. It never overwrites a
category you chose, so everything below is about the accounts it cannot know.

Map any remaining account to a denník column with *Cash Journal Category*. Three habits
worth following, all of them learned from a practising accountant's questions:

* **Give a two-way account a category for each direction.** ``461`` / ``479``
  úvery: prijatý úver inbound, splátka istiny outbound. ``343`` DPH: nadmerný
  odpočet inbound, odvod outbound. Mapped one way, the two columns net into one
  and the book understates both; the row is flagged rather than guessed.
* **Post a zálohová faktúra to the account the final supply will land on.** A
  received advance is taxable income when the money arrives (and a paid one a
  taxable expense), classified by what it is for — so the ordinary category
  mapping produces the right column with no special case.
* **Fix the partial-payment model once**, in the internal directive: pro rata,
  VAT first or base first, kept for the whole year and used for income and
  expenses alike. It is a setting under Accounting → Configuration.

Balances come from account code prefixes
========================================

``DPFO_1A_SLOTS`` maps tabuľka 1a to účtové triedy: 01+07 nehmotný, 02+03+08
hmotný (so the slot yields zostatková cena), 1 zásoby, 31 pohľadávky, 32
záväzky, 21+22+25+26 finančný majetok. ``account_type`` cannot make those
distinctions; the chart can.

Status
======

**Functional, tested live on Community 19.0** (10 tests: the catalogue, the
tax-expense treatment of poistné, the grid columns, a running balance that ties
to the ledger, an unnamed category still landing in the book, tabuľka 1 totals,
a non-taxable payment staying out of the base, tabuľka 1a balances, and tabuľka
1b for a paušál payer).

**Open:** the § 6 split across tabuľka 1 rows 1–9 is driven by the category's
``tax_return_code``, and the shipped catalogue tags everything as r. 2 (živnosť).
A trader with several § 6 sources needs their own categories, or a per-activity
tag on the document — worth settling with the accountant before the first filing.

Credits
=======

Data Dance s.r.o. — https://www.datadance.eu
