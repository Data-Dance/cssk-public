from odoo import api, fields, models


class AbstractWizard(models.AbstractModel):
    _inherit = "account_financial_report_abstract_wizard"

    cssk_exclude_closing_journals = fields.Boolean(
        string="Exclude year-end closing and archive journals",
        compute="_compute_cssk_exclude_closing_journals", store=True,
        readonly=False,
        help="Leave out the journals the company names as year-end closing / "
        "reopening and migration archive journals (Accounting settings), as "
        "the statutory statements do. Without it a fiscal year's opening entry "
        "is reported as movement inside the year.")

    @api.depends("company_id")
    def _compute_cssk_exclude_closing_journals(self):
        """Ticked when the company CHOSEN IN THE WIZARD names closing
        journals — the same company whose journals are then left out. It
        used to follow the company the user happened to be working in, so in
        a multi-company database the box could start unticked for a company
        that has them, or ticked for one that has none."""
        for wizard in self:
            company = wizard.company_id or self.env.company
            wizard.cssk_exclude_closing_journals = bool(
                company.l10n_cssk_closing_journal_ids)

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
