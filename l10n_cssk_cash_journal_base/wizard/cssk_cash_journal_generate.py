# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class CsskCashJournalGenerate(models.TransientModel):
    """Rebuild the denník for a period.

    Deliberately a manual action rather than a hook on payment or a nightly
    cron. A statutory book is written when the accountant says the period is
    ready, and a row that appeared on its own between two closings would be
    noticed only at filing time. A cron can call ``_cssk_regenerate`` where a
    customer wants one; nothing here prevents it.
    """

    _name = "cssk.cash.journal.generate"
    _description = "Generate the Cash Journal (peňažný denník)"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    @api.model
    def default_get(self, fields_list):
        """Default to the current year, which is the period a denník is read in."""
        values = super().default_get(fields_list)
        today = fields.Date.context_today(self)
        values.setdefault("date_from", today.replace(month=1, day=1))
        values.setdefault("date_to", today)
        return values

    def action_generate(self):
        self.ensure_one()
        rows = self.env["cssk.cash.journal.line"]._cssk_regenerate(
            self.company_id, self.date_from, self.date_to)
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_cssk_cash_journal_base.action_cssk_cash_journal_line")
        action["domain"] = [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]
        review = rows.filtered("needs_review")
        if review:
            action["context"] = dict(
                self.env.context,
                cssk_review_notice=_(
                    "%(count)s of %(total)s rows need review.",
                    count=len(review), total=len(rows),
                ),
            )
        return action
