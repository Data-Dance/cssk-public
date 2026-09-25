# -*- coding: utf-8 -*-
import logging
import re

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

_ALLOWED = re.compile(r"[^0-9a-zA-Z\.,:;/#\-_ ]")


class AccountPayment(models.Model):
    _inherit = "account.payment"

    l10n_cz_eet2_transaction_id = fields.Many2one(
        "l10n.cz.eet2.transaction", string="EET 2.0 Message", copy=False)
    l10n_cz_eet2_pok = fields.Char(
        related="l10n_cz_eet2_transaction_id.pok", store=True, string="EET 2.0 POK")
    l10n_cz_eet2_state = fields.Selection(
        related="l10n_cz_eet2_transaction_id.state", store=True,
        string="EET 2.0 Status")
    l10n_cz_eet2_needed = fields.Boolean(
        string="EET 2.0 Applicable", compute="_compute_l10n_cz_eet2_needed")

    @api.depends("journal_id.l10n_cz_eet2_contact", "company_id.l10n_cz_eet2_enabled",
                "company_id.l10n_cz_eet2_eic_popl", "state")
    def _compute_l10n_cz_eet2_needed(self):
        for pay in self:
            company = pay.company_id
            pay.l10n_cz_eet2_needed = bool(
                company.l10n_cz_eet2_enabled
                and company.l10n_cz_eet2_eic_popl
                and pay.journal_id.l10n_cz_eet2_contact)

    # ------------------------------------------------------------------
    @staticmethod
    def _l10n_cz_eet2_sanitize(value, maxlen):
        return _ALLOWED.sub("-", (value or "").strip())[:maxlen] or "0"

    def _l10n_cz_eet2_prepare_values(self):
        self.ensure_one()
        journal = self.journal_id
        company = self.company_id
        # A refund/outbound customer payment reduces recorded income -> negative.
        sign = 1 if self.payment_type == "inbound" else -1
        # Combine the payment date with the current time so the timestamp is
        # unambiguous; the stored Datetime is interpreted in the user's tz.
        dt = fields.Datetime.now()
        if self.date:
            dt = fields.Datetime.to_datetime(self.date).replace(
                hour=dt.hour, minute=dt.minute, second=dt.second)
        return {
            "environment": company.l10n_cz_eet2_environment,
            "certificate_id": company.l10n_cz_eet2_certificate_id.id or False,
            "eic_popl": company.l10n_cz_eet2_eic_popl,
            "id_jednotky": (journal.l10n_cz_eet2_id_jednotky
                            or company.l10n_cz_eet2_id_jednotky),
            "id_pokl": self._l10n_cz_eet2_sanitize(
                journal.l10n_cz_eet2_id_pokl or journal.code, 20),
            "porad_cis": self._l10n_cz_eet2_sanitize(self.name or self.memo, 25),
            "dat_trzby": dt,
            "celk_trzba": sign * self.amount,
            "currency_id": self.currency_id.id,
            "prvni_zaslani": True,
        }

    def _l10n_cz_eet2_try_register(self):
        """Queue the payment for EET 2.0. Never blocks posting.

        Back-office payments are sent asynchronously by the scheduled job so
        posting stays fast; the POK appears once the job runs (within the cron
        interval). Failures are retried by the same job.
        """
        Tx = self.env["l10n.cz.eet2.transaction"]
        for pay in self:
            if pay.l10n_cz_eet2_transaction_id or pay.state not in ("in_process", "paid"):
                continue
            if not pay.l10n_cz_eet2_needed:
                continue
            try:
                tx = Tx.create_from_values(
                    pay.company_id, **pay._l10n_cz_eet2_prepare_values())
                pay.l10n_cz_eet2_transaction_id = tx
                tx._enqueue()
            except Exception as exc:  # noqa: BLE001 - must never block posting
                _logger.warning(
                    "EET 2.0: failed to queue payment %s: %s", pay.name, exc)

    def action_post(self):
        res = super().action_post()
        self.sudo()._l10n_cz_eet2_try_register()
        return res

    def l10n_cz_eet2_action_send(self):
        """Manual (re)send, e.g. after a temporary error kod<0."""
        for pay in self:
            pay.l10n_cz_eet2_transaction_id = False
            pay._l10n_cz_eet2_try_register()
