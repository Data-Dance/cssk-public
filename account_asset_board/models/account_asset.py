# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    @api.model
    def get_schedule(self, date_from=False, date_to=False):
        """Return the depreciation schedule for the period as grouped JSON.

        Called by the ``account_asset_board.depreciation_schedule`` client
        action.  Runs as the current user (no sudo), so ACLs and record
        rules apply, and only assets of ``self.env.company`` are reported.

        Scope: assets in state open / close / removed whose life intersects
        the window, i.e. ``date_start <= date_to`` and, for removed assets,
        ``date_remove >= date_from``.  Fully depreciated but still-held
        assets (state ``close``) therefore keep showing with a zero period
        movement.

        Per asset (all amounts from the depreciation board — posted and
        planned lines alike; ``init_entry`` lines count as prior
        depreciation):

        * opening  = sum of ``depreciate`` lines with line_date < date_from
        * period   = sum of ``depreciate`` lines with
          date_from <= line_date <= date_to
        * disposal = sum of ``remove`` lines in the window: the residual
          value written off by the OCA removal wizard.  Fallback for
          removed assets without a remove line (e.g. removal forced without
          journal entry): the undepreciated remainder
          (depreciation_base - closing).
        * closing  = opening + period
        * residual = depreciation_base - closing - disposal
          (zero for assets disposed of in the period)
        """
        company = self.env.company
        today = fields.Date.context_today(self)
        if not date_from or not date_to:
            fy = company.compute_fiscalyear_dates(today)
            date_from = date_from or fy["date_from"]
            date_to = date_to or fy["date_to"]
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        currency = company.currency_id

        assets = self.search(
            [
                ("state", "in", ("open", "close", "removed")),
                ("company_id", "=", company.id),
                ("date_start", "<=", date_to),
            ]
        ).filtered(
            lambda a: a.state != "removed"
            or not a.date_remove
            or a.date_remove >= date_from
        )

        line_model = self.env["account.asset.line"]

        def _sums(domain):
            res = line_model._read_group(
                domain + [("asset_id", "in", assets.ids)],
                groupby=["asset_id"],
                aggregates=["amount:sum"],
            )
            return {asset.id: amount for asset, amount in res}

        opening_by_asset = _sums(
            [("type", "=", "depreciate"), ("line_date", "<", date_from)]
        )
        period_by_asset = _sums(
            [
                ("type", "=", "depreciate"),
                ("line_date", ">=", date_from),
                ("line_date", "<=", date_to),
            ]
        )
        disposal_by_asset = _sums(
            [
                ("type", "=", "remove"),
                ("line_date", ">=", date_from),
                ("line_date", "<=", date_to),
            ]
        )

        keys = (
            "acquisition_value",
            "opening_depreciated",
            "period_depreciation",
            "disposal",
            "closing_depreciated",
            "residual",
        )
        groups = {}
        totals = dict.fromkeys(keys, 0.0)
        for asset in assets:
            opening = currency.round(opening_by_asset.get(asset.id) or 0.0)
            period = currency.round(period_by_asset.get(asset.id) or 0.0)
            closing = currency.round(opening + period)
            disposal = currency.round(disposal_by_asset.get(asset.id) or 0.0)
            if (
                not disposal
                and asset.state == "removed"
                and asset.date_remove
                and date_from <= asset.date_remove <= date_to
            ):
                disposal = currency.round(asset.depreciation_base - closing)
            residual = currency.round(asset.depreciation_base - closing - disposal)
            row = {
                "id": asset.id,
                "name": asset.name,
                "code": asset.code or "",
                "date_start": fields.Date.to_string(asset.date_start),
                "state": asset.state,
                "acquisition_value": asset.purchase_value,
                "opening_depreciated": opening,
                "period_depreciation": period,
                "disposal": disposal,
                "closing_depreciated": closing,
                "residual": residual,
            }
            profile = asset.profile_id
            group = groups.setdefault(
                profile.id,
                {
                    "profile_id": profile.id,
                    "profile": profile.display_name,
                    "assets": [],
                    "totals": dict.fromkeys(keys, 0.0),
                },
            )
            group["assets"].append(row)
            for key in keys:
                group["totals"][key] += row[key]
                totals[key] += row[key]

        group_list = sorted(groups.values(), key=lambda g: (g["profile"] or "", g["profile_id"]))
        for group in group_list:
            group["assets"].sort(key=lambda r: (r["date_start"], r["code"], r["name"]))
            group["totals"] = {k: currency.round(v) for k, v in group["totals"].items()}
        return {
            "date_from": fields.Date.to_string(date_from),
            "date_to": fields.Date.to_string(date_to),
            "company_name": company.name,
            "currency_id": currency.id,
            "groups": group_list,
            "totals": {k: currency.round(v) for k, v in totals.items()},
        }
