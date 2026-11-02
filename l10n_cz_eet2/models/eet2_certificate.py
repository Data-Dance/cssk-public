# -*- coding: utf-8 -*-
import base64
import logging
from datetime import timedelta

import psycopg2

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules import module

from ..lib import caeet_client, eet2_client

_logger = logging.getLogger(__name__)

# Days before ``valid_to`` at which the expiry cron raises an activity. A
# pokladní certifikát lives 366 days (CA EET production profile; FS answer 4178).
EXPIRY_WARNING_DAYS = (30, 14, 7)

# CA EET 2.0 renewal API hosts per EET environment, overridable through the
# system parameters ``l10n_cz_eet2.caeet_url_production`` /
# ``l10n_cz_eet2.caeet_url_playground``. The published spec names three hosts
# (testovací, zkušební, produkční) without saying which non-production one
# issues playground certificates; "zkušební" is our best reading and must be
# confirmed against the playground kit before relying on it.
CAEET_DEFAULT_URLS = {
    "production": caeet_client.HOSTS["prod"],
    "playground": caeet_client.HOSTS["zkus"],
}
CAEET_URL_PARAM = "l10n_cz_eet2.caeet_url_%s"
# When the CA gives no Retry-After / pollAfterSeconds, or is unreachable.
RENEWAL_RETRY_MINUTES = 15
RENEWAL_POLL_MINUTES = 60

RENEWAL_STATES = [
    ("none", "Not requested"),
    ("requested", "Requested"),
    ("issued", "Issued by the CA"),
    ("claimed", "Downloaded"),
    ("verified", "Verified, awaiting acknowledgement"),
    ("switched", "Renewed"),
    ("rejected", "Rejected by the CA"),
    ("failed", "Failed"),
]
RENEWAL_IN_PROGRESS = ("requested", "issued", "claimed", "verified")


class Eet2Certificate(models.Model):
    _name = "l10n.cz.eet2.certificate"
    _description = "EET 2.0 Cash-register Certificate (pokladní certifikát)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "valid_to desc, id desc"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company)
    environment = fields.Selection(
        [("playground", "Playground (non-production)"),
        ("production", "Production")],
        required=True, default="playground",
        help="Which EET 2.0 environment this certificate is valid for.")
    # The pokladní certifikát is delivered as a legacy PKCS#12 (.p12). Python's
    # `cryptography` loads its RC2-40/3DES bags fine; see the internal EET 2.0 notes, §12.
    p12_file = fields.Binary(string="PKCS#12 (.p12)", required=True, attachment=True)
    p12_filename = fields.Char(string="Filename")
    password = fields.Char(
        required=True,
        help="Password protecting the .p12 file (shown in the DIS+ app).")

    # Read-only metadata, filled from the certificate on save.
    subject_cn = fields.Char(string="Subject CN (EIČ)", readonly=True)
    valid_from = fields.Datetime(readonly=True)
    valid_to = fields.Datetime(readonly=True)
    active = fields.Boolean(default=True)
    expiry_warned_days = fields.Integer(
        string="Last expiry warning (days)", readonly=True, copy=False,
        help="The smallest days-before-expiry threshold already warned about, "
            "so each threshold raises one activity only.")

    # --- automatic renewal through the CA EET 2.0 API ---
    renewal_state = fields.Selection(
        RENEWAL_STATES, string="Renewal", default="none", required=True,
        copy=False, readonly=True, tracking=True,
        help="Progress of the follow-up certificate requested from CA EET 2.0 "
            "with this one. 'Renewed' means the follow-up certificate was "
            "verified against the gateway, is now the company's certificate, "
            "and this one was archived.")
    renewal_req_id = fields.Char(
        string="CA request id", copy=False, readonly=True,
        help="reqId of the renewal request at CA EET 2.0.")
    renewal_last_check = fields.Datetime(
        string="Last CA contact", copy=False, readonly=True)
    renewal_next_check = fields.Datetime(
        string="Next CA contact", copy=False, readonly=True,
        help="The scheduled job does not contact the CA about this certificate "
            "before this moment (pollAfterSeconds / Retry-After of the last answer).")
    renewal_error = fields.Char(
        string="Renewal error", copy=False, readonly=True)
    renewed_by_id = fields.Many2one(
        "l10n.cz.eet2.certificate", string="Renewed by", copy=False,
        readonly=True, ondelete="set null",
        help="The follow-up certificate downloaded from CA EET 2.0.")
    renews_id = fields.Many2one(
        "l10n.cz.eet2.certificate", string="Renews", copy=False,
        readonly=True, ondelete="set null",
        help="The certificate this one was issued as a follow-up to.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._load_metadata()
        return records

    def write(self, vals):
        if "p12_file" in vals and "expiry_warned_days" not in vals:
            vals = dict(vals, expiry_warned_days=0)   # a new file, new warnings
        res = super().write(vals)
        if {"p12_file", "password"} & set(vals):
            self._load_metadata()
            # A re-uploaded certificate is the usual fix for messages that could
            # not be built/signed: put them back in the queue.
            Tx = self.env["l10n.cz.eet2.transaction"].sudo()
            Tx.search([
                ("state", "in", ("error", "rejected")),
                "|", ("certificate_id", "in", self.ids),
                "&", ("certificate_id", "=", False),
                ("company_id.l10n_cz_eet2_certificate_id", "in", self.ids),
            ]).action_requeue()
        return res

    def _get_cert(self):
        """Return an ``eet2_client.Certificate`` for this record."""
        self.ensure_one()
        if not self.p12_file:
            raise UserError(_("No .p12 file uploaded on certificate %s.", self.name))
        try:
            return eet2_client.Certificate(
                base64.b64decode(self.p12_file), self.password or "")
        except Exception as exc:  # noqa: BLE001 - surface a readable error
            raise UserError(_(
                "Could not load the PKCS#12 certificate %(name)s: %(err)s",
                name=self.name, err=exc)) from exc

    def _load_metadata(self):
        for rec in self:
            if not rec.p12_file:
                continue
            cert = rec._get_cert().cert
            cn = [a.value for a in cert.subject
                if a.oid.dotted_string == "2.5.4.3"]
            rec.subject_cn = cn[0] if cn else False
            rec.valid_from = fields.Datetime.to_string(
                cert.not_valid_before_utc.replace(tzinfo=None))
            rec.valid_to = fields.Datetime.to_string(
                cert.not_valid_after_utc.replace(tzinfo=None))

    # ------------------------------------------------------------------
    def _send_verification(self):
        """Send a message in verification mode (overeni=true) with this certificate.

        The gateway validates schema, signature and EIC and answers kod 0 without
        issuing a POK, so it proves the certificate, the password and the network
        path against the certificate's environment without recording a sale.
        The transaction is kept for audit; returns it.
        """
        self.ensure_one()
        company = self.company_id
        Tx = self.env["l10n.cz.eet2.transaction"]
        tx = Tx.create_from_values(
            company,
            environment=self.environment,
            certificate_id=self.id,
            eic_popl=company.l10n_cz_eet2_eic_popl or self.subject_cn,
            id_jednotky=company.l10n_cz_eet2_id_jednotky or 11,
            id_pokl="TEST",
            porad_cis="TEST-%d" % self.id,
            dat_trzby=fields.Datetime.now(),
            celk_trzba=1.0,
            overeni=True,
        )
        tx._send()
        return tx

    def action_test_verification(self):
        self.ensure_one()
        tx = self._send_verification()
        if tx.state == "verified":
            kind, title = "success", _("Certificate OK")
            message = _("The EET 2.0 gateway (%(env)s) accepted a verification-mode "
                        "message signed with %(name)s.",
                        env=self.environment, name=self.name)
            if tx.warning_text:
                message += "\n" + _("Warnings: %s", tx.warning_text)
        else:
            kind, title = "danger", _("Certificate test failed")
            message = _("State %(state)s, error %(kod)s: %(text)s",
                        state=tx.state, kod=tx.chyba_kod if tx.chyba_kod is not None else "-",
                        text=tx.chyba_text or "-")
        return self._notification(title, message, kind)

    @staticmethod
    def _notification(title, message, kind):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": title, "message": message, "type": kind,
                    "sticky": kind == "danger", "next": {"type": "ir.actions.act_window_close"}},
        }

    @api.model
    def _cron_check_expiry(self):
        """Raise one activity per threshold as a certificate nears expiry."""
        now = fields.Datetime.now()
        horizon = now + timedelta(days=max(EXPIRY_WARNING_DAYS))
        certs = self.search([("valid_to", "!=", False), ("valid_to", "<=", horizon)])
        for cert in certs:
            days_left = max((cert.valid_to - now).days, 0)
            due = [d for d in EXPIRY_WARNING_DAYS if days_left <= d]
            if not due:
                continue
            threshold = min(due)
            if cert.expiry_warned_days and cert.expiry_warned_days <= threshold:
                continue
            try:
                cert.activity_schedule(
                    "mail.mail_activity_data_warning",
                    user_id=cert._renewal_user().id,
                    summary=_("EET 2.0 certificate expires in %s days", days_left),
                    note=_("Certificate %(name)s (%(env)s) is valid until %(to)s. "
                        "Generate a new pokladní certifikát in DIS+, upload it "
                        "here or as a new record, test it and select it in the "
                        "EET 2.0 settings.",
                        name=cert.name, env=cert.environment, to=cert.valid_to))
            except Exception:  # noqa: BLE001 - keep the cron alive
                _logger.exception("EET 2.0: expiry activity failed for %s", cert.name)
            cert.expiry_warned_days = threshold
        return True

    # ------------------------------------------------------------------
    # Automatic renewal (CA EET 2.0 API, caeetapi_jwt.yml)
    #
    # The request is authorised by a JWT signed with THIS certificate, which
    # must still be valid, so the whole cycle has to finish before valid_to:
    # request -> poll -> claim the new PKCS#12 -> verify it against the EET
    # gateway in verification mode -> switch the company to it -> acknowledge
    # the download (the CA then deletes its copy) -> archive this one.  The
    # acknowledgement comes LAST: until the new certificate is proven to work
    # the CA keeps the PKCS#12 re-claimable for 30 days.
    # ------------------------------------------------------------------
    @api.model
    def _caeet_base_url(self, environment):
        default = CAEET_DEFAULT_URLS[environment]
        return (self.env["ir.config_parameter"].sudo().get_param(
            CAEET_URL_PARAM % environment, default) or default)

    def _caeet_client(self):
        self.ensure_one()
        return caeet_client.CaeetClient(
            self._caeet_base_url(self.environment), self._get_cert())

    def _renewal_lock(self):
        """Serialise the cycle per certificate: the cron and the button, or two
        cron workers, must not both ask the CA or both raise the activity.
        Returns False, without waiting, when another transaction holds the row;
        the caller then simply skips this round.  Re-reads the record afterwards
        so the state checks see what the other transaction committed."""
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    "SELECT id FROM l10n_cz_eet2_certificate WHERE id = %s FOR UPDATE NOWAIT",
                    (self.id,))
        except psycopg2.errors.LockNotAvailable:
            _logger.info("EET 2.0: renewal of %s is being handled elsewhere", self.name)
            return False
        self.invalidate_recordset(["renewal_state", "renewal_req_id", "renewal_next_check",
                                   "renewed_by_id", "renewal_error"])
        return True

    def _renewal_user(self):
        """Who gets renewal and expiry activities: an EET 2.0 manager of the company."""
        self.ensure_one()
        group = self.env.ref("l10n_cz_eet2.group_eet2_manager", raise_if_not_found=False)
        users = group.user_ids if group else self.env["res.users"]
        users = users.filtered(
            lambda u: u.active and self.company_id in u.company_ids and not u.share)
        return users[:1] or self.env.ref("base.user_admin")

    def _renewal_notify(self, summary, note):
        self.ensure_one()
        try:
            self.activity_schedule(
                "mail.mail_activity_data_warning",
                user_id=self._renewal_user().id, summary=summary, note=note)
        except Exception:  # noqa: BLE001 - a notification must not break the cycle
            _logger.exception("EET 2.0: could not schedule the renewal activity")

    def _renewal_fail(self, state, error, note=None):
        """Stop the cycle in ``rejected`` / ``failed`` with one activity."""
        self.ensure_one()
        error = (error or "")[:500]
        _logger.warning("EET 2.0: renewal of certificate %s %s: %s",
                        self.name, state, error)
        already = self.renewal_state == state
        self.write({"renewal_state": state, "renewal_error": error,
                    "renewal_next_check": False,
                    "renewal_last_check": fields.Datetime.now()})
        if not already:
            self._renewal_notify(
                _("EET 2.0 certificate renewal %s", dict(RENEWAL_STATES)[state].lower()),
                note or _("The automatic renewal of certificate %(name)s (%(env)s) "
                        "stopped: %(error)s. It stays in use until %(to)s; renew it "
                        "by hand in DIS+ if the problem is not resolved in time.",
                        name=self.name, env=self.environment, error=error,
                        to=self.valid_to))

    def _renewal_defer(self, exc):
        """A temporary CA problem (429, 5xx, unreachable): try again later,
        after the CA's Retry-After when it gave one. State is unchanged."""
        self.ensure_one()
        seconds = getattr(exc, "retry_after", None) or RENEWAL_RETRY_MINUTES * 60
        self.write({"renewal_last_check": fields.Datetime.now(),
                    "renewal_next_check": fields.Datetime.now() + timedelta(seconds=seconds),
                    "renewal_error": str(exc)[:500]})
        _logger.info("EET 2.0: CA EET deferred the renewal of %s: %s", self.name, exc)

    def _renewal_guard(self, step):
        """Run one step of the cycle, sorting CA errors into defer / fail."""
        self.ensure_one()
        try:
            step()
        except (caeet_client.CaeetRateLimited, caeet_client.CaeetServerError) as exc:
            self._renewal_defer(exc)
        except caeet_client.CaeetError as exc:
            if exc.status == 0:            # network: the CA never answered
                self._renewal_defer(exc)
            else:
                self._renewal_fail("failed", str(exc))

    def _renewal_request(self):
        """Step 1: ask the CA for a follow-up certificate."""
        self.ensure_one()
        now = fields.Datetime.now()
        if not self.valid_to or self.valid_to <= now:
            raise UserError(_(
                "Certificate %s has expired; the CA renews only a valid certificate. "
                "Generate a new one in DIS+ and upload it.", self.name))
        if self.renewal_state in RENEWAL_IN_PROGRESS:
            return                      # another transaction got there first
        req_id = self._caeet_client().renew()
        self.write({"renewal_req_id": req_id, "renewal_state": "requested",
                    "renewal_error": False, "renewal_last_check": now,
                    "renewal_next_check": now, "renewed_by_id": False})
        self.message_post(body=_("Renewal requested from CA EET 2.0 (request %s).", req_id))

    def _renewal_poll(self):
        """Step 2: follow the request until the CA has issued the certificate."""
        self.ensure_one()
        now = fields.Datetime.now()
        info = self._caeet_client().status(self.renewal_req_id)
        state = info["state"]
        self.renewal_last_check = now
        if state == caeet_client.INPROCESS:
            seconds = info["poll_after"] or RENEWAL_POLL_MINUTES * 60
            self.renewal_next_check = now + timedelta(seconds=seconds)
        elif state in caeet_client.CLAIMABLE_STATES:
            self.write({"renewal_state": "issued", "renewal_next_check": now})
            self._renewal_claim()
        elif state == caeet_client.REJECTED:
            self._renewal_fail("rejected", info["rejected_reason"] or state)
        elif state == caeet_client.FINISHED:
            # Somebody (DIS+, another system) downloaded and acknowledged it;
            # the CA will not hand it out again.
            self._renewal_fail("failed", _(
                "The CA reports the request as finished, but this installation "
                "never downloaded the certificate. Upload the follow-up "
                "certificate by hand."))
        else:
            self._renewal_fail("failed", _("Unknown request state %s", state))

    def _renewal_claim(self):
        """Step 3: download the new PKCS#12 and store it as a new record."""
        self.ensure_one()
        bundle = self._caeet_client().claim_download(self.renewal_req_id)
        new = self.create({
            "name": _("%(name)s · renewed %(date)s",
                    name=self.name, date=fields.Date.context_today(self)),
            "company_id": self.company_id.id,
            "environment": self.environment,
            "p12_file": base64.b64encode(bundle["p12"]),
            "p12_filename": "%s.p12" % (bundle["certificate"].get("sn") or "renewed"),
            "password": bundle["password"],
            "renews_id": self.id,
        })
        self.write({"renewed_by_id": new.id, "renewal_state": "claimed",
                    "renewal_last_check": fields.Datetime.now()})
        self.message_post(body=_("Follow-up certificate downloaded as %s.", new.name))
        self._renewal_verify_and_switch()

    def _renewal_verify_and_switch(self):
        """Step 4: prove the new certificate against the gateway, then use it."""
        self.ensure_one()
        new = self.renewed_by_id
        if not new:
            return self._renewal_fail("failed", _("The downloaded certificate is gone."))
        tx = new._send_verification()
        if tx.state != "verified":
            # The old certificate stays in use and the download stays
            # unacknowledged, so the CA keeps the PKCS#12 for a retry.
            return self._renewal_fail("failed", _(
                "the follow-up certificate %(new)s failed the verification-mode "
                "test (state %(state)s, error %(kod)s: %(text)s)",
                new=new.name, state=tx.state,
                kod=tx.chyba_kod if tx.chyba_kod is not None else "-",
                text=tx.chyba_text or "-"))
        self.renewal_state = "verified"
        companies = self.env["res.company"].sudo().search(
            [("l10n_cz_eet2_certificate_id", "=", self.id)])
        companies.write({"l10n_cz_eet2_certificate_id": new.id})
        self._renewal_switch_references(new)
        new.message_post(body=_("Verified against the EET 2.0 gateway and put in use."))
        self._renewal_ack()

    def _renewal_switch_references(self, new):
        """Hook for modules that point other records at a certificate."""
        self.ensure_one()

    def _renewal_ack(self):
        """Step 5: tell the CA the download is complete, retire this certificate.

        The company already runs on the new certificate here, so an answer
        that means "nothing left to acknowledge" (409: already finished, 404:
        the request is gone) or one that can never succeed again (401: this
        certificate can no longer sign the JWT) must not undo that: the cycle
        is complete either way, and the CA discards an unclaimed PKCS#12 after
        30 days on its own.  Temporary CA trouble (429, 5xx, unreachable) is
        left to the guard, which defers and retries the acknowledgement.
        """
        self.ensure_one()
        note = False
        try:
            self._caeet_client().ack_download(self.renewal_req_id)
        except (caeet_client.CaeetConflict, caeet_client.CaeetNotFound,
                caeet_client.CaeetAuthError) as exc:
            note = _("The CA did not take the acknowledgement (%s); the new "
                     "certificate is in use regardless.", exc)
            _logger.warning("EET 2.0: ack-download for %s not accepted: %s", self.name, exc)
        self.write({"renewal_state": "switched", "renewal_error": note,
                    "renewal_next_check": False, "active": False,
                    "renewal_last_check": fields.Datetime.now()})
        self.message_post(body=note or _(
            "Download acknowledged to CA EET 2.0; %s is now the company's certificate.",
            self.renewed_by_id.name))

    def _renewal_step(self):
        """Advance one in-progress renewal by one step (cron and button)."""
        self.ensure_one()
        if not self._renewal_lock():
            return
        step = {
            "requested": self._renewal_poll,
            "issued": self._renewal_poll,
            "claimed": self._renewal_verify_and_switch,
            "verified": self._renewal_ack,
        }.get(self.renewal_state)
        if step:
            self._renewal_guard(step)

    def action_renew(self):
        """Renew now, or push a stuck cycle along.

        From a fresh / rejected / failed state a new request is made; a failed
        verification with the download still in hand is retried instead of
        asking the CA again.
        """
        self.ensure_one()
        if not self._renewal_lock():
            raise UserError(_("The renewal of %s is being handled right now; "
                              "try again in a moment.", self.name))
        if self.renewal_state in RENEWAL_IN_PROGRESS:
            self._renewal_step()
        elif self.renewal_state == "failed" and self.renewed_by_id and self.renewal_req_id:
            self._renewal_guard(self._renewal_verify_and_switch)
        else:
            self._renewal_guard(self._renewal_request)
            if self.renewal_state == "requested":
                self._renewal_step()
        label = dict(RENEWAL_STATES)[self.renewal_state]
        if self.renewal_state in ("rejected", "failed"):
            return self._notification(
                _("Renewal %s", label.lower()), self.renewal_error or label, "danger")
        return self._notification(
            _("Renewal: %s", label.lower()),
            self.renewal_error or _("Request %s", self.renewal_req_id or "-"),
            "success" if self.renewal_state == "switched" else "info")

    @api.model
    def _cron_renew_certificates(self):
        """Request renewals ahead of expiry and follow the ones in progress.

        Only the certificate a company actually uses is renewed; one uploaded
        and never selected is not worth a CA request. A company with the
        setting at 0 opts out of automatic renewal.
        """
        now = fields.Datetime.now()
        due = self.search([
            ("renewal_state", "=", "none"),
            ("valid_to", ">", now),
            ("company_id.l10n_cz_eet2_renew_days_before", ">", 0),
            "|", ("renewal_next_check", "=", False), ("renewal_next_check", "<=", now),
        ]).filtered(lambda c: (
            c.company_id.l10n_cz_eet2_certificate_id == c
            and c.valid_to <= now + timedelta(days=c.company_id.l10n_cz_eet2_renew_days_before)))
        in_progress = self.with_context(active_test=False).search([
            ("renewal_state", "in", RENEWAL_IN_PROGRESS),
            "|", ("renewal_next_check", "=", False), ("renewal_next_check", "<=", now),
        ])
        for cert in due:
            self._cron_one(cert, lambda c=cert: (
                c._renewal_lock() and c._renewal_guard(c._renewal_request)))
        for cert in in_progress:
            self._cron_one(cert, cert._renewal_step)
        return True

    def _cron_one(self, cert, step):
        try:
            with self.env.cr.savepoint():
                step()
        except Exception as exc:  # noqa: BLE001 - one certificate must not stop the others
            _logger.exception("EET 2.0: renewal step failed for %s", cert.name)
            # The savepoint rolled the step back; park this certificate for a
            # while so a persistent crash does not retry on every hour's tick
            # for nothing, and leave a trace of why on the record.
            try:
                with self.env.cr.savepoint():
                    cert._renewal_defer(exc)
            except Exception:  # noqa: BLE001
                _logger.exception("EET 2.0: could not record the failed renewal step")
        if not module.current_test:
            self.env["ir.cron"]._commit_progress(1)
