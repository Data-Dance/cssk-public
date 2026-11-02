# -*- coding: utf-8 -*-
import logging
import re

import psycopg2

from odoo import _, fields, models
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

# Allowed charset for id_pokl / porad_cis per the XSD (string20 / string25).
_ALLOWED = re.compile(r"[^0-9a-zA-Z\.,:;/#\-_ ]")
_PAID_STATES = ("paid", "done", "invoiced")


class PosOrder(models.Model):
    _inherit = "pos.order"

    l10n_cz_eet2_transaction_id = fields.Many2one(
        "l10n.cz.eet2.transaction", string="EET 2.0 Message", copy=False)
    l10n_cz_eet2_pok = fields.Char(
        related="l10n_cz_eet2_transaction_id.pok", store=True, string="EET 2.0 POK")
    l10n_cz_eet2_state = fields.Selection(
        related="l10n_cz_eet2_transaction_id.state", store=True,
        string="EET 2.0 Status")
    l10n_cz_eet2_is_test = fields.Boolean(
        related="l10n_cz_eet2_transaction_id.is_test_response", store=True)

    # ------------------------------------------------------------------
    @staticmethod
    def _l10n_cz_eet2_sanitize(value, maxlen):
        return _ALLOWED.sub("-", (value or "").strip())[:maxlen] or "0"

    def _l10n_cz_eet2_contact_payments(self):
        """Payment lines made through a contact payment method (§ 6 ZoET).

        Change given back is a negative cash line, so the sum is what the
        customer actually left at the till; a refund's lines are negative.
        """
        self.ensure_one()
        return self.payment_ids.filtered(
            lambda p: p.payment_method_id.l10n_cz_eet2_contact_payment)

    def _l10n_cz_eet2_contact_total(self):
        self.ensure_one()
        return self.currency_id.round(
            sum(self._l10n_cz_eet2_contact_payments().mapped("amount")))

    def _l10n_cz_eet2_in_scope(self):
        """True when this order carries contact money that must be recorded.

        Only the contact part counts: an order paid half in cash and half by
        a method flagged as remote (an e-shop gateway, a transfer paid from
        home) registers the cash half, and one with no contact money at all
        registers nothing.
        """
        self.ensure_one()
        company = self.company_id
        if not company.l10n_cz_eet2_enabled or not company.l10n_cz_eet2_eic_popl:
            return False
        return not float_is_zero(self._l10n_cz_eet2_contact_total(),
                                precision_rounding=self.currency_id.rounding)

    def _l10n_cz_eet2_sale_datetime(self):
        """§ 16 odst. 2 ZoET: the sale happens when the payment is received or
        the payment order is issued, i.e. at the till's payment step, not when
        the order was opened (a restaurant table can sit for hours)."""
        self.ensure_one()
        dates = self.payment_ids.mapped("payment_date")
        return max(dates) if dates else self.date_order

    def _l10n_cz_eet2_amounts(self):
        """Amounts in the order currency: total, intended-for-drawdown, drawn.

        ``celk_trzba`` is the sum of the contact payment lines, not
        ``amount_total``: § 17 odst. 1 písm. f) ZoET evidences the payment
        received, and only the contact part of it (§ 5–6). Hook for bridges
        (loyalty gift cards / eWallets) that fill ``urceno_cerp_zuct`` /
        ``cerp_zuct`` and widen the total by the drawdown.
        """
        self.ensure_one()
        return {"celk_trzba": self._l10n_cz_eet2_contact_total(),
                "urceno_cerp_zuct": 0.0, "cerp_zuct": 0.0}

    def _l10n_cz_eet2_prepare_values(self):
        self.ensure_one()
        config = self.config_id
        company = self.company_id
        id_pokl = config.l10n_cz_eet2_id_pokl or config.name
        amounts = self._l10n_cz_eet2_amounts()
        return {
            "environment": company.l10n_cz_eet2_environment,
            "certificate_id": company.l10n_cz_eet2_certificate_id.id or False,
            "eic_popl": company.l10n_cz_eet2_eic_popl,
            "id_jednotky": (config.l10n_cz_eet2_id_jednotky
                            or company.l10n_cz_eet2_id_jednotky),
            "id_pokl": self._l10n_cz_eet2_sanitize(id_pokl, 20),
            "porad_cis": self._l10n_cz_eet2_sanitize(
                self.pos_reference or self.name, 25),
            "dat_trzby": self._l10n_cz_eet2_sale_datetime(),
            "celk_trzba": amounts["celk_trzba"],
            "urceno_cerp_zuct": amounts["urceno_cerp_zuct"] or False,
            "cerp_zuct": amounts["cerp_zuct"] or False,
            "currency_id": self.currency_id.id,
            "prvni_zaslani": True,
            "pos_order_id": self.id,
        }

    def _l10n_cz_eet2_try_register(self):
        """Register the order with EET 2.0. Never blocks the sale."""
        Tx = self.env["l10n.cz.eet2.transaction"]
        for order in self:
            if order.l10n_cz_eet2_transaction_id:
                continue
            if order.state not in _PAID_STATES:
                continue
            if not order._l10n_cz_eet2_in_scope():
                if order._l10n_cz_eet2_contact_payments():
                    # Contact lines that net to zero: nothing was received.
                    order.message_post(body=_(
                        "EET 2.0: nothing registered, the contact payments of "
                        "this order add up to zero."))
                continue
            try:
                try:
                    with self.env.cr.savepoint():
                        # The live-sale unique index is checked by Postgres on
                        # the INSERT, against columns: land pending links first.
                        Tx.flush_model(["pos_order_id", "storno_of_id", "reversed_by_id"])
                        tx = Tx.create_from_values(
                            order.company_id, **order._l10n_cz_eet2_prepare_values())
                        Tx.flush_model()
                except psycopg2.IntegrityError:
                    # Another worker registered this order first (a sync and a
                    # resend, or two syncs): adopt its message instead of
                    # evidencing the sale twice.
                    tx = Tx.search([("pos_order_id", "=", order.id),
                                    ("storno_of_id", "=", False),
                                    ("reversed_by_id", "=", False)], limit=1)
                    if not tx:
                        raise
                    order.l10n_cz_eet2_transaction_id = tx
                    continue
                order.l10n_cz_eet2_transaction_id = tx
                # Synchronous, bounded by the company's mezní doba odezvy (§ 19);
                # on a timeout the sale goes through and the cron resends (§ 20).
                tx._send(sync=True)
            except Exception as exc:  # noqa: BLE001 - EET must never block a sale
                _logger.warning(
                    "EET 2.0: failed to register POS order %s: %s", order.name, exc)

    def _process_order(self, order, existing_order):
        order_id = super()._process_order(order, existing_order)
        self.browse(order_id).sudo()._l10n_cz_eet2_try_register()
        return order_id

    def get_l10n_cz_eet2_pos_data(self):
        """Called synchronously from the POS payment-validation flow.

        Ensures the order is registered (idempotent) and returns the POK so the
        frontend can print it on the receipt *before* leaving the screen.
        """
        self.sudo()._l10n_cz_eet2_try_register()
        order = self[:1]
        return {
            "l10n_cz_eet2_pok": order.l10n_cz_eet2_pok or False,
            "l10n_cz_eet2_state": order.l10n_cz_eet2_state or False,
            "l10n_cz_eet2_is_test": order.l10n_cz_eet2_is_test,
        }

    def l10n_cz_eet2_resend(self):
        """Manual send now. The order's message is reused: a second message
        for the same sale would be a second sale (methodology ch. 6: a repeat
        is the same Data with a new UUID, not a new record), and the live-sale
        index would refuse it anyway."""
        for order in self:
            tx = order.l10n_cz_eet2_transaction_id
            if tx and tx.state == "accepted":
                continue
            if tx:
                if tx.state in ("error", "rejected"):
                    tx.action_requeue()
                tx._send()
            else:
                order._l10n_cz_eet2_try_register()

    # NOTE: do NOT override _load_pos_data_fields for pos.order. Its base returns
    # [] which read() treats as "all fields", so our stored related fields
    # (l10n_cz_eet2_pok/state/is_test) load automatically. Returning a non-empty
    # list here restricts the load and drops `lines`/`payment_ids`, breaking POS
    # price computation (this.lines undefined -> _computeAllPrices crash).
