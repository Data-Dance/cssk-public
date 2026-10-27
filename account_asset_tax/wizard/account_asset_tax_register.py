# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetTaxRegister(models.TransientModel):
    _name = "account.asset.tax.register"
    _description = "Tax Depreciation Register"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    fiscal_year = fields.Integer(
        string="Tax period (year)",
        required=True,
        default=lambda self: fields.Date.context_today(self).year,
    )

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            "account_asset_tax.action_report_asset_tax_register"
        ).report_action(self)

    def get_register(self):
        """Return the tax-depreciation register for ``fiscal_year``, grouped by
        odpisová skupina (tax depreciation group):

            [{group, lines: [{asset, input, opening, amount, accumulated,
              closing, method}...], input, amount, closing}, ...]

        plus the grand totals are summed by the caller. Input price and opening
        residual are derived from the board line (input = residual + cumulative,
        opening = residual + amount) so the figures are correct even when the
        explicit tax entry value was left at zero.
        """
        self.ensure_one()
        Line = self.env["account.asset.tax.line"]
        if "asset_id" not in Line._fields:
            return [], {}
        lines = Line.search(
            [
                ("company_id", "=", self.company_id.id),
                ("fiscal_year", "=", self.fiscal_year),
            ]
        )
        method_labels = dict(
            self.env["account.asset.tax.mixin"]
            ._fields["tax_method"]
            ._description_selection(self.env)
        )
        # One register row per asset and year. A §30a board carries one line
        # per month: fold them, so the year shows once — opening from the
        # first month, closing from the last, the year's charge summed and the
        # book figures (which sit on the year's last line only) once.
        by_asset = {}
        for line in lines:
            if line.asset_id:
                by_asset.setdefault(line.asset_id, []).append(line)
        groups = {}
        for asset, asset_lines in by_asset.items():
            asset_lines.sort(key=lambda l: (l.date_from, l.year_index, l.id))
            first, last = asset_lines[0], asset_lines[-1]
            amount = sum(l.amount for l in asset_lines)
            book = sum(l.book_amount for l in asset_lines)
            tax_class = asset.tax_class_id
            grp = groups.setdefault(
                tax_class.id,
                {"group": tax_class, "lines": [], "input": 0.0, "amount": 0.0,
                 "closing": 0.0, "book": 0.0, "difference": 0.0},
            )
            input_price = last.residual + last.amount_cumulative
            grp["lines"].append(
                {
                    "asset": asset.display_name,
                    "input": input_price,
                    "opening": first.residual + first.amount,
                    "amount": amount,
                    "book": book,
                    "difference": book - amount,
                    "accumulated": last.amount_cumulative,
                    "closing": last.residual,
                    "method": method_labels.get(asset.tax_method, asset.tax_method or ""),
                }
            )
            grp["input"] += input_price
            grp["amount"] += amount
            grp["closing"] += last.residual
            grp["book"] += book
            grp["difference"] += book - amount
        register = sorted(groups.values(), key=lambda g: g["group"].code or "")
        totals = {
            "input": sum(g["input"] for g in register),
            "amount": sum(g["amount"] for g in register),
            "closing": sum(g["closing"] for g in register),
            "book": sum(g["book"] for g in register),
            "difference": sum(g["difference"] for g in register),
        }
        return register, totals
