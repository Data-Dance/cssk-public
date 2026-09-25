from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    advance_deduction_order_id = fields.Many2one(
        "purchase.order",
        string="Deducted Advance",
        copy=False,
        index="btree_not_null",
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    advance_purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Received Advance Invoice",
        copy=False,
        domain="[('is_advance_invoice', '=', True)]",
        index="btree_not_null",
    )
    is_advance_purchase_tax_document = fields.Boolean(
        compute="_compute_is_advance_purchase_tax_document",
    )

    @api.depends("move_type", "advance_purchase_order_id")
    def _compute_is_advance_purchase_tax_document(self):
        for move in self:
            move.is_advance_purchase_tax_document = (
                move.move_type == "in_invoice"
                and bool(move.advance_purchase_order_id)
            )

    def _reconcile_purchase_advance_clearing_lines(self):
        """Match the tax document's clearing-account leg (the rewritten
        payable, e.g. 314001) against the advance payments' legs on the
        same account, so the clearing account nets to zero per advance."""
        for move in self.filtered(
            lambda m: m.is_advance_purchase_tax_document
            and m.state == "posted"
        ):
            clearing = move.company_id.advance_paid_clearing_account_id
            if not clearing or not clearing.reconcile:
                continue
            doc_lines = move.line_ids.filtered(
                lambda line: line.account_id == clearing
                and not line.reconciled
            )
            if not doc_lines:
                continue
            order = move.advance_purchase_order_id
            pay_lines = order._advance_effective_payments().move_id.line_ids.filtered(
                lambda line: line.account_id == clearing
                and not line.reconciled
                and line.parent_state == "posted"
            )
            if pay_lines:
                (doc_lines | pay_lines).reconcile()

    def action_post(self):
        result = super().action_post()
        self._reconcile_purchase_advance_clearing_lines()
        return result

    def action_open_link_purchase_advance_wizard(self):
        self.ensure_one()
        if self.move_type != "in_invoice":
            raise UserError(
                _("This action is only available for vendor bills.")
            )
        if self.state != "draft":
            raise UserError(
                _("Advance invoices can only be linked on a draft bill.")
            )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "purchase_order_advance_invoice."
            "action_account_move_link_purchase_advance_wizard"
        )
        action["context"] = {
            **self.env.context,
            "active_model": "account.move",
            "active_id": self.id,
        }
        return action
