"""Concrete ePošťák connector speaking SAPI-SK 1.0 (REST/JSON over HTTPS).

Reference: https://epostak.sk/api/docs (SAPI-SK 1.0) and
https://epostak.sk/api/docs/enterprise (lifecycle endpoints).

SAPI is the UBL-in / UBL-out surface: ``POST /document/send`` takes the Peppol
XML as an opaque string next to a small routing envelope, and
``GET /document/receive`` hands inbound documents back the same way. That is a
direct fit for this stack, where ``account.edi.xml.ubl_bis3`` (or a national
subclass) has already produced the document — the Enterprise JSON invoice
model would mean re-deriving an invoice we already hold as valid UBL.

Two lifecycle endpoints have no SAPI equivalent and are called on the
Enterprise base URL with the *same* token:
  * ``GET /documents/{id}/status``   — delivery outcome, polled by cron;
  * ``POST /peppol/capabilities``    — can this participant receive this type.
Both are best-effort: a key scoped to ``documents:send`` alone will be refused
there, which must not break sending.
"""

import hashlib
import logging
import time
import uuid
from urllib.parse import quote
from datetime import datetime, timezone

import requests

from odoo import SUPERUSER_ID, _, fields, models
from odoo.exceptions import UserError

from odoo.addons.edi_epostak_base.models.epostak_connector import (
    DEFAULT_API_URLS,
    DEFAULT_SAPI_URLS,
    PRODUCTION,
)

_logger = logging.getLogger(__name__)

# Module-level access-token cache, keyed by (mode, client_id).
# Tokens live 15 minutes; the docs are explicit that the token endpoint must
# not be called per request. Cached per worker process — see _get_token for
# why we re-mint rather than rotate the refresh token.
_TOKEN_CACHE = {}

# Re-mint this many seconds before the token actually expires, so a request
# that is slow to leave does not arrive with a just-expired token.
TOKEN_SKEW = 60

# ePošťák issues two shapes of secret: sk_live_* identifies a single firm, so
# the firm is implied; sk_int_* is an integrator credential speaking for many,
# and needs X-Firm-Id on every call to pick one.
INTEGRATOR_SECRET_PREFIX = "sk_int_"

# Listing the firms an integrator may act for is gated on its own scope,
# which the ordinary documents:* token deliberately does not carry.
FIRMS_SCOPE = "firms:manage"

DEFAULT_TIMEOUT = 60
DEFAULT_LIMIT = 20          # API allows 1..100 per page
DEFAULT_MAX_PAGES = 5

# HTTP statuses worth another attempt. 409 is ePošťák's "same Idempotency-Key
# still in flight"; 423 is the 10-minute lock after repeated auth failures.
RETRYABLE_STATUS = {409, 423, 429, 500, 502, 503, 504}
# ...except when the body names a permanent conflict: replaying a key against a
# *different* payload will never succeed, so retrying only burns attempts.
PERMANENT_CODES = {"IDEMPOTENCY_KEY_MISMATCH", "VALIDATION", "UBL_VALIDATION_ERROR"}

# GET /documents/{id}/status vocabulary (Enterprise API).
STATUS_DONE = {"delivered"}
STATUS_ERROR = {
    "rejected",
    "send_failed",
    "delivery_failed",
    "validation_failed",
}
# queued / sent are not delivery proof — the message stays 'sent' until the
# network says one way or the other.


class EpostakApiError(Exception):
    """An ePošťák API call failed. ``retryable`` drives job retry policy."""

    def __init__(self, message, status=None, code=None, retryable=False,
                 retry_after=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after


class EpostakConnectorSapi(models.TransientModel):
    _inherit = "epostak.connector"

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _get_sapi_config(self, mode=None):
        """Credentials + endpoints for one environment.

        Credentials are per-environment on purpose: sandbox keys are rejected
        by the production host by design, so keeping both sets lets a
        deployment flip environments without re-entering secrets.
        """
        ICP = self.env["ir.config_parameter"].sudo()
        cfg = self._get_config(mode=mode)
        mode = cfg["mode"]
        prefix = "epostak.sapi.%s" % ("prod" if mode == PRODUCTION else "sandbox")
        cfg.update(
            {
                "sapi_url": (
                    ICP.get_param("%s.base_url" % prefix, "")
                    or DEFAULT_SAPI_URLS[mode]
                ).rstrip("/"),
                "api_url": (
                    ICP.get_param(
                        "epostak.api.%s.base_url"
                        % ("prod" if mode == PRODUCTION else "sandbox"),
                        "",
                    )
                    or DEFAULT_API_URLS[mode]
                ).rstrip("/"),
                "client_id": ICP.get_param("%s.client_id" % prefix, ""),
                "client_secret": ICP.get_param("%s.client_secret" % prefix, ""),
                "scope": ICP.get_param(
                    "epostak.sapi.scope",
                    "documents:send documents:read documents:write",
                ),
                "timeout": int(
                    ICP.get_param("epostak.sapi.timeout", DEFAULT_TIMEOUT)
                ),
                "limit": max(
                    1,
                    min(
                        100,
                        int(ICP.get_param("epostak.sapi.limit", DEFAULT_LIMIT)),
                    ),
                ),
                "max_pages": max(
                    1,
                    int(ICP.get_param("epostak.sapi.max_pages", DEFAULT_MAX_PAGES)),
                ),
                "status_tracking": ICP.get_param(
                    "epostak.sapi.status_tracking", "True"
                ).lower()
                not in ("0", "false"),
            }
        )
        return cfg

    def _validate_config(self, mode=None):
        """Check credentials *and* Peppol addressability for one environment.

        Validated against the same ``mode`` the caller will then transmit in —
        checking the active setting while sending in a message's stamped mode
        can green-light an environment whose credentials are blank.
        """
        super()._validate_config(mode=mode)
        cfg = self._get_sapi_config(mode=mode)
        if not cfg["client_id"] or not cfg["client_secret"]:
            raise UserError(
                _(
                    "ePošťák credentials are not configured for the %s "
                    "environment. Go to Settings ▸ EDI ▸ ePošťák and fill in "
                    "the client ID and client secret.",
                    cfg["mode"],
                )
            )
        self._assert_firm_scope(cfg)
        return cfg

    def _assert_firm_scope(self, cfg):
        """Refuse an integrator key that does not say which firm it acts for.

        An ``sk_int_*`` secret speaks for several firms, so every request has to
        name the one it is acting for in ``X-Firm-Id``. Without it the API
        answers 400 BAD_REQUEST on each call -- correct, and its message is even
        a good one, but it reaches the user as a traceback from whichever button
        they happened to press. Decide it here instead: the check is free, it
        runs before any HTTP call, and it can name the field to fill.

        Kept out of ``_validate_config`` as its own method so ``_list_firms``
        can skip it -- that call is how you find the firm id, so it has to work
        before one is configured.
        """
        if (
            cfg.get("client_secret", "").startswith(INTEGRATOR_SECRET_PREFIX)
            and not cfg.get("firm_id")
        ):
            raise UserError(
                _(
                    "The ePošťák client secret configured for the %(mode)s "
                    "environment is an integrator key (sk_int_*), which acts on "
                    "behalf of firms rather than being one, so every request "
                    "must name the firm it is acting for.\n\n"
                    "Set Settings ▸ EDI ▸ ePošťák ▸ ePošťák Firm ID to the "
                    "UUID of the firm this database invoices as — the Test "
                    "Connection button there lists the firms this key may act "
                    "for.\n\n"
                    "If this database has its own ePošťák contract instead, the "
                    "secret should be a firm key (sk_live_*), and the Firm ID "
                    "stays empty.",
                    mode=cfg["mode"],
                )
            )

    def _clear_token_cache(self):
        """Drop cached access tokens (called when settings change)."""
        _TOKEN_CACHE.clear()

    # ------------------------------------------------------------------
    # OAuth 2.0 client credentials
    # ------------------------------------------------------------------

    def _get_token(self, cfg, force_refresh=False):
        """Return a cached-or-freshly-minted access token for ``cfg``.

        We deliberately do NOT use the refresh-token rotation flow. Rotation
        is one-shot — replaying a spent refresh token is a 401 — and this
        cache is per worker process, so two Odoo workers holding the same
        credentials would invalidate each other's tokens and start flapping.
        A client_credentials mint has no such shared state and is cheap
        against the 200/min token budget.
        """
        # Keyed by scope as well: a token minted for firms:manage must not be
        # handed to a send, nor a documents-only token to the firm listing --
        # the API answers 403 INSUFFICIENT_SCOPE on the mismatch, which would
        # look like a permissions problem rather than a cache one.
        key = (cfg["mode"], cfg["client_id"], cfg["scope"])
        cached = _TOKEN_CACHE.get(key)
        if (
            not force_refresh
            and cached
            and cached["expires_at"] > time.time() + TOKEN_SKEW
        ):
            return cached["access_token"]

        payload = {
            "grant_type": "client_credentials",
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "scope": cfg["scope"],
        }
        try:
            response = requests.post(
                "%s/auth/token" % cfg["sapi_url"],
                json=payload,
                timeout=cfg["timeout"],
                headers={"Accept": "application/json"},
            )
        except requests.RequestException as e:
            raise EpostakApiError(
                _("Could not reach the ePošťák token endpoint: %s", e),
                retryable=True,
            ) from e

        if response.status_code != 200:
            detail = self._error_detail(response)
            raise EpostakApiError(
                _(
                    "ePošťák authentication failed (HTTP %(status)s): "
                    "%(detail)s",
                    status=response.status_code,
                    detail=detail["message"],
                ),
                status=response.status_code,
                code=detail["code"],
                # 423 LOCKED clears itself after the lockout window.
                retryable=(
                    detail["retryable"]
                    if detail["retryable"] is not None
                    else response.status_code in (423, 429, 500, 502, 503, 504)
                ),
                retry_after=detail["retry_after"],
            )

        try:
            data = response.json()
        except ValueError as e:
            # A 200 that is not JSON means something in front of the API is
            # answering (captive portal, proxy error page); retry rather than
            # crashing the job with a bare ValueError.
            raise EpostakApiError(
                _("ePošťák token endpoint returned a non-JSON body."),
                status=response.status_code,
                retryable=True,
            ) from e
        token = data.get("access_token")
        if not token:
            raise EpostakApiError(
                _("ePošťák returned no access_token."), retryable=True
            )
        _TOKEN_CACHE[key] = {
            "access_token": token,
            "expires_at": time.time() + int(data.get("expires_in") or 900),
        }
        return token

    # ------------------------------------------------------------------
    # HTTP plumbing
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitise(text, limit=500):
        """Flatten untrusted remote text for a log line and a UI field.

        Error bodies come from the network and land both in the log and in
        ``edi.message.error_message``. Newlines and control characters there
        let a hostile (or merely broken) peer forge extra log lines, so
        collapse all whitespace and drop the rest before truncating.
        """
        text = "".join(
            ch if ch.isprintable() else " " for ch in (text or "")
        )
        return " ".join(text.split())[:limit]

    @staticmethod
    def _error_detail(response):
        """Normalise an error body into {'code', 'message', 'retry_after'}.

        The two API surfaces spell errors differently and an edge proxy may
        return no JSON at all, so read defensively and always come back with
        something a user can act on.
        """
        code = ""
        message = ""
        retryable = None
        correlation = ""
        hint = ""
        try:
            body = response.json()
        except ValueError:
            body = None
        if isinstance(body, dict):
            # ePošťák nests everything one level down:
            #   {"error": {"category", "code", "message", "retryable",
            #              "correlation_id"}}
            # Reading the top level only would stringify that whole dict into
            # the message the user sees.
            inner = body.get("error")
            if isinstance(inner, dict):
                body = {**body, **inner}
            code = str(
                body.get("code") or body.get("errorCode") or ""
            )
            if not code and isinstance(body.get("error"), str):
                code = body["error"]
            message = str(
                body.get("message")
                or body.get("detail")
                or body.get("error_description")
                or body.get("errorDescription")
                or ""
            )
            errors = body.get("errors")
            if not message and isinstance(errors, list):
                message = "; ".join(str(e) for e in errors)
            # The API states retryability itself; trust that over our
            # status-code heuristic when it is present.
            if isinstance(body.get("retryable"), bool):
                retryable = body["retryable"]
            # The two surfaces spell the support handle differently:
            # correlation_id on SAPI, request_id/requestId on the Enterprise
            # errors. Both are what support asks for first.
            correlation = str(
                body.get("correlation_id")
                or body.get("request_id")
                or body.get("requestId")
                or ""
            )
            # Several Enterprise errors carry an actionable fix_hint. It is the
            # most useful sentence in the body, so do not drop it.
            hint = str(body.get("fix_hint") or "")
        if not message:
            message = (response.text or "") or response.reason or ""
        message = EpostakConnectorSapi._sanitise(message)
        code = EpostakConnectorSapi._sanitise(code, limit=100)
        retry_after = None
        raw_retry = response.headers.get("Retry-After")
        if raw_retry:
            try:
                retry_after = int(float(raw_retry))
            except (TypeError, ValueError):
                retry_after = None
        # The correlation id is what ePošťák support asks for first, so keep
        # it in the message the user actually sees on the message record.
        parts = (
            code,
            message,
            hint,
            "[%s]" % correlation if correlation else "",
        )
        return {
            "code": code,
            "message": " ".join(filter(None, parts)).strip(),
            "retry_after": retry_after,
            "retryable": retryable,
        }

    def _request(self, cfg, method, url, participant_id=None, json_body=None,
                 params=None, extra_headers=None, expected=(200,)):
        """Perform one authenticated ePošťák call and return the parsed body.

        Raises ``EpostakApiError`` on anything unexpected, with ``retryable``
        already decided so callers do not re-derive the policy. A 401 is
        retried exactly once against a freshly minted token, which covers the
        ordinary case of a cached token expiring mid-flight.
        """
        headers = {"Accept": "application/json"}
        if participant_id:
            headers["X-Peppol-Participant-Id"] = participant_id
        if cfg.get("firm_id"):
            headers["X-Firm-Id"] = cfg["firm_id"]
        if extra_headers:
            headers.update(extra_headers)

        for attempt in (0, 1):
            headers["Authorization"] = "Bearer %s" % self._get_token(
                cfg, force_refresh=bool(attempt)
            )
            try:
                response = requests.request(
                    method,
                    url,
                    json=json_body,
                    params=params,
                    headers=headers,
                    timeout=cfg["timeout"],
                )
            except requests.RequestException as e:
                raise EpostakApiError(
                    _("ePošťák transport error on %(method)s %(url)s: %(err)s",
                      method=method, url=url, err=e),
                    retryable=True,
                ) from e

            if response.status_code == 401 and attempt == 0:
                # Cached token rejected — mint a new one and try once more.
                _TOKEN_CACHE.pop(
                    (cfg["mode"], cfg["client_id"], cfg["scope"]), None
                )
                continue
            break

        if response.status_code in expected:
            if not response.content:
                return {}
            try:
                return response.json()
            except ValueError:
                raise EpostakApiError(
                    _("ePošťák returned a non-JSON body for %s", url),
                    status=response.status_code,
                )

        detail = self._error_detail(response)
        if detail["retryable"] is not None:
            retryable = detail["retryable"]
        else:
            retryable = (
                response.status_code in RETRYABLE_STATUS
                and detail["code"] not in PERMANENT_CODES
            )
        raise EpostakApiError(
            _(
                "ePošťák %(method)s %(path)s failed (HTTP %(status)s): "
                "%(detail)s",
                method=method,
                path=url.rsplit("/v1", 1)[-1],
                status=response.status_code,
                detail=detail["message"],
            ),
            status=response.status_code,
            code=detail["code"],
            retryable=retryable,
            retry_after=detail["retry_after"],
        )

    # ------------------------------------------------------------------
    # Transport: authenticate
    # ------------------------------------------------------------------

    def _authenticate(self):
        """Mint a token to prove the configuration works end to end."""
        cfg = self._validate_config()
        self._get_token(cfg, force_refresh=True)
        return True

    # ------------------------------------------------------------------
    # Transport: send
    # ------------------------------------------------------------------

    @staticmethod
    def _idempotency_key(msg, payload_bytes):
        """A content-addressed Idempotency-Key: uuid5 over the payload digest.

        The key means "this exact document", which is the semantics
        idempotency is for, and gives the two behaviours that matter:

        * a retry of the same bytes presents the same key, so a send that
          actually succeeded before timing out is collapsed rather than
          delivered twice;
        * a document regenerated after a correction — which ``_peppol_emit``
          writes onto the *same* edi.message — hashes differently and gets a
          new key, instead of a permanent IDEMPOTENCY_KEY_MISMATCH.

        Deliberately NOT scoped by ``msg.id``: two records carrying the same
        invoice (a re-created message after a deleted one, say) must collapse
        into one submission. A duplicate VAT invoice on the network is the
        worse failure, and two *different* invoices cannot collide — their
        cbc:ID differs, so their bytes do.
        """
        digest = hashlib.sha256(payload_bytes).hexdigest()
        return str(uuid.uuid5(uuid.NAMESPACE_URL, "epostak:%s" % digest))

    def _stamp_failure(self, msg, message, blocking_level="error"):
        """Record a send failure so it survives the job rollback.

        Delegates to ``edi.message._write_outside_job`` — see there for why an
        inline write is discarded and why the job cursor is rolled back first.
        """
        msg._write_outside_job(
            {
                "state": "error",
                "blocking_level": blocking_level,
                "error_message": self._sanitise(message, limit=2000),
            }
        )

    def _send_message(self, message_record):
        return self._send_messages(message_record)

    def _send_messages(self, message_records):
        """Send outbound messages one at a time.

        SAPI carries exactly one document per call (there is no batch
        endpoint), so a failure isolates to its own message instead of
        poisoning a batch. Grouped by stamped mode so a message prepared in
        the sandbox is never transmitted with production credentials.
        """
        from odoo.addons.edi_base.exceptions import (
            FailedJobError,
            RetryableJobError,
        )

        if not message_records:
            return True

        for msg in message_records:
            try:
                self._send_one(msg, msg._epostak_mode())
            except (EpostakApiError, UserError) as e:
                # A UserError here is a configuration/addressing problem: no
                # amount of retrying fixes it, and its text already says what
                # to change.
                retryable = isinstance(e, EpostakApiError) and e.retryable
                # Aborts the whole call rather than sending the rest of a
                # batch: _stamp_failure rolls the cursor back, so continuing
                # would silently discard the state of anything already sent.
                # That is safe — the content-addressed Idempotency-Key means a
                # re-run collapses server-side instead of duplicating.
                self._stamp_failure(
                    msg, str(e), "warning" if retryable else "error"
                )
                if not retryable:
                    _logger.error(
                        "ePošťák permanent send failure for %s: %s", msg.name, e
                    )
                    raise FailedJobError(str(e)) from e
                if e.retry_after:
                    # 429 is backpressure, not a failure of this message —
                    # honour Retry-After without spending a retry attempt.
                    raise RetryableJobError(
                        str(e),
                        seconds=e.retry_after,
                        ignore_retry=e.status == 429,
                    ) from e
                raise RetryableJobError(str(e)) from e
        return True

    def _send_one(self, msg, mode):
        """POST one Peppol document to ``/document/send``."""
        cfg = self._validate_config(mode=mode)
        xml_content = msg._get_xml_content()
        if not xml_content:
            raise UserError(
                _("EDI message %s has no XML payload to send.", msg.display_name)
            )
        payload_bytes = (
            xml_content.encode("utf-8")
            if isinstance(xml_content, str)
            else xml_content
        )
        meta = self._epostak_document_metadata(msg, xml_content)

        # The sender in the document is authoritative: the API rejects a
        # mismatch between it and the participant header (SAPI-DOC-025).
        participant_id = meta["sender"]
        own = self._epostak_own_participant_id(msg.company_id or self.env.company)
        if own and own != participant_id:
            _logger.warning(
                "ePošťák: message %s is addressed from %s but this company is "
                "%s; sending as the document says.",
                msg.name,
                participant_id,
                own,
            )

        idempotency_key = self._idempotency_key(msg, payload_bytes)
        if msg.transmission_uuid != idempotency_key:
            msg.transmission_uuid = idempotency_key

        body = {
            "metadata": {
                "documentId": meta["document_id"],
                "documentTypeId": meta["document_type_id"],
                "processId": meta["process_id"],
                "senderParticipantId": meta["sender"],
                "receiverParticipantId": meta["receiver"],
                "creationDateTime": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            },
            "payload": (
                payload_bytes.decode("utf-8")
                if isinstance(payload_bytes, bytes)
                else payload_bytes
            ),
            "payloadFormat": "XML",
            "payloadEncoding": "UTF-8",
            "checksum": hashlib.sha256(payload_bytes).hexdigest(),
        }

        data = self._request(
            cfg,
            "POST",
            "%s/document/send" % cfg["sapi_url"],
            participant_id=participant_id,
            json_body=body,
            extra_headers={"Idempotency-Key": idempotency_key},
            # 202 is the documented intake status; accept 200/201 too rather
            # than treating a successful send as a failure over a status code.
            expected=(200, 201, 202),
        )

        provider_id = (
            data.get("providerDocumentId")
            or data.get("documentId")
            or data.get("id")
            or ""
        )
        msg.write(
            {
                # 202 is intake, NOT delivery proof — the status cron promotes
                # this to 'done' once the network confirms delivery.
                "state": "sent",
                "blocking_level": False,
                "error_message": False,
                "provider_interchange_id": provider_id or False,
            }
        )
        _logger.info(
            "ePošťák accepted %s as %s (%s)", msg.name, provider_id, cfg["mode"]
        )
        return True

    # ------------------------------------------------------------------
    # Transport: poll inbound
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Inbound health
    # ------------------------------------------------------------------
    #
    # Sending reports itself: a failure lands on the invoice's edi.message and
    # the user sees it. Receiving had NO user-facing signal at all -- the base
    # _poll_provider swallows any exception from _poll_inbound into the log, and
    # a misconfiguration here returned an empty result and said nothing. So with
    # the Firm ID blank, sending failed loudly while receiving quietly stopped.
    # These three parameters are what Settings reads to show otherwise.

    PARAM_POLL_AT = "epostak.inbound.last_poll"
    PARAM_POLL_OK = "epostak.inbound.last_ok"
    PARAM_POLL_ERROR = "epostak.inbound.last_error"
    PARAM_POLL_COUNT = "epostak.inbound.last_count"
    PARAM_POLL_STREAK = "epostak.inbound.fail_streak"
    PARAM_POLL_ACTIVITY_AFTER = "epostak.inbound.fail_activity_after"

    #: Marker on the activity we raise, so we recognise our own and never
    #: stack a second one. Matched on, so it must not be translated.
    POLL_ACTIVITY_MARKER = "[ePostak-inbound]"
    DEFAULT_ACTIVITY_AFTER = 3

    def _record_poll(self, error=None, count=0):
        """Remember how the last inbound poll went, for Settings to show.

        Written even on the failure paths, which is the whole point: a stale
        "last OK" timestamp is the only evidence a user gets that receiving has
        stopped. Never raises -- this is bookkeeping around a poll that may
        already be failing.
        """
        try:
            ICP = self.env["ir.config_parameter"].sudo()
            now = fields.Datetime.to_string(fields.Datetime.now())
            ICP.set_param(self.PARAM_POLL_AT, now)
            ICP.set_param(self.PARAM_POLL_ERROR, error or "")
            if error:
                streak = int(ICP.get_param(self.PARAM_POLL_STREAK, "0") or "0") + 1
                ICP.set_param(self.PARAM_POLL_STREAK, str(streak))
                self._poll_failure_activity(error, streak)
                return
            ICP.set_param(self.PARAM_POLL_OK, now)
            ICP.set_param(self.PARAM_POLL_COUNT, str(count))
            ICP.set_param(self.PARAM_POLL_STREAK, "0")
            self._poll_failure_resolved()
        except Exception:  # noqa: BLE001
            _logger.exception("Could not record the ePošťák inbound poll state")

    def _poll_activity_anchor(self):
        """What the failure activity hangs on: our own company partner.

        ``res.company`` carries no activity mixin, and there is no document to
        attach to — a poll that fetches nothing has produced no record. The
        company partner is both a valid target and the right subject: it *is*
        the Peppol participant that is not receiving.
        """
        return self.env.company.partner_id

    def _poll_activity_user(self):
        """Who gets told. An EDI manager if there is one, else an EDI user,
        else the admin — never nobody, which would make the activity invisible
        and defeat the point."""
        Users = self.env["res.users"].sudo()
        for group in ("edi_base.group_edi_manager", "edi_base.group_edi_user"):
            grp = self.env.ref(group, raise_if_not_found=False)
            if grp and grp.user_ids:
                return grp.user_ids[0]
        return (
            self.env.ref("base.user_admin", raise_if_not_found=False)
            or Users.browse(SUPERUSER_ID)
        )

    def _poll_failure_activity(self, error, streak):
        """Raise ONE to-do once inbound has failed repeatedly.

        The Settings line already records every failure, but it only reaches
        someone who opens Settings and notices the date is old. This is the part
        that reaches a person who never looks.

        Deliberately not on the first failure: a single blip is normal and an
        activity per poll would train everyone to ignore them. Deliberately only
        one: it is re-used until the poll succeeds again, then closed by
        :meth:`_poll_failure_resolved`.
        """
        ICP = self.env["ir.config_parameter"].sudo()
        after = int(
            ICP.get_param(self.PARAM_POLL_ACTIVITY_AFTER, self.DEFAULT_ACTIVITY_AFTER)
            or self.DEFAULT_ACTIVITY_AFTER
        )
        if after <= 0 or streak < after:
            return
        anchor = self._poll_activity_anchor()
        if not anchor:
            return
        Activity = self.env["mail.activity"].sudo()
        model_id = self.env["ir.model"]._get_id(anchor._name)
        existing = Activity.search([
            ("res_model_id", "=", model_id),
            ("res_id", "=", anchor.id),
            ("summary", "like", self.POLL_ACTIVITY_MARKER),
        ], limit=1)
        note = _(
            "ePošťák inbound polling has failed %(streak)s times in a row, so "
            "incoming documents are not being received.\n\n"
            "Last error: %(error)s\n\n"
            "Check Settings ▸ EDI ▸ ePošťák — 'Last inbound poll' shows the "
            "same detail, and 'Poll inbound now' retries immediately.",
            streak=streak,
            error=(error or "")[:500],
        )
        if existing:
            # Keep one activity and let it carry the current count, rather than
            # adding one per failed poll.
            existing.write({"note": note})
            return
        try:
            Activity.create({
                "res_model_id": model_id,
                "res_id": anchor.id,
                "activity_type_id": self.env.ref(
                    "mail.mail_activity_data_todo").id,
                "summary": "%s %s" % (
                    self.POLL_ACTIVITY_MARKER,
                    _("Incoming ePošťák documents are not arriving"),
                ),
                "note": note,
                "user_id": self._poll_activity_user().id,
                "date_deadline": fields.Date.context_today(self),
            })
            _logger.warning(
                "ePošťák: raised an inbound-failure activity after %s "
                "consecutive failures", streak,
            )
        except Exception:  # noqa: BLE001
            _logger.exception("Could not raise the ePošťák inbound activity")

    def _poll_failure_resolved(self):
        """Close our activity once documents are arriving again.

        Without this the admin is left with a stale to-do about a problem that
        fixed itself, which is how people learn to ignore them.
        """
        anchor = self._poll_activity_anchor()
        if not anchor:
            return
        Activity = self.env["mail.activity"].sudo()
        open_ones = Activity.search([
            ("res_model_id", "=", self.env["ir.model"]._get_id(anchor._name)),
            ("res_id", "=", anchor.id),
            ("summary", "like", self.POLL_ACTIVITY_MARKER),
        ])
        if open_ones:
            open_ones.action_feedback(
                feedback=_("Inbound polling succeeded again; closed automatically.")
            )

    def _poll_inbound(self):
        """Pull new documents out of the participant mailbox.

        Two calls per document: the listing carries metadata only, the payload
        comes from ``GET /document/receive/{id}``. Documents whose payload
        cannot be fetched are simply left unacknowledged — they stay RECEIVED
        and reappear on the next poll rather than being silently dropped.

        Every exit records the outcome through :meth:`_record_poll`.
        """
        try:
            cfg = self._validate_config()
        except UserError as e:
            # ERROR, not warning: a configuration fault is never transient, and
            # this one stops inbound completely. It is also the exact shape of
            # the ticket that prompted this -- an integrator key with no Firm ID.
            _logger.error("ePošťák inbound poll skipped, not configured: %s", e)
            self._record_poll(error=str(e))
            return {"messages": [], "has_more": False}

        participant_id = self._epostak_own_participant_id()
        messages = []
        page_token = None
        has_more = False

        for _page in range(cfg["max_pages"]):
            params = {"status": "RECEIVED", "limit": cfg["limit"]}
            if page_token:
                params["pageToken"] = page_token
            try:
                listing = self._request(
                    cfg,
                    "GET",
                    "%s/document/receive" % cfg["sapi_url"],
                    participant_id=participant_id,
                    params=params,
                )
            except EpostakApiError as e:
                _logger.exception("ePošťák inbound listing failed")
                self._record_poll(error=str(e), count=len(messages))
                # Hand back what we already fetched and stop. has_more stays
                # False on purpose: the connector re-returns payloads the base
                # may discard as duplicates, so re-triggering the cron on a
                # persistent listing failure would spin instead of draining.
                return {"messages": messages, "has_more": False}

            documents = listing.get("documents") or listing.get("items") or []
            for doc in documents:
                package = self._fetch_inbound_document(cfg, participant_id, doc)
                if package:
                    messages.append(package)

            page_token = listing.get("nextPageToken") or listing.get("next_cursor")
            if not page_token:
                break
        else:
            # Page budget exhausted with a cursor still open — let the base
            # re-trigger the cron for the remainder.
            has_more = bool(page_token)

        self._record_poll(count=len(messages))
        return {"messages": messages, "has_more": has_more}

    def _fetch_inbound_document(self, cfg, participant_id, doc):
        """Fetch one inbound document's UBL and shape it as a base package."""
        document_id = doc.get("documentId") or doc.get("id")
        if not document_id:
            _logger.warning("ePošťák inbound entry without a document id: %s", doc)
            return None
        try:
            detail = self._request(
                cfg,
                "GET",
                # Quoted: the id is echoed from the provider's listing, and
                # a stray '/' or '..' in it would rewrite the endpoint path.
                "%s/document/receive/%s"
                % (cfg["sapi_url"], quote(str(document_id), safe="")),
                participant_id=participant_id,
            )
        except EpostakApiError:
            _logger.exception(
                "ePošťák: could not fetch inbound document %s; leaving it "
                "unacknowledged for the next poll",
                document_id,
            )
            return None

        payload = detail.get("payload") or ""
        if not payload:
            # Not acknowledged on purpose — acknowledging what we did not
            # store would lose the document. It therefore reappears on every
            # poll, so log loudly enough that someone acts on it.
            _logger.error(
                "ePošťák inbound document %s carries no payload; it stays "
                "RECEIVED and will be re-fetched on every poll until ePošťák "
                "returns a payload for it.",
                document_id,
            )
            return None
        metadata = detail.get("metadata") or {}
        # The business document id (invoice number) if the API gives one;
        # otherwise the provider handle, which is at least traceable.
        external_id = metadata.get("documentId") or document_id
        return {
            "name": "%s.xml" % document_id,
            "xml_content": payload,
            "raw_id": document_id,
            "external_id": external_id,
        }

    # ------------------------------------------------------------------
    # Transport: acknowledge
    # ------------------------------------------------------------------

    def _acknowledge_inbound(self, raw_id):
        """Mark a document processed so it leaves the RECEIVED queue.

        This is a *local* acknowledgement only — it sends no transport receipt
        to the sender. A Peppol MLR, if the deployment sends one, is an
        ordinary outbound document.
        """
        from odoo.addons.edi_base.exceptions import RetryableJobError

        if not raw_id:
            return True
        try:
            cfg = self._validate_config()
        except UserError:
            return True
        try:
            self._request(
                cfg,
                "POST",
                "%s/document/receive/%s/acknowledge"
                % (cfg["sapi_url"], quote(str(raw_id), safe="")),
                participant_id=self._epostak_own_participant_id(),
                # 404 means it is already gone from the queue — the outcome we
                # wanted. 409 likewise: another worker acknowledged it.
                expected=(200, 204, 404, 409),
            )
        except EpostakApiError as e:
            if e.retryable:
                raise RetryableJobError(str(e)) from e
            _logger.error("ePošťák acknowledge failed for %s: %s", raw_id, e)
            return False
        return True

    # ------------------------------------------------------------------
    # Outbound delivery status (Enterprise API, polled by cron)
    # ------------------------------------------------------------------

    def _query_status(self, message_records=None):
        """Resolve 'sent' messages to delivered or failed.

        ``POST /document/send`` returning 202 is intake, not delivery, so a
        message sits in 'sent' until this cron sees a terminal status. Runs on
        the Enterprise base URL; a key without ``documents:read`` there simply
        cannot track delivery, so a refusal disables tracking for the run
        instead of filling the log every 30 minutes.
        """
        if message_records is None:
            message_records = self.env["edi.message"].search(
                [
                    ("provider", "=", "epostak"),
                    ("direction", "=", "out"),
                    ("state", "=", "sent"),
                    ("provider_interchange_id", "!=", False),
                ],
                limit=500,
            )
        if not message_records:
            return

        by_mode = {}
        for msg in message_records:
            by_mode.setdefault(msg._epostak_mode(), self.env["edi.message"])
            by_mode[msg._epostak_mode()] |= msg

        for mode, msgs in by_mode.items():
            try:
                cfg = self._validate_config(mode=mode)
            except UserError:
                continue
            if not cfg["status_tracking"]:
                continue
            self._query_status_for_mode(cfg, msgs)

    def _query_status_for_mode(self, cfg, msgs):
        for msg in msgs:
            # Address as the company that sent the document, not as whichever
            # company the cron user happens to default to.
            participant_id = self._epostak_own_participant_id(
                msg.company_id or self.env.company
            )
            try:
                data = self._request(
                    cfg,
                    "GET",
                    "%s/documents/%s/status"
                    % (
                        cfg["api_url"],
                        quote(str(msg.provider_interchange_id), safe=""),
                    ),
                    participant_id=participant_id,
                )
            except EpostakApiError as e:
                if e.status in (401, 403):
                    _logger.warning(
                        "ePošťák status tracking is not available with these "
                        "credentials (%s); skipping this run.", e
                    )
                    return
                _logger.info(
                    "ePošťák status query failed for %s: %s", msg.name, e
                )
                continue
            self._apply_status(msg, data)

    def _apply_status(self, msg, data):
        # Coerced and stripped: the two API surfaces disagree on case, and a
        # terminal status that fails to match would leave a delivered invoice
        # in 'sent' for ever (or a rejected one looking fine).
        status = str(data.get("status") or "").strip().lower()
        if status in STATUS_DONE:
            msg.write(
                {
                    "state": "done",
                    "blocking_level": False,
                    "error_message": False,
                }
            )
        elif status in STATUS_ERROR:
            reason = self._sanitise(
                data.get("statusReason")
                or data.get("errorMessage")
                or data.get("detail")
                or ""
            )
            msg.write(
                {
                    "state": "error",
                    "blocking_level": "error",
                    "error_message": " ".join(
                        filter(None, (_("ePošťák status: %s", status), reason))
                    ),
                }
            )
        # queued / sent (and anything unrecognised) → leave as 'sent'.

    # ------------------------------------------------------------------
    # Participant capability lookup (Enterprise API)
    # ------------------------------------------------------------------

    def _list_firms(self):
        """The firms this credential may act for.

        Returns ``[{'id', 'name', 'peppol_id', 'peppol_status'}, ...]``. The
        Peppol id is what makes the answer usable: an integrator acting for
        several firms picks the right one by matching its own Peppol address,
        where two firms can easily share a similar name.

        Deliberately does NOT go through ``_validate_config``: this call is how
        a deployment finds the firm id that validation insists on, so requiring
        one first would be a closed loop. It also must not carry ``X-Firm-Id``
        -- it is scoped to the credential, not to one firm.

        Enterprise API only. Not restricted to integrator keys: verified
        against the sandbox 2026-10-01, a firm key returns its own single firm.
        The gate is the ``firms:manage`` scope, not the shape of the key.
        """
        cfg = self._get_sapi_config()
        if not cfg["client_id"] or not cfg["client_secret"]:
            raise UserError(
                _(
                    "ePošťák credentials are not configured for the %s "
                    "environment.",
                    cfg["mode"],
                )
            )
        # /firms is gated on firms:manage, which our ordinary token does not
        # carry -- the default scope is documents:* by design, since least
        # privilege is right for the credential that sends invoices all day.
        # Mint a separate, narrower token just for this call. Verified against
        # the sandbox 2026-10-01: without it the endpoint answers 403
        # INSUFFICIENT_SCOPE naming exactly this scope.
        cfg = dict(cfg, scope=FIRMS_SCOPE)
        return self._parse_firms(
            self._request(cfg, "GET", "%s/firms" % cfg["api_url"])
        )

    @staticmethod
    def _parse_firms(data):
        """Shape the /firms body into our own rows.

        Split from the HTTP call so the parsing is testable against a captured
        response rather than only against a live integrator key, which we do
        not have one of here.
        """
        rows = data if isinstance(data, list) else (
            data.get("firms") or data.get("items") or []
        )
        firms = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            firm_id = row.get("id") or row.get("firmId") or row.get("firm_id")
            if firm_id:
                firms.append({
                    "id": str(firm_id),
                    "name": str(row.get("name") or row.get("companyName") or ""),
                    # IČO is what a Slovak user recognises their own company by;
                    # the Peppol id is DIČ-derived and the name may be a
                    # sandbox variant, so dropping this left no reliable way to
                    # match a firm to the company in front of you.
                    "ico": str(row.get("ico") or ""),
                    "peppol_id": str(row.get("peppolId") or ""),
                    "peppol_status": str(row.get("peppolStatus") or ""),
                })
        return firms

    def _check_capabilities(self, participant_id, document_types=None):
        """Ask the Peppol directory whether a participant can receive a type.

        Returns the raw API answer ({'found', 'accepts', 'networkReady', ...}).
        Cheap preflight against the commonest support case — a counterparty
        whose EAS/endpoint is wrong or who is not registered at all, which
        otherwise only surfaces as a 422 at send time.
        """
        cfg = self._validate_config()
        participant_id = self._epostak_normalize_participant(participant_id)
        scheme, _sep, identifier = participant_id.partition(":")
        if not scheme or not identifier:
            raise UserError(
                _(
                    "%s is not a Peppol participant identifier (expected "
                    "scheme:value, e.g. 0245:2121576435).",
                    participant_id or "''",
                )
            )
        body = {"participant": {"scheme": scheme, "identifier": identifier}}
        if document_types:
            body["documentTypes"] = list(document_types)
        return self._request(
            cfg,
            "POST",
            "%s/peppol/capabilities" % cfg["api_url"],
            participant_id=self._epostak_own_participant_id(),
            json_body=body,
        )
