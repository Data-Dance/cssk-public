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
"""

from datetime import timedelta

from odoo import _, api, fields, models

CASH_PAYMENT_LIMIT = 5000.0
PAID_STATES = ("in_process", "paid")


def _limit_warning(env, company, currency, amount, day, earlier_payments):
    """The warning text for one cash payment, or ``False``."""
    if company.account_fiscal_country_id.code != "SK" or not amount or not currency:
        return False
    rate_day = (day or fields.Date.context_today(env.user)) - timedelta(days=1)
    value = currency._convert(amount, company.currency_id, company, rate_day)
    total = value + sum(abs(x.amount_company_currency_signed) for x in earlier_payments)
    if company.currency_id.compare_amounts(total, CASH_PAYMENT_LIMIT) <= 0:
        return False
    return _(
        "Cash payments for this document total %(total).2f €, above the "
        "5 000 € limit of § 4 zákona č. 394/2012 Z. z. Parts of one payment "
        "are added together (§ 6 ods. 2). Check that an exemption under § 8 "
        "applies, or pay by bank transfer.",
        total=total,
    )


def _earlier_cash_payments(invoices, exclude):
    return (invoices.matched_payment_ids - exclude).filtered(
        lambda p: p.journal_id.type == "cash" and p.state in PAID_STATES
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
                    _earlier_cash_payments(payment.invoice_ids, payment),
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
                    _earlier_cash_payments(
                        wizard.line_ids.move_id, self.env["account.payment"]
                    ),
                )
            ) or False
