from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    amount_tax = fields.Monetary(
        string="Tax",
        compute="_compute_amount_tax",
        currency_field="currency_id",
    )

    @api.depends("price_subtotal", "price_total")
    def _compute_amount_tax(self):
        for line in self:
            line.amount_tax = line.price_total - line.price_subtotal


class AccountMove(models.Model):
    _inherit = "account.move"

    is_advance_invoice_tax_document = fields.Boolean(
        compute="_compute_is_advance_invoice_tax_document",
    )

    @api.depends("move_type", "invoice_line_ids.sale_line_ids.order_id.is_advance_invoice")
    def _compute_is_advance_invoice_tax_document(self):
        for move in self:
            if move.move_type != "out_invoice":
                move.is_advance_invoice_tax_document = False
                continue
            move.is_advance_invoice_tax_document = bool(
                move.invoice_line_ids.sale_line_ids.order_id.filtered(
                    lambda o: o.is_advance_invoice
                )
            )

    @api.constrains('journal_id', 'move_type')
    def _check_journal_move_type(self):
        if not self.env.context.get("allow_advance_invoice_journal_mismatch"):
            return super()._check_journal_move_type()

        allowed_moves = self.filtered(
            lambda move: move.is_sale_document(include_receipts=True)
            and move.journal_id == move.company_id.advance_invoice_journal_id
        )
        remaining_moves = self - allowed_moves
        if remaining_moves:
            return super(AccountMove, remaining_moves)._check_journal_move_type()
        return

    def action_open_link_advance_invoices_wizard(self):
        self.ensure_one()
        if self.move_type != "out_invoice":
            raise UserError(_("This action is only available for customer invoices."))
        if self.state != "draft":
            raise UserError(_("You can only link advance invoices on a draft invoice."))

        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale_order_advance_invoice.action_account_move_link_advance_invoice_wizard"
        )
        action_context = dict(self.env.context)
        action_context.update({
            "active_model": "account.move",
            "active_id": self.id,
        })
        action["context"] = action_context
        return action

    def _sync_advance_tracking_for_sale_orders(self):
        for move in self.filtered(lambda m: m.move_type == "out_invoice"):
            advance_orders = move.invoice_line_ids.sale_line_ids.order_id.filtered(
                lambda o: o.is_advance_invoice
            )
            for advance in advance_orders:
                parent = advance.advance_invoice_parent_order_id
                if parent:
                    parent._sync_advance_tracking_line_from_advance(advance)

    def _reconcile_advance_clearing_lines(self):
        """Match the tax document's clearing-account leg (the rewritten
        receivable, e.g. 324001) against the advance payments' legs on the
        same account, so the clearing account nets to zero per advance."""
        for move in self.filtered(
            lambda m: m.is_advance_invoice_tax_document and m.state == "posted"
        ):
            clearing = move.company_id.advance_received_account_id
            if not clearing or not clearing.reconcile:
                continue
            doc_lines = move.line_ids.filtered(
                lambda l: l.account_id == clearing and not l.reconciled
            )
            if not doc_lines:
                continue
            orders = move.invoice_line_ids.sale_line_ids.order_id.filtered(
                "is_advance_invoice"
            )
            pay_lines = orders.transaction_ids.payment_id.move_id.line_ids.filtered(
                lambda l: l.account_id == clearing
                and not l.reconciled
                and l.parent_state == "posted"
            )
            if pay_lines:
                (doc_lines | pay_lines).reconcile()

    def action_post(self):
        res = super().action_post()
        self._sync_advance_tracking_for_sale_orders()
        self._reconcile_advance_clearing_lines()
        return res

    def button_draft(self):
        res = super().button_draft()
        self._sync_advance_tracking_for_sale_orders()
        return res

    def button_cancel(self):
        res = super().button_cancel()
        self._sync_advance_tracking_for_sale_orders()
        return res
