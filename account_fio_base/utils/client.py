# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Fio banka REST client.

Reference: *FIO API BANKOVNICTVÍ*, version 1.9 of 16 October 2025, §3, §5.2, §6.

Two properties of this API shape everything below.

**The token is in the URL path.** ``https://fioapi.fio.cz/v1/rest/periods/{token}/…``
means the credential ends up in every ``requests`` exception message, every
proxy log and every traceback Odoo writes to its log or a record's chatter.
So the client never lets a raw URL escape: :func:`mask_token` is applied to
every message it raises or logs, and it also masks token-shaped path segments
it did not itself produce.

**A token may be used once per 30 seconds**, for reading *or* writing, whatever
the format (§5.2, §8.3). This module does not sleep — throttling belongs to the
caller that owns the persistent "last call" timestamp. What it does is turn the
resulting ``409`` into :class:`FioRateLimited` rather than a bare HTTP error.

Pure Python: no Odoo imports, so the whole protocol surface is unit-testable
without a database.
"""

import logging
import re
from datetime import date

import requests

_logger = logging.getLogger(__name__)

FIO_BASE_URL = "https://fioapi.fio.cz/v1/rest"

#: Fio is slow on wide date ranges; 60 s is comfortably above what a month of
#: movements takes and well below any sane worker timeout.
REQUEST_TIMEOUT = 60

#: §5.2 — "Doporučený nejmenší interval dotazu na stejný token je 30 sekund."
#: Enforced by the caller; exported here so there is one number, not three.
MIN_CALL_INTERVAL = 30

#: §8.6 — the bank refuses to serve more than this many movements at once.
MAX_MOVEMENTS_PER_CALL = 50000

#: §6.1 — errorCode 13, "příliš dlouhý soubor".
MAX_UPLOAD_BYTES = 2 * 1024 * 1024

DOWNLOAD_FORMATS = ("xml", "json", "gpc", "csv", "ofx", "sta", "cba_xml", "sba_xml", "pdf")
UPLOAD_TYPES = ("xml", "abo", "pain001_xml", "pain008_xml")

# A Fio token is 64 characters; accept 16+ so a truncated or test token is
# masked too. Applied to whole URLs, hence the surrounding path separators.
_TOKEN_IN_PATH_RE = re.compile(r"(/rest/[A-Za-z0-9-]+/)[A-Za-z0-9]{16,}")


class FioError(Exception):
    """Base class for every Fio API failure."""


class FioTransportError(FioError):
    """Network-level failure: DNS, TLS, connection reset, timeout."""


class FioUploadUncertain(FioTransportError):
    """A payment-order upload failed *after* the request left the process.

    The bank may or may not have created the batch. Never retried
    automatically — see ``account_payment_fio``'s ``unknown`` state.
    """


class FioAuthError(FioError):
    """HTTP 500 — §8.4 says this means a missing, expired or inactive token."""


class FioNotFound(FioError):
    """HTTP 404 — §8.2, malformed request path."""


class FioRateLimited(FioError):
    """HTTP 409 — §8.3, less than 30 s since the previous call on this token."""


class FioTooMuchData(FioError):
    """HTTP 413 — §8.6, more than 50 000 movements in the requested range."""


class FioHistoryLocked(FioError):
    """HTTP 422 — §8.7, data older than 90 days without the IB unlock."""


class FioResponseError(FioError):
    """Any other non-200 response."""


def mask_token(text, token=None):
    """Replace credentials in ``text`` with ``***``.

    Masks the token we know about, then any token-shaped path segment, so a
    message assembled by ``requests`` from a URL we did not build is covered
    too.
    """
    if text is None:
        return ""
    text = str(text)
    if token:
        text = text.replace(token, "***")
    return _TOKEN_IN_PATH_RE.sub(r"\1***", text)


def _fmt_date(value):
    """``date`` or ``'YYYY-MM-DD'`` → ``'YYYY-MM-DD'``."""
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


class FioClient:
    """Thin, stateless wrapper over the Fio REST endpoints.

    :param token: the 64-character token from internet banking (§2). One token
        is bound to one account, and to one right set (read, or read + submit).
    :param session: optional ``requests.Session``; injected by the tests.
    """

    def __init__(self, token, base_url=FIO_BASE_URL, timeout=REQUEST_TIMEOUT,
                 session=None):
        if not token:
            raise FioAuthError("No Fio token configured.")
        self.token = token
        self.base_url = (base_url or FIO_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = session or requests

    # ------------------------------------------------------------------
    # transport
    # ------------------------------------------------------------------

    def _url(self, *parts):
        return "/".join([self.base_url] + [str(p).strip("/") for p in parts])

    def _mask(self, text):
        return mask_token(text, self.token)

    def _check(self, response, context):
        """Map the documented HTTP statuses (§8) onto named exceptions."""
        status = response.status_code
        if status == 200:
            return response.content
        if status == 409:
            raise FioRateLimited(
                "Fio allows one call per token every %s seconds. Wait and retry "
                "(%s)." % (MIN_CALL_INTERVAL, context)
            )
        if status == 413:
            raise FioTooMuchData(
                "Fio refuses to return more than %s movements at once. Narrow "
                "the date range (%s)." % (MAX_MOVEMENTS_PER_CALL, context)
            )
        if status == 422:
            raise FioHistoryLocked(
                "Fio serves data older than 90 days only after you unlock the "
                "full history for this token in internet banking (Nastavení → "
                "API → padlock). The unlock lasts 10 minutes (%s)." % context
            )
        if status == 500:
            raise FioAuthError(
                "Fio rejected the token as unknown, expired or inactive. Check "
                "it in internet banking (%s)." % context
            )
        if status == 404:
            raise FioNotFound("Fio does not know this request (%s)." % context)
        raise FioResponseError(
            "Fio returned HTTP %s (%s): %s"
            % (status, context, self._mask(response.text[:500]))
        )

    def _get(self, *parts, **kwargs):
        url = self._url(*parts)
        context = kwargs.pop("context", parts[0] if parts else "")
        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            # str(exc) carries the URL, and the URL carries the token.
            raise FioTransportError(
                "Could not reach Fio: %s" % self._mask(exc)
            ) from None
        return self._check(response, context)

    # ------------------------------------------------------------------
    # export (§5)
    # ------------------------------------------------------------------

    def periods(self, date_from, date_to, fmt="xml"):
        """Movements in a closed date range. Idempotent — safe to re-run."""
        return self._get(
            "periods", self.token, _fmt_date(date_from), _fmt_date(date_to),
            "transactions.%s" % fmt,
            context="movements %s..%s" % (_fmt_date(date_from), _fmt_date(date_to)),
        )

    def by_id(self, year, number, fmt="xml"):
        """One official numbered statement (§5.2.2)."""
        return self._get(
            "by-id", self.token, year, number, "transactions.%s" % fmt,
            context="official statement %s/%s" % (number, year),
        )

    def last(self, fmt="xml"):
        """Movements since the server-side bookmark, which this call advances.

        The bookmark lives on the token, so two consumers sharing one token
        silently steal each other's movements (§5.2.3).
        """
        return self._get(
            "last", self.token, "transactions.%s" % fmt,
            context="movements since bookmark",
        )

    def last_statement(self):
        """``(year, number)`` of the newest official statement (§5.2.6)."""
        raw = self._get(
            "lastStatement", self.token, "statement",
            context="last statement number",
        )
        text = raw.decode("utf-8", "replace").strip()
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise FioResponseError(
                "Unexpected lastStatement response: %r" % text[:100]
            )
        return int(parts[0]), int(parts[1])

    def set_last_id(self, movement_id):
        """Move the bookmark to a movement id (§5.2.4). Rarely correct."""
        return self._get(
            "set-last-id", self.token, movement_id, "",
            context="set bookmark to movement %s" % movement_id,
        )

    def set_last_date(self, value):
        """Move the bookmark to a date (§5.2.4). Rarely correct."""
        return self._get(
            "set-last-date", self.token, _fmt_date(value), "",
            context="set bookmark to %s" % _fmt_date(value),
        )

    def merchant(self, date_from, date_to, fmt="xml"):
        """Card transactions from POS terminals / payment gateway (§5.2.5)."""
        return self._get(
            "merchant", self.token, _fmt_date(date_from), _fmt_date(date_to),
            "transactions.%s" % fmt,
            context="merchant transactions",
        )

    # ------------------------------------------------------------------
    # import (§6)
    # ------------------------------------------------------------------

    def import_orders(self, payload, order_type="xml", filename="orders.xml",
                      lng="cs"):
        """Upload a payment-order batch. Returns the raw response XML.

        The orders arrive in the bank as an **unauthorised** batch: somebody
        with signing rights still has to confirm it in internet banking (§6).
        Nothing here moves money on its own.

        Any transport failure raises :class:`FioUploadUncertain`, *including*
        ones that look like the request never left — telling "connection
        refused" from "response lost" is not reliable enough to bet a duplicate
        payment run on, so the caller is made to check the bank instead.
        """
        if order_type not in UPLOAD_TYPES:
            raise ValueError("Unknown Fio import type %r" % order_type)
        if len(payload) > MAX_UPLOAD_BYTES:
            raise FioResponseError(
                "The payment file is %.1f MB; Fio rejects anything above 2 MB "
                "(errorCode 13). Split the payment order."
                % (len(payload) / 1024.0 / 1024.0)
            )
        url = self._url("import", "")
        try:
            response = self.session.post(
                url,
                data={"type": order_type, "token": self.token, "lng": lng},
                files={"file": (filename, payload, "text/xml")},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise FioUploadUncertain(
                "The payment file was sent to Fio but the answer was lost: %s. "
                "Check internet banking for an unauthorised batch BEFORE "
                "sending it again." % self._mask(exc)
            ) from None
        return self._check(response, "payment order upload")
