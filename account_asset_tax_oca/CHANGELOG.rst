=========
Changelog
=========

All notable changes to **account_asset_tax_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.4.4] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the tax depreciation report and hit *not allowed to access*. On
  Community, ``account.group_account_manager`` does not imply
  ``account.group_account_user`` (and on Enterprise ``account_accountant``
  only adds ``group_account_basic``), so a model granted to
  ``group_account_user`` alone is closed to an Administrator who lacks "Show
  Full Accounting Features". Its menu was already restricted to
  ``group_account_manager``, so every manager-only user who opened it hit the
  error. ``group_account_manager`` now has the same access as
  ``group_account_user`` on ``account.asset.book.tax.report`` (read-only, as
  for users). Takes effect on module update.

[19.0.1.4.2] — 2026-07-04
-------------------------

Added
~~~~~

- Concrete ``account.asset.book.tax.report`` SQL-view model (OCA/Community edition)
  over the ``account.asset.book.tax.report.mixin``: the book side aggregates the
  OCA asset depreciation table (``account.asset.line``, type *depreciate*) per
  (asset, year) — every depreciation line in ``book_amount``, lines with a journal
  entry in ``book_amount_posted``. Pivot / graph / list views + menu *Accounting →
  Reporting → Book vs Tax Depreciation*, with a company ``ir.rule`` and read ACL.

[19.0.1.4.0]
------------

Added
~~~~~

- Tax-default fields on account.asset.profile + inheritance on asset create; vehicle-cap flag on the form; icon; README. Validated on 19CE-TEST (11 tests).

[19.0.1.3.0]
------------

Added
~~~~~

- Disposal hook: ``write(state='removed')`` records the tax disposal event; ``_tax_accounting_residual`` reads OCA book value at a date for deferred tax; ``tax_increased_first_year`` on the form. Tests: disposal-on-remove, deferred tax. Validated on 19CE-TEST (8 tests green).

[19.0.1.2.3]
------------

Changed
~~~~~~~

- ``tax_value_depreciated`` / ``tax_value_residual`` now derived from the board (filed lines vs board total), consistent with technical improvements.

[19.0.1.2.2]
------------

Fixed
~~~~~

- Asset-form xpath used a ``string`` selector (forbidden in Odoo 19) → anchor the Tax Depreciation page to ``//notebook position=inside``.

Verified
~~~~~~~~

- Installs clean on Odoo 19 CE with OCA ``account_asset_management``; all 6 integration tests green; l10n_cz/sk data loads against the real CZ/SK charts (6 + 7 groups).

[19.0.1.2.1]
------------

Added
~~~~~

- Integration tests (``tests/test_tax_board_oca.py``): SK linear/accelerated board, suspension, disposal pro-rata, method lock, reconciliation.

[19.0.1.1.0]
------------

Added
~~~~~

- ``tax_event_ids`` board and the asset relation on ``account.asset.tax.event``.
- ``_tax_accounting_depreciation_for_period`` reads posted OCA depreciation lines for the DPPO reconciliation.
- Lifecycle-event buttons and events list on the asset *Tax Depreciation* page.

Renamed
~~~~~~~

- Module renamed from ``account_asset_tax_cssk_oca``.

[19.0.1.0.0]
------------

Added
~~~~~

- OCA/Community bridge: mixes ``account.asset.tax.mixin`` into OCA ``account_asset_management``.
- Adds ``asset_id`` to ``account.asset.tax.line`` and the ``tax_line_ids`` board.
- Reads the tax base from ``purchase_value`` and the in-service date from ``date_start``.
- *Tax Depreciation* page on the asset form.

[19.0.1.4.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak or Czech screen. The template and the catalogues now carry them,
  and the Slovak or Czech is written.

