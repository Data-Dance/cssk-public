# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules import module
from odoo.tools import SQL, sql

from ..lib import eet2_client

_logger = logging.getLogger(__name__)

ENDPOINTS = {
    "playground": eet2_client.ENDPOINT_PLAYGROUND,
    "production": eet2_client.ENDPOINT_PRODUCTION,
}

# Error codes that warrant a retry (temporary technical errors). Everything else
# positive (2/3=schema, 4=signature, 6=EIC, 7=too big) is a permanent rejection.
RETRYABLE_KODS = {8}          # 8 = technical/data error; kod<0 (e.g. -1) also retries
BACKOFF_BASE_MINUTES = 2      # 2, 4, 8, 16, 32, 60, 60, ... (capped)
BACKOFF_CAP_MINUTES = 60
# § 20 ZoET: after the response-time limit is exceeded the data must be sent
# "bezodkladně po pominutí příčiny, nejpozději však do 48 hodin od uskutečnění
# evidované tržby" — and the duty survives that deadline (FS answer 5570), so a
# message is never abandoned: past 48 h it keeps going at the capped cadence.
OVERDUE_HOURS = 48
ERROR_RETRY_MINUTES = 60      # a build-phase failure is re-tried hourly, not parked
# Timeout for the asynchronous (cron / manual) path; the synchronous POS path
# uses the company's "mezní doba odezvy" instead.
ASYNC_TIMEOUT = 30


class Eet2Transaction(models.Model):
    _name = "l10n.cz.eet2.transaction"
    _description = "EET 2.0 Registered-sale Data Message"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "uuid_zpravy"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company)
    certificate_id = fields.Many2one(
        "l10n.cz.eet2.certificate", string="Certificate")
    environment = fields.Selection(
        [("playground", "Playground (non-production)"),
        ("production", "Production")],
        required=True, default="playground")

    # --- Hlavicka ---
    uuid_zpravy = fields.Char(string="Message UUID", copy=False, index=True)
    uuid_history = fields.Text(
        string="Previous message UUIDs", copy=False, readonly=True,
        help="One line per earlier attempt. Every attempt carries a fresh "
            "uuid_zpravy, dat_odesl and prvni_zaslani while the sale data stays "
            "identical (item methodology, ch. 6); the gateway recognises the "
            "sale by the data, not by the UUID.")
    prvni_zaslani = fields.Boolean(string="First sending", default=True)
    overeni = fields.Boolean(
        string="Verification mode",
        help="If set, the message is only validated; no valid POK is issued.")

    # --- source document and § 8 storno links ---
    payment_id = fields.Many2one(
        "account.payment", string="Payment", ondelete="set null", copy=False,
        index="btree_not_null",
        help="The back-office payment this message registers or reverses.")
    storno_of_id = fields.Many2one(
        "l10n.cz.eet2.transaction", string="Storno of", copy=False,
        ondelete="set null", index="btree_not_null",
        help="Set on a negative message that reverses this sale (§ 8 ZoET).")
    reversed_by_id = fields.Many2one(
        "l10n.cz.eet2.transaction", string="Reversed by", copy=False,
        ondelete="set null",
        help="The storno message that reversed this sale.")

    # --- Data (mandatory) ---
    eic_popl = fields.Char(string="Taxpayer EIC", required=True)
    id_jednotky = fields.Integer(string="Unit ID", required=True)
    id_pokl = fields.Char(string="PoS ID", required=True)
    porad_cis = fields.Char(string="Sequence number", required=True)
    dat_trzby = fields.Datetime(string="Sale date/time", required=True)
    # § 17 odst. 1 písm. f) ZoET: the total is always in CZK. ``currency_id`` is
    # therefore CZK; the amount the sale was actually made in is kept beside it.
    celk_trzba = fields.Monetary(string="Total amount (CZK)", required=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.ref("base.CZK"))
    source_amount = fields.Monetary(
        string="Original amount", currency_field="source_currency_id", copy=False,
        help="The total in the currency the sale was made in, before the "
            "conversion to CZK. Empty when the sale was already in CZK.")
    source_currency_id = fields.Many2one(
        "res.currency", string="Original currency", copy=False)
    # --- Data (optional) ---
    eic_poverujiciho = fields.Char(string="Authorizing taxpayer EIC")
    povereni_vice_popl = fields.Boolean(string="Multi-taxpayer authorization")
    urceno_cerp_zuct = fields.Monetary(string="Intended for drawing/settlement")
    cerp_zuct = fields.Monetary(string="Drawn/settled")

    # --- response ---
    state = fields.Selection(
        [("draft", "Draft"),
        ("to_send", "To Send"),
        ("retry", "Retry Scheduled"),
        ("accepted", "Accepted"),
        ("verified", "Verified (mode)"),
        ("rejected", "Rejected"),
        ("error", "Error")],
        default="draft", required=True, copy=False, index=True)
    attempt_count = fields.Integer(string="Attempts", default=0, copy=False)
    next_attempt = fields.Datetime(
        string="Next attempt", copy=False, index=True,
        help="When the scheduled job will next try to send this message.")
    is_overdue = fields.Boolean(
        string="Past 48 h", copy=False, index=True,
        help="The message was still unsent 48 hours after the sale (§ 20 ZoET). "
            "Retries continue hourly; the duty to send does not lapse.")
    pok = fields.Char(string="POK (Acknowledgement code)", copy=False)
    dat_prij = fields.Datetime(string="Received at", copy=False)
    dat_odmit = fields.Datetime(string="Rejected at", copy=False)
    is_test_response = fields.Boolean(string="Non-production response", copy=False)
    chyba_kod = fields.Integer(string="Error code", copy=False)
    chyba_text = fields.Char(string="Error message", copy=False)
    warning_text = fields.Text(string="Warnings", copy=False)
    xgtid = fields.Char(string="X-Global-Transaction-Id", copy=False)
    request_xml = fields.Text(string="Request XML", copy=False)
    response_xml = fields.Text(string="Response XML", copy=False)

    # One storno per sale and one live sale per payment, enforced where two
    # workers could otherwise both pass the Python guard (a double click on
    # Reset to draft, two posts of one payment): the second insert fails and
    # the caller's try/except logs it instead of evidencing the sale twice.
    # 18.0 has no ``models.UniqueIndex``; the partial unique indexes are
    # created in ``init()`` instead (same names and definitions as on 19.0).
    _PARTIAL_UNIQUE_INDEXES = (
        ("l10n_cz_eet2_transaction_storno_once",
         "(storno_of_id) WHERE storno_of_id IS NOT NULL"),
        ("l10n_cz_eet2_transaction_one_live_sale_per_payment",
         "(payment_id) WHERE payment_id IS NOT NULL AND storno_of_id IS NULL "
         "AND reversed_by_id IS NULL"),
    )

    def init(self):
        super().init()
        for name, definition in self._PARTIAL_UNIQUE_INDEXES:
            if not sql.index_exists(self.env.cr, name):
                self.env.cr.execute(SQL(
                    "CREATE UNIQUE INDEX %s ON %s %s",
                    SQL.identifier(name), SQL.identifier(self._table), SQL(definition)))

    @api.model_create_multi
    def create(self, vals_list):
        # No "created" note in the chatter: the message itself is the record.
        return super(Eet2Transaction, self.with_context(mail_create_nolog=True)).create(vals_list)

    # ------------------------------------------------------------------
    @staticmethod
    def _fmt_amount(value):
        """Format a monetary value per the XSD mask (exactly 2 decimals, no -0.00)."""
        if value is None:
            return None
        text = "%.2f" % (value + 0.0)
        return "0.00" if text == "-0.00" else text

    def _get_endpoint(self):
        return ENDPOINTS[self.environment]

    def _local_iso(self, value):
        """Naive UTC -> ISO-8601 with the user's offset (e.g. +02:00), as the
        XSD dateTime mask requires; Odoo stores datetimes as naive UTC."""
        return fields.Datetime.context_timestamp(
            self, value).replace(microsecond=0).isoformat()

    def _prepare_trzba(self):
        """One attempt's message. The header is new every time: a fresh
        ``uuid_zpravy`` and the real ``dat_odesl``; the Data block never
        changes between attempts (item methodology, ch. 6)."""
        self.ensure_one()
        dt = fields.Datetime.context_timestamp(self, self.dat_trzby)
        dt = dt.replace(microsecond=0)
        trzba = eet2_client.Trzba(
            eic_popl=self.eic_popl,
            id_jednotky=self.id_jednotky,
            id_pokl=self.id_pokl,
            porad_cis=self.porad_cis,
            dat_trzby=dt.isoformat(),
            celk_trzba=self._fmt_amount(self.celk_trzba),
            eic_poverujiciho=self.eic_poverujiciho or None,
            povereni_vice_popl=self.povereni_vice_popl or None,
            urceno_cerp_zuct=self._fmt_amount(self.urceno_cerp_zuct)
                            if self.urceno_cerp_zuct else None,
            cerp_zuct=self._fmt_amount(self.cerp_zuct) if self.cerp_zuct else None,
            prvni_zaslani=self.prvni_zaslani,
            overeni=self.overeni,
            dat_odesl=self._local_iso(fields.Datetime.now()),
            uuid_zpravy=None,          # a new UUID for every attempt
        )
        return trzba

    def _rotate_uuid(self, new_uuid):
        """Archive the previous attempt's UUID and take the new one."""
        self.ensure_one()
        if self.uuid_zpravy and self.uuid_zpravy != new_uuid:
            self.uuid_history = "\n".join(
                line for line in [self.uuid_history, self.uuid_zpravy] if line)
        self.uuid_zpravy = new_uuid

    def action_send(self):
        for rec in self:
            rec._send()
        return True

    def action_requeue(self):
        """Put failed messages back in the queue (new certificate, fixed data).

        Works from ``error`` (could not be built: missing/expired certificate)
        and ``rejected`` (permanent gateway error such as kod 4 bad signature),
        both of which a replaced certificate typically cures. Attempt history
        is kept: it is still the same sale, and any later try is a resend.
        """
        todo = self.filtered(lambda t: t.state in ("error", "rejected"))
        todo.write({"state": "to_send", "next_attempt": fields.Datetime.now(),
                    "chyba_kod": False, "chyba_text": False})
        return True

    def _enqueue(self):
        """Queue for the scheduled job to pick up (fully async path)."""
        self.write({"state": "to_send", "next_attempt": fields.Datetime.now()})

    def _warn_attempts(self):
        return self.company_id.l10n_cz_eet2_max_attempts or 0

    def _overdue_deadline(self):
        self.ensure_one()
        return self.dat_trzby + timedelta(hours=OVERDUE_HOURS)

    def _backoff_delay(self, now=None):
        """Exponential backoff, capped at an hour, that never sleeps past the
        48 h deadline: the attempt before the line falls exactly on it. After
        the line the cap keeps the cadence hourly."""
        now = now or fields.Datetime.now()
        minutes = min(BACKOFF_BASE_MINUTES * (2 ** max(self.attempt_count - 1, 0)),
                    BACKOFF_CAP_MINUTES)
        delay = timedelta(minutes=minutes)
        deadline = self._overdue_deadline()
        if now < deadline:
            delay = min(delay, max(deadline - now, timedelta(seconds=1)))
        return delay

    def _mark_overdue(self, now, vals):
        """Flag and notify once when an unsent message crosses the 48 h line."""
        if now >= self._overdue_deadline() and not self.is_overdue:
            vals["is_overdue"] = True
            self._notify_overdue()
        return vals

    def _schedule_retry(self, error):
        """Bump the attempt counter and reschedule. Never gives up (§ 20 ZoET)."""
        self.attempt_count += 1
        now = fields.Datetime.now()
        vals = {"state": "retry", "chyba_text": (error or "")[:500],
                "next_attempt": now + self._backoff_delay(now)}
        self.write(self._mark_overdue(now, vals))
        warn_after = self._warn_attempts()
        if warn_after and self.attempt_count >= warn_after:
            _logger.warning("EET 2.0: %s still unsent after %d attempts: %s",
                            self.uuid_zpravy, self.attempt_count, error)

    def _overdue_user(self):
        """Who gets the overdue activity: an EET 2.0 manager of the company."""
        group = self.env.ref("l10n_cz_eet2.group_eet2_manager", raise_if_not_found=False)
        users = group.users if group else self.env["res.users"]
        users = users.filtered(
            lambda u: u.active and self.company_id in u.company_ids and not u.share)
        return users[:1] or self.env.ref("base.user_admin")

    def _notify_overdue(self):
        self.ensure_one()
        _logger.warning("EET 2.0: message %s (%s %s) is past the 48 h deadline "
                        "and still unsent", self.uuid_zpravy, self.id_pokl,
                        self.porad_cis)
        try:
            self.activity_schedule(
                "mail.mail_activity_data_warning",
                user_id=self._overdue_user().id,
                summary=_("EET 2.0 sale unsent for 48 hours"),
                note=_("Sale %(ref)s of %(amount)s CZK made on %(date)s has not been "
                    "accepted by the EET 2.0 gateway within 48 hours (§ 20 ZoET). "
                    "Retries continue hourly; check the certificate, the network "
                    "and the last error: %(error)s",
                    ref="%s / %s" % (self.id_pokl, self.porad_cis),
                    amount=self._fmt_amount(self.celk_trzba),
                    date=self.dat_trzby, error=self.chyba_text or "-"))
        except Exception:  # noqa: BLE001 - a notification must never break a resend
            _logger.exception("EET 2.0: could not schedule the overdue activity")

    def _send(self, sync=False):
        """Build, sign and send; ``sync`` = at the till, bounded by § 19.

        The synchronous path waits at most the company's response-time limit
        (mezní doba odezvy); the asynchronous one (cron, manual button) can
        afford a longer transport timeout.
        """
        self.ensure_one()
        cert_rec = self.certificate_id or self.company_id.l10n_cz_eet2_certificate_id
        try:
            if not cert_rec:
                raise UserError(_("No EET 2.0 certificate configured."))
            # First attempt is prvni_zaslani=true; any later attempt is a resend.
            if self.attempt_count:
                self.prvni_zaslani = False
            cert = cert_rec._get_cert()
            trzba = self._prepare_trzba()
            self._rotate_uuid(trzba.uuid_zpravy)
            envelope = eet2_client.build_signed_request(trzba, cert)
            self.request_xml = envelope.decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001 - cert/build error
            # Usually a configuration problem (no / expired / wrong-password
            # certificate) that a certificate write re-queues at once; still
            # retried hourly so a transient failure (attachment store, I/O)
            # cannot park a sale for good (§ 20 ZoET).
            now = fields.Datetime.now()
            self.write(self._mark_overdue(now, {
                "state": "error", "chyba_text": str(exc)[:500],
                "next_attempt": now + timedelta(minutes=ERROR_RETRY_MINUTES)}))
            _logger.exception("EET 2.0: cannot build message %s", self.uuid_zpravy)
            return
        timeout = (self.company_id.l10n_cz_eet2_response_timeout or ASYNC_TIMEOUT
                if sync else ASYNC_TIMEOUT)
        try:
            result = eet2_client.send(envelope, endpoint=self._get_endpoint(),
                                    timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - transport failure -> retry
            self._schedule_retry(str(exc))
            _logger.info("EET 2.0 send failed for %s (will retry): %s",
                        self.uuid_zpravy, exc)
            return
        self._apply_response(envelope, result)

    def _apply_response(self, envelope, result):
        odp = result.odpoved
        vals = {
            "response_xml": (result.raw or b"").decode("utf-8", "replace"),
            "xgtid": result.xgtid,
            "pok": odp.pok,
            "is_test_response": odp.test,
            "dat_prij": self._parse_dt(odp.dat_prij),
            "dat_odmit": self._parse_dt(odp.dat_odmit),
            "chyba_kod": odp.chyba_kod,
            "chyba_text": odp.chyba_text,
            "warning_text": "\n".join("[%s] %s" % (k, t) for k, t in odp.varovani)
                            or False,
        }
        if odp.ok:
            vals["state"] = "accepted"
            vals["next_attempt"] = False
        elif odp.chyba_kod == 0:
            vals["state"] = "verified"  # verification-mode success
            vals["next_attempt"] = False
        elif odp.chyba_kod is not None and (
                odp.chyba_kod < 0 or odp.chyba_kod in RETRYABLE_KODS):
            self.write(vals)                       # store the response first
            return self._schedule_retry(odp.chyba_text or "kod=%s" % odp.chyba_kod)
        else:
            vals["state"] = "rejected"             # permanent critical error
            vals["next_attempt"] = False
        self.write(vals)
        if vals["state"] in ("accepted", "verified") and self.activity_ids:
            try:
                warning = self.env.ref("mail.mail_activity_data_warning",
                                    raise_if_not_found=False)
                self.activity_ids.sudo().filtered(
                    lambda a: a.activity_type_id == warning
                ).action_feedback(feedback=_("Accepted by the EET 2.0 gateway."))
            except Exception:  # noqa: BLE001 - closing a warning must not undo an acceptance
                _logger.exception("EET 2.0: could not close the overdue activity")

    @api.model
    def _cron_send_pending(self, limit=200):
        """Scheduled sender: process queued and retry-due messages.

        Commits per record so one failure never rolls back the whole batch and
        progress survives a mid-run interruption.
        """
        now = fields.Datetime.now()
        domain = [
            ("state", "in", ("to_send", "retry", "error")),
            "|", ("next_attempt", "=", False), ("next_attempt", "<=", now),
        ]
        pending = self.search(domain, limit=limit, order="next_attempt asc, id asc")
        done = 0
        for tx in pending:
            try:
                with self.env.cr.savepoint():
                    tx._send()
            except Exception as exc:  # noqa: BLE001 - never let one message kill the run
                _logger.exception("EET 2.0 cron: unexpected error on %s",
                                tx.uuid_zpravy)
                # The savepoint rolled the half-done send back; record the
                # attempt so the same crash does not re-run every two minutes.
                tx._schedule_retry("internal: %s" % exc)
            done += 1
            # Commit per message so one failure never rolls back the batch.
            # A test transaction must not be committed, so skip it there.
            if not module.current_test:
                self.env.cr.commit()
        if not module.current_test:
            # More due than this batch took: a non-zero ``remaining`` makes the
            # scheduler run the job again right away (18.0 progress API).
            remaining = self.search_count(domain) if len(pending) == limit else 0
            self.env["ir.cron"]._notify_progress(done=done, remaining=remaining)
        return True

    @staticmethod
    def _parse_dt(iso):
        """ISO-8601 with offset -> naive UTC string, whatever the host's zone."""
        if not iso:
            return False
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return fields.Datetime.to_string(dt)

    # ------------------------------------------------------------------
    @api.model
    def _to_czk(self, amount, currency, company, date):
        """Convert ``amount`` in ``currency`` to CZK at the company rate.

        FS answer 5012: the total is always in CZK, converted at the rate the
        taxpayer declares at that moment (the till's / the books' rate).
        """
        czk = self.env.ref("base.CZK")
        if not amount or not currency or currency == czk:
            return amount
        return currency._convert(amount, czk, company, date or fields.Date.today())

    def _create_storno(self, **kw):
        """A negative message reversing this sale (§ 8 ZoET, methodology ch. 4).

        Same taxpayer, unit, till and sequence number; amounts negated; dated
        at the reversal (the methodology dates a storno when the money goes
        back, or when the error is found). It is not linked to the original
        on the wire, only here. The caller enqueues or sends it.

        It goes to the environment the sale went to: a playground sale is
        never reversed on production or the other way round. The certificate
        is the company's current one when the company still points at that
        environment (the sale's may have expired since), else the sale's own.
        """
        self.ensure_one()
        company = self.company_id
        if company.l10n_cz_eet2_environment == self.environment:
            certificate = company.l10n_cz_eet2_certificate_id or self.certificate_id
        else:
            certificate = self.certificate_id
        vals = {
            "company_id": company.id,
            "environment": self.environment,
            "certificate_id": certificate.id or False,
            "eic_popl": self.eic_popl,
            "eic_poverujiciho": self.eic_poverujiciho or False,
            "povereni_vice_popl": self.povereni_vice_popl,
            "id_jednotky": self.id_jednotky,
            "id_pokl": self.id_pokl,
            "porad_cis": self.porad_cis,
            "dat_trzby": fields.Datetime.now(),
            "celk_trzba": -self.celk_trzba,
            "urceno_cerp_zuct": -self.urceno_cerp_zuct if self.urceno_cerp_zuct else False,
            "cerp_zuct": -self.cerp_zuct if self.cerp_zuct else False,
            "currency_id": self.currency_id.id,
            "payment_id": self.payment_id.id,
            "storno_of_id": self.id,
        }
        vals.update(kw)
        storno = self.create(vals)
        self.reversed_by_id = storno
        # The partial unique index on live sales reads the column, not the
        # cache: flush so a re-post in the same transaction can insert.
        self.flush_recordset(["reversed_by_id"])
        return storno

    @api.model
    def create_from_values(self, company, **kw):
        """Convenience factory for POS / accounting callers.

        Callers pass amounts in their own ``currency_id``; here they are
        converted to CZK (§ 17 odst. 1 písm. f) ZoET) and the original kept.
        """
        company = company or self.env.company
        vals = {
            "company_id": company.id,
            "environment": company.l10n_cz_eet2_environment,
            "certificate_id": company.l10n_cz_eet2_certificate_id.id or False,
            "eic_popl": company.l10n_cz_eet2_eic_popl,
            "id_jednotky": company.l10n_cz_eet2_id_jednotky,
        }
        vals.update(kw)
        czk = self.env.ref("base.CZK")
        currency = self.env["res.currency"].browse(vals.get("currency_id")) \
            if vals.get("currency_id") else czk
        if currency and currency != czk:
            date = vals.get("dat_trzby")
            if date:
                # The rate of the sale's local day, not of its UTC day.
                tz = company.partner_id.tz or "Europe/Prague"
                date = fields.Datetime.context_timestamp(
                    self.with_context(tz=tz), fields.Datetime.to_datetime(date)).date()
            vals["source_amount"] = vals.get("celk_trzba") or 0.0
            vals["source_currency_id"] = currency.id
            for key in ("celk_trzba", "urceno_cerp_zuct", "cerp_zuct"):
                if vals.get(key):
                    vals[key] = self._to_czk(vals[key], currency, company, date)
        vals["currency_id"] = czk.id
        return self.create(vals)
