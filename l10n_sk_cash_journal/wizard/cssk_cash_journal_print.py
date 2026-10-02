# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CsskCashJournalPrint(models.TransientModel):
    """Point the PDF button at the Slovak layout for a Slovak company."""

    _inherit = "cssk.cash.journal.print"

    def _cssk_pdf_report(self):
        self.ensure_one()
        if self.company_id.country_id.code == "SK":
            return self.env.ref(
                "l10n_sk_cash_journal.action_report_penazny_dennik")
        return super()._cssk_pdf_report()
