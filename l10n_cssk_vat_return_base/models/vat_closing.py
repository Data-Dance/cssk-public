# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""VAT closing entry on Community.

At the end of a VAT period the 343 sub-accounts the taxes posted to (input and
output, per rate) are cleared into one settlement account, which is then left
holding the period's own tax liability or excess deduction - the figure on the
filed return. Enterprise does this with its tax closing; Community has the
data (``use_in_tax_closing`` on the repartition lines) and no action, so this
module provides one, driven by the return rather than by a date range:

* **The return decides what is closed.** Its own period selection
  (``_cssk_period_move_ids``: tax point for output, deduction date for input)
  picks the documents, so the entry cannot disagree with the return about
  which documents belong to the period.
* **Each closed tax line remembers its closing entry**, so a line is closed
  once. A later return over the same period - an amended or corrective one -
  closes exactly the lines that were not closed yet.
* **The entry must agree with the return.** The net it moves is compared with
  the return's own tax minus excess deduction (less whatever earlier returns of
  the same period already closed). A difference within the company tolerance
  is rounding - the return is rounded per line, to whole crowns in CZ - and
  goes to the rounding accounts; a larger one means the ledger and the return
  disagree, and no entry is made.
* **Draft only.** The accountant reviews and posts it.

The § 79 carry-forward is deliberately not in the entry: an excess carried
forward is already the balance the previous closing left on the settlement
account.
"""
from collections import defaultdict

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cssk_vat_settlement_account_id = fields.Many2one(
        "account.account", string="VAT settlement account",
        check_company=True,
        help="Account the VAT closing clears the 343 sub-accounts into "
             "(343000 when empty). It then holds the period's own tax "
             "liability or excess deduction.")
    l10n_cssk_vat_rounding_loss_account_id = fields.Many2one(
        "account.account", string="VAT rounding loss account",
        check_company=True,
        help="Rounding of the return against the ledger, when the return "
             "pays more (548000 when empty).")
    l10n_cssk_vat_rounding_gain_account_id = fields.Many2one(
        "account.account", string="VAT rounding gain account",
        check_company=True,
        help="Rounding of the return against the ledger, when the return "
             "pays less (648000 when empty).")
    l10n_cssk_vat_closing_tolerance = fields.Monetary(
        string="VAT closing tolerance", currency_field="currency_id", default=10.0,
        help="Largest difference between the ledger and the return the VAT "
             "closing books as rounding. A larger one stops the closing.")

    def _cssk_vat_closing_account(self, field_name, code):
        self.ensure_one()
        account = self[field_name]
        if not account:
            account = self.env["account.account"].with_company(self).search([
                *self.env["account.account"]._check_company_domain(self),
                ("code", "=", code),
            ], limit=1)
        return account


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Domains repeated: Odoo drops a string domain on a related field.
    l10n_cssk_vat_settlement_account_id = fields.Many2one(
        related="company_id.l10n_cssk_vat_settlement_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]")
    l10n_cssk_vat_rounding_loss_account_id = fields.Many2one(
        related="company_id.l10n_cssk_vat_rounding_loss_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]")
    l10n_cssk_vat_rounding_gain_account_id = fields.Many2one(
        related="company_id.l10n_cssk_vat_rounding_gain_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]")
    l10n_cssk_vat_closing_tolerance = fields.Monetary(
        related="company_id.l10n_cssk_vat_closing_tolerance", readonly=False,
        currency_field="currency_id")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_cssk_vat_closing_move_id = fields.Many2one(
        "account.move", string="VAT closing entry", copy=False, readonly=True,
        index="btree_not_null", ondelete="set null", check_company=True,
        help="The VAT closing entry that cleared this tax line.")


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cssk_vat_closing_return_id = fields.Many2one(
        "cssk.vat.return", string="VAT closing of", copy=False, readonly=True,
        index="btree_not_null", check_company=True)
    # What the closing moved to the settlement account (positive = payable),
    # frozen when it is made: a later return of the same period subtracts it,
    # and must not re-derive it from the entry's lines, which a changed
    # settlement account or an added line would make wrong.
    l10n_cssk_vat_closing_amount = fields.Monetary(
        string="VAT closed", copy=False, readonly=True, currency_field="company_currency_id")


class CsskVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    l10n_cssk_closing_move_ids = fields.One2many(
        "account.move", "l10n_cssk_vat_closing_return_id", string="VAT closing entries")
    l10n_cssk_closing_count = fields.Integer(compute="_compute_l10n_cssk_closing_count")

    @api.depends("l10n_cssk_closing_move_ids")
    def _compute_l10n_cssk_closing_count(self):
        for ret in self:
            ret.l10n_cssk_closing_count = len(ret.l10n_cssk_closing_move_ids)

    # ------------------------------------------------------------------
    def _cssk_vat_closing_lines(self):
        """Tax lines of this return's documents that no live closing has
        cleared yet."""
        self.ensure_one()
        move_ids = self._cssk_period_move_ids(self.company_id, self.date_from, self.date_to)
        if not move_ids:
            return self.env["account.move.line"]
        lines = self.env["account.move.line"].search([
            ("move_id", "in", move_ids),
            ("company_id", "=", self.company_id.id),
            ("parent_state", "=", "posted"),
            ("tax_repartition_line_id.use_in_tax_closing", "=", True),
        ])
        return lines.filtered(
            lambda l: not l.l10n_cssk_vat_closing_move_id
            or l.l10n_cssk_vat_closing_move_id.state == "cancel")

    def _cssk_vat_period_returns(self):
        """This return and every other return of the same period chain."""
        self.ensure_one()
        root = self
        while root.original_return_id:
            root = root.original_return_id
        chain = root
        todo = root
        while todo:
            todo = todo.amendment_ids - chain
            chain |= todo
        return chain

    def _cssk_vat_return_net(self):
        """Own tax liability minus excess deduction, before any § 79 carry
        (positive = payable). Zero when the version names no such lines."""
        self.ensure_one()
        own_code = self.version_id.own_tax_line_code
        excess_code = self.version_id.excess_line_code
        if not own_code or not excess_code:
            raise UserError(_(
                "The return version %(version)s does not name its own-tax and "
                "excess-deduction lines, so the VAT closing has nothing to agree "
                "with.", version=self.version_id.display_name))
        vals = {line.code: line.value for line in self.line_ids}
        return vals.get(own_code, 0.0) - vals.get(excess_code, 0.0)

    def _cssk_vat_already_closed(self):
        """Net (positive = payable) already moved to the settlement account by
        live closings of the other returns of this period."""
        self.ensure_one()
        others = self._cssk_vat_period_returns() - self
        closings = others.l10n_cssk_closing_move_ids.filtered(lambda m: m.state != "cancel")
        return sum(closings.mapped("l10n_cssk_vat_closing_amount"))

    def action_cssk_vat_closing(self):
        self.ensure_one()
        if self.state not in ("exported", "submitted"):
            raise UserError(_("Export or submit the return before closing its VAT."))
        company = self.company_id
        curr = company.currency_id
        settlement = company._cssk_vat_closing_account("l10n_cssk_vat_settlement_account_id", "343000")
        if not settlement:
            raise UserError(_("Set the VAT settlement account in the accounting settings."))
        lines = self._cssk_vat_closing_lines()
        if not lines:
            raise UserError(_("Every tax line of this return's period is already closed."))

        by_account = defaultdict(float)
        for line in lines:
            by_account[line.account_id] += line.balance
        ledger_net = -curr.round(sum(by_account.values()))       # positive = payable
        expected = curr.round(self._cssk_vat_return_net() - self._cssk_vat_already_closed())
        rounding = curr.round(expected - ledger_net)
        if curr.compare_amounts(abs(rounding), company.l10n_cssk_vat_closing_tolerance) > 0:
            raise UserError(_(
                "The ledger and the return disagree by %(diff)s: the tax lines of "
                "the period net to %(ledger)s, the return to %(expected)s. Check "
                "the unreconciled rows of the return before closing.",
                diff=curr.format(rounding), ledger=curr.format(ledger_net),
                expected=curr.format(expected)))

        name = _("VAT closing %s", self.name or "")
        line_vals = []
        for account, balance in sorted(by_account.items(), key=lambda kv: kv[0].code or ""):
            balance = curr.round(balance)
            if curr.is_zero(balance):
                continue
            line_vals.append({
                "account_id": account.id, "name": name,
                "debit": -balance if balance < 0 else 0.0,
                "credit": balance if balance > 0 else 0.0,
            })
        if not curr.is_zero(rounding):
            account = company._cssk_vat_closing_account(
                "l10n_cssk_vat_rounding_loss_account_id" if rounding > 0
                else "l10n_cssk_vat_rounding_gain_account_id",
                "548000" if rounding > 0 else "648000")
            if not account:
                raise UserError(_("Set the VAT rounding accounts in the accounting settings."))
            line_vals.append({
                "account_id": account.id, "name": _("%s - rounding", name),
                "debit": rounding if rounding > 0 else 0.0,
                "credit": -rounding if rounding < 0 else 0.0,
            })
        # The settlement line takes whatever balances the entry: -expected.
        line_vals.append({
            "account_id": settlement.id, "name": name,
            "debit": -expected if expected < 0 else 0.0,
            "credit": expected if expected > 0 else 0.0,
        })
        journal = self.env["account.journal"].search([
            *self.env["account.journal"]._check_company_domain(company),
            ("type", "=", "general"),
        ], limit=1)
        if not journal:
            raise UserError(_("No miscellaneous journal to post the VAT closing in."))
        move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": journal.id,
            "company_id": company.id,
            "date": self.date_to,
            "ref": name,
            "l10n_cssk_vat_closing_return_id": self.id,
            "l10n_cssk_vat_closing_amount": expected,
            "line_ids": [Command.create(v) for v in line_vals],
        })
        lines.l10n_cssk_vat_closing_move_id = move
        return self.action_cssk_open_vat_closing()

    def action_cssk_open_vat_closing(self):
        self.ensure_one()
        moves = self.l10n_cssk_closing_move_ids
        action = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "name": _("VAT closing"),
        }
        if len(moves) == 1:
            action.update(view_mode="form", res_id=moves.id)
        else:
            action.update(view_mode="list,form", domain=[("id", "in", moves.ids)])
        return action
