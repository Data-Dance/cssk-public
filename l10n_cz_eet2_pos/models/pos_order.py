# -*- coding: utf-8 -*-
import logging
import re

from odoo import fields, models

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

    def _l10n_cz_eet2_in_scope(self):
        """True when this order carries a contact payment that must be recorded."""
        self.ensure_one()
        company = self.company_id
        if not company.l10n_cz_eet2_enabled or not company.l10n_cz_eet2_eic_popl:
            return False
        # In scope only if at least one payment uses a contact payment method.
        methods = self.payment_ids.payment_method_id
        return any(m.l10n_cz_eet2_contact_payment for m in methods)

    def _l10n_cz_eet2_prepare_values(self):
        self.ensure_one()
        config = self.config_id
        company = self.company_id
        id_pokl = config.l10n_cz_eet2_id_pokl or config.name
        return {
            "environment": company.l10n_cz_eet2_environment,
            "certificate_id": company.l10n_cz_eet2_certificate_id.id or False,
            "eic_popl": company.l10n_cz_eet2_eic_popl,
            "id_jednotky": (config.l10n_cz_eet2_id_jednotky
                            or company.l10n_cz_eet2_id_jednotky),
            "id_pokl": self._l10n_cz_eet2_sanitize(id_pokl, 20),
            "porad_cis": self._l10n_cz_eet2_sanitize(
                self.pos_reference or self.name, 25),
            "dat_trzby": self.date_order,
            "celk_trzba": self.amount_total,
            "currency_id": self.currency_id.id,
            "prvni_zaslani": True,
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
                continue
            try:
                tx = Tx.create_from_values(
                    order.company_id, **order._l10n_cz_eet2_prepare_values())
                order.l10n_cz_eet2_transaction_id = tx
                tx._send()
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
        """Manual retry (e.g. after a temporary error kod<0). Clears the old link."""
        for order in self:
            order.l10n_cz_eet2_transaction_id = False
            order._l10n_cz_eet2_try_register()

    # NOTE: do NOT override _load_pos_data_fields for pos.order. Its base returns
    # [] which read() treats as "all fields", so our stored related fields
    # (l10n_cz_eet2_pok/state/is_test) load automatically. Returning a non-empty
    # list here restricts the load and drops `lines`/`payment_ids`, breaking POS
    # price computation (this.lines undefined -> _computeAllPrices crash).
