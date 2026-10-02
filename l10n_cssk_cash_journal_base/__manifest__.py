{
    "name": "CZ/SK Cash Journal — Shared Framework (peňažný denník / peněžní deník)",
    "version": "19.0.1.5.0",
    "summary": "Country-neutral single-entry cash journal derived from ordinary "
               "double-entry books: payments become dated, categorised denník "
               "rows, with the year-end balances the tax return asks for.",
    "description": """
CZ/SK Cash Journal — Shared Framework
=====================================

The country-neutral engine behind the Slovak **peňažný denník** and the Czech
**peněžní deník**, for a sole trader who keeps **daňová evidencia** (SK § 6
ods. 11 ZDP), **daňová evidence** (CZ § 7b ZDP), **jednoduché účtovníctvo**
(SK, ZoÚ § 15) or **paušálne výdavky**.

**The books stay double-entry.** Nothing here replaces ``account.move``: the
denník is a *derived, stored* projection of ordinary Odoo accounting onto the
cash basis, which is how POHODA, Money S3 and ABRA Flexi work too (one engine,
a posting rule carrying the category). Everything else therefore keeps working
untouched — invoicing, bank import, DPH/KV DPH/KH, e-invoicing, assets, POS.

What it does:

* **A payment creates the row, not the invoice.** A bank or cash line is
  expanded through its reconciliation into the paid document's own lines, so a
  denník row carries the *category* of what was actually bought or sold.
* **A partial payment is split pro rata** across every line and VAT rate of the
  document. This is Odoo's own cash-basis convention
  (``account_reports_cash_basis``); POHODA instead settles VAT first. The rule
  is one method, ``_cssk_split_document``, so a country or a customer can
  override it.
* **Transit legs are followed.** An Odoo payment lands on an *outstanding*
  account and only the statement line reaches the bank, so money would
  otherwise be counted twice. Outstanding, suspense and other liquidity
  accounts are treated as *priebežné položky / průběžné položky* and the chain
  is followed to the document behind them.
* **Non-cash rows** (depreciation, tax-base adjustments) are carried by
  categories flagged ``non_cash`` — POHODA's *nepeněžní deník*.
* **Nothing is guessed.** A payment whose category cannot be resolved produces
  a row flagged ``needs_review`` with the reason, rather than a silent zero.

Provides:

* ``cssk.cash.category`` — the členenie: income/expense/transit, whether it
  affects the tax base, per country.
* ``cssk.cash.journal.line`` — the stored, numbered denník row.
* ``account.account.cssk_cash_category_id`` / ``account.move.line`` override —
  where a row's category comes from.
* ``cssk.cash.journal.generate`` — the regeneration wizard.
* ``cssk.cash.figures`` — the arithmetic the income-tax return needs: the
  period's flows out of the denník and the year-end balances out of the ledger.

Country modules ship the category catalogue, the denník grid and the rows of
the personal income-tax return (SK DPFO typ B tabuľka 1/1a, CZ Příloha č. 1).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "l10n_cssk_core", "report_xlsx"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/cssk_cash_category_views.xml",
        "views/cssk_cash_journal_line_views.xml",
        "views/account_views.xml",
        "views/res_config_settings_views.xml",
        "wizard/cssk_cash_journal_generate_views.xml",
        "wizard/cssk_cash_journal_print_views.xml",
        "report/cssk_cash_journal_reports.xml",
        "views/cssk_cash_journal_menus.xml",
    ],
    "installable": True,
}
