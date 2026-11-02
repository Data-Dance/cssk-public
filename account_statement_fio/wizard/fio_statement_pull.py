# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Manual pull / backfill."""

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.account_fio_base.utils.client import FioError

from ..models.account_journal import HISTORY_LIMIT_DAYS


class FioStatementPull(models.TransientModel):
    _name = "fio.statement.pull"
    _description = "Pull Fio Bank Statements"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Bank Journal",
        required=True,
        domain=[("type", "=", "bank")],
        default=lambda self: self.env.context.get("active_id"),
    )
    mode = fields.Selection(
        selection=[
            ("movements", "Movements in a date range"),
            ("official", "Official numbered statements"),
        ],
        default="movements",
        required=True,
    )
    date_from = fields.Date(
        default=lambda self: fields.Date.context_today(self) - timedelta(days=7),
    )
    date_to = fields.Date(default=fields.Date.context_today)
    statement_year = fields.Integer(
        default=lambda self: fields.Date.context_today(self).year,
    )
    statement_from = fields.Integer(string="First statement number", default=1)
    statement_to = fields.Integer(string="Last statement number", default=1)
    needs_history_unlock = fields.Boolean(compute="_compute_needs_history_unlock")
    history_unlocked = fields.Boolean(
        string="History unlocked in internet banking",
        help="Tick this only after clicking the padlock on this token in Fio "
             "internet banking. The unlock lasts ten minutes.",
    )
    call_count = fields.Integer(compute="_compute_call_count")

    @api.depends("date_from", "mode")
    def _compute_needs_history_unlock(self):
        limit = fields.Date.context_today(self) - timedelta(days=HISTORY_LIMIT_DAYS)
        for wizard in self:
            wizard.needs_history_unlock = bool(
                wizard.mode == "movements"
                and wizard.date_from
                and wizard.date_from < limit
            )

    @api.depends("mode", "date_from", "date_to", "statement_from", "statement_to",
                 "journal_id")
    def _compute_call_count(self):
        """Tell the user up front how long this will take.

        Fio allows one call per token every 30 seconds, so a year of movements
        is a twelve-chunk, six-minute operation. Better said before than
        discovered.
        """
        for wizard in self:
            if wizard.mode == "official":
                wizard.call_count = max(
                    0, (wizard.statement_to or 0) - (wizard.statement_from or 0) + 1,
                )
            elif wizard.date_from and wizard.date_to:
                wizard.call_count = len(
                    wizard.journal_id._fio_chunks(wizard.date_from, wizard.date_to)
                ) if wizard.journal_id else 0
            else:
                wizard.call_count = 0

    def action_pull(self):
        self.ensure_one()
        account = self.journal_id
        try:
            if self.mode == "official":
                lines = self._pull_official(account)
            else:
                if not self.date_from or not self.date_to:
                    raise UserError(_("Give both dates."))
                if self.date_from > self.date_to:
                    raise UserError(_("The first date is after the last one."))
                account._fio_check_history_window(
                    self.date_from, self.history_unlocked,
                )
                lines = account._fio_pull_movements(self.date_from, self.date_to)
        except FioError as exception:
            raise UserError(account._fio_explain(exception)) from None

        account.message_post(body=_(
            "Manual pull: %(count)s new transaction(s).", count=len(lines),
        ))
        return self._show(lines)

    def _pull_official(self, account):
        if self.statement_from > self.statement_to:
            raise UserError(_("The first statement number is after the last."))
        lines = self.env["account.bank.statement.line"]
        for number in range(self.statement_from, self.statement_to + 1):
            raw = account._fio_call(
                "by_id", self.statement_year, number, account.fio_download_format,
            )
            parsed = account._fio_parse(raw)
            if not parsed.transactions:
                continue
            statement_vals = {"name": "%s/%s" % (number, self.statement_year)}
            account._fio_add_balances(statement_vals, parsed.info)
            lines |= account._fio_import_lines(parsed.transactions, statement_vals)
        return lines

    def _show(self, lines):
        if not lines:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "warning",
                    "message": _("Nothing new — every movement Fio returned was "
                                 "already in Odoo."),
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Imported transactions"),
            "res_model": "account.bank.statement.line",
            "view_mode": "list,form",
            "domain": [("id", "in", lines.ids)],
        }
