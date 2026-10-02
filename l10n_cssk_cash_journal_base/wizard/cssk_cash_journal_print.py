# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CsskCashJournalPrint(models.TransientModel):
    """Print the denník for a period, as PDF or as a spreadsheet.

    Both, because the two are read differently: the PDF is the book as the
    statute lays it out and what goes in the file, the spreadsheet is what an
    accountant actually works in — she can filter it, pivot it and tie it to her
    own workings. The accountant who reviewed this asked for both by name.

    The PDF layout is national, so the wizard asks the country module for it
    through ``_cssk_pdf_report``. The spreadsheet is country-neutral: the same
    rows, with the categories as they are named in that country's catalogue.
    """

    _name = "cssk.cash.journal.print"
    _description = "Print the Cash Journal"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    output = fields.Selection(
        [("pdf", "PDF"), ("xlsx", "Spreadsheet")],
        required=True, default="pdf",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        today = fields.Date.context_today(self)
        values.setdefault("date_from", today.replace(month=1, day=1))
        values.setdefault("date_to", today)
        return values

    def _cssk_pdf_report(self):
        """The national PDF report for this company, or an empty recordset.

        Overridden by the country modules; the base has no layout of its own
        because a denník's columns are a national matter.
        """
        self.ensure_one()
        return self.env["ir.actions.report"]

    def action_print(self):
        self.ensure_one()
        if self.output == "xlsx":
            return self.env.ref(
                "l10n_cssk_cash_journal_base.action_report_cash_journal_xlsx"
            ).report_action(self)
        report = self._cssk_pdf_report()
        if not report:
            raise UserError(_(
                "There is no cash journal layout for %s. Install the country "
                "module, or print the spreadsheet instead.",
                self.company_id.country_id.display_name or self.company_id.name,
            ))
        return report.report_action(self, data={
            "company_id": self.company_id.id,
            "date_from": fields.Date.to_string(self.date_from),
            "date_to": fields.Date.to_string(self.date_to),
        })

    def _cssk_rows(self):
        """The denník rows of the period, in book order."""
        self.ensure_one()
        return self.env["cssk.cash.journal.line"].search([
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ])
