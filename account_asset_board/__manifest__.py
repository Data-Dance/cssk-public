# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Asset Depreciation Board",
    "version": "19.0.1.0.0",
    "summary": "Interactive depreciation schedule and pivot/graph analysis "
    "for OCA assets (Community)",
    "description": """
Asset Depreciation Board
========================

Gives Odoo Community an interactive asset depreciation board comparable to
Enterprise's *Depreciation Schedule* report, on top of the OCA
``account_asset_management`` framework (which only ships a static XLSX
report).

Two screens, both under *Accounting → Assets*:

* **Depreciation Analysis** — pivot/graph views on the depreciation lines
  (``account.asset.line``, type *Depreciation*): rows per asset, columns per
  year, measures *Amount* and *Remaining Value*, with Posted/Planned filters
  and asset / profile / year group-bys.

* **Depreciation Schedule** — a dynamic, EE-style schedule for a chosen date
  range (default: current fiscal year). One row per asset, grouped by asset
  profile with subtotals and a grand total, columns: acquisition value,
  opening depreciated value, depreciation in period, disposals in period,
  closing depreciated value and residual at end. Asset rows open the asset
  form; profile groups fold/unfold.

Disposal semantics: the *Disposals* column shows the residual value written
off by the OCA removal wizard (the ``remove``-type depreciation line) for
assets removed inside the period; if a removed asset has no such line, the
undepreciated remainder (depreciation base − closing) is used instead.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Accounting",
    "depends": ["account_asset_management", "web"],
    "data": [
        "views/account_asset_line_views.xml",
        "views/depreciation_schedule_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_asset_board/static/src/**/*",
        ],
    },
    "installable": True,
}
