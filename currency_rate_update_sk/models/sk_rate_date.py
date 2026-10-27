# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The Slovak preceding-day rule for the rate a document is converted at.

§ 24 ods. 2 písm. a) zákona 431/2002 Z. z. converts an accounting case at the
reference rate "určeným a vyhláseným Európskou centrálnou bankou alebo Národnou
bankou Slovenska ... v deň predchádzajúci dňu uskutočnenia účtovného prípadu",
and § 26 ods. 1 zákona 222/2004 Z. z. converts a VAT base at the reference rate
announced "v deň predchádzajúci dňu vzniku daňovej povinnosti".

The ECB provider stores each rate under the day the ECB announced it, and Odoo
gives a document the newest rate dated on or before its own date — i.e. the
rate announced ON that day. For a Slovak company the document date is therefore
moved back by one day before the rate is looked up. The newest rate on or
before that day is the last one announced before the document's day, which is
also what a weekend or a holiday falls back to (a Monday document takes
Friday's rate, as does a Saturday or a Sunday one).

Deliberately NOT applied to the balance-sheet revaluation: § 24 ods. 2
písm. b) values the closing balances at the rate of the balance-sheet day
itself, so the shift is limited to the documents below rather than placed on
res.currency for every caller.
"""

from datetime import timedelta

from odoo import api, fields, models

#: Context key: conversions made under it follow the preceding-day rule when
#: the converting company is Slovak.
SK_PRECEDING_DAY_KEY = "l10n_sk_preceding_day_rate"


def sk_rate_date(company, date):
    """The date whose rate a Slovak document dated ``date`` is converted at."""
    if date and company and company._l10n_sk_uses_preceding_day_rate():
        return fields.Date.to_date(date) - timedelta(days=1)
    return date


class ResCompany(models.Model):
    _inherit = "res.company"

    def _l10n_sk_uses_preceding_day_rate(self):
        """Whether this company converts at the rate of the preceding day.

        Either country naming Slovakia counts, for the reason given on
        ``_sk_default_provider_companies``: a fiscal country filled from a
        foreign template is never re-synced, so reading it alone misses
        exactly the databases that were made Slovak afterwards.
        """
        self.ensure_one()
        return "SK" in (
            self.country_id.code,
            self.account_fiscal_country_id.code,
        )


class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company=None,
                             date=None):
        if self.env.context.get(SK_PRECEDING_DAY_KEY):
            date = sk_rate_date(
                company or self.env.company,
                date or fields.Date.context_today(self),
            )
        return super()._get_conversion_rate(
            from_currency, to_currency, company=company, date=date
        )


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_invoice_currency_rate_date(self):
        # An invoice's tax liability arises on the day of supply (§ 19 ods. 1
        # ZDPH), which is the taxable supply date when one is entered; that
        # day is also the accounting case. Odoo's own default is the invoice
        # date, kept when no supply date is given.
        date = super()._get_invoice_currency_rate_date()
        if self.company_id._l10n_sk_uses_preceding_day_rate():
            return sk_rate_date(self.company_id, self.taxable_supply_date or date)
        return date


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_currency_rate(self):
        # Invoices take the rate of the move (above); this is the rate of a
        # foreign-currency line in any other journal entry.
        return super(
            AccountMoveLine, self.with_context(**{SK_PRECEDING_DAY_KEY: True})
        )._compute_currency_rate()


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_move_line_default_vals(self, write_off_line_vals=None,
                                        force_balance=None):
        return super(
            AccountPayment, self.with_context(**{SK_PRECEDING_DAY_KEY: True})
        )._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance
        )

    def _compute_amount_company_currency_signed(self):
        return super(
            AccountPayment, self.with_context(**{SK_PRECEDING_DAY_KEY: True})
        )._compute_amount_company_currency_signed()


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        return super(
            AccountBankStatementLine,
            self.with_context(**{SK_PRECEDING_DAY_KEY: True}),
        )._prepare_move_line_default_vals(
            counterpart_account_id=counterpart_account_id
        )

    def _compute_amount_currency(self):
        return super(
            AccountBankStatementLine,
            self.with_context(**{SK_PRECEDING_DAY_KEY: True}),
        )._compute_amount_currency()
