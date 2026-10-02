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

    @api.depends(
        "move_id.invoice_line_ids.price_unit",
        "move_id.invoice_line_ids.quantity",
        "move_id.invoice_line_ids.discount",
        "move_id.invoice_line_ids.tax_ids",
        "move_id.invoice_line_ids.sale_line_ids",
    )
    def _compute_currency_rate(self):
        super()._compute_currency_rate()
        for move in self.move_id:
            rates = move._advance_currency_rates()
            for line in self.filtered(lambda l, m=move: l.move_id == m):
                if line in rates:
                    line.currency_rate = rates[line]


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

    def _advance_currency_rates(self):
        """Rates for the lines of a foreign-currency invoice that deducts advances.

        An advance's tax document declared its VAT in the company currency at
        the rate of ITS date (§ 38 ZDPH), and a received advance is a
        non-monetary item carried at that rate. So the deduction gives back
        exactly what the tax document declared, and the part of the supply the
        advance paid for is valued at the same rate: only the remainder is
        converted at the invoice's own rate. A fully covered supply then nets to
        zero VAT and leaves nothing on the receivable in either currency.

        Coverage is matched by the taxes the lines carry, as the deductions are
        split per rate (``sale.order._advance_deduction_tax_groups``). Supply
        lines at taxes no deduction carries keep the invoice's rate.

        Returns ``{line: rate}`` for the lines to revalue only.
        """
        self.ensure_one()
        rates = {}
        if (self.move_type != "out_invoice"
                or not self.currency_id
                or self.currency_id == self.company_currency_id
                or not self.invoice_currency_rate):
            return rates
        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == "product")
        if self.state != "draft":
            # currency_rate is not stored and the balances are: a posted
            # invoice reports the rate each line was booked at, whatever has
            # happened to an advance's tax document since.
            company_currency = self.company_currency_id
            return {
                line: abs(line.amount_currency / line.balance)
                for line in lines
                if line.balance and company_currency.compare_amounts(
                    line.balance,
                    company_currency.round(line.amount_currency / self.invoice_currency_rate))
            }

        def net(line):
            # Net of tax, but not price_subtotal: the rate is read while the
            # invoice is being built, before the subtotals are, and a rate read
            # too early is the one its balance and taxes keep.
            price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            return line.tax_ids.compute_all(
                price, currency=self.currency_id, quantity=line.quantity,
                product=line.product_id, partner=self.partner_id,
            )["total_excluded"]

        covered = {}
        deductions = self.env["account.move.line"]
        for line in lines:
            advance = line.sale_line_ids.filtered("is_advance_tracking").advance_source_order_id
            if len(advance) != 1:
                continue
            rate = advance._advance_tax_document_rate(self.currency_id)
            if not rate:
                continue
            rates[line] = rate
            deductions |= line
            # A deduction is a negative line: its amount is what it covers.
            entry = covered.setdefault(frozenset(line.tax_ids.ids), [0.0, 0.0])
            entry[0] -= net(line)
            entry[1] -= net(line) / rate
        for key, (amount, value) in covered.items():
            supply = (lines - deductions).filtered(
                lambda l, k=key: frozenset(l.tax_ids.ids) == k)
            total = sum(net(line) for line in supply)
            if total <= 0.0 or amount <= 0.0:
                continue
            if amount >= total:
                target = value * total / amount
            else:
                target = value + (total - amount) / self.invoice_currency_rate
            for line in supply:
                rates[line] = total / target
        return rates

    def _get_product_base_line_currency_rate(self, product_line):
        # Taxes follow the rate of their own base line, so the VAT a deduction
        # gives back is converted at the advance's rate like its base.
        if self.move_type == "out_invoice" and product_line.currency_rate:
            return product_line.currency_rate
        return super()._get_product_base_line_currency_rate(product_line)

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
