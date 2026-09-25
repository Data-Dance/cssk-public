from odoo import _, fields, models


class AccountAssetTaxCloseYear(models.TransientModel):
    """Freeze the tax-depreciation board up to a filed fiscal year.

    Once a tax period is filed, its tax-depreciation figures must not move on a
    later recompute. This marks every board line up to and including the chosen
    fiscal year as filed (``posted=True``) across all tax-tracked assets of the
    company, and locks their method.
    """

    _name = "account.asset.tax.close.year"
    _description = "Close Tax Depreciation Year"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
    )
    fiscal_year = fields.Integer(required=True)

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        today = fields.Date.context_today(self)
        res.setdefault("fiscal_year", today.year - 1)
        return res

    def action_close(self):
        self.ensure_one()
        assets = self.env["account.asset"].search([
            ("tax_depreciation_enabled", "=", True),
            ("company_id", "=", self.company_id.id),
        ])
        frozen_assets = 0
        frozen_lines = 0
        for asset in assets:
            lines = asset.tax_line_ids.filtered(
                lambda l: l.fiscal_year <= self.fiscal_year and not l.posted)
            if lines:
                lines.write({"posted": True})
                frozen_lines += len(lines)
                frozen_assets += 1
                if not asset.tax_method_locked:
                    asset.tax_method_locked = True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Tax year %s filed", self.fiscal_year),
                "message": _("%(l)d board line(s) frozen on %(a)d asset(s).",
                             l=frozen_lines, a=frozen_assets),
                "sticky": False,
            },
        }
