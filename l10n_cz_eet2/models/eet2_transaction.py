# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules import module

from ..lib import eet2_client

_logger = logging.getLogger(__name__)

ENDPOINTS = {
    "playground": eet2_client.ENDPOINT_PLAYGROUND,
    "production": eet2_client.ENDPOINT_PRODUCTION,
}

# Error codes that warrant a retry (temporary technical errors). Everything else
# positive (3=schema, 4=signature, 6=EIC, 7=too big) is a permanent rejection.
RETRYABLE_KODS = {8}          # 8 = technical/data error; kod<0 (e.g. -1) also retries
DEFAULT_MAX_ATTEMPTS = 12
BACKOFF_BASE_MINUTES = 2      # 2, 4, 8, 16, 32, 60, 60, ... (capped)
BACKOFF_CAP_MINUTES = 60


class Eet2Transaction(models.Model):
    _name = "l10n.cz.eet2.transaction"
    _description = "EET 2.0 Registered-sale Data Message"
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
    prvni_zaslani = fields.Boolean(string="First sending", default=True)
    overeni = fields.Boolean(
        string="Verification mode",
        help="If set, the message is only validated; no valid POK is issued.")

    # --- Data (mandatory) ---
    eic_popl = fields.Char(string="Taxpayer EIC", required=True)
    id_jednotky = fields.Integer(string="Unit ID", required=True)
    id_pokl = fields.Char(string="PoS ID", required=True)
    porad_cis = fields.Char(string="Sequence number", required=True)
    dat_trzby = fields.Datetime(string="Sale date/time", required=True)
    celk_trzba = fields.Monetary(string="Total amount", required=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.ref("base.CZK"))
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

    def _prepare_trzba(self):
        self.ensure_one()
        # Odoo stores datetimes as naive UTC; convert to the user's tz so the
        # ISO-8601 string carries the correct offset (e.g. +02:00), as required.
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
            uuid_zpravy=self.uuid_zpravy or None,
        )
        return trzba

    def action_send(self):
        for rec in self:
            rec._send()
        return True

    def _enqueue(self):
        """Queue for the scheduled job to pick up (fully async path)."""
        self.write({"state": "to_send", "next_attempt": fields.Datetime.now()})

    def _max_attempts(self):
        return (self.company_id.l10n_cz_eet2_max_attempts
                or DEFAULT_MAX_ATTEMPTS)

    def _backoff_delay(self):
        from datetime import timedelta
        minutes = min(BACKOFF_BASE_MINUTES * (2 ** max(self.attempt_count - 1, 0)),
                    BACKOFF_CAP_MINUTES)
        return timedelta(minutes=minutes)

    def _schedule_retry(self, error):
        """Bump the attempt counter; reschedule, or give up after max attempts."""
        self.attempt_count += 1
        if self.attempt_count >= self._max_attempts():
            self.write({"state": "error", "chyba_text": (error or "")[:500],
                        "next_attempt": False})
            _logger.warning("EET 2.0: giving up on %s after %d attempts: %s",
                            self.uuid_zpravy, self.attempt_count, error)
        else:
            self.write({"state": "retry", "chyba_text": (error or "")[:500],
                        "next_attempt": fields.Datetime.now() + self._backoff_delay()})

    def _send(self):
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
            self.uuid_zpravy = trzba.uuid_zpravy  # persist the generated UUID
            envelope = eet2_client.build_signed_request(trzba, cert)
            self.request_xml = envelope.decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001 - cert/build error is permanent
            self.write({"state": "error", "chyba_text": str(exc)[:500],
                        "next_attempt": False})
            _logger.exception("EET 2.0: cannot build message %s", self.uuid_zpravy)
            return
        try:
            result = eet2_client.send(envelope, endpoint=self._get_endpoint())
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

    @api.model
    def _cron_send_pending(self, limit=200):
        """Scheduled sender: process queued and retry-due messages.

        Commits per record so one failure never rolls back the whole batch and
        progress survives a mid-run interruption.
        """
        now = fields.Datetime.now()
        pending = self.search([
            ("state", "in", ("to_send", "retry")),
            "|", ("next_attempt", "=", False), ("next_attempt", "<=", now),
        ], limit=limit, order="next_attempt asc, id asc")
        for tx in pending:
            try:
                tx._send()
            except Exception:  # noqa: BLE001 - never let one message kill the run
                _logger.exception("EET 2.0 cron: unexpected error on %s",
                                tx.uuid_zpravy)
            # Commit per message so one failure never rolls back the batch.
            # Odoo 19 forbids commit inside a test transaction, so skip it there.
            if not module.current_test:
                self.env.cr.commit()
        return True

    @staticmethod
    def _parse_dt(iso):
        if not iso:
            return False
        from datetime import datetime
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo:
            dt = dt.astimezone().replace(tzinfo=None)
        return fields.Datetime.to_string(dt)

    @api.model
    def create_from_values(self, company, **kw):
        """Convenience factory for POS / accounting callers."""
        company = company or self.env.company
        vals = {
            "company_id": company.id,
            "environment": company.l10n_cz_eet2_environment,
            "certificate_id": company.l10n_cz_eet2_certificate_id.id or False,
            "eic_popl": company.l10n_cz_eet2_eic_popl,
            "id_jednotky": company.l10n_cz_eet2_id_jednotky,
        }
        vals.update(kw)
        return self.create(vals)
