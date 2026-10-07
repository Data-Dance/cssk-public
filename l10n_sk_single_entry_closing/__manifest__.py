{
    "name": "Slovakia — Účtovná závierka v jednoduchom účtovníctve",
    "version": "19.0.1.0.2",
    "summary": "The closing a SZČO keeping jednoduché účtovníctvo files: výkaz "
               "o príjmoch a výdavkoch from the peňažný denník, výkaz o majetku "
               "a záväzkoch from the ledger.",
    "description": """
Slovakia — Účtovná závierka v jednoduchom účtovníctve
====================================================

A natural person who keeps **jednoduché účtovníctvo** is an účtovná jednotka
(ZoÚ § 1 ods. 1 písm. a) bod 3) and files an účtovná závierka — unlike one
keeping **daňová evidencia**, who is outside the accounting act and files
nothing of the sort. That distinction is the reason this module exists: it is
what a cooperating accountant identified as the actual deliverable for the
segment.

The closing has two components:

* **Výkaz o príjmoch a výdavkoch** — what was received and paid, in the denník's
  own členenie. Computed from ``cssk.cash.journal.line`` through a new line kind
  (``cash_categories``) rather than from account balances, because the cash basis
  already lives in the denník and rebuilding it from the ledger a second time
  would mean a second set of bugs. Non-cash rows (odpisy) are excluded: they
  belong to the income-tax base, not to a statement of money.
* **Výkaz o majetku a záväzkoch** — balances at the end of the period, read from
  the ledger by account code, which is what the shared framework already does.

Built on ``l10n_cssk_fs_base``, so it inherits the states, the comparison
period, manual overrides with an audit trail, the unmapped-amount check and the
XSD-validated export.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_fs_base", "l10n_sk_cash_journal"],
    "data": [
        "report/l10n_sk_ju_zavierka_templates.xml",
        "data/cssk_uzfo_v14_version_data.xml",
        "views/l10n_sk_ju_zavierka_views.xml",
    ],
    "installable": True,
}
