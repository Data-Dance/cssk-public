# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The cash payment limit of zákon č. 394/2012 Z. z. at the Point of Sale.

§ 6 ods. 1 values foreign cash at the ECB/NBS rate valid on the day before
the payment. § 6 ods. 2 adds up parts of one payment arising from one legal
relationship. The Finančné riaditeľstvo's guidance (pokyn k zákonu 394/2012,
čl. 2.3, príklady 15 and 17) treats one purchase paid in parts as one payment
but separately concluded purchases as separate ones. A till cannot tell the
two apart; the nearest it can see is the same customer paying cash again on
the same day, so those orders are added together and the cashier decides.
"""

from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models

from odoo.addons.l10n_sk_invoice.models.account_payment import (
    CASH_PAYMENT_LIMIT,
    _limit_warning,
)

TIMEZONE = pytz.timezone("Europe/Bratislava")
PAID_ORDER_STATES = ("paid", "done")


def _rate_day(moment):
    """The day before the payment, by the Slovak calendar (§ 6 ods. 1)."""
    local = pytz.utc.localize(moment).astimezone(TIMEZONE) if moment else None
    day = local.date() if local else fields.Date.today()
    return day - timedelta(days=1)


def _day_bounds(moment):
    """Naive-UTC start and end of the Slovak calendar day of ``moment``."""
    local_day = pytz.utc.localize(moment).astimezone(TIMEZONE).date()
    start = TIMEZONE.localize(datetime.combine(local_day, time.min))
    end = TIMEZONE.localize(datetime.combine(local_day + timedelta(days=1), time.min))
    return (start.astimezone(pytz.utc).replace(tzinfo=None),
            end.astimezone(pytz.utc).replace(tzinfo=None))


class PosOrder(models.Model):
    _inherit = "pos.order"

    l10n_sk_cash_limit_warning = fields.Char(
        compute="_compute_l10n_sk_cash_limit_warning",
    )

    def _l10n_sk_cash_amount(self):
        """Net cash of the order in its own currency; change is a negative line."""
        self.ensure_one()
        return sum(
            self.payment_ids.filtered("payment_method_id.is_cash_count").mapped("amount")
        )

    def _l10n_sk_cash_value(self):
        """The cash in company currency at the rate of the day before (§ 6 ods. 1)."""
        self.ensure_one()
        company = self.company_id
        currency = self.currency_id or company.currency_id
        return currency._convert(
            abs(self._l10n_sk_cash_amount()), company.currency_id, company,
            _rate_day(self.date_order),
        )

    @api.model
    def _l10n_sk_same_day_cash_orders(self, partner, company, moment, exclude=None):
        """Paid orders of the same customer with cash, on the same Slovak day."""
        if not partner:
            return self.browse()
        start, end = _day_bounds(moment or fields.Datetime.now())
        orders = self.search([
            ("company_id", "=", company.id),
            ("partner_id", "child_of", partner.commercial_partner_id.id),
            ("state", "in", PAID_ORDER_STATES),
            ("date_order", ">=", start),
            ("date_order", "<", end),
            ("payment_ids.payment_method_id.is_cash_count", "=", True),
        ])
        if exclude:
            orders -= exclude
        # A refund paid out in cash runs the other way: it is not a part of
        # the customer's payment, and abs() would wrongly add it.
        return orders.filtered(lambda o: o._l10n_sk_cash_amount() > 0)

    @api.depends("payment_ids.amount", "payment_ids.payment_method_id", "date_order", "partner_id")
    def _compute_l10n_sk_cash_limit_warning(self):
        """§ 4 ods. 1 with the same customer's cash orders of the day (§ 6 ods. 2)."""
        for order in self:
            earlier = self._l10n_sk_same_day_cash_orders(
                order.partner_id, order.company_id, order.date_order,
                exclude=order._origin,
            )
            if order.date_order:
                # Only what came before: the first order of a series was
                # within the limit when it was paid.
                earlier = earlier.filtered(
                    lambda o: (o.date_order, o.id) < (order.date_order, order._origin.id or 0)
                    if order._origin.id else o.date_order <= order.date_order
                )
            cash = order._l10n_sk_cash_amount()
            if cash < 0:
                earlier = earlier.browse()  # a refund stands on its own
            order.l10n_sk_cash_limit_warning = _limit_warning(
                self.env, order.company_id,
                order.currency_id or order.company_id.currency_id,
                cash,
                _rate_day(order.date_order) + timedelta(days=1),
                sum(o._l10n_sk_cash_value() for o in earlier),
            )

    @api.model
    def l10n_sk_cash_paid_today(self, partner_id, config_id):
        """For the till: cash the customer already paid today, in company currency."""
        config = self.env["pos.config"].browse(config_id)
        partner = self.env["res.partner"].browse(partner_id).exists()
        orders = self._l10n_sk_same_day_cash_orders(
            partner, config.company_id, fields.Datetime.now()
        )
        return sum(o._l10n_sk_cash_value() for o in orders)


class PosConfig(models.Model):
    _inherit = "pos.config"

    def _l10n_sk_cash_rate(self):
        """Company currency per unit of the till's currency, valid yesterday.

        ``False`` outside Slovakia, or when the rate is unknown: a missing rate
        would otherwise convert at 1 and silently move the limit.
        """
        self.ensure_one()
        company = self.company_id
        if company.account_fiscal_country_id.code != "SK":
            return False
        currency = self.currency_id
        if currency == company.currency_id:
            return 1.0
        day = _rate_day(fields.Datetime.now())
        if not self.env["res.currency.rate"].sudo().search_count([
            ("currency_id", "=", currency.id),
            ("name", "<=", day),
            ("company_id", "in", [False, company.root_id.id]),
        ]):
            return False
        return currency._get_conversion_rate(currency, company.currency_id, company, day)

    @api.model
    def _load_pos_data_read(self, records, config):
        read_records = super()._load_pos_data_read(records, config)
        if read_records:
            read_records[0]["_l10n_sk_cash_rate"] = config._l10n_sk_cash_rate()
            read_records[0]["_l10n_sk_cash_limit"] = CASH_PAYMENT_LIMIT
        return read_records
