"""Authoritative ledger of NOP KVERKOM transactions.

One record per transaction id minted via ``generateNewTransactionId``.

State machine
=============

::

    draft   — placeholder (rarely used)
    pending — tx id minted, waiting for bank push
       │
       ├── received   — bank push arrived, integrity + amount match
       │       └── confirmed — downstream consumer (POS, account) finalized it
       ├── mismatch   — bank push arrived with bad hash or wrong amount
       ├── cancelled  — cashier explicitly said "customer did not pay"
       │       └── mismatch (on late push)
       ├── expired    — retention window closed without push (cancel-like)
       └── unconfirmed_closed
              — cashier closed the POS sale without waiting for NOP; a
                separate non-confirmation receipt ("doklad o nepotvrdení
                zrealizovanej platby") was issued. The sale was completed
                with a different payment method, so the NOP push, if it
                eventually arrives, represents a duplicate payment that
                must be refunded to the debtor.
              ├── refund_pending    — late push arrived (valid), refund owed
              │       └── refunded  — back-office recorded the outbound SEPA refund
              ├── mismatch          — late push arrived with bad hash/amount
              └── expired_unreceived — 7 days passed without any push
"""

import hashlib
import logging

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class NopTransaction(models.Model):
    _name = "nop.transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "NOP KVERKOM Transaction"
    _order = "create_date desc"
    _rec_name = "transaction_id"

    pos_config_id = fields.Many2one(
        "pos.config", ondelete="restrict", index=True, tracking=True,
        string="POS Config",
    )
    company_id = fields.Many2one(
        related="pos_config_id.company_id", store=True, readonly=True
    )
    transaction_id = fields.Char(
        string="Transaction ID",
        required=True,
        index=True,
        copy=False,
        tracking=True,
        help='NOP-issued end-to-end id, always formatted "QR-<32-hex-uuid>".',
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("received", "Received"),
            ("confirmed", "Confirmed"),
            ("mismatch", "Mismatch"),
            ("cancelled", "Cancelled"),
            ("expired", "Expired"),
            ("unconfirmed_closed", "Closed without confirmation"),
            ("refund_pending", "Refund pending"),
            ("refunded", "Refunded"),
            ("expired_unreceived", "Expired (no notification)"),
        ],
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )

    # Expected values — filled by the caller when minting the tx id.
    expected_iban = fields.Char(
        required=True, tracking=True,
        help="Merchant IBAN expected to receive the payment.",
    )
    expected_amount = fields.Float(required=True, digits=(16, 2), tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.ref("base.EUR"),
    )
    comment = fields.Char()
    expires_at = fields.Datetime(
        help="When the merchant-side UI should stop waiting. The NOP retention window is 2 h; "
        "a shorter window is usually set to match the POS / checkout UX.",
    )

    # Actual values — filled when the bank push arrives.
    received_at = fields.Datetime(copy=False, tracking=True)
    bank_iban = fields.Char(
        copy=False,
        help="Creditor IBAN from the NOP payload (the merchant account the bank credited).",
    )
    bank_creditor_name = fields.Char(copy=False)
    debtor_iban = fields.Char(
        copy=False, tracking=True,
        help="Payer IBAN from the NOP payload. Needed to refund a late-arriving unconfirmed payment.",
    )
    received_amount = fields.Float(digits=(16, 2), copy=False, tracking=True)
    data_integrity_hash = fields.Char(copy=False)
    integrity_ok = fields.Boolean(copy=False)
    amount_ok = fields.Boolean(copy=False)
    raw_payload = fields.Text(copy=False)

    # Close-without-confirmation tracking.
    closed_unconfirmed_at = fields.Datetime(copy=False, tracking=True)
    closed_unconfirmed_by_id = fields.Many2one("res.users", copy=False)
    refunded_at = fields.Datetime(copy=False, tracking=True)
    refunded_by_id = fields.Many2one("res.users", copy=False)
    refund_reference = fields.Char(
        copy=False, tracking=True,
        help="Merchant-entered reference of the outbound SEPA refund (bank statement line, internal ticket id, etc.).",
    )

    history_lookup_count = fields.Integer(
        copy=False, default=0,
        help="How many times the public getTransactionHistory endpoint has been queried for this tx.",
    )
    history_last_lookup_at = fields.Datetime(copy=False)

    # Polymorphic back-reference so POS / invoice modules can link to their own records.
    source_model = fields.Char(index=True, copy=False)
    source_id = fields.Integer(index=True, copy=False)
    payment_transaction_id = fields.Many2one(
        "payment.transaction", copy=False, ondelete="set null", index=True,
        help="Mirror record in the Odoo payment module (created by downstream integrations).",
    )

    qr_code_url = fields.Char(
        help="payme.sk URL encoded in the QR code shown to the customer.",
        readonly=True,
        copy=False,
    )

    public_history_url = fields.Char(
        compute="_compute_public_history_url",
        help="Public (no-auth) URL where anyone can verify the settlement status of this tx.",
    )

    _transaction_id_uniq = models.Constraint(
        "unique(transaction_id)",
        "A NOP transaction with this id already exists.",
    )

    @api.depends("pos_config_id.nop_history_url", "transaction_id")
    def _compute_public_history_url(self):
        for rec in self:
            url = rec.pos_config_id.nop_history_url
            if url and rec.transaction_id:
                rec.public_history_url = (
                    f"{url}/api/v1/getTransactionHistory/{rec.transaction_id}"
                )
            else:
                rec.public_history_url = False

    # ------------------------------------------------------------------
    # Ingestion of NOP-side notifications
    # ------------------------------------------------------------------

    @api.model
    def _compute_integrity_hash(self, iban, amount, end_to_end_id, currency="EUR"):
        """Compute SHA-256 of ``IBAN|AMOUNT|CURRENCY|endToEndId`` per SBA standard."""
        if isinstance(amount, (int, float)):
            amount_str = f"{amount:.2f}"
        else:
            amount_str = str(amount)
        payload = f"{iban}|{amount_str}|{currency}|{end_to_end_id}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    # States that accept a late NOP push. Anything outside this set is either
    # already-finalized (confirmed/refunded) or terminal-failure (mismatch,
    # expired*), so a duplicate message must be dropped.
    _INGESTABLE_STATES = frozenset((
        "draft", "pending", "cancelled", "expired",
        "unconfirmed_closed",
    ))

    def _ingest_notification(self, notification):
        """Apply a parsed NOP notification dict to self.

        Expected keys (per SBA Push Payment Notification / NOP response):
            transactionStatus, transactionAmount{currency, amount},
            endToEndId, dataIntegrityHash,
            creditorAccount{iban}, debtorAccount{iban}, creditorName, receivedAt

        Returns True if the record's state moved, False if this was a
        duplicate / no-op (e.g. the tx was already finalized).
        """
        self.ensure_one()
        if self.state not in self._INGESTABLE_STATES:
            _logger.debug(
                "Dropping NOP notification for %s: state %s is terminal",
                self.transaction_id, self.state,
            )
            return False

        amount_info = notification.get("transactionAmount") or {}
        raw_amount = amount_info.get("amount")
        currency = amount_info.get("currency") or "EUR"
        received_amount = float(raw_amount) if raw_amount is not None else 0.0
        bank_iban = (notification.get("creditorAccount") or {}).get("iban") or ""
        debtor_iban = (
            (notification.get("debtorAccount") or {}).get("iban")
            or notification.get("debtorIBAN")  # bank-side alias seen in live payloads
            or ""
        )
        received_hash = notification.get("dataIntegrityHash") or ""
        end_to_end = notification.get("endToEndId") or self.transaction_id

        # The bank signs the hash over the values it credits, so recompute
        # against received amount + advertised creditor IBAN. A short/over
        # payment is tracked separately via ``amount_ok``.
        hash_iban = bank_iban or self.expected_iban
        expected_hash = self._compute_integrity_hash(
            hash_iban, received_amount, end_to_end, currency=currency,
        )
        integrity_ok = received_hash.lower() == expected_hash.lower()

        tol = self.currency_id.rounding or 0.01
        amount_ok = abs(received_amount - self.expected_amount) < tol

        vals = {
            "received_at": fields.Datetime.now(),
            "bank_iban": bank_iban,
            "bank_creditor_name": notification.get("creditorName"),
            "debtor_iban": debtor_iban,
            "received_amount": received_amount,
            "data_integrity_hash": received_hash,
            "integrity_ok": integrity_ok,
            "amount_ok": amount_ok,
            "raw_payload": str(notification),
        }

        prior_state = self.state
        if not integrity_ok or not amount_ok:
            vals["state"] = "mismatch"
            _logger.warning(
                "NOP notification mismatch for %s — integrity_ok=%s amount_ok=%s "
                "(expected %s %s, got %s %s)",
                self.transaction_id, integrity_ok, amount_ok,
                self.expected_amount, self.currency_id.name,
                received_amount, currency,
            )
        elif prior_state == "cancelled":
            vals["state"] = "mismatch"
            _logger.warning("Late NOP push for cancelled transaction %s", self.transaction_id)
        elif prior_state == "unconfirmed_closed":
            # The sale was already closed with a different payment method.
            # This late push means the customer *also* paid via QR — owe them
            # a refund.
            vals["state"] = "refund_pending"
            _logger.info(
                "Late NOP push for unconfirmed_closed transaction %s — refund owed "
                "to debtor %s for %s %s",
                self.transaction_id, debtor_iban or "?",
                received_amount, currency,
            )
        elif prior_state == "expired":
            # Payment arrived after we gave up on it. Treat like unconfirmed_closed.
            vals["state"] = "refund_pending"
        else:
            vals["state"] = "received"

        self.write(vals)

        if vals["state"] == "refund_pending":
            self._post_refund_pending_notification()
        elif vals["state"] == "received":
            self._notify_downstream()
        return True

    def _post_refund_pending_notification(self):
        """Surface late-arriving duplicates to bookkeeping via chatter + bus."""
        self.ensure_one()
        self.message_post(
            # The IBAN comes off an inbound payment message, so it is escaped
            # by ``%`` on the Markup rather than trusted into the template.
            body=Markup(_(
                "Late NOP payment received after the sale was closed without "
                "confirmation. Refund %(amount)s %(currency)s to debtor IBAN "
                "<b>%(iban)s</b>."
            )) % {
                "amount": self.received_amount,
                "currency": self.currency_id.name,
                "iban": self.debtor_iban or _("(not provided)"),
            },
        )
        self.env["bus.bus"]._sendone(
            (self.env.cr.dbname, "nop.refund_pending", self.company_id.id),
            "nop.refund_pending",
            {"id": self.id, "transaction_id": self.transaction_id},
        )

    def _notify_downstream(self):
        """Hook for downstream modules (POS, account) to finalize the payment.

        Concrete integrations override this to create pos.payment / account.payment.
        Called only when state transitions to ``received``; we never downstream-
        finalize ``refund_pending`` because the sale was paid with a different
        method and a duplicate pos.payment would mis-state the accounts.
        """
        return True

    # ------------------------------------------------------------------
    # Minting helper
    # ------------------------------------------------------------------

    @api.model
    def _create_for_pos_config(
        self,
        pos_config,
        amount,
        comment=None,
        source_model=None,
        source_id=None,
        expires_in_seconds=300,
        currency=None,
    ):
        """Mint a new NOP transaction id and persist a ``pending`` record."""
        from datetime import timedelta
        client = self.env["nop.client"]
        tx_id = client._generate_transaction_id(pos_config, comment=comment)
        expires_at = fields.Datetime.now() + timedelta(seconds=expires_in_seconds)
        return self.create({
            "pos_config_id": pos_config.id,
            "transaction_id": tx_id,
            "state": "pending",
            "expected_iban": pos_config.nop_iban_id.sanitized_acc_number,
            "expected_amount": amount,
            "currency_id": (currency or self.env.ref("base.EUR")).id,
            "comment": (comment or "")[:256],
            "expires_at": expires_at,
            "source_model": source_model,
            "source_id": source_id,
        })

    # ------------------------------------------------------------------
    # User-facing transitions
    # ------------------------------------------------------------------

    def action_cancel(self):
        """Cashier explicitly says "the customer did not pay"."""
        for rec in self.filtered(lambda r: r.state in ("draft", "pending")):
            rec.state = "cancelled"
        return True

    def action_close_unconfirmed(self):
        """Close the POS sale without waiting for NOP.

        The cashier concluded the customer could not wait; a separate
        non-confirmation receipt ("doklad o nepotvrdení zrealizovanej platby")
        is issued and the sale is completed with a different payment method.
        If the NOP push does arrive later, the late credit must be refunded to
        the debtor — the tx will auto-transition to ``refund_pending``.

        Idempotent: if the NOP push already arrived and the tx is already
        ``received`` or ``confirmed``, this is a no-op (returns False).
        """
        for rec in self:
            if rec.state == "pending":
                rec.write({
                    "state": "unconfirmed_closed",
                    "closed_unconfirmed_at": fields.Datetime.now(),
                    "closed_unconfirmed_by_id": self.env.user.id,
                })
        return True

    def action_mark_refunded(self, refund_reference=None):
        """Back-office flag: the outbound SEPA refund has been executed."""
        for rec in self:
            if rec.state != "refund_pending":
                raise UserError(
                    _("Transaction %s is not awaiting a refund (state=%s).")
                    % (rec.transaction_id, rec.state),
                )
            rec.write({
                "state": "refunded",
                "refunded_at": fields.Datetime.now(),
                "refunded_by_id": self.env.user.id,
                "refund_reference": refund_reference or rec.refund_reference,
            })
        return True

    def action_print_non_confirmation(self):
        """Trigger the QWeb non-confirmation receipt report."""
        self.ensure_one()
        return self.env.ref(
            "nop_kverkom_base.action_report_non_confirmation"
        ).report_action(self)

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------

    @api.model
    def _cron_expire_pending(self):
        """Mark stale records as expired.

        * ``pending`` older than 2h5m → ``expired`` (NOP retention is 2h)
        * ``unconfirmed_closed`` older than 7d → ``expired_unreceived``
          (we've given up on getting a late confirmation, back-office should
          close the case).
        """
        from datetime import timedelta
        now = fields.Datetime.now()

        stale_pending = self.search([
            ("state", "=", "pending"),
            ("create_date", "<", now - timedelta(hours=2, minutes=5)),
        ])
        if stale_pending:
            stale_pending.write({"state": "expired"})

        stale_unconfirmed = self.search([
            ("state", "=", "unconfirmed_closed"),
            ("closed_unconfirmed_at", "<", now - timedelta(days=7)),
        ])
        if stale_unconfirmed:
            stale_unconfirmed.write({"state": "expired_unreceived"})
        return True

    @api.model
    def _cron_fetch_history(self):
        """Poll the public ``getTransactionHistory`` endpoint for
        ``unconfirmed_closed`` transactions older than 2h (beyond NOP's live
        retention window) and up to 7 days old. Confirmations found this way
        transition the tx to ``refund_pending``.

        At most once per day per transaction to avoid hammering the public
        endpoint.
        """
        from datetime import timedelta
        now = fields.Datetime.now()
        cutoff_from = now - timedelta(days=7)
        cutoff_to = now - timedelta(hours=2)
        last_try_cutoff = now - timedelta(hours=23)

        candidates = self.search([
            ("state", "=", "unconfirmed_closed"),
            ("closed_unconfirmed_at", ">=", cutoff_from),
            ("closed_unconfirmed_at", "<=", cutoff_to),
            "|",
            ("history_last_lookup_at", "=", False),
            ("history_last_lookup_at", "<", last_try_cutoff),
        ])

        client = self.env["nop.client"]
        for tx in candidates:
            try:
                payload = client._fetch_history(tx.pos_config_id, tx.transaction_id)
            except Exception:
                _logger.exception(
                    "getTransactionHistory failed for %s", tx.transaction_id,
                )
                tx.write({
                    "history_last_lookup_at": fields.Datetime.now(),
                    "history_lookup_count": tx.history_lookup_count + 1,
                })
                continue
            tx.write({
                "history_last_lookup_at": fields.Datetime.now(),
                "history_lookup_count": tx.history_lookup_count + 1,
            })
            if payload and isinstance(payload, dict) and payload.get("endToEndId"):
                tx._ingest_notification(payload)
        return True
