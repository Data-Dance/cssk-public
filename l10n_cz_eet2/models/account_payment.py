# -*- coding: utf-8 -*-
import logging
import re

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

_ALLOWED = re.compile(r"[^0-9a-zA-Z\.,:;/#\-_ ]")


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # The current sale message; related fields below follow it. Every message
    # the payment ever produced (sales, § 8 stornos) is in the one2many.
    l10n_cz_eet2_transaction_id = fields.Many2one(
        "l10n.cz.eet2.transaction", string="EET 2.0 Message", copy=False)
    l10n_cz_eet2_transaction_ids = fields.One2many(
        "l10n.cz.eet2.transaction", "payment_id", string="EET 2.0 Messages",
        copy=False)
    l10n_cz_eet2_transaction_count = fields.Integer(
        string="EET 2.0 Message Count",
        compute="_compute_l10n_cz_eet2_transaction_count")
    l10n_cz_eet2_pok = fields.Char(
        related="l10n_cz_eet2_transaction_id.pok", store=True, string="EET 2.0 POK")
    l10n_cz_eet2_state = fields.Selection(
        related="l10n_cz_eet2_transaction_id.state", store=True,
        string="EET 2.0 Status")
    # The journal only gives the default: the same bank account receives a QR
    # scanned at the counter (a contact payment, § 6 ZoET) and the same QR paid
    # from home (not one). The cashier decides per payment.
    l10n_cz_eet2_contact = fields.Boolean(
        string="EET 2.0 Contact Payment",
        compute="_compute_l10n_cz_eet2_contact", store=True, readonly=False,
        copy=False,
        help="Received in person or on the premises (cash, card, QR scanned at "
            "the counter): recorded by EET 2.0. Defaults from the journal; untick "
            "for a remote payment, tick for a counter payment in a bank journal.")
    l10n_cz_eet2_needed = fields.Boolean(
        string="EET 2.0 Applicable", compute="_compute_l10n_cz_eet2_needed")
    l10n_cz_eet2_available = fields.Boolean(
        string="EET 2.0 Available", compute="_compute_l10n_cz_eet2_needed")

    @api.depends("journal_id")
    def _compute_l10n_cz_eet2_contact(self):
        for pay in self:
            pay.l10n_cz_eet2_contact = bool(pay.journal_id.l10n_cz_eet2_contact)

    @api.depends("l10n_cz_eet2_transaction_ids")
    def _compute_l10n_cz_eet2_transaction_count(self):
        for pay in self:
            pay.l10n_cz_eet2_transaction_count = len(pay.l10n_cz_eet2_transaction_ids)

    def _l10n_cz_eet2_is_registrable(self):
        """Hook: whether this payment may register a sale at all. The POS
        bridge answers no for payments that close a POS session, whose
        orders were registered one by one already."""
        self.ensure_one()
        return True

    @api.depends("l10n_cz_eet2_contact", "company_id.l10n_cz_eet2_enabled",
                "company_id.l10n_cz_eet2_eic_popl", "state", "partner_type")
    def _compute_l10n_cz_eet2_needed(self):
        for pay in self:
            company = pay.company_id
            pay.l10n_cz_eet2_available = bool(
                company.l10n_cz_eet2_enabled and company.l10n_cz_eet2_eic_popl)
            # Only customer money is a tržba: cash paid to a supplier is not
            # a sale, and a customer refund is a negative one (§ 8 ZoET).
            pay.l10n_cz_eet2_needed = bool(
                pay.l10n_cz_eet2_available and pay.l10n_cz_eet2_contact
                and pay.partner_type == "customer"
                and pay._l10n_cz_eet2_is_registrable())

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
            if pay.state not in ("in_process", "paid"):
                continue
            current = pay.l10n_cz_eet2_transaction_id
            # A sale that was reversed (§ 8) is finished; a re-posted payment
            # is a new sale and gets a new message.
            if current and not current.reversed_by_id:
                continue
            if not pay.l10n_cz_eet2_needed:
                continue
            try:
                # The live-sale unique index is checked by Postgres on the
                # INSERT, against columns, so any pending reversal must land first.
                Tx.flush_model(["reversed_by_id", "storno_of_id", "payment_id"])
                tx = Tx.create_from_values(
                    pay.company_id, payment_id=pay.id,
                    **pay._l10n_cz_eet2_prepare_values())
                pay.l10n_cz_eet2_transaction_id = tx
                tx._enqueue()
            except Exception as exc:  # noqa: BLE001 - must never block posting
                _logger.warning(
                    "EET 2.0: failed to queue payment %s: %s", pay.name, exc)

    def action_post(self):
        res = super().action_post()
        self.sudo()._l10n_cz_eet2_try_register()
        return res

    # § 8 ZoET: "Vrací-li se evidovaná tržba nebo její část nebo provádí-li se
    # její opravy, použijí se ustanovení ... obdobně s tím, že je tato tržba
    # evidována jako záporná." Resetting a posted payment to draft or
    # cancelling it undoes a registered sale, so a negative message goes out,
    # dated now (methodology ch. 4: a correction is evidenced when its reason
    # is found). The sale message is left as it is: the gateway keeps both.
    _L10N_CZ_EET2_REVERSIBLE = ("to_send", "retry", "error", "accepted")

    def _l10n_cz_eet2_storno_registered(self):
        for pay in self:
            sale = pay.l10n_cz_eet2_transaction_id
            if pay.state not in ("in_process", "paid") or not sale:
                continue
            if sale.reversed_by_id or sale.storno_of_id:
                continue
            # A rejected sale was never evidenced and will not be unless
            # someone requeues it; a pending one will be, so it needs its
            # counterpart just like an accepted one.
            if sale.state not in self._L10N_CZ_EET2_REVERSIBLE:
                continue
            try:
                sale._create_storno()._enqueue()
            except Exception as exc:  # noqa: BLE001 - must never block the reversal
                _logger.warning(
                    "EET 2.0: failed to queue the storno of payment %s: %s", pay.name, exc)

    def action_draft(self):
        self.sudo()._l10n_cz_eet2_storno_registered()
        return super().action_draft()

    def action_cancel(self):
        self.sudo()._l10n_cz_eet2_storno_registered()
        return super().action_cancel()

    def l10n_cz_eet2_action_send(self):
        """Manual send now. The existing message is reused: a second message
        for the same sale would be a second sale (methodology ch. 6: a repeat
        is the same Data with a new UUID, not a new record)."""
        for pay in self:
            tx = pay.l10n_cz_eet2_transaction_id
            if tx and tx.state == "accepted":
                continue                      # already evidenced: nothing to redo
            if tx and not tx.reversed_by_id:
                if tx.state in ("error", "rejected"):
                    tx.action_requeue()
                tx._send()
            else:
                pay._l10n_cz_eet2_try_register()

    def action_l10n_cz_eet2_open_transactions(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_cz_eet2.action_eet2_transaction")
        action["domain"] = [("payment_id", "=", self.id)]
        action["context"] = {"default_payment_id": self.id}
        return action
