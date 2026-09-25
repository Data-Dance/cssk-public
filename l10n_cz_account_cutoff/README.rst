==================================================
CZ Deferrals — default accounts (časové rozlišení)
==================================================

Thin glue between the Czech chart of accounts (``l10n_cz``) and the OCA cut-off /
deferral engine (``account_cutoff_start_end_dates``). It pre-fills the company's
default cut-off / deferral accounts with the Czech *časové rozlišení* accounts so
accruals and deferrals work out of the box.

Mapping:

* prepaid expense  → **381** Náklady příštích období
* deferred revenue → **384** Výnosy příštích období
* accrued expense  → **383** Výdaje příštích období
* accrued revenue  → **385** Příjmy příštích období

Licensed **AGPL-3** because it depends on the AGPL OCA cut-off engine.

Features
========

* Sets the four Czech *časové rozlišení* default accounts (381 / 383 / 384 / 385)
  on the company so the OCA cut-off wizards have correct defaults.
* Picks a default cut-off journal if none is set.
* ``post_init_hook`` backfills the defaults on CZ companies that already had the
  ``l10n_cz`` chart loaded before this module was installed.

Usage
=====

Install on a company using the Czech chart; the deferral default accounts are set
automatically. Then use the standard OCA cut-off / deferral wizards (from
``account_cutoff_start_end_dates``) to recognise prepaid expenses and deferred
revenue — they will post against the Czech 381/383/384/385 accounts.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
