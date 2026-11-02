# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
# ``odoo.tests.BaseCase`` rather than ``unittest.TestCase``: it is the same
# plain TestCase — no database, no cursor — but its ``__init_subclass__``
# assigns the ``standard``/``at_install`` tags. Odoo's TagsSelector silently
# SKIPS any class without ``test_tags``, so a bare unittest.TestCase in a
# tests/ package never runs under ``odoo-bin --test-enable`` at all.
from odoo.tests import BaseCase as TestCase

import requests

from odoo.addons.account_fio_base.utils.client import (
    FioAuthError,
    FioClient,
    FioHistoryLocked,
    FioNotFound,
    FioRateLimited,
    FioResponseError,
    FioTooMuchData,
    FioTransportError,
    FioUploadUncertain,
    mask_token,
)

TOKEN = "aGEMQB9Idh35fh1g51h3ekkQwyGlQaGEMQB9Idh35fh1g51h3ekkQwyGlQ123456"


class FakeResponse:
    def __init__(self, status_code=200, content=b"", text=""):
        self.status_code = status_code
        self.content = content
        self.text = text or content.decode("utf-8", "replace")


class FakeSession:
    """Records the calls and replays canned answers."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        answer = self.responses.pop(0) if self.responses else FakeResponse()
        if isinstance(answer, Exception):
            raise answer
        return answer

    def get(self, url, **kwargs):
        return self._next("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._next("POST", url, **kwargs)


def client(*responses):
    return FioClient(TOKEN, session=FakeSession(*responses))


class TestTokenMasking(TestCase):
    """Fio puts the credential in the URL path, so it leaks through tracebacks."""

    def test_masks_the_known_token(self):
        url = "https://fioapi.fio.cz/v1/rest/periods/%s/2026-01-01" % TOKEN
        self.assertNotIn(TOKEN, mask_token(url, TOKEN))

    def test_masks_an_unknown_token_shaped_segment(self):
        other = "b" * 64
        url = "https://fioapi.fio.cz/v1/rest/last/%s/transactions.xml" % other
        masked = mask_token(url, TOKEN)
        self.assertNotIn(other, masked)
        self.assertIn("/rest/last/***", masked)

    def test_transport_error_does_not_leak_the_token(self):
        api = client(requests.ConnectionError(
            "HTTPSConnectionPool: /v1/rest/periods/%s/x (timed out)" % TOKEN
        ))
        with self.assertRaises(FioTransportError) as caught:
            api.periods(date(2026, 1, 1), date(2026, 1, 2))
        self.assertNotIn(TOKEN, str(caught.exception))

    def test_http_error_body_does_not_leak_the_token(self):
        api = client(FakeResponse(503, text="down: /v1/rest/last/%s/x" % TOKEN))
        with self.assertRaises(FioResponseError) as caught:
            api.last()
        self.assertNotIn(TOKEN, str(caught.exception))

    def test_upload_failure_does_not_leak_the_token(self):
        api = client(requests.Timeout("POST /v1/rest/import/ token=%s" % TOKEN))
        with self.assertRaises(FioUploadUncertain) as caught:
            api.import_orders(b"<Import/>")
        self.assertNotIn(TOKEN, str(caught.exception))


class TestStatusMapping(TestCase):
    """§8 documents what each status actually means; none of them are generic."""

    def _raises(self, status, exception):
        api = client(FakeResponse(status, text="x"))
        with self.assertRaises(exception):
            api.periods(date(2026, 1, 1), date(2026, 1, 2))

    def test_409_is_the_rate_limit(self):
        self._raises(409, FioRateLimited)

    def test_413_is_too_many_movements(self):
        self._raises(413, FioTooMuchData)

    def test_422_is_the_locked_history(self):
        self._raises(422, FioHistoryLocked)

    def test_500_is_a_bad_token(self):
        self._raises(500, FioAuthError)

    def test_404_is_a_bad_request(self):
        self._raises(404, FioNotFound)

    def test_422_explains_the_ten_minute_unlock(self):
        api = client(FakeResponse(422, text="x"))
        with self.assertRaises(FioHistoryLocked) as caught:
            api.periods(date(2020, 1, 1), date(2020, 1, 2))
        self.assertIn("90 days", str(caught.exception))
        self.assertIn("10 minutes", str(caught.exception))


class TestUrls(TestCase):
    def test_periods(self):
        api = client(FakeResponse(200, b"<AccountStatement/>"))
        api.periods(date(2026, 1, 1), date(2026, 1, 31))
        self.assertEqual(
            api.session.calls[0][1],
            "https://fioapi.fio.cz/v1/rest/periods/%s/2026-01-01/2026-01-31/"
            "transactions.xml" % TOKEN,
        )

    def test_by_id(self):
        api = client(FakeResponse(200, b"<AccountStatement/>"))
        api.by_id(2026, 4)
        self.assertTrue(api.session.calls[0][1].endswith("/2026/4/transactions.xml"))

    def test_set_last_id_keeps_the_trailing_slash(self):
        api = client(FakeResponse(200, b""))
        api.set_last_id(1147608196)
        self.assertTrue(api.session.calls[0][1].endswith("/1147608196/"))

    def test_last_statement(self):
        api = client(FakeResponse(200, b"2026,4"))
        self.assertEqual(api.last_statement(), (2026, 4))

    def test_last_statement_rejects_junk(self):
        api = client(FakeResponse(200, b"<html>no</html>"))
        with self.assertRaises(FioResponseError):
            api.last_statement()

    def test_set_last_date(self):
        api = client(FakeResponse(200, b""))
        api.set_last_date(date(2026, 7, 27))
        self.assertTrue(api.session.calls[0][1].endswith("/2026-07-27/"))

    def test_merchant(self):
        api = client(FakeResponse(200, b"<AccountStatement/>"))
        api.merchant(date(2026, 7, 1), date(2026, 7, 31))
        self.assertIn("/merchant/", api.session.calls[0][1])
        self.assertTrue(
            api.session.calls[0][1].endswith("/2026-07-01/2026-07-31/transactions.xml")
        )

    def test_a_date_may_be_given_as_a_string(self):
        api = client(FakeResponse(200, b"<AccountStatement/>"))
        api.periods("2026-01-01", "2026-01-31")
        self.assertIn("/2026-01-01/2026-01-31/", api.session.calls[0][1])

    def test_the_format_reaches_the_url(self):
        api = client(FakeResponse(200, b"{}"))
        api.by_id(2026, 4, "json")
        self.assertTrue(api.session.calls[0][1].endswith("transactions.json"))

    def test_the_timeout_is_passed_to_every_call(self):
        api = FioClient(TOKEN, timeout=7, session=FakeSession(
            FakeResponse(200, b"<AccountStatement/>"),
        ))
        api.periods(date(2026, 1, 1), date(2026, 1, 2))
        self.assertEqual(api.session.calls[0][2]["timeout"], 7)

    def test_an_empty_200_is_returned_as_is(self):
        """A period with no movements answers 200 with a header-only body."""
        api = client(FakeResponse(200, b""))
        self.assertEqual(api.periods(date(2026, 1, 1), date(2026, 1, 2)), b"")


class TestUpload(TestCase):
    def test_multipart_fields(self):
        api = client(FakeResponse(200, b"<responseImport/>"))
        api.import_orders(b"<Import/>", "xml", "orders.xml")
        _method, url, kwargs = api.session.calls[0]
        self.assertEqual(url, "https://fioapi.fio.cz/v1/rest/import/")
        self.assertEqual(kwargs["data"]["type"], "xml")
        self.assertEqual(kwargs["data"]["token"], TOKEN)
        self.assertEqual(kwargs["files"]["file"][0], "orders.xml")

    def test_unknown_type(self):
        with self.assertRaises(ValueError):
            client().import_orders(b"<Import/>", "csv")

    def test_oversized_file_is_refused_before_sending(self):
        api = client()
        with self.assertRaises(FioResponseError):
            api.import_orders(b"x" * (2 * 1024 * 1024 + 1))
        self.assertEqual(api.session.calls, [])

    def test_a_lost_answer_is_uncertain_not_failed(self):
        """The batch may exist. Nothing here may report "not sent"."""
        api = client(requests.Timeout("read timed out"))
        with self.assertRaises(FioUploadUncertain) as caught:
            api.import_orders(b"<Import/>")
        self.assertIn("BEFORE sending it again", str(caught.exception))

    def test_connection_refused_is_also_uncertain(self):
        """Deliberately conservative: a wrong "not sent" costs a double payment."""
        api = client(requests.ConnectionError("Connection refused"))
        with self.assertRaises(FioUploadUncertain):
            api.import_orders(b"<Import/>")


class TestConstruction(TestCase):
    def test_no_token(self):
        with self.assertRaises(FioAuthError):
            FioClient("")
