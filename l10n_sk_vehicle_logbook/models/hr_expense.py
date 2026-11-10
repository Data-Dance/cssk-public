# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    l10n_sk_travel_order_id = fields.Many2one(
        "l10n.sk.travel.order", string="Travel order", index="btree_not_null",
        ondelete="restrict", copy=False,
        help="The cost is settled with this travel order and approved with it.",
    )
    l10n_sk_travel_allowance = fields.Boolean(
        string="Travel allowances", readonly=True, copy=False,
        help="Meal allowance, pocket money and vehicle reimbursement of a "
             "travel order settlement.",
    )

    @api.constrains("l10n_sk_travel_order_id", "employee_id")
    def _check_l10n_sk_travel_order(self):
        for expense in self.filtered("l10n_sk_travel_order_id"):
            if expense.employee_id != expense.l10n_sk_travel_order_id.employee_id:
                raise ValidationError(_(
                    "%(expense)s belongs to the travel order %(order)s of "
                    "another employee.",
                    expense=expense.name, order=expense.l10n_sk_travel_order_id.name,
                ))

    def action_submit(self):
        if not self.env.su:
            linked = self.filtered("l10n_sk_travel_order_id")
            if linked:
                raise UserError(_(
                    "%(expenses)s belong to a travel order; they are approved "
                    "with its settlement, not on their own.",
                    expenses=", ".join(linked.mapped("name")),
                ))
        return super().action_submit()

    def _check_l10n_sk_travel_order_open(self):
        """A cost joins a travel order only while its settlement is being
        prepared, so nothing slips in after the approver has looked."""
        if self.env.su:
            return
        for expense in self.filtered("l10n_sk_travel_order_id"):
            order = expense.l10n_sk_travel_order_id
            if order.state not in ("draft", "approved"):
                raise UserError(_(
                    "%(order)s no longer takes new costs.", order=order.name,
                ))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            if any(vals.get("l10n_sk_travel_allowance") for vals in vals_list):
                raise UserError(_("Travel allowances come only from a travel order settlement."))
        expenses = super().create(vals_list)
        expenses._check_l10n_sk_travel_order_open()
        return expenses

    def write(self, vals):
        if "l10n_sk_travel_allowance" in vals and not self.env.su:
            raise UserError(_("Travel allowances come only from a travel order settlement."))
        # A settlement under approval is what the approver sees: its costs
        # stay as submitted until it is approved or sent back.
        if not self.env.su:
            locked = self.filtered(
                lambda e: e.state == "draft"
                and e.l10n_sk_travel_order_id.state in ("submitted", "reported")
            )
            if locked:
                raise UserError(_(
                    "%(expenses)s are part of a settlement waiting for approval.",
                    expenses=", ".join(locked.mapped("name")),
                ))
        res = super().write(vals)
        if "l10n_sk_travel_order_id" in vals:
            self._check_l10n_sk_travel_order_open()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_l10n_sk_travel_settlement(self):
        for expense in self:
            if expense.l10n_sk_travel_order_id.state in ("submitted", "reported", "settled"):
                raise UserError(_(
                    "%(expense)s is part of the settlement of %(order)s.",
                    expense=expense.name, order=expense.l10n_sk_travel_order_id.name,
                ))
