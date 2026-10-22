# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from markupsafe import Markup

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = "hr.expense"

    cssk_receipt_id = fields.Many2one(
        "cssk.receipt", string="Captured receipt", readonly=True, index=True,
        ondelete="set null", copy=False)
    # Related fields are read as superuser, which is the point: the employee who
    # uploaded the photograph has no access to cssk.receipt (an accounting
    # record), but must be able to see what became of it. Before these, a
    # failed reading left an "Untitled Expense, 0.00" and nothing else.
    cssk_receipt_state = fields.Selection(
        related="cssk_receipt_id.state", string="Receipt reading")
    cssk_receipt_reason = fields.Text(
        related="cssk_receipt_id.review_reason", string="Why")

    # ------------------------------------------------------------------
    # upload
    # ------------------------------------------------------------------
    @api.model
    def create_expense_from_attachments(self, attachment_ids=None, view_type="list"):
        """Also capture a receipt per uploaded image, and say how it went.

        Odoo's own flow makes one blank "Untitled Expense" per image and leaves
        the reading to the Enterprise OCR. This keeps that and hands each image
        to the capture providers: the QR code is read off the photograph and
        looked up, or the photograph is read by the AI reader. A receipt that
        reads cleanly fills its expense — one expense, whatever its VAT rates —
        and every outcome, failure included, is posted on the expense and
        announced to the uploader.

        The receipt is handled with superuser rights: the uploader is usually an
        employee without access to accounting records. What they see is the
        status and the reason, through the related fields above.
        """
        result = super().create_expense_from_attachments(
            attachment_ids=attachment_ids, view_type=view_type)
        if not self.env.company.cssk_receipt_capture_on_expense_upload:
            return result
        outcomes = {"captured": 0, "review": 0, "error": 0, "new": 0}
        for expense in self._cssk_uploaded_expenses(result, attachment_ids):
            attachment = self.env["ir.attachment"].sudo().search(
                [("res_model", "=", "hr.expense"), ("res_id", "=", expense.id)],
                limit=1)
            if not attachment:
                continue
            receipt = self.env["cssk.receipt"].sudo()._create_from_attachment(
                attachment, {"company_id": expense.company_id.id})
            expense.cssk_receipt_id = receipt.id
            try:
                # A savepoint, so a database error inside the capture rolls back
                # only this receipt's reading and leaves the upload — and the
                # write below — working.
                with self.env.cr.savepoint():
                    receipt.action_capture()
            except Exception as error:  # noqa: BLE001 - an upload must never break
                _logger.exception("Receipt capture failed for attachment %s",
                                  attachment.id)
                receipt.write({"state": "error", "review_reason": str(error)})
            if receipt.state == "captured":
                expense._cssk_apply_captured_receipt(receipt)
            expense._cssk_post_reading_result(receipt)
            outcomes[receipt.state if receipt.state in outcomes else "error"] += 1
        self._cssk_notify_upload(outcomes)
        return result

    @api.model
    def _cssk_uploaded_expenses(self, result, attachment_ids):
        """The expenses core has just made for the uploaded images.

        18.0 ONLY, AND IT IS WHY THIS PATH DID NOTHING ON THIS BRANCH. 19.0's
        ``create_expense_from_attachments`` returns ``expenses.ids``; 18.0's
        returns the ``act_window`` dictionary that opens them
        (hr_expense.py:595). The ported code tested ``isinstance(..., list)``
        and always took the empty branch, so every receipt uploaded in the
        Expenses app since this module landed here was left unread —
        silently, because an upload that captures nothing looks exactly like
        an upload with no provider for it. The uploaded expenses are the ones
        the attachments now point at, which holds on both series.
        """
        if isinstance(result, list):
            return self.browse(result)
        attachments = self.env["ir.attachment"].sudo().browse(attachment_ids or [])
        return self.browse(
            attachments.filtered(lambda a: a.res_model == "hr.expense").mapped("res_id"))

    def _cssk_message_note(self, body):
        """Post a status note on the expense without needing an author e-mail.

        18.0 ONLY. ``mail_thread._message_compute_author(raise_on_email=True)``
        refuses the post when a non-superuser posts and the author partner has
        no e-mail address (18.0 mail_thread.py:2906); 19.0 dropped that
        requirement, so the 19.0 copy of this file posts unconditionally. An
        employee user whose partner carries no e-mail is perfectly ordinary,
        and these notes are written on the upload path — which must never
        break, since the whole point of them is to report a failure. The same
        note goes in through ``_message_log`` instead, which is the identical
        record without the notification mail.
        """
        self.ensure_one()
        if self.env.su or self.env.user.partner_id.email_formatted:
            self.message_post(body=body)
        else:
            self._message_log(body=body)

    def _cssk_post_reading_result(self, receipt):
        """Say on the expense what the reading did — failures above all."""
        self.ensure_one()
        if receipt.state == "captured":
            body = Markup("<p>%s</p>") % _(
                "Receipt read: %(seller)s, %(total)s.",
                seller=receipt.partner_id.name or receipt.seller_name or "?",
                total="%.2f %s" % (receipt.amount_total, receipt.currency_id.name))
        else:
            title = {
                "review": _("The receipt was read, but its figures need checking:"),
                "error": _("The receipt could not be read:"),
                "new": _("The receipt was not read:"),
            }.get(receipt.state, _("The receipt could not be read:"))
            reasons = (receipt.review_reason or receipt.qr_detected or "").splitlines()
            body = Markup("<p>%s</p><ul>%s</ul>") % (
                title, Markup().join(Markup("<li>%s</li>") % r for r in reasons if r))
        self._cssk_message_note(body)

    @api.model
    def _cssk_notify_upload(self, outcomes):
        total = sum(outcomes.values())
        if not total:
            return
        failed = outcomes["error"] + outcomes["new"]
        parts = []
        if outcomes["captured"]:
            parts.append(_("%s read", outcomes["captured"]))
        if outcomes["review"]:
            parts.append(_("%s need checking", outcomes["review"]))
        if failed:
            parts.append(_("%s could not be read", failed))
        self.env.user._bus_send("simple_notification", {
            "title": _("Receipts uploaded"),
            "message": ", ".join(parts) + (
                ". " + _("Open an expense to see why.") if failed or outcomes["review"]
                else "."),
            "type": "warning" if failed or outcomes["review"] else "success",
            "sticky": bool(failed),
        })

    # ------------------------------------------------------------------
    # filling an expense from a reading
    # ------------------------------------------------------------------
    def _cssk_apply_captured_receipt(self, receipt):
        """Fill this expense from a receipt that read cleanly.

        One receipt, one expense: its total, and the tax of every VAT rate on
        it. The rates are kept apart in the VAT figure and in the journal entry
        (``_cssk_rate_parts``). Left untouched, with the reason posted, when the
        receipt's VAT cannot be mapped.
        """
        self.ensure_one()
        receipt = receipt.sudo()
        try:
            vals = receipt._expense_amount_vals()
        except UserError as error:
            self._cssk_message_note(_(
                "The receipt was read but not filled in: %s", error))
            return False
        if receipt.partner_id:
            vals["vendor_id"] = receipt.partner_id.id
        self.write(vals)
        if not receipt.vat_deductible and receipt.vat_deductible_note:
            self._cssk_message_note(receipt.vat_deductible_note)
        return True

    # ------------------------------------------------------------------
    # one expense, several VAT rates
    # ------------------------------------------------------------------
    def _cssk_rate_parts(self):
        """The receipt's per-rate split this expense must post, or None.

        ``hr.expense`` holds one amount and applies all its taxes to it as one
        base, which for 23 % and 5 % on one restaurant bill would be a 28 % tax
        on everything. For an expense from a receipt with deductible VAT at
        more than one rate, the VAT figure and the journal entry are built
        from the receipt's own recap instead. None for everything else, which
        Odoo handles unaided.
        """
        self.ensure_one()
        receipt = self.sudo().cssk_receipt_id
        if not receipt or not receipt.vat_deductible:
            return None
        try:
            parts = receipt._expense_parts()
        except UserError:
            return None
        return parts if len(parts) > 1 else None

    def _cssk_matches_parts(self, parts):
        """Whether the expense still says what the receipt says."""
        self.ensure_one()
        taxes = self.env["account.tax"].union(*(tax for _gross, tax, _rate in parts))
        gross = sum(part[0] for part in parts)
        return (self.currency_id.compare_amounts(self.total_amount_currency, gross) == 0
                and set(self.tax_ids.ids) == set(taxes.ids))

    def _cssk_check_parts(self, parts):
        self.ensure_one()
        if not self._cssk_matches_parts(parts):
            raise UserError(_(
                "%(expense)s no longer matches its receipt (%(total).2f with VAT "
                "at %(rates)s). Its VAT is posted rate by rate from the receipt, "
                "so the amount and the taxes cannot be edited; reset them, or "
                "detach the receipt and enter the expense by hand.",
                expense=self.display_name,
                total=sum(part[0] for part in parts),
                rates=", ".join("%g %%" % part[2] for part in parts)))

    def _cssk_part_details(self, parts):
        """Odoo's own tax computation, run on each rate's gross separately."""
        self.ensure_one()
        AccountTax = self.env["account.tax"]
        details = []
        for gross, tax, _rate in parts:
            base_line = self._prepare_base_line_for_taxes_computation(
                price_unit=gross, quantity=1.0, tax_ids=tax)
            AccountTax._add_tax_details_in_base_line(base_line, self.company_id)
            AccountTax._round_base_lines_tax_details([base_line], self.company_id)
            details.append(base_line["tax_details"])
        return details

    def _cssk_company_amounts(self, parts):
        """Each rate's gross in company currency, summing to ``total_amount``."""
        self.ensure_one()
        currency = self.company_currency_id
        if not self.is_multiple_currency:
            return [gross for gross, _tax, _rate in parts]
        amounts = [currency.round(gross * self.currency_rate) for gross, _t, _r in parts]
        amounts[-1] = currency.round(self.total_amount - sum(amounts[:-1]))
        return amounts

    def _compute_tax_amount_currency(self):
        super()._compute_tax_amount_currency()
        for expense in self.filtered("company_id"):
            parts = expense._cssk_rate_parts()
            if not parts or not expense._cssk_matches_parts(parts):
                continue
            details = expense._cssk_part_details(parts)
            expense.untaxed_amount_currency = sum(
                d["total_excluded_currency"] for d in details)
            expense.tax_amount_currency = sum(
                d["total_included_currency"] - d["total_excluded_currency"]
                for d in details)

    def _compute_tax_amount(self):
        super()._compute_tax_amount()
        for expense in self.filtered(lambda e: e.company_id and e.is_multiple_currency):
            parts = expense._cssk_rate_parts()
            if not parts or not expense._cssk_matches_parts(parts):
                continue
            expense.tax_amount = expense.company_currency_id.round(
                expense.tax_amount_currency * expense.currency_rate)
            # 19.0 also sets ``untaxed_amount`` here. 18.0 has no such field —
            # only ``untaxed_amount_currency`` — and its own
            # ``_compute_tax_amount`` likewise sets ``tax_amount`` alone.

    def _prepare_payments_vals(self):
        """Company-paid: the payment entry carries a base and a VAT line per rate.

        The same construction as ``hr_expense``'s, with one base line per rate
        instead of one for the whole amount. The base lines absorb the rounding
        so the entry balances on ``total_amount``, as Odoo's single line does.
        """
        parts = self._cssk_rate_parts()
        if not parts:
            return super()._prepare_payments_vals()
        self._cssk_check_parts(parts)
        move_vals, payment_vals = super()._prepare_payments_vals()
        AccountTax = self.env["account.tax"]
        rate = abs(self.total_amount_currency / self.total_amount) if self.total_amount else 0.0
        base_lines = [
            self._prepare_base_line_for_taxes_computation(
                price_unit=gross, quantity=1.0, account_id=self._get_base_account(),
                rate=rate, tax_ids=tax)
            for gross, tax, _rate in parts
        ]
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id)
        AccountTax._add_accounting_data_in_base_lines_tax_details(
            # Written the way 18.0 core writes it. This path is the
            # company-paid one, so the flag is True either way.
            base_lines, self.company_id,
            include_caba_tags=self.payment_mode == "company_account")
        tax_results = AccountTax._prepare_tax_lines(base_lines, self.company_id)

        base_move_lines, move_lines = [], []
        for (base_line, to_update), (_gross, _tax, part_rate) in zip(
                tax_results["base_lines_to_update"], parts):
            base_move_line = {
                "name": "%s (%g %%)" % (self._get_move_line_name(), part_rate),
                "account_id": base_line["account_id"].id,
                "product_id": base_line["product_id"].id,
                "analytic_distribution": base_line["analytic_distribution"],
                "expense_id": self.id,
                "tax_ids": [Command.set(base_line["tax_ids"].ids)],
                "tax_tag_ids": to_update["tax_tag_ids"],
                "amount_currency": to_update["amount_currency"],
                "balance": to_update["balance"],
                "currency_id": base_line["currency_id"].id,
                "partner_id": self.vendor_id.id,
            }
            base_move_lines.append(base_move_line)
            move_lines.append(base_move_line)
        tax_balance = 0.0
        for tax_line in tax_results["tax_lines_to_add"]:
            tax_balance += tax_line["balance"]
            move_lines.append(tax_line)
        base_move_lines[-1]["balance"] += (
            self.total_amount - tax_balance
            - sum(line["balance"] for line in base_move_lines))
        move_lines.append({
            "name": self._get_move_line_name(),
            # 18.0 keeps this on the sheet, which owns the payment method.
            "account_id": self.sheet_id._get_expense_account_destination(),
            "balance": -self.total_amount,
            "amount_currency": self.currency_id.round(-self.total_amount_currency),
            "currency_id": self.currency_id.id,
            "partner_id": self.vendor_id.id,
        })
        move_vals["line_ids"] = [Command.create(line) for line in move_lines]
        return move_vals, payment_vals

    # ------------------------------------------------------------------
    # camera scan from the Expenses app
    # ------------------------------------------------------------------
    @api.model
    def action_capture_from_scan(self, text):
        """Scan a receipt's QR code and land on the resulting expense(s).

        The employee always lands on an expense they can open: filled from the
        receipt when it read cleanly, otherwise a draft carrying the reason.
        """
        Receipt = self.env["cssk.receipt"].sudo()
        text = (text or "").strip()
        if not text or not Receipt._provider_accepting(text):
            return {
                "retry": True,
                "message": " ".join(filter(None, [
                    _("That is not a receipt verification code (it reads "
                      "“%s”).", text[:80]),
                    Receipt._scan_hints(),
                ])),
            }
        receipt = Receipt.search([
            ("company_id", "=", self.env.company.id), ("qr_raw", "=", text),
        ], limit=1)
        if receipt:
            # Searched as superuser: an employee sees only their own expenses,
            # so a colleague's claim on the same receipt was invisible here and
            # the receipt could be reimbursed twice.
            claimed = self.sudo().search([("cssk_receipt_id", "=", receipt.id)])
            mine = claimed.filtered(lambda e: e.employee_id.user_id == self.env.user)
            if mine:
                return {"retry": False, "action": self._cssk_open(self.browse(mine.ids))}
            if claimed:
                return {"retry": True, "message": _(
                    "This receipt has already been claimed by %s.",
                    ", ".join(claimed.mapped("employee_id.name")))}
        if not receipt:
            receipt = Receipt.create({"qr_raw": text, "qr_source": "scanned"})
        if receipt.state in ("new", "error"):
            receipt.action_capture()
        expense = self.create({
            "name": receipt.display_name,
            "employee_id": receipt._expense_employee().id,
            "product_id": receipt._expense_product().id,
            "cssk_receipt_id": receipt.id,
        })
        if receipt.state == "captured":
            expense._cssk_apply_captured_receipt(receipt)
        expense._cssk_post_reading_result(receipt)
        return {"retry": False, "action": self._cssk_open(expense)}

    @api.model
    def _cssk_open(self, expenses):
        if len(expenses) == 1:
            return {"type": "ir.actions.act_window", "res_model": "hr.expense",
                    "res_id": expenses.id, "views": [[False, "form"]],
                    "target": "current"}
        return {"type": "ir.actions.act_window", "res_model": "hr.expense",
                "name": _("Expenses from the receipt"),
                "domain": [("id", "in", expenses.ids)],
                "views": [[False, "list"], [False, "form"]],
                "target": "current"}

    def action_open_cssk_receipt(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "cssk.receipt",
                "res_id": self.cssk_receipt_id.id, "views": [[False, "form"]],
                "target": "current"}
