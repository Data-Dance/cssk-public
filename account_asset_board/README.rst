========================
Asset Depreciation Board
========================

Interactive asset depreciation board for Odoo Community, on top of the OCA
``account_asset_management`` framework — a Community counterpart to
Enterprise's *Depreciation Schedule* report.

Features
========

Both screens live under *Accounting → Assets* (group *Accountant*,
``account.group_account_user``).

Depreciation Analysis
    Pivot and graph views on the depreciation lines
    (``account.asset.line``, type *Depreciation*): rows per asset,
    columns per year, measures *Amount* and *Remaining Value*.
    Filters *Posted* / *Planned* (with / without an accounting entry) and
    group-bys asset / asset profile / year.

Depreciation Schedule (dynamic)
    An OWL client action rendering the schedule for a chosen date range
    (default: the current fiscal year of the active company).  One row per
    asset, grouped by asset profile with fold/unfold, group subtotals and a
    grand total.  Columns: acquisition value, opening depreciated value,
    depreciation in period, disposals / decreases, closing depreciated
    value, residual at end.  Clicking an asset row opens the asset form.

Disposal semantics
==================

The *Disposals / Decreases* column shows, for assets removed inside the
period, the residual value written off by the OCA removal wizard (the
``remove``-type depreciation line).  If a removed asset carries no such
line, the undepreciated remainder (depreciation base − closing depreciated
value) is used as an approximation.  The end residual of a disposed asset
is therefore zero.

All figures come from the depreciation board (posted **and** planned lines;
``init_entry`` lines count as prior depreciation), so the schedule matches
the plan the OCA module maintains.

Security
========

The schedule is computed by ``account.asset.get_schedule()`` running as the
current user — ACLs and record rules fully apply; only assets of the active
company are reported.

License
=======

AGPL-3 — see the ``LICENSE`` file.

Author: Data Dance s.r.o. — https://www.datadance.eu
