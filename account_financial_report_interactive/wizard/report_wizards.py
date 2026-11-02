# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import fields, models


def _jsonable(data):
    """The wizard data as the client action can carry it (dates as strings)."""
    return {
        key: fields.Date.to_string(value) if isinstance(value, date) else value
        for key, value in data.items()
    }


class GeneralLedgerReportWizard(models.TransientModel):
    _inherit = "general.ledger.report.wizard"

    def button_interactive(self):
        self.ensure_one()
        return self._interactive_action(
            self._prepare_report_general_ledger(), self.env._("General Ledger"))

    def _interactive_action(self, data, title):
        return {
            "type": "ir.actions.client",
            "tag": "afr_interactive_ledger",
            "name": "%s %s - %s" % (title, self.date_from, self.date_to),
            "params": {"data": _jsonable(data), "title": title},
        }


class TrialBalanceReportWizard(models.TransientModel):
    _inherit = "trial.balance.report.wizard"

    def button_interactive(self):
        self.ensure_one()
        return GeneralLedgerReportWizard._interactive_action(
            self, self._prepare_report_trial_balance(), self.env._("Trial Balance"))
