# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Keep 343 in step with the VAT return when VAT is declared in a later period.

``cssk_vat_deduction_date`` moves a document onto a later return — a deduction
claimed when the document arrives (CZ § 73, SK equivalent), a document entered
late, a § 42 correction declared when it reaches the customer. The return
follows it; the ledger does not. The tax stays on 343 in the period it was
BOOKED, so 343 for that period no longer equals the return, and the
difference only disappears in the period that declares it.

Optionally (company setting *VAT declared in a later period*), the tax is
moved off 343 on the booking date and back on the declaration date, by two
plain journal entries. They carry no taxes and no tax tags, so no return reads
them; they only move the balance, which is all the reconciliation needs.
"""

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    cssk_vat_deferral_origin_id = fields.Many2one(
        "account.move", string="VAT Deferral Of", copy=False, readonly=True,
        index="btree_not_null", ondelete="restrict",
        help="The document whose VAT this entry moves to or from the account "
        "for VAT declared in a later period.")
    cssk_vat_deferral_move_ids = fields.One2many(
        "account.move", "cssk_vat_deferral_origin_id",
        string="VAT Deferral Entries", readonly=True)
    cssk_vat_deferral_count = fields.Integer(
        compute="_compute_cssk_vat_deferral_count")

    def _compute_cssk_vat_deferral_count(self):
        for move in self:
            move.cssk_vat_deferral_count = len(move.cssk_vat_deferral_move_ids)

    def action_view_cssk_vat_deferral(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("VAT deferral entries"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("cssk_vat_deferral_origin_id", "=", self.id)],
            "context": {"create": False},
        }

    # ------------------------------------------------------------------
    def _cssk_vat_deferral_needed(self):
        """Whether this posted document's VAT sits in the wrong period.

        Only a LATER declaration month counts: that is what leaves 343 out of
        step with the return. Documents already carrying live deferral
        entries, and the deferral entries themselves, are never deferred.
        """
        self.ensure_one()
        declared = self.cssk_vat_deduction_date
        return bool(
            self.state == "posted"
            and self.company_id.cssk_vat_deferral_account_id
            and declared and self.date
            and (declared.year, declared.month) > (self.date.year, self.date.month)
            and not self.cssk_vat_deferral_origin_id
            and not self.cssk_vat_deferral_move_ids.filtered(
                lambda m: m.state != "cancel")
            and self._cssk_vat_deferral_source_lines()
        )

    def _cssk_vat_deferral_source_lines(self):
        """The tax lines standing on a VAT account: those the tax closing
        settles. A non-deductible leg posted onto the expense is not VAT on
        343 and stays where it is."""
        self.ensure_one()
        return self.line_ids.filtered(
            lambda line: line.tax_line_id
            and line.tax_repartition_line_id.use_in_tax_closing
            and not line.company_currency_id.is_zero(line.balance))

    def _cssk_vat_deferral_journal(self):
        self.ensure_one()
        journal = self.env["account.journal"].search([
            *self.env["account.journal"]._check_company_domain(self.company_id),
            ("type", "=", "general"),
        ], limit=1)
        if not journal:
            raise UserError(_(
                "%s: VAT declared in a later period is moved through a "
                "miscellaneous journal, and the company has none.",
                self.company_id.display_name))
        return journal

    def _cssk_vat_deferral_line_vals(self, sign):
        """Lines moving the tax off its account (sign 1) or back (sign -1)."""
        self.ensure_one()
        deferral = self.company_id.cssk_vat_deferral_account_id
        vals = []
        for line in self._cssk_vat_deferral_source_lines():
            common = {
                "partner_id": line.partner_id.id,
                "currency_id": line.currency_id.id,
                "name": _("VAT declared on %(date)s: %(label)s",
                          date=self.cssk_vat_deduction_date, label=line.name or ""),
            }
            # amount_currency is carried with the balance, never left at 0:
            # an explicit 0 next to a real balance zeroes the line.
            vals.append(dict(common, account_id=line.account_id.id,
                             balance=-sign * line.balance,
                             amount_currency=-sign * line.amount_currency))
            vals.append(dict(common, account_id=deferral.id,
                             balance=sign * line.balance,
                             amount_currency=sign * line.amount_currency))
        return vals

    def _cssk_create_vat_deferral(self):
        """Create the out-entry (booking date) and back-entry (declaration
        date). The back-entry posts itself on its date when that is still
        ahead."""
        today = fields.Date.context_today(self)
        created = self.browse()
        for move in self.filtered(lambda m: m._cssk_vat_deferral_needed()):
            journal = move._cssk_vat_deferral_journal()
            common = {
                "move_type": "entry",
                "journal_id": journal.id,
                "company_id": move.company_id.id,
                "cssk_vat_deferral_origin_id": move.id,
            }
            out = self.create(dict(
                common, date=move.date,
                ref=_("VAT of %s declared later", move.name),
                line_ids=[(0, 0, v) for v in move._cssk_vat_deferral_line_vals(1)]))
            back_date = move.cssk_vat_deduction_date
            back = self.create(dict(
                common, date=back_date,
                ref=_("VAT of %s declared now", move.name),
                auto_post="at_date" if back_date > today else "no",
                line_ids=[(0, 0, v) for v in move._cssk_vat_deferral_line_vals(-1)]))
            out.action_post()
            if back_date <= today:
                back.action_post()
            created |= out | back
        return created

    def _cssk_cancel_vat_deferral(self):
        """Withdraw the deferral entries of documents going back to draft or
        getting another declaration date. Cancelled rather than deleted: a
        posted entry with a number stays on record."""
        entries = self.cssk_vat_deferral_move_ids.filtered(
            lambda m: m.state != "cancel")
        if not entries:
            return
        posted = entries.filtered(lambda m: m.state == "posted")
        if posted:
            posted.button_draft()
        entries.button_cancel()

    # ------------------------------------------------------------------
    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted._cssk_create_vat_deferral()
        return posted

    def button_draft(self):
        origins = self.filtered("cssk_vat_deferral_move_ids")
        if origins:
            origins._cssk_cancel_vat_deferral()
        return super().button_draft()

    def button_cancel(self):
        origins = self.filtered("cssk_vat_deferral_move_ids")
        if origins:
            origins._cssk_cancel_vat_deferral()
        return super().button_cancel()

    def write(self, vals):
        if "cssk_vat_deduction_date" not in vals:
            return super().write(vals)
        # Only a real change rebuilds: rewriting the same date must not
        # cancel and renumber entries (or trip a lock date) for nothing.
        before = {m.id: m.cssk_vat_deduction_date for m in self}
        res = super().write(vals)
        redo = self.filtered(
            lambda m: m.state == "posted"
            and not m.cssk_vat_deferral_origin_id
            and m.cssk_vat_deduction_date != before.get(m.id))
        if redo:
            redo._cssk_cancel_vat_deferral()
            redo._cssk_create_vat_deferral()
        return res
