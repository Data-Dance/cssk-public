# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The cash payment limit of zákon č. 394/2012 Z. z.

§ 4 ods. 1 forbids a cash payment above 5 000 €. The 15 000 € limit in ods. 2
applies only between individuals who are not in business, so it can never apply
to a company keeping its books here. § 6 ods. 2 adds up a payment split into
parts when the parts arise from one legal relationship, which is approximated
by the invoices the payments settle. § 6 ods. 1 values foreign cash at the rate
of the preceding day.

Warn, do not block: § 8 lists exemptions the system cannot see, such as payments
in tax administration or enforcement proceedings.

Payments and cash statement lines are both counted: a document settled partly
through each still adds up to one payment. A statement line warns only when it
has a partner other than the company itself, so cash deposited to the bank or
taken out of a point-of-sale drawer is left alone.
"""

from datetime import timedelta

from odoo import _, api, fields, models

CASH_PAYMENT_LIMIT = 5000.0
PAID_STATES = ("in_process", "paid")


def _limit_warning(env, company, currency, amount, day, earlier_total):
    """The warning text for one cash payment, or ``False``.

    ``earlier_total`` is what other cash payments of the same documents
    already came to, in company currency.
    """
    if company.account_fiscal_country_id.code != "SK" or not amount or not currency:
        return False
    rate_day = (day or fields.Date.context_today(env.user)) - timedelta(days=1)
    value = currency._convert(abs(amount), company.currency_id, company, rate_day)
    total = value + earlier_total
    if company.currency_id.compare_amounts(total, CASH_PAYMENT_LIMIT) <= 0:
        return False
    return _(
        "Cash payments for this document total %(total).2f €, above the "
        "5 000 € limit of § 4 zákona č. 394/2012 Z. z. Parts of one payment "
        "are added together (§ 6 ods. 2). Check that an exemption under § 8 "
        "applies, or pay by bank transfer.",
        total=total,
    )


def _earlier_cash_total(invoices, exclude_payment=None, exclude_line=None):
    """Cash already paid on ``invoices`` by payments and statement lines."""
    payments = invoices.matched_payment_ids.filtered(
        lambda p: p.journal_id.type == "cash" and p.state in PAID_STATES
    )
    if exclude_payment:
        payments -= exclude_payment
    lines = invoices._get_reconciled_statement_lines().filtered(
        lambda line: line.journal_id.type == "cash"
    )
    if exclude_line:
        lines -= exclude_line
    # A payment reconciled through a statement line would count twice.
    lines = lines.filtered(lambda line: not line.move_id.origin_payment_id)
    return sum(abs(p.amount_company_currency_signed) for p in payments) + sum(
        abs(sum(line._seek_for_lines()[0].mapped("balance"))) for line in lines
    )


class AccountPayment(models.Model):
    _inherit = "account.payment"

    l10n_sk_cash_limit_warning = fields.Char(
        compute="_compute_l10n_sk_cash_limit_warning",
    )

    @api.depends("amount", "currency_id", "date", "journal_id", "invoice_ids")
    def _compute_l10n_sk_cash_limit_warning(self):
        for payment in self:
            payment.l10n_sk_cash_limit_warning = (
                payment.journal_id.type == "cash"
                and _limit_warning(
                    self.env, payment.company_id, payment.currency_id,
                    payment.amount, payment.date,
                    _earlier_cash_total(payment.invoice_ids, exclude_payment=payment),
                )
            ) or False


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    l10n_sk_cash_limit_warning = fields.Char(
        compute="_compute_l10n_sk_cash_limit_warning",
    )

    @api.depends("amount", "currency_id", "payment_date", "journal_id", "line_ids")
    def _compute_l10n_sk_cash_limit_warning(self):
        for wizard in self:
            wizard.l10n_sk_cash_limit_warning = (
                wizard.journal_id.type == "cash"
                and _limit_warning(
                    self.env, wizard.company_id, wizard.currency_id,
                    wizard.amount, wizard.payment_date,
                    _earlier_cash_total(wizard.line_ids.move_id),
                )
            ) or False


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    l10n_sk_cash_limit_warning = fields.Char(
        compute="_compute_l10n_sk_cash_limit_warning",
    )

    def _l10n_sk_is_third_party_cash(self):
        self.ensure_one()
        return (
            self.journal_id.type == "cash"
            and self.partner_id
            and self.partner_id.commercial_partner_id
            != self.company_id.partner_id.commercial_partner_id
        )

    @api.depends("amount", "date", "journal_id", "partner_id", "is_reconciled")
    def _compute_l10n_sk_cash_limit_warning(self):
        for line in self:
            warning = False
            if line._l10n_sk_is_third_party_cash():
                invoices = line.move_id._get_reconciled_invoices()
                warning = _limit_warning(
                    self.env, line.company_id,
                    line.journal_id.currency_id or line.company_id.currency_id,
                    line.amount, line.date,
                    _earlier_cash_total(invoices, exclude_line=line),
                )
            line.l10n_sk_cash_limit_warning = warning

    def _l10n_sk_note_cash_limit(self):
        """Leave the warning in the chatter, which every statement UI shows."""
        for line in self:
            warning = line.l10n_sk_cash_limit_warning
            if warning and line.move_id:
                line.move_id.message_post(body=warning, message_type="comment",
                                          subtype_xmlid="mail.mt_note")

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._l10n_sk_note_cash_limit()
        return lines

    def write(self, vals):
        before = {line.id: line.l10n_sk_cash_limit_warning for line in self}
        result = super().write(vals)
        if {"amount", "partner_id", "journal_id"} & set(vals):
            self.filtered(
                lambda line: line.l10n_sk_cash_limit_warning
                and line.l10n_sk_cash_limit_warning != before.get(line.id)
            )._l10n_sk_note_cash_limit()
        return result
