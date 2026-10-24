from odoo import fields, models


class AbstractWizard(models.AbstractModel):
    _inherit = "account_financial_report_abstract_wizard"

    cssk_exclude_closing_journals = fields.Boolean(
        string="Exclude year-end closing and archive journals",
        default=lambda self: bool(
            self.env.company.l10n_cssk_closing_journal_ids),
        help="Leave out the journals the company names as year-end closing / "
        "reopening and migration archive journals (Accounting settings), as "
        "the statutory statements do. Without it a fiscal year's opening entry "
        "is reported as movement inside the year.")

    def _cssk_excluded_journals(self):
        """The journals this run leaves out — none unless the box is ticked."""
        self.ensure_one()
        if not self.cssk_exclude_closing_journals:
            return self.env["account.journal"]
        return self.company_id.l10n_cssk_closing_journal_ids

    def _cssk_included_journal_ids(self, chosen):
        """The journal filter to report with: an explicit choice as it is,
        otherwise every journal of the company but the excluded ones."""
        excluded = self._cssk_excluded_journals()
        if chosen or not excluded:
            return chosen.ids
        return (self.env["account.journal"].with_context(
            active_test=False).search(
            [("company_id", "=", self.company_id.id)]) - excluded).ids


class TrialBalanceWizard(models.TransientModel):
    _inherit = "trial.balance.report.wizard"

    def _prepare_report_trial_balance(self):
        res = super()._prepare_report_trial_balance()
        res["journal_ids"] = self._cssk_included_journal_ids(self.journal_ids)
        return res


class GeneralLedgerWizard(models.TransientModel):
    _inherit = "general.ledger.report.wizard"

    def _prepare_report_general_ledger(self):
        res = super()._prepare_report_general_ledger()
        res["journal_ids"] = self._cssk_included_journal_ids(
            self.account_journal_ids)
        return res


class OpenItemsWizard(models.TransientModel):
    _inherit = "open.items.report.wizard"

    def _prepare_report_open_items(self):
        res = super()._prepare_report_open_items()
        res["cssk_exclude_journal_ids"] = self._cssk_excluded_journals().ids
        return res


class AgedPartnerBalanceWizard(models.TransientModel):
    _inherit = "aged.partner.balance.report.wizard"

    def _prepare_report_aged_partner_balance(self):
        res = super()._prepare_report_aged_partner_balance()
        res["cssk_exclude_journal_ids"] = self._cssk_excluded_journals().ids
        return res
