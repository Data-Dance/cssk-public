# l10n_sk_account_loan_oca: developer notes

Not user documentation: this file is not rendered into a page.

## Defaults

Two integration points, because one is not enough: `default_get` fills a new
record, and `_onchange_company` refills after a company change — the engine
deliberately *clears* those three accounts when the company changes, since they are
company-specific, and without this the user would be left with blanks.
