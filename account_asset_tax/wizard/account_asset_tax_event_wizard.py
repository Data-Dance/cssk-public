from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountAssetTaxEventWizard(models.TransientModel):
    """Record a lifecycle event (improvement / suspension / disposal) on an asset.

    Launched from the asset form; the asset is taken from the context
    (``active_id``) so the wizard needs no relational field to ``account.asset``
    and stays in the core module.
    """

    _name = "account.asset.tax.event.wizard"
    _description = "Tax Depreciation Event Wizard"

    event_type = fields.Selection(
        [
            ("improvement", "Technical Improvement (TZ)"),
            ("suspension", "Suspension / Interruption"),
            ("disposal", "Disposal"),
        ],
        required=True,
        default="improvement",
    )
    date = fields.Date(required=True)
    amount = fields.Monetary(string="Improvement Amount")
    duration_years = fields.Integer(string="Years to Suspend", default=1)
    note = fields.Char()
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    asset_display = fields.Char(string="Asset", readonly=True)

    def _asset(self):
        if self.env.context.get("active_model") != "account.asset":
            raise UserError(_("Open this from an asset."))
        active_id = self.env.context.get("active_id")
        if not active_id:
            raise UserError(_("No asset in context."))
        return self.env["account.asset"].browse(active_id)

    def _compute_currency_id(self):
        for wiz in self:
            asset = self.env["account.asset"].browse(
                self.env.context.get("active_id"))
            wiz.currency_id = asset.company_id.currency_id if asset else self.env.company.currency_id

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "account.asset":
            asset = self.env["account.asset"].browse(self.env.context.get("active_id"))
            if asset:
                res["asset_display"] = asset.display_name
        if self.env.context.get("default_event_type"):
            res["event_type"] = self.env.context["default_event_type"]
        return res

    def action_apply(self):
        self.ensure_one()
        asset = self._asset()
        if not asset.tax_depreciation_enabled:
            raise UserError(_("This asset does not track tax depreciation."))
        if self.event_type == "improvement" and self.amount <= 0:
            raise UserError(_("Enter the technical-improvement amount."))
        asset._add_tax_event(
            self.event_type, self.date,
            amount=self.amount or 0.0,
            duration_years=max(self.duration_years or 1, 1),
            note=self.note,
        )
        return {"type": "ir.actions.act_window_close"}
