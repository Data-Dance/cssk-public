# -*- coding: utf-8 -*-
"""Client for the CA EET 2.0 certificate-renewal API (``caeetapi_jwt.yml``,
OpenAPI 3.1, published by the Financial Administration on 2026-09-30).

Free of any Odoo import, like :mod:`eet2_client`, so it can be unit-tested
standalone.  Depends on ``cryptography`` and ``requests`` only.

The API renews a *pokladní certifikát* that is still valid:

* ``POST /request/renew``                 -> 201 ``{"reqId": <uuid>}``
* ``GET  /request/{reqId}/status``        -> ``INPROCESS`` (with
  ``pollAfterSeconds`` and a ``Retry-After`` header), ``ISSUED``,
  ``DELIVERING``, ``FINISHED`` or ``REJECTED`` (with ``rejectedReason``)
* ``POST /request/{reqId}/claim-download`` -> the new PKCS#12 (base64), its
  8-character password and the certificate metadata; allowed in ``ISSUED`` and
  ``DELIVERING`` and re-callable until the download is acknowledged or 30 days
  after issue
* ``POST /request/{reqId}/ack-download``  -> 204; the server then deletes the
  PKCS#12 and the request becomes ``FINISHED``
* ``GET  /request/not-finished``          -> the open ``reqId``s of the EIC

Authorisation is a JWS compact token in ``Authorization: Bearer``: JOSE header
``{"alg": "RS256", "typ": "JWT", "x5t#S256": base64url(SHA-256(DER(cert)))}``,
payload ``{}`` is enough, signature RS256 (PKCS#1 v1.5 + SHA-256) made with the
private key of the certificate being renewed.  No ``x5c``: the CA finds the
certificate by its thumbprint.

The claim response is sensitive.  Nothing here logs request or response bodies.
"""
import base64
import binascii
import json
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

HOSTS = {
    "test": "https://ca.test.caeet.gov.cz/api",   # "testovací prostředí"
    "zkus": "https://ca.zkus.caeet.gov.cz/api",   # "zkušební prostředí"
    "prod": "https://ca.caeet.gov.cz/api",        # "produkční prostředí"
}
DEFAULT_TIMEOUT = 20

# Request states as the API spells them.
INPROCESS, ISSUED, DELIVERING, FINISHED, REJECTED = (
    "INPROCESS", "ISSUED", "DELIVERING", "FINISHED", "REJECTED")
CLAIMABLE_STATES = (ISSUED, DELIVERING)


# --- errors -----------------------------------------------------------------
class CaeetError(Exception):
    """Any failure talking to the CA; ``status`` is the HTTP status (0 when the
    request never got an answer), ``code``/``message`` the API's ErrorDTO."""

    def __init__(self, message, status=0, code=None, additional_info=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.additional_info = additional_info

    def __str__(self):
        parts = [super().__str__()]
        if self.status:
            parts.append("HTTP %s" % self.status)
        if self.code is not None:
            parts.append("code %s" % self.code)
        if self.additional_info:
            parts.append(str(self.additional_info))
        return " / ".join(parts)


class CaeetInputError(CaeetError):
    """400 - the request did not match the API's expectations."""


class CaeetAuthError(CaeetError):
    """401 - the JWT was refused (expired/revoked certificate, bad signature)."""


class CaeetNotFound(CaeetError):
    """404 - unknown reqId."""


class CaeetConflict(CaeetError):
    """409 - the request is not in a state that allows this call."""


class CaeetRateLimited(CaeetError):
    """429 - too many requests; try again later (``retry_after`` seconds)."""

    def __init__(self, message, retry_after=None, **kw):
        super().__init__(message, **kw)
        self.retry_after = retry_after


class CaeetServerError(CaeetError):
    """5xx - the CA itself failed; try again later."""


class CaeetMalformed(CaeetError):
    """A 2xx answer whose body is not what the spec promises."""


_ERRORS = {400: CaeetInputError, 401: CaeetAuthError, 404: CaeetNotFound,
           409: CaeetConflict, 429: CaeetRateLimited}


# --- JWT --------------------------------------------------------------------
def _retry_after_seconds(value):
    """``Retry-After`` as seconds, whether it came as a delay or an HTTP-date."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return int(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(int((when - datetime.now(timezone.utc)).total_seconds()), 0)


def _json(response, *required):
    """The JSON body of a 2xx answer, or :class:`CaeetMalformed`."""
    try:
        body = response.json()
    except ValueError as exc:
        raise CaeetMalformed("CA EET answered with no JSON body",
                             status=response.status_code) from exc
    if not isinstance(body, dict):
        raise CaeetMalformed("CA EET answered with an unexpected body",
                             status=response.status_code)
    missing = [key for key in required if not body.get(key)]
    if missing:
        raise CaeetMalformed("CA EET answer lacks %s" % ", ".join(missing),
                             status=response.status_code)
    return body


def _b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def thumbprint_s256(cert):
    """``x5t#S256`` of an ``x509.Certificate``: base64url(SHA-256(DER))."""
    der = cert.public_bytes(serialization.Encoding.DER)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(der)
    return _b64url(digest.finalize())


def make_jwt(private_key, cert, claims=None):
    """JWS compact serialisation signed RS256 with ``private_key``.

    ``cert`` is the X.509 certificate matching the key: its thumbprint goes
    into the ``x5t#S256`` header, which is how the CA identifies the caller.
    ``claims`` defaults to ``{}``, the minimum the API accepts.
    """
    header = {"alg": "RS256", "typ": "JWT", "x5t#S256": thumbprint_s256(cert)}
    signing_input = ".".join([
        _b64url(json.dumps(header, separators=(",", ":")).encode()),
        _b64url(json.dumps(claims or {}, separators=(",", ":")).encode()),
    ])
    signature = private_key.sign(
        signing_input.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    return signing_input + "." + _b64url(signature)


# --- client -----------------------------------------------------------------
class CaeetClient:
    """One certificate's view of the renewal API.

    ``certificate`` is an :class:`eet2_client.Certificate` (anything with
    ``.private_key`` and ``.cert``).  A fresh JWT is minted per call; the token
    carries no expiry, so there is nothing to cache.
    """

    def __init__(self, base_url, certificate, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.certificate = certificate
        self.timeout = timeout

    # -- transport --
    def _headers(self):
        token = make_jwt(self.certificate.private_key, self.certificate.cert)
        return {"Authorization": "Bearer " + token, "Accept": "application/json"}

    def _request(self, method, path, expect=(200,)):
        url = self.base_url + path
        try:
            response = requests.request(
                method, url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as exc:
            raise CaeetError("CA EET unreachable: %s" % exc.__class__.__name__) from exc
        if response.status_code in expect:
            return response
        self._raise(response, method, path)

    @staticmethod
    def _raise(response, method, path):
        try:
            body = response.json() or {}
        except ValueError:
            body = {}
        message = body.get("message") or "%s %s failed" % (method, path)
        kw = dict(status=response.status_code, code=body.get("code"),
                  additional_info=body.get("additionalInfo"))
        if response.status_code == 429:
            raise CaeetRateLimited(
                message, retry_after=_retry_after_seconds(response.headers.get("Retry-After")),
                **kw)
        cls = _ERRORS.get(response.status_code)
        if cls is None:
            cls = CaeetServerError if response.status_code >= 500 else CaeetError
        raise cls(message, **kw)

    # -- endpoints --
    def renew(self):
        """Ask for a follow-up certificate; returns the request id."""
        return _json(self._request("POST", "/request/renew", expect=(201,)), "reqId")["reqId"]

    def status(self, req_id):
        """``{"state": …, "poll_after": seconds|None, "rejected_reason": …}``.

        ``poll_after`` is the larger of the body's ``pollAfterSeconds`` and the
        ``Retry-After`` header, when either is present.
        """
        response = self._request("GET", "/request/%s/status" % req_id)
        body = _json(response, "state")
        poll_after = body.get("pollAfterSeconds")
        header = _retry_after_seconds(response.headers.get("Retry-After"))
        if header is not None:
            poll_after = max(header, poll_after or 0)
        return {
            "state": body.get("state"),
            "poll_after": poll_after,
            "rejected_reason": body.get("rejectedReason"),
        }

    def claim_download(self, req_id):
        """The issued PKCS#12: ``{"p12": bytes, "password": str, "certificate": {…}}``.

        Allowed while the request is ISSUED or DELIVERING.  Call
        :meth:`ack_download` only once the new certificate has been verified
        and installed: after the ack the CA deletes its copy for good.
        """
        body = _json(self._request("POST", "/request/%s/claim-download" % req_id),
                     "pkcs12", "password")
        try:
            p12 = base64.b64decode(body["pkcs12"], validate=True)
        except (binascii.Error, TypeError) as exc:
            raise CaeetMalformed("CA EET returned a PKCS#12 that is not base64",
                                 status=200) from exc
        return {
            "p12": p12,
            "password": body["password"],
            "certificate": body.get("certificate") or {},
        }

    def ack_download(self, req_id):
        """Confirm the download; the CA discards the PKCS#12 and the password."""
        self._request("POST", "/request/%s/ack-download" % req_id, expect=(204,))

    def not_finished(self):
        """Open request ids (INPROCESS / ISSUED / DELIVERING) for this EIC."""
        body = _json(self._request("GET", "/request/not-finished"))
        return list(body.get("data") or [])
