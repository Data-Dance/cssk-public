# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The cash payment limit of zákon č. 254/2004 Sb.

§ 4 odst. 1 obliges whoever pays more than 270 000 Kč to pay by transfer, and
odst. 2 forbids the payee to take it in cash. What is measured is not one
document but one day: "Do limitu se započítávají všechny platby v české i
cizí měně, provedené týmž poskytovatelem platby témuž příjemci platby v
průběhu jednoho kalendářního dne" (odst. 4). So the sum here runs over the
cash paid between the company and one partner on one day, in one direction,
whatever documents it settles. This is not the Slovak rule, which adds up
the parts of one legal relationship over any number of days.

A payment in another currency counts at the rate "platným ke dni provedení
platby" (odst. 3).

Warn, do not block: § 3 odst. 2 lists payments outside the duty (taxes,
obligatory payments under employment law, pensions, a declared krizový stav)
that the system cannot tell apart, and § 2 odst. 2 says a deposit to or a
withdrawal from a bank account is no payment at all. A cash statement line
therefore warns only when it has a partner other than the company itself.
"""

from odoo import api, fields, models

CASH_PAYMENT_LIMIT = 270000.0
PAID_STATES = ("in_process", "paid")


def _to_czk(env, company, amount, day):
    """``amount`` of company currency in Czech crowns on ``day``."""
    czk = env.ref("base.CZK")
    if company.currency_id == czk:
        return amount
    return company.currency_id._convert(amount, czk, company, day)


def _same_day_cash(env, company, partner, day, outbound,
                   exclude_payment=None, exclude_line=None):
    """Cash already paid that day between the company and ``partner`` in
    one direction, in company currency."""
    partner = partner.commercial_partner_id
    payments = env["account.payment"].search([
        ("company_id", "=", company.id),
        ("journal_id.type", "=", "cash"),
        ("date", "=", day),
        ("state", "in", PAID_STATES),
        ("payment_type", "=", "outbound" if outbound else "inbound"),
        ("partner_id", "child_of", partner.id),
    ])
    if exclude_payment:
        payments -= exclude_payment
    lines = env["account.bank.statement.line"].search([
        ("company_id", "=", company.id),
        ("journal_id.type", "=", "cash"),
        ("date", "=", day),
        ("partner_id", "child_of", partner.id),
        ("amount", "<" if outbound else ">", 0.0),
    ])
    if exclude_line:
        lines -= exclude_line
    # A payment that also has its statement line would count twice.
    lines = lines.filtered(lambda line: not line.move_id.origin_payment_id)
    total = sum(abs(p.amount_company_currency_signed) for p in payments)
    for line in lines:
        currency = line.journal_id.currency_id or company.currency_id
        total += currency._convert(
            abs(line.amount), company.currency_id, company, day)
    return total


def _limit_warning(env, company, partner, currency, amount, day, outbound,
                   exclude_payment=None, exclude_line=None):
    """The warning text for one cash payment, or ``False``."""
    if (company.account_fiscal_country_id.code != "CZ" or not amount
            or not currency or not partner):
        return False
    if (partner.commercial_partner_id
            == company.partner_id.commercial_partner_id):
        return False
    day = day or fields.Date.context_today(env.user)
    value = currency._convert(abs(amount), company.currency_id, company, day)
    total = _to_czk(env, company, value + _same_day_cash(
        env, company, partner, day, outbound,
        exclude_payment=exclude_payment, exclude_line=exclude_line), day)
    if total <= CASH_PAYMENT_LIMIT:
        return False
    # ``env._``: a module-level helper has no ``self`` for ``_`` to read the
    # language from, and the warning would stay English. Two whole sentences
    # rather than one with a word swapped in: the word order differs between
    # the languages.
    values = {"partner": partner.commercial_partner_id.display_name,
              "day": day, "total": total}
    if outbound:
        return env._(
            "Cash paid to %(partner)s on %(day)s totals %(total).2f Kč, "
            "above the 270 000 Kč limit of § 4 zákona č. 254/2004 Sb. All "
            "cash payments between the same payer and payee in one calendar "
            "day are added together (§ 4 odst. 4). Check that the payment "
            "is outside the duty under § 3 odst. 2, or pay by bank transfer.",
            **values)
    return env._(
        "Cash received from %(partner)s on %(day)s totals %(total).2f Kč, "
        "above the 270 000 Kč limit of § 4 zákona č. 254/2004 Sb. All cash "
        "payments between the same payer and payee in one calendar day are "
        "added together (§ 4 odst. 4). Check that the payment is outside "
        "the duty under § 3 odst. 2, or have it paid by bank transfer.",
        **values)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    l10n_cz_cash_limit_warning = fields.Char(
        compute="_compute_l10n_cz_cash_limit_warning")

    @api.depends("amount", "currency_id", "date", "journal_id", "partner_id",
                 "payment_type", "state")
    def _compute_l10n_cz_cash_limit_warning(self):
        for payment in self:
            payment.l10n_cz_cash_limit_warning = (
                payment.journal_id.type == "cash"
                and _limit_warning(
                    self.env, payment.company_id, payment.partner_id,
                    payment.currency_id, payment.amount, payment.date,
                    payment.payment_type == "outbound",
                    exclude_payment=payment)
            ) or False


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    l10n_cz_cash_limit_warning = fields.Char(
        compute="_compute_l10n_cz_cash_limit_warning")

    @api.depends("amount", "currency_id", "payment_date", "journal_id",
                 "partner_id", "payment_type")
    def _compute_l10n_cz_cash_limit_warning(self):
        for wizard in self:
            wizard.l10n_cz_cash_limit_warning = (
                wizard.journal_id.type == "cash"
                and _limit_warning(
                    self.env, wizard.company_id, wizard.partner_id,
                    wizard.currency_id, wizard.amount, wizard.payment_date,
                    wizard.payment_type == "outbound")
            ) or False


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    l10n_cz_cash_limit_warning = fields.Char(
        compute="_compute_l10n_cz_cash_limit_warning")

    @api.depends("amount", "date", "journal_id", "partner_id")
    def _compute_l10n_cz_cash_limit_warning(self):
        for line in self:
            warning = False
            # A line that belongs to a payment is that payment's to warn
            # about.
            if (line.journal_id.type == "cash" and line.partner_id
                    and not line.move_id.origin_payment_id):
                warning = _limit_warning(
                    self.env, line.company_id, line.partner_id,
                    line.journal_id.currency_id or line.company_id.currency_id,
                    line.amount, line.date, line.amount < 0,
                    exclude_line=line)
            line.l10n_cz_cash_limit_warning = warning

    def _l10n_cz_note_cash_limit(self):
        """Leave the warning in the chatter, which every statement screen
        shows."""
        for line in self:
            warning = line.l10n_cz_cash_limit_warning
            if warning and line.move_id:
                line.move_id.message_post(
                    body=warning, message_type="comment",
                    subtype_xmlid="mail.mt_note")

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._l10n_cz_note_cash_limit()
        return lines

    def write(self, vals):
        before = {line.id: line.l10n_cz_cash_limit_warning for line in self}
        result = super().write(vals)
        if {"amount", "partner_id", "journal_id", "date"} & set(vals):
            self.filtered(
                lambda line: line.l10n_cz_cash_limit_warning
                and line.l10n_cz_cash_limit_warning != before.get(line.id)
            )._l10n_cz_note_cash_limit()
        return result
