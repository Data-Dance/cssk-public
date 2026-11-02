# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Saved views of the interactive ledger.

A view keeps what the report shows - filters, comparison, the extra filter -
and its period, either fixed or relative to the day it is opened ("this
month" stays this month). It is personal or shared; each user may mark one
as their default, which the *Interactive Ledger* menu opens.
"""
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

PERIODS = [
    ("fixed", "Fixed dates"),
    ("this_month", "This month"),
    ("last_month", "Last month"),
    ("this_quarter", "This quarter"),
    ("last_quarter", "Last quarter"),
    ("this_year", "This fiscal year"),
    ("last_year", "Last fiscal year"),
]


class AccountFinancialReportInteractiveView(models.Model):
    _name = "account.financial.report.interactive.view"
    _description = "Saved interactive ledger view"
    _order = "name"

    name = fields.Char(required=True)
    user_id = fields.Many2one("res.users", string="Owner", required=True,
                              default=lambda s: s.env.user, ondelete="cascade")
    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company)
    shared = fields.Boolean(help="Visible to every user, editable by its owner only.")
    is_default = fields.Boolean(string="My default",
                                help="Opened by the Interactive Ledger menu for its owner.")
    title = fields.Char(help="Report title shown in the breadcrumb.")
    period = fields.Selection(PERIODS, required=True, default="fixed")
    data = fields.Json(required=True)
    comparison = fields.Json()

    @api.constrains("is_default", "user_id")
    def _check_one_default(self):
        for view in self.filtered("is_default"):
            if self.search_count([("user_id", "=", view.user_id.id), ("is_default", "=", True)]) > 1:
                raise ValidationError(self.env._("A user can have only one default view."))

    def _period_dates(self, today=None):
        """(date_from, date_to, fy_start) for a relative period."""
        self.ensure_one()
        today = today or fields.Date.context_today(self)
        company = self.company_id
        if self.period in ("this_month", "last_month"):
            start = today.replace(day=1) - relativedelta(months=1 if self.period == "last_month" else 0)
            end = start + relativedelta(months=1, days=-1)
        elif self.period in ("this_quarter", "last_quarter"):
            first = today.replace(day=1, month=((today.month - 1) // 3) * 3 + 1)
            start = first - relativedelta(months=3 if self.period == "last_quarter" else 0)
            end = start + relativedelta(months=3, days=-1)
        else:
            ref = today if self.period == "this_year" else (
                company.compute_fiscalyear_dates(today)["date_from"] - relativedelta(days=1))
            fy = company.compute_fiscalyear_dates(ref)
            start, end = fy["date_from"], fy["date_to"]
        return start, end, company.compute_fiscalyear_dates(start)["date_from"]

    def _resolved_data(self, today=None):
        self.ensure_one()
        data = dict(self.data or {})
        if self.period != "fixed":
            start, end, fy_start = self._period_dates(today)
            data.update(date_from=fields.Date.to_string(start), date_to=fields.Date.to_string(end),
                        fy_start_date=fields.Date.to_string(fy_start))
        return data

    def action_open(self):
        self.ensure_one()
        data = self._resolved_data()
        return {
            "type": "ir.actions.client",
            "tag": "afr_interactive_ledger",
            "name": "%s %s - %s" % (self.name, data.get("date_from"), data.get("date_to")),
            "params": {"data": data, "title": self.title or self.name,
                       "comparison": self.comparison or False, "view_id": self.id},
        }

    @api.model
    def action_open_default(self):
        """The menu: the user's default view, else a trial balance of the
        current fiscal year."""
        view = self.search([("user_id", "=", self.env.uid), ("is_default", "=", True)], limit=1)
        if view:
            return view.action_open()
        company = self.env.company
        fy = company.compute_fiscalyear_dates(fields.Date.context_today(self))
        data = {
            "company_id": company.id, "date_from": fields.Date.to_string(fy["date_from"]),
            "date_to": fields.Date.to_string(fields.Date.context_today(self)),
            "fy_start_date": fields.Date.to_string(fy["date_from"]),
            "only_posted_moves": True, "hide_account_at_0": True,
            "account_ids": [], "partner_ids": [], "journal_ids": [],
        }
        title = self.env._("Trial Balance")
        return {
            "type": "ir.actions.client", "tag": "afr_interactive_ledger",
            "name": "%s %s - %s" % (title, data["date_from"], data["date_to"]),
            "params": {"data": data, "title": title},
        }

    @api.model
    def save_view(self, values):
        """Create a view from the interactive ledger's current state."""
        vals = {
            "name": values["name"], "shared": bool(values.get("shared")),
            "is_default": bool(values.get("is_default")), "period": values.get("period") or "fixed",
            "title": values.get("title"), "data": values["data"],
            "comparison": values.get("comparison") or False,
            "company_id": values["data"].get("company_id") or self.env.company.id,
        }
        if vals["is_default"]:
            self.search([("user_id", "=", self.env.uid), ("is_default", "=", True)]).is_default = False
        return self.create(vals).id

    @api.model
    def list_views(self):
        return [{"id": v.id, "name": v.name, "shared": v.shared, "mine": v.user_id == self.env.user,
                 "is_default": v.is_default and v.user_id == self.env.user}
                for v in self.search([])]
