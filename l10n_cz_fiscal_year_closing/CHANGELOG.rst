=========
Changelog
=========

All notable changes to **l10n_cz_fiscal_year_closing** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The closing template of 19.0.2.0.0 is not on 18.0.** Port the template
  data, the engine overrides, the pre-close list, the two views and the
  tests together, as the Slovak twin has them.

Changed
~~~~~~~

- **Renamed from ``l10n_cz_zavierka``.** *Závierka* is Slovak (the Czech
  word is *závěrka*), and the technical name is now English like most of the
  repository. No migration is shipped, because the module was not yet
  installed in production. A development database that had it installed
  keeps an orphaned ``l10n_cz_zavierka`` row. Install
  ``l10n_cz_fiscal_year_closing`` there. Its retype is idempotent, so it
  finds nothing left to change.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_cz_zavierka``. Rename it together with the rest of the 2026-09-30
  batch (the fiscal-year closing, surcharges, annual tax settlement and
  inventory verification modules). Rename every reference too: dependent
  manifests, ``odoo.addons.*`` imports, the ``.pot`` file name and
  ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_cz_zavierka``. Rename it together with the rest of the 2026-09-30
  batch (the fiscal-year closing, surcharges, annual tax settlement and
  inventory verification modules). Rename every reference too: dependent
  manifests, ``odoo.addons.*`` imports, the ``.pot`` file name and
  ``module_*`` settings toggles. The 19.0 commit is the checklist.

[19.0.2.0.0]
------------

Added
~~~~~

- **A closing template for the Czech chart** on the OCA
  ``account_fiscal_year_closing`` engine: class 5 and 6 to 710, classes 0–4
  and 710 to 702, and the opening through 701 (ČÚS 002 body 2.2.2, 2.2.3
  and 2.1.2). Receivables and payables are carried per partner.
- **The result is opened on 431**, against 701: ČÚS 002 bod 2.1.3 puts the
  profit or loss on an account of group 43 when the books are opened. A
  plain reversal of the closing would reopen it on 710.
- **702 carries a counter-entry for every closed account**, where the engine
  would post one netted line (zero on a complete balance sheet).
- **Before closing the year**: the closing form lists draft entries,
  numbering gaps, balances on 431, 395 and 261, draft payslips, unposted
  depreciation and an unfiled VAT return for the last period, for companies
  whose fiscal country is the Czech Republic.
- *Closing Type* on the journal entry form is shown on journal entries only;
  the engine showed it on every invoice and bill.

Changed
~~~~~~~

- **The module now depends on ``account_fiscal_year_closing``** and installs
  itself when that module and ``l10n_cz`` are both installed. Upgrading an
  installation that had only the retyped accounts installs the engine.

[19.0.1.0.0]
------------

Added
~~~~~

- Baseline: retypes ``l10n_cz``'s 701000 / 702000 / 710000 from
  ``off_balance`` to ``equity`` so that a Czech year-end closing and an
  opening balance can be posted. This works through the chart template and,
  for existing companies, through a ``post_init_hook``.
