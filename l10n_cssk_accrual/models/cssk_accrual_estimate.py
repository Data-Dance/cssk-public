# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class CSSKAccrualEstimate(models.Model):
    _name = "cssk.accrual.estimate"
    _description = "Estimated Accrual (dohadná položka)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(default="/", copy=False, readonly=True, index=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, tracking=True
    )
    accrual_type = fields.Selection(
        [
            ("payable", "Estimated payable"),
            ("receivable", "Estimated receivable"),
        ],
        default="payable",
        required=True,
        tracking=True,
        help="Estimated payable: a cost not yet invoiced (Dr expense / Cr "
        "accrual). Estimated receivable: revenue not yet invoiced (Dr accrual "
        "/ Cr income). Which account takes it is chosen below.",
    )
    date = fields.Date(
        required=True, default=fields.Date.context_today, tracking=True,
        help="Date the estimate is booked (usually the period end).",
    )
    amount = fields.Monetary(required=True, tracking=True)
    label = fields.Char(
        string="Description", required=True,
        help="What is being accrued (printed on the journal items).",
    )
    journal_id = fields.Many2one(
        "account.journal", required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    )
    accrual_account_id = fields.Many2one(
        "account.account", string="Accrual Account", required=True,
        domain="[('company_ids', 'in', company_id)]",
        help="CZ: 389 Dohadné účty pasivní / 388 Dohadné účty aktivní. "
        "SK, which has no dohadné účty: 326 Nevyfaktúrované dodávky when the "
        "amount is known from a contract or delivery note (§ 50 ods. 6 "
        "opatrenia 740/2002; an uncertain amount is a provision on 323 "
        "instead), and an unbilled receivable on a separate analytic account "
        "of the receivable it belongs to (§ 48 ods. 3). Must allow "
        "reconciliation.",
    )
    counterpart_account_id = fields.Many2one(
        "account.account", string="Counterpart Account", required=True,
        domain="[('company_ids', 'in', company_id)]",
        help="Expense account (for an estimated payable) or income account "
        "(for an estimated receivable).",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("settled", "Settled"),
            ("cancelled", "Cancelled"),
        ],
        default="draft", tracking=True, index=True,
    )
    move_id = fields.Many2one(
        "account.move", string="Estimate Entry", readonly=True, copy=False
    )
    reversal_move_id = fields.Many2one(
        "account.move", string="True-up / Reversal Entry", readonly=True,
        copy=False,
    )
    invoice_id = fields.Many2one(
        "account.move", string="Actual Invoice", copy=False, tracking=True,
        domain="[('move_type', 'in', ('in_invoice', 'in_refund', 'out_invoice',"
        " 'out_refund')), ('partner_id', '=', partner_id), "
        "('state', '=', 'posted'), ('company_id', '=', company_id)]",
        help="The real invoice, once received. Settling reverses the estimate "
        "at this invoice's date so only the difference stays in the period.",
    )
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("cssk.accrual.estimate")
                    or "/"
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    def _build_estimate_move(self):
        self.ensure_one()
        if self.accrual_type == "payable":
            debit_acc, credit_acc = self.counterpart_account_id, self.accrual_account_id
        else:
            debit_acc, credit_acc = self.accrual_account_id, self.counterpart_account_id
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.journal_id.id,
                "date": self.date,
                "company_id": self.company_id.id,
                "ref": _("Accrual estimate %s", self.name),
                "line_ids": [
                    Command.create(
                        {
                            "name": self.label,
                            "account_id": debit_acc.id,
                            "partner_id": self.partner_id.id,
                            "debit": self.amount,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": self.label,
                            "account_id": credit_acc.id,
                            "partner_id": self.partner_id.id,
                            "debit": 0.0,
                            "credit": self.amount,
                        }
                    ),
                ],
            }
        )

    def _check_accrual_lines_unreconciled(self):
        """`_reverse_moves(cancel=True)` silently unreconciles the original
        move's lines first — if someone already matched the accrual line
        (e.g. manually against the invoice), that matching would be thrown
        away without warning. Refuse with a clear message instead."""
        self.ensure_one()
        reconciled = self.move_id.line_ids.filtered(
            lambda l: l.account_id == self.accrual_account_id
            and (l.matched_debit_ids or l.matched_credit_ids)
        )
        if reconciled:
            raise UserError(
                _("The accrual line of %(name)s on account %(account)s is "
                  "already reconciled (moves: %(moves)s). Unreconcile it "
                  "first if you really want to reverse this estimate.",
                  name=self.name,
                  account=self.accrual_account_id.display_name,
                  moves=", ".join(
                      (reconciled.matched_debit_ids.debit_move_id
                       | reconciled.matched_credit_ids.credit_move_id)
                      .mapped("move_id.name")
                  ))
            )

    def _check_reversal_date_unlocked(self, date):
        """Pre-check the lock dates so the user gets an error naming the
        accrual instead of a generic journal-entry message."""
        self.ensure_one()
        violations = self.company_id._get_lock_date_violations(
            date, fiscalyear=True, sale=False, purchase=False,
            tax=False, hard=True,
        )
        if violations:
            raise UserError(
                _("Cannot reverse accrual %(name)s on %(date)s: that date "
                  "falls in a locked period (%(locks)s). Adjust the lock "
                  "date or use a later reversal date.",
                  name=self.name,
                  date=format_date(self.env, date),
                  locks=self.company_id._format_lock_dates(violations))
            )

    def _reverse_estimate(self, date, ref):
        self.ensure_one()
        self._check_accrual_lines_unreconciled()
        self._check_reversal_date_unlocked(date)
        # cancel=True reverses the estimate and reconciles it with the reversal
        # on the (reconcilable) accrual account, clearing the dohadný účet.
        return self.move_id._reverse_moves([{"date": date, "ref": ref}], cancel=True)

    # ------------------------------------------------------------------
    def action_post(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Only a draft estimate can be posted."))
            if rec.amount <= 0:
                raise UserError(_("The estimate amount must be positive."))
            if not rec.accrual_account_id.reconcile:
                raise UserError(
                    _("The accrual account %(account)s of %(name)s must "
                      "allow reconciliation, otherwise the estimate cannot "
                      "be cleared against its reversal when settled.",
                      account=rec.accrual_account_id.display_name,
                      name=rec.name)
                )
            move = rec._build_estimate_move()
            move.action_post()
            rec.move_id = move
            rec.state = "posted"
        return True

    def action_settle(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("Only a posted estimate can be settled."))
        if not self.invoice_id:
            raise UserError(
                _("Select the actual invoice to settle this estimate against.")
            )
        # Reverse at the invoice date, but never BEFORE the estimate itself:
        # an invoice dated inside the accrued period (or earlier) must not
        # produce a reversal that precedes the estimate entry.
        invoice_date = self.invoice_id.invoice_date or self.invoice_id.date
        self.reversal_move_id = self._reverse_estimate(
            max(invoice_date, self.date),
            _("True-up of %(est)s vs %(inv)s",
              est=self.name, inv=self.invoice_id.name),
        )
        self.state = "settled"
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state not in ("draft", "posted"):
                raise UserError(
                    _("Only a draft or posted estimate can be cancelled "
                      "(%(name)s is %(state)s).",
                      name=rec.name, state=rec.state)
                )
            if rec.state == "posted" and rec.move_id:
                rec.reversal_move_id = rec._reverse_estimate(
                    fields.Date.context_today(rec),
                    _("Cancellation of %s", rec.name),
                )
            rec.state = "cancelled"
        return True

    def _estimate_entry_reversed(self):
        """True when the estimate entry is cancelled out by its reversal."""
        self.ensure_one()
        return bool(
            self.reversal_move_id
            and self.reversal_move_id.state == "posted"
            and self.reversal_move_id.reversed_entry_id == self.move_id
        )

    def action_reset_to_draft(self):
        """Bring a cancelled estimate back to draft, to correct and post again.

        Cancelling a posted estimate does not unpost its entry, it reverses it,
        and both entries stay posted: they are the books' record that the
        estimate existed and was withdrawn. So the estimate lets go of them
        rather than requiring them to disappear, which they never would.
        Posting again books a new entry.
        """
        for rec in self:
            if rec.state != "cancelled":
                raise UserError(
                    _("Only a cancelled estimate can be reset to draft "
                      "(%(name)s is %(state)s).",
                      name=rec.name, state=rec.state)
                )
            if (rec.move_id and rec.move_id.state == "posted"
                    and not rec._estimate_entry_reversed()):
                raise UserError(
                    _("Cancel the estimate first — it has a posted entry.")
                )
            if rec.move_id:
                rec.message_post(
                    body=_("Reset to draft. The estimate entry %(move)s and "
                           "its reversal %(reversal)s stay in the books; "
                           "posting again books a new entry.",
                           move=rec.move_id.name,
                           reversal=rec.reversal_move_id.name or "-")
                )
            rec.write({
                "state": "draft",
                "move_id": False,
                "reversal_move_id": False,
            })
        return True
