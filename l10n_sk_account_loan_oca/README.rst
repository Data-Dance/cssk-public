==================================
SK Lízing — Community engine (OCA)
==================================

Bridge between ``l10n_sk_account_loan_base`` (the Slovak account roles) and the
**Community** leasing engine, OCA ``account_loan`` + ``account_leasing``.

A new loan or leasing contract opens with the Slovak accounts already filled in:

* long-term liability → ``long_term_loan_account_id``     (474000)
* current portion     → ``short_term_loan_account_id``    (474100)
* interest expense    → ``interest_expenses_account_id``  (562000)
* leased asset        → ``leased_asset_account_id``       (022000, ``account_leasing``)

Two integration points, because one is not enough: ``default_get`` fills a new
record, and ``_onchange_company`` refills after a company change — the engine
deliberately *clears* those three accounts when the company changes, since they are
company-specific, and without this the user would be left with blanks.

Non-Slovak companies are left untouched.

The Enterprise counterpart is ``l10n_sk_account_loan_ee``. Exactly one of the two may
be installed: the two engines declare the same models, and Odoo refuses the
combination. See the base module and ``PORTED-OCA.md``.

Licensed **AGPL-3** because it depends on the AGPL OCA engine.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
