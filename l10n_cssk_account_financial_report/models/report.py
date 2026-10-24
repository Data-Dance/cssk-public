from odoo import api, models


class AbstractReport(models.AbstractModel):
    """Open items and the aged partner balance have no journal filter; their
    move lines come from these two domains, which leave out the journals the
    wizard excluded (passed down in the context by the report itself)."""

    _inherit = "report.account_financial_report.abstract_report"

    def _cssk_journal_exclusion(self):
        excluded = self.env.context.get("cssk_exclude_journal_ids")
        return [("journal_id", "not in", excluded)] if excluded else []

    @api.model
    def _get_move_lines_domain_not_reconciled(self, *args, **kwargs):
        return (super()._get_move_lines_domain_not_reconciled(*args, **kwargs)
                + self._cssk_journal_exclusion())

    @api.model
    def _get_new_move_lines_domain(self, *args, **kwargs):
        return (super()._get_new_move_lines_domain(*args, **kwargs)
                + self._cssk_journal_exclusion())


class OpenItemsReport(models.AbstractModel):
    _inherit = "report.account_financial_report.open_items"

    def _get_report_values(self, docids, data):
        return super(OpenItemsReport, self.with_context(
            cssk_exclude_journal_ids=data.get("cssk_exclude_journal_ids"),
        ))._get_report_values(docids, data)


class AgedPartnerBalanceReport(models.AbstractModel):
    _inherit = "report.account_financial_report.aged_partner_balance"

    def _get_report_values(self, docids, data):
        return super(AgedPartnerBalanceReport, self.with_context(
            cssk_exclude_journal_ids=data.get("cssk_exclude_journal_ids"),
        ))._get_report_values(docids, data)
