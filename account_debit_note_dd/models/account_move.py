from collections import defaultdict
from contextlib import nullcontext

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Command
from odoo.tools import format_date, formatLang, get_lang


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param bool soft: if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :returns: the Model<account.move> documents that have been posted
        """
        if not self.env.su and not self.env.user.has_group(
            "account.group_account_invoice"
        ):
            raise AccessError(_("You don't have the access rights to post an invoice."))

        # Avoid marking is_manually_modified as True when posting an invoice
        self = self.with_context(skip_is_manually_modified=True)  # noqa: PLW0642

        validation_msgs = set()

        for invoice in self.filtered(
            lambda move: move.is_invoice(include_receipts=True)
        ):
            if (
                invoice.quick_edit_mode
                and invoice.quick_edit_total_amount
                and invoice.currency_id.compare_amounts(
                    invoice.quick_edit_total_amount, invoice.amount_total
                )
                != 0
            ):
                validation_msgs.add(
                    _(
                        "The current total is %(current_total)s but the expected total is %(expected_total)s. In order to post the invoice/bill, "
                        "you can adjust its lines or the expected Total (tax inc.).",
                        current_total=formatLang(
                            self.env,
                            invoice.amount_total,
                            currency_obj=invoice.currency_id,
                        ),
                        expected_total=formatLang(
                            self.env,
                            invoice.quick_edit_total_amount,
                            currency_obj=invoice.currency_id,
                        ),
                    )
                )
            if invoice.partner_bank_id and not invoice.partner_bank_id.active:
                validation_msgs.add(
                    _(
                        "The recipient bank account linked to this invoice is archived.\n"
                        "So you cannot confirm the invoice."
                    )
                )

            if not invoice.partner_id:
                if invoice.is_sale_document():
                    validation_msgs.add(
                        _(
                            "The 'Customer' field is required to validate the invoice.\n"
                            "You probably don't want to explain to your auditor that you invoiced an invisible man :)"
                        )
                    )
                elif invoice.is_purchase_document():
                    validation_msgs.add(
                        _(
                            "The field 'Vendor' is required, please complete it to validate the Vendor Bill."
                        )
                    )

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly (if the user didnt' change the rate manually)
            if not invoice.invoice_date:
                if invoice.is_sale_document(include_receipts=True):
                    is_manual_rate = (
                        invoice.invoice_currency_rate
                        != invoice._get_expected_currency_rate_at(
                            invoice.create_date.date()
                        )
                    )
                    with (
                        self.env.protecting(
                            [self._fields["invoice_currency_rate"]], invoice
                        )
                        if is_manual_rate
                        else nullcontext()
                    ):
                        invoice.invoice_date = fields.Date.context_today(self)
                elif invoice.is_purchase_document(include_receipts=True):
                    validation_msgs.add(
                        _("The Bill/Refund date is required to validate this document.")
                    )

        for move in self:
            if move.state in ["posted", "cancel"]:
                validation_msgs.add(
                    _(
                        "The entry %(name)s (id %(id)s) must be in draft.",
                        name=move.name,
                        id=move.id,
                    )
                )
            if not move.line_ids.filtered(
                lambda line: line.display_type
                not in ("line_section", "line_subsection", "line_note")
            ):
                validation_msgs.add(_("Even magicians can't post nothing!"))
            if (
                not soft
                and move.auto_post != "no"
                and move.date > fields.Date.context_today(self)
            ):
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                validation_msgs.add(
                    _(
                        "This move is configured to be auto-posted on %(date)s",
                        date=date_msg,
                    )
                )
            if not move.journal_id.active:
                validation_msgs.add(
                    _(
                        "You cannot post an entry in an archived journal (%(journal)s)",
                        journal=move.journal_id.display_name,
                    )
                )
            if move.display_inactive_currency_warning:
                validation_msgs.add(
                    _(
                        "You cannot validate a document with an inactive currency: %s",
                        move.currency_id.name,
                    )
                )

            if move.line_ids.account_id.filtered(
                lambda account: not account.active
            ) and not self.env.context.get("skip_account_deprecation_check"):
                validation_msgs.add(
                    _(
                        "A line of this move is using a archived account, you cannot post it."
                    )
                )

        if validation_msgs:
            msg = "\n".join([line for line in validation_msgs])
            raise UserError(msg)

        if soft:
            future_moves = self.filtered(
                lambda move: move.date > fields.Date.context_today(self)
            )
            for move in future_moves:
                if move.auto_post == "no":
                    move.auto_post = "at_date"
                msg = _(
                    "This move will be posted at the accounting date: %(date)s",
                    date=format_date(self.env, move.date),
                )
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self

        for move in to_post:
            affects_tax_report = move._affect_tax_report()
            lock_dates = move._get_violated_lock_dates(move.date, affects_tax_report)
            if lock_dates:
                move.date = move._get_accounting_date(
                    move._get_accounting_date_source(),
                    affects_tax_report,
                    lock_dates=lock_dates,
                )

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        to_post.line_ids._create_analytic_lines()

        # Trigger copying for recurring invoices
        to_post.filtered(
            lambda m: m.auto_post not in ("no", "at_date")
        )._copy_recurring_entries()

        for invoice in to_post:
            # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
            # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
            wrong_lines = invoice.is_invoice() and invoice.line_ids.filtered(
                lambda aml: aml.partner_id != invoice.commercial_partner_id
                and aml.display_type
                not in ("line_section", "line_subsection", "line_note")
            )
            if wrong_lines:
                wrong_lines.write({"partner_id": invoice.commercial_partner_id.id})

        # reconcile if state is in draft and move has reversal_entry_id set
        draft_reverse_moves = to_post.filtered(
            lambda move: move.reversed_entry_id
            and move.reversed_entry_id.state == "posted"
        )

        # deal with the eventually related draft moves to the ones we want to post
        partials_to_unlink = self.env["account.partial.reconcile"]

        for aml in self.line_ids:
            for partials, counterpart_field in [
                (aml.matched_debit_ids, "debit_move_id"),
                (aml.matched_credit_ids, "credit_move_id"),
            ]:
                for partial in partials:
                    counterpart_move = partial[counterpart_field].move_id
                    if (
                        counterpart_move.state == "posted"
                        or counterpart_move in to_post
                    ):
                        if partial.exchange_move_id:
                            to_post |= partial.exchange_move_id
                            # If the draft invoice changed since it was reconciled, in a way that would affect the exchange diff,
                            # any existing reconcilation and draft exchange move would be deleted already (to force the user to
                            # re-do the reconciliation).
                            # This is ensured by the the checks in env['account.move.line'].write():
                            #     see env[account.move.line]._get_lock_date_protected_fields()['reconciliation']

                        if (
                            partial._get_draft_caba_move_vals()
                            != partial.draft_caba_move_vals
                        ):
                            # draft invoice changed since it was reconciled, the cash basis entry isn't correct anymore
                            # and the user has to re-do the reconciliation. Existing draft cash basis move will be unlinked
                            partials_to_unlink |= partial

                        elif move.tax_cash_basis_created_move_ids:
                            to_post |= move.tax_cash_basis_created_move_ids.filtered(
                                lambda m: m.tax_cash_basis_rec_id == partial
                            )
                        elif counterpart_move.tax_cash_basis_created_move_ids:
                            to_post |= counterpart_move.tax_cash_basis_created_move_ids.filtered(
                                lambda m: m.tax_cash_basis_rec_id == partial
                            )

        if partials_to_unlink:
            partials_to_unlink.unlink()

        to_post.write(
            {
                "state": "posted",
                "posted_before": True,
            }
        )

        if not self.env.user.has_group(
            "account.group_partial_purchase_deductibility"
        ) and self.filtered(
            lambda move: move.move_type == "in_invoice"
            and move.invoice_line_ids.filtered(lambda l: l.deductible_amount != 100)
        ):
            self.env.user.sudo().group_ids = [
                Command.link(
                    self.env.ref("account.group_partial_purchase_deductibility").id
                )
            ]

        # Add the move number to the non_deductible lines for easier auditing
        if non_deductible_lines := self.line_ids.filtered(
            lambda line: (
                line.display_type
                in ("non_deductible_product_total", "non_deductible_tax")
            )
        ):
            for line in non_deductible_lines:
                line.name = (
                    _("%s - private part", line.move_id.name)
                    if line.display_type == "non_deductible_product_total"
                    else _("%s - private part (taxes)", line.move_id.name)
                )

        draft_reverse_moves.reversed_entry_id._reconcile_reversed_moves(
            draft_reverse_moves, self.env.context.get("move_reverse_cancel", False)
        )
        to_post.line_ids._reconcile_marked()

        customer_count, supplier_count = defaultdict(int), defaultdict(int)
        for invoice in to_post:
            if invoice.is_sale_document():
                customer_count[invoice.partner_id] += 1
            elif invoice.is_purchase_document():
                supplier_count[invoice.partner_id] += 1
            elif invoice.move_type == "entry":
                sale_amls = invoice.line_ids.filtered(
                    lambda line: line.partner_id
                    and line.account_id.account_type == "asset_receivable"
                )
                for partner in sale_amls.mapped("partner_id"):
                    customer_count[partner] += 1
                purchase_amls = invoice.line_ids.filtered(
                    lambda line: line.partner_id
                    and line.account_id.account_type == "liability_payable"
                )
                for partner in purchase_amls.mapped("partner_id"):
                    supplier_count[partner] += 1
        for partner, count in customer_count.items():
            (partner | partner.commercial_partner_id)._increase_rank(
                "customer_rank", count
            )
        for partner, count in supplier_count.items():
            (partner | partner.commercial_partner_id)._increase_rank(
                "supplier_rank", count
            )

        # Trigger action for paid invoices if amount is zero
        to_post.filtered(
            lambda m: m.is_invoice(include_receipts=True)
            and m.currency_id.is_zero(m.amount_total)
        )._invoice_paid_hook()

        return to_post
