===================================================
SK Deferrals — default accounts (časové rozlíšenie)
===================================================

Thin glue between the Slovak chart of accounts (``l10n_sk``) and the OCA cut-off /
deferral engine (``account_cutoff_start_end_dates``). It maps the company's
default cut-off accounts to the Slovak *časové rozlíšenie* accounts so the
deferral feature works out of the box.

Account mapping:

* prepaid expense  → **381** Náklady budúcich období
* deferred revenue → **384** Výnosy budúcich období
* accrued expense  → **383** Výdavky budúcich období
* accrued revenue  → **385** Príjmy budúcich období

New companies receive the mapping when the SK chart loads (via the chart
template); existing SK companies get it on install (post-init hook). The cut-off
journal is set to a general journal if one exists.

It is licensed **AGPL-3** because it depends on the AGPL OCA cut-off engine.

Features
========

* Pre-fills the OCA cut-off / deferral default accounts with the Slovak
  381/383/384/385 accounts.
* Sets the cut-off journal to an existing general journal.
* Applies to new SK companies via the chart template and to existing SK
  companies via a post-init hook.

Usage
=====

Install the module on a database using the Slovak chart of accounts. The deferral
default accounts are then pre-set, so *Accounting ▸ Cut-offs* (časové rozlíšenie)
works with no further configuration. The mapping can be reviewed/overridden in
*Settings ▸ Accounting ▸ Cut-offs*.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
